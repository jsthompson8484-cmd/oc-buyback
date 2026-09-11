// POST /api/resend-label — admin re-sends the order confirmation email
// (with the shipping label / QR) to the customer. Body: { trade_in_id }.

import { buildOrderConfirmation } from "./lib/issue-emails.mjs";

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const RESEND_KEY = process.env.RESEND_API_KEY;
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

export default async (req) => {
  if (req.method !== "POST") return json(405, { error: "POST only" });
  const userToken = (req.headers.get("authorization") || "").replace(/^Bearer /, "");
  if (!userToken) return json(401, { error: "Missing auth token" });
  const who = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
    headers: { apikey: SERVICE_KEY, authorization: `Bearer ${userToken}` },
  }).then((r) => (r.ok ? r.json() : null));
  if (!who?.email || !ADMIN_EMAILS.includes(who.email.toLowerCase()))
    return json(403, { error: "Not an admin" });

  const { trade_in_id } = await req.json().catch(() => ({}));
  if (!trade_in_id) return json(400, { error: "trade_in_id required" });
  if (!RESEND_KEY) return json(503, { error: "Email is not configured (RESEND_API_KEY)" });

  const [t] = await db(`trade_ins?id=eq.${encodeURIComponent(trade_in_id)}&select=*,trade_in_items(*)`)
    .then((r) => r.json());
  if (!t) return json(404, { error: "Trade-in not found" });
  if (!t.label_url && !t.label_qr_url) return json(400, { error: "This order has no shipping label" });

  const lockedPretty = t.price_locked_until
    ? new Date(t.price_locked_until + "T12:00:00").toLocaleDateString("en-US", { month: "long", day: "numeric" })
    : "your lock date";
  const items = (t.trade_in_items || []).map((i) => ({
    brand: i.brand, device: i.model, cond: i.condition,
    price: Number(i.final_price ?? i.quoted_price), qty: i.qty,
  }));
  const { subject, html } = buildOrderConfirmation({
    orderNumber: t.order_number, firstName: t.first_name, items,
    total: Number(t.total_quote), lockedUntil: lockedPretty, payMethod: t.payment_method,
    trackUrl: `${new URL(req.url).origin}/trade-in/track`,
    labelUrl: t.label_url, qrUrl: t.label_qr_url, tracking: t.tracking_number,
    shipCarrier: t.ship_carrier || "USPS",
  });

  const sent = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { authorization: `Bearer ${RESEND_KEY}`, "content-type": "application/json" },
    body: JSON.stringify({ from: FROM, to: t.email, subject: `[Resent] ${subject}`, html,
                           reply_to: "support@ocbuyback.com" }),
  });
  if (!sent.ok) return json(502, { error: "Email send failed" });

  await db("trade_in_events", { method: "POST", body: JSON.stringify({
    trade_in_id: t.id, status: t.status,
    note: `Label email re-sent to ${t.email} by ${who.email}` }) }).catch(() => {});
  return json(200, { ok: true, to: t.email });
};

export const config = { path: "/api/resend-label" };
