// POST /api/pay-trade-in — admin sends the payout for a trade-in and marks it paid.
//
// Payment rails by method:
//   paypal -> PayPal Payouts API (PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET)
//   check  -> Lob mailed check (LOB_API_KEY / LOB_BANK_ACCOUNT_ID / LOB_FROM_ADDRESS_ID)
//   zelle / venmo / cash -> recorded as paid manually (those are sent by hand)
//
// Auth: caller must be an allow-listed admin (same check as send-issue-email).
// Body: { trade_in_id, amount? }  — amount defaults to sum of final/quoted prices.

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const ADMIN_EMAILS = (process.env.ADMIN_EMAILS || "js@neartechpartners.com")
  .split(",").map((e) => e.trim().toLowerCase());
const LOB_KEY = process.env.LOB_API_KEY;
const LOB_BANK = process.env.LOB_BANK_ACCOUNT_ID;
const LOB_FROM = process.env.LOB_FROM_ADDRESS_ID;
const PP_ID = process.env.PAYPAL_CLIENT_ID;
const PP_SECRET = process.env.PAYPAL_CLIENT_SECRET;
const PP_BASE = process.env.PAYPAL_BASE || "https://api-m.paypal.com";

const db = (path, init = {}) =>
  fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    ...init,
    headers: { apikey: SERVICE_KEY, authorization: `Bearer ${SERVICE_KEY}`,
      "content-type": "application/json", prefer: "return=representation", ...init.headers },
  });
const json = (status, body) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

async function paypalPayout(t, amount) {
  if (!PP_ID || !PP_SECRET) throw new Error("PayPal keys not configured (PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET)");
  const tok = await fetch(`${PP_BASE}/v1/oauth2/token`, {
    method: "POST",
    headers: { authorization: "Basic " + btoa(`${PP_ID}:${PP_SECRET}`),
               "content-type": "application/x-www-form-urlencoded" },
    body: "grant_type=client_credentials",
  }).then((r) => r.json());
  if (!tok.access_token) throw new Error("PayPal auth failed");
  const receiver = t.payment_detail || t.email;
  const res = await fetch(`${PP_BASE}/v1/payments/payouts`, {
    method: "POST",
    headers: { authorization: `Bearer ${tok.access_token}`, "content-type": "application/json" },
    body: JSON.stringify({
      sender_batch_header: {
        sender_batch_id: `ocb-${t.order_number}-${Date.now()}`,
        email_subject: "Your OCBuyBack payment is on the way!",
      },
      items: [{ recipient_type: "EMAIL", receiver,
        amount: { value: amount.toFixed(2), currency: "USD" },
        note: `OCBuyBack trade-in ${t.order_number}`,
        sender_item_id: t.order_number }],
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "PayPal payout failed");
  return { ref: data.batch_header?.payout_batch_id, note: `PayPal payout sent to ${receiver}` };
}

async function lobCheck(t, amount) {
  if (!LOB_KEY || !LOB_BANK) throw new Error("Lob not configured (LOB_API_KEY / LOB_BANK_ACCOUNT_ID)");
  const form = new URLSearchParams({
    description: `OCBuyBack trade-in ${t.order_number}`,
    bank_account: LOB_BANK,
    amount: amount.toFixed(2),
    memo: `Trade-in ${t.order_number}`,
    "to[name]": `${t.first_name} ${t.last_name}`,
    "to[address_line1]": t.address1,
    ...(t.address2 ? { "to[address_line2]": t.address2 } : {}),
    "to[address_city]": t.city,
    "to[address_state]": t.state,
    "to[address_zip]": t.zip,
    ...(LOB_FROM ? { from: LOB_FROM } : {}),
  });
  const res = await fetch("https://api.lob.com/v1/checks", {
    method: "POST",
    headers: { authorization: "Basic " + btoa(LOB_KEY + ":"),
               "content-type": "application/x-www-form-urlencoded" },
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Lob check failed");
  return { ref: data.id, note: `Check mailed via Lob to ${t.first_name} ${t.last_name} (expected delivery ${data.expected_delivery_date || "soon"})` };
}

export default async (req) => {
  if (req.method !== "POST") return json(405, { error: "POST only" });
  const userToken = (req.headers.get("authorization") || "").replace(/^Bearer /, "");
  const who = userToken ? await fetch(`${SUPABASE_URL}/auth/v1/user`, {
    headers: { apikey: SERVICE_KEY, authorization: `Bearer ${userToken}` },
  }).then((r) => (r.ok ? r.json() : null)) : null;
  if (!who?.email || !ADMIN_EMAILS.includes(who.email.toLowerCase()))
    return json(403, { error: "Not an admin" });

  const { trade_in_id, amount: amountIn } = await req.json().catch(() => ({}));
  if (!trade_in_id) return json(400, { error: "trade_in_id required" });

  const [t] = await db(`trade_ins?id=eq.${trade_in_id}&select=*,trade_in_items(*)`).then((r) => r.json());
  if (!t) return json(404, { error: "Trade-in not found" });
  if (t.status === "paid") return json(409, { error: "Already marked paid" });

  const amount = Number(amountIn) ||
    t.trade_in_items.reduce((a, i) => a + (Number(i.final_price ?? i.quoted_price)) * i.qty, 0) + Number(t.promo_amount || 0);
  if (!(amount > 0)) return json(400, { error: "Amount must be positive" });

  let result;
  try {
    if (t.payment_method === "paypal") result = await paypalPayout(t, amount);
    else if (t.payment_method === "check") result = await lobCheck(t, amount);
    else result = { ref: null, note: `Marked paid — ${t.payment_method} sent manually` };
  } catch (e) {
    return json(502, { error: e.message });
  }

  await db(`trade_ins?id=eq.${trade_in_id}`, {
    method: "PATCH", body: JSON.stringify({ status: "paid", total_paid: amount }),
  });
  await db("trade_in_events", {
    method: "POST",
    body: JSON.stringify({ trade_in_id, status: "paid",
      note: result.note + (result.ref ? ` — ref ${result.ref}` : "") }),
  });
  return json(200, { paid: amount, method: t.payment_method, ref: result.ref, note: result.note });
};

export const config = { path: "/api/pay-trade-in" };
