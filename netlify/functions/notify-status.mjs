// POST /api/notify-status — admin changed an order's status; email the customer.
// Body: { trade_in_id, status }
//
// The admin's status dropdown writes straight to the database, so without this
// the customer heard nothing between "order confirmed" and whatever came next.
// Only two statuses are worth an email:
//   received -> "we've got your device, inspection next"
//   paid     -> "your payment is on the way" (same copy as the Send payment button)
// Everything else returns ok:true, emailed:false so the admin can call this
// unconditionally.

import { buildReceived, buildPaymentSent } from "./lib/issue-emails.mjs";
import { sendEmail, emailConfigured } from "./lib/send-email.mjs";

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
// keep in sync with is_admin() in supabase/schema.sql
const ADMIN_EMAILS = (process.env.ADMIN_EMAILS || "js@neartechpartners.com,henry@ocbuyback.com")
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

  const { trade_in_id, status } = await req.json().catch(() => ({}));
  if (!trade_in_id || !status) return json(400, { error: "trade_in_id and status required" });
  if (!["received", "paid"].includes(status)) return json(200, { ok: true, emailed: false, reason: "no email for this status" });
  if (!emailConfigured()) return json(200, { ok: true, emailed: false, reason: "email not configured" });

  const [t] = await db(`trade_ins?id=eq.${encodeURIComponent(trade_in_id)}&select=*,trade_in_items(*)`)
    .then((r) => r.json());
  if (!t) return json(404, { error: "Trade-in not found" });
  if (t.payment_method === "cash" && status === "paid")
    return json(200, { ok: true, emailed: false, reason: "cash is handed over in person" });

  const items = (t.trade_in_items || []).map((i) => ({
    brand: i.brand, device: i.model, cond: i.condition,
    price: Number(i.final_price ?? i.quoted_price), qty: i.qty,
  }));
  const amount = Number(t.total_paid) ||
    items.reduce((a, i) => a + i.price * i.qty, 0) + Number(t.promo_amount || 0);

  const { subject, html } = status === "received"
    ? buildReceived({ orderNumber: t.order_number, firstName: t.first_name, items, total: amount })
    : buildPaymentSent({ orderNumber: t.order_number, firstName: t.first_name, amount,
                         method: t.payment_method, detail: t.payment_detail || t.email });

  const sent = await sendEmail({ to: t.email, subject, html });
  await db("trade_in_events", { method: "POST", body: JSON.stringify({
    trade_in_id: t.id, status: t.status,
    note: sent.ok ? `"${status}" email sent to ${t.email}`
                  : `⚠️ "${status}" email FAILED to ${t.email} (${sent.detail})` }) }).catch(() => {});
  return json(sent.ok ? 200 : 502, { ok: sent.ok, emailed: sent.ok, to: t.email, detail: sent.detail });
};

export const config = { path: "/api/notify-status" };
