// GET /api/track-order?order=OCB-XXXXXX&email=... — public order tracking.
// Requires BOTH the order number and the matching email so order numbers
// alone can't be enumerated.

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

const db = (path) =>
  fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    headers: { apikey: SERVICE_KEY, authorization: `Bearer ${SERVICE_KEY}` },
  });

const json = (status, body) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

const STATUS_LABELS = {
  initiated: "Order received — ship your device with the label we emailed you",
  shipped: "On the way — USPS has your package",
  delivered: "Delivered to our Brea location — check-in is next",
  received: "Device received at our Brea location",
  evaluating: "Device being evaluated",
  adjusted: "Revised offer sent — check your email",
  action_pending: "Action needed — check your email to keep things moving",
  paid: "Paid — all done!",
  returned: "Device returned to you",
  cancelled: "Order cancelled",
};

export default async (req) => {
  const url = new URL(req.url);
  const order = (url.searchParams.get("order") || "").trim().toUpperCase();
  const email = (url.searchParams.get("email") || "").trim().toLowerCase();
  if (!order || !email) return json(400, { error: "Order number and email required" });
  if (!/^[A-Z0-9-]{4,20}$/.test(order)) return json(404, { error: "No order found for that number and email" });

  // Fetch by order number only, then compare the email in JS — never put the
  // email in a pattern operator (ilike lets "%" match any address).
  const r = await db(
    `trade_ins?order_number=eq.${encodeURIComponent(order)}` +
    `&select=order_number,email,status,total_quote,total_paid,price_locked_until,tracking_number,created_at,` +
    `trade_in_items(model,brand,condition,quoted_price,qty,final_price,final_condition),` +
    `trade_in_events(status,note,created_at)`
  );
  const rows = await r.json();
  if (!rows.length || (rows[0].email || "").toLowerCase() !== email)
    return json(404, { error: "No order found for that number and email" });

  const t = rows[0];
  return json(200, {
    order_number: t.order_number,
    status: t.status,
    status_label: STATUS_LABELS[t.status] || t.status,
    total_quote: t.total_quote,
    total_paid: t.total_paid,
    price_locked_until: t.price_locked_until,
    tracking_number: t.tracking_number,
    created_at: t.created_at,
    items: t.trade_in_items,
    // history: status timeline only — event notes are internal ops notes
    // (e.g. label-purchase failures) and never belong in the public response
    history: (t.trade_in_events || [])
      .sort((a, b) => a.created_at.localeCompare(b.created_at))
      .map((h) => ({ status: h.status, note: STATUS_LABELS[h.status] || h.status, created_at: h.created_at })),
  });
};

export const config = { path: "/api/track-order" };
