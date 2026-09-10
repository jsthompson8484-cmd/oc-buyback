// POST /api/send-issue-email — admin raises an issue on a trade-in item and
// the customer gets an actionable email (iCloud/Google lock, financing,
// condition requote, or a custom issue with an optional revised price).
//
// Auth: the admin panel passes the signed-in user's Supabase access token;
// we verify it and check the email against the allowlist before doing anything.
//
// Body: { trade_in_id, item_id?, type, message?, new_condition?, new_price? }
// For type "requote": if new_price is omitted we grab the current catalog
// price for the item's variant at new_condition — the quote the site shows.

import { buildIssueEmail } from "./lib/issue-emails.mjs";

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const RESEND_KEY = process.env.RESEND_API_KEY;
const SITE_URL = process.env.SITE_URL || "https://www.ocbuyback.com";
// until ocbuyback.com is verified in Resend, only the resend.dev sender works
const FROM = process.env.EMAIL_FROM || "OCBuyBack <onboarding@resend.dev>";
const ADMIN_EMAILS = (process.env.ADMIN_EMAILS || "js@neartechpartners.com")
  .split(",").map((e) => e.trim().toLowerCase());

const db = (path, init = {}) =>
  fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    ...init,
    headers: { apikey: SERVICE_KEY, authorization: `Bearer ${SERVICE_KEY}`,
      "content-type": "application/json", prefer: "return=representation", ...init.headers },
  });

const json = (status, body) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

const TYPES = ["icloud_lock", "google_lock", "financing", "requote", "other"];

export default async (req) => {
  if (req.method !== "POST") return json(405, { error: "POST only" });

  // -- verify the caller is an allow-listed admin
  const userToken = (req.headers.get("authorization") || "").replace(/^Bearer /, "");
  if (!userToken) return json(401, { error: "Missing auth token" });
  const who = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
    headers: { apikey: SERVICE_KEY, authorization: `Bearer ${userToken}` },
  }).then((r) => (r.ok ? r.json() : null));
  if (!who?.email || !ADMIN_EMAILS.includes(who.email.toLowerCase()))
    return json(403, { error: "Not an admin" });

  let body;
  try { body = await req.json(); } catch { return json(400, { error: "Invalid JSON" }); }
  const { trade_in_id, item_id, type, message, new_condition } = body;
  let { new_price } = body;
  if (!TYPES.includes(type)) return json(400, { error: "Invalid issue type" });
  if (!trade_in_id) return json(400, { error: "trade_in_id required" });

  // -- load the trade-in + item
  const tiRes = await db(`trade_ins?id=eq.${trade_in_id}&select=*,trade_in_items(*)`);
  const [ti] = await tiRes.json();
  if (!ti) return json(404, { error: "Trade-in not found" });
  const item = item_id
    ? ti.trade_in_items.find((i) => i.id === item_id)
    : ti.trade_in_items[0];
  if (!item) return json(404, { error: "Item not found" });

  // -- requote: grab the live catalog price for the re-graded condition
  if (type === "requote") {
    if (!new_condition) return json(400, { error: "new_condition required for a requote" });
    if (new_price == null) {
      const params = new URLSearchParams({
        select: "price", category: `eq.${item.category}`, brand: `eq.${item.brand}`,
        model: `eq.${item.model}`, carrier: `eq.${item.carrier || "-"}`,
        storage: `eq.${item.storage || "-"}`, condition: `eq.${new_condition}`,
      });
      const rows = await db(`catalog_flat?${params}`).then((r) => r.json());
      new_price = rows[0]?.price;
      if (new_price == null)
        return json(409, { error: `No catalog price for ${new_condition} — enter one manually` });
    }
  }
  if (type === "other" && !message) return json(400, { error: "Describe the issue for the customer" });

  // -- create the issue with a response token
  const token = crypto.randomUUID().replace(/-/g, "") +
    Array.from(crypto.getRandomValues(new Uint8Array(8))).map((b) => b.toString(16).padStart(2, "0")).join("");
  const issueRes = await db("trade_in_issues", {
    method: "POST",
    body: JSON.stringify({
      trade_in_id, item_id: item.id, type,
      message: message || null, new_condition: new_condition || null,
      new_price: new_price ?? null, token, email_sent_at: new Date().toISOString(),
    }),
  });
  if (!issueRes.ok) return json(500, { error: "Could not create issue", detail: await issueRes.text() });
  const [issue] = await issueRes.json();

  // -- compose + send (links use the origin this request came from, so
  // staging emails link to staging and production emails to production)
  const origin = new URL(req.url).origin;
  const device = `${item.brand} ${item.model}`;
  const { subject, html } = buildIssueEmail(issue, {
    orderNumber: ti.order_number,
    firstName: ti.first_name,
    device,
    condition: item.condition,
    quotedPrice: item.quoted_price,
    respondUrl: (action) => `${origin}/api/issue-respond?token=${token}&action=${action}`,
  });

  let emailed = false;
  if (RESEND_KEY) {
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { authorization: `Bearer ${RESEND_KEY}`, "content-type": "application/json" },
      body: JSON.stringify({ from: FROM, to: ti.email, subject, html, reply_to: "support@ocbuyback.com" }),
    });
    emailed = r.ok;
    if (!r.ok) return json(502, { error: "Email send failed", detail: await r.text() });
  }

  const labels = { icloud_lock: "iCloud lock", google_lock: "Google lock",
                   financing: "carrier financing", requote: "condition requote", other: "issue" };
  await db("trade_in_events", {
    method: "POST",
    body: JSON.stringify({
      trade_in_id, status: ti.status,
      note: `${labels[type]} email sent for ${device}` +
            (new_price != null ? ` — revised offer $${new_price}` : ""),
    }),
  });
  // auto-advance the order status so the admin never has to set it by hand:
  // requote -> adjusted; any other issue -> action_pending (waiting on customer)
  const FINAL = ["paid", "returned", "cancelled"];
  const target = type === "requote" ? "adjusted" : "action_pending";
  if (!FINAL.includes(ti.status) && ti.status !== target)
    await db(`trade_ins?id=eq.${trade_in_id}`, { method: "PATCH", body: JSON.stringify({ status: target }) });

  return json(200, { issue_id: issue.id, emailed, subject });
};

export const config = { path: "/api/send-issue-email" };
