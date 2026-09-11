// POST /api/create-trade-in — creates a trade-in from the checkout page.
//
// Server-side rules:
//  - every item's price is re-verified against the catalog (client totals are never trusted)
//  - promo codes are validated + usage counted here (codes are not readable by the browser)
//  - order number is generated here
//
// Env vars (Netlify site settings):
//  SUPABASE_URL          e.g. https://xxxx.supabase.co
//  SUPABASE_SERVICE_KEY  service-role key (bypasses RLS — never exposed client-side)
//  RESEND_API_KEY        (optional for now) confirmation email
//
// TODO before launch: shipping label purchase (awaiting customer's carrier account
// details) and Twilio SMS opt-in confirmation.

import { buildOrderConfirmation } from "./lib/issue-emails.mjs";

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const RESEND_KEY = process.env.RESEND_API_KEY;
const SITE_URL = process.env.SITE_URL || "https://www.ocbuyback.com";
const FROM = process.env.EMAIL_FROM || "OCBuyBack <onboarding@resend.dev>";
const EASYPOST_KEY = process.env.EASYPOST_API_KEY;

const STORE_ADDR = { name: "OCBuyBack", street1: "1203 W Imperial Hwy", street2: "STE 103",
  city: "Brea", state: "CA", zip: "92821", country: "US", phone: "6572868274" };

// Buy a return label (customer -> store).
// USPS (default): scan-based USPSReturns product when available (billed only
//   when the customer actually ships), lithium hazmat marking, Label Broker QR.
// FedEx / UPS (game-console orders only, per Henry's cheaper heavy-parcel
//   rates): cheapest ground rate on that carrier, printable label only —
//   hazmat CLASS_9_USED_LITHIUM is a USPS option and QR codes are USPS Label
//   Broker. Falls back to USPS if the requested carrier returns no rate.
const cheapest = (rs) => rs.sort((a, b) => parseFloat(a.rate) - parseFloat(b.rate))[0];
const RATE_PICKERS = {
  USPS: (rates) => rates.find((r) => r.carrier === "USPSReturns" && r.service === "GroundAdvantageReturn")
    || cheapest(rates.filter((r) => r.carrier === "USPS")),
  FedEx: (rates) => rates.find((r) => r.carrier === "FedEx" && r.service === "FEDEX_GROUND")
    || cheapest(rates.filter((r) => r.carrier === "FedEx")),
  UPS: (rates) => cheapest(rates.filter((r) => /^UPS/.test(r.carrier) && /ground/i.test(r.service)))
    || cheapest(rates.filter((r) => /^UPS/.test(r.carrier))),
};

async function buyReturnLabel(customer, weightOz, orderNumber, shipCarrier = "USPS") {
  const ep = (path, body) => fetch(`https://api.easypost.com/v2/${path}`, {
    method: "POST",
    headers: { authorization: "Basic " + btoa(EASYPOST_KEY + ":"), "content-type": "application/json" },
    body: JSON.stringify(body),
  }).then((r) => r.json());

  const options = { print_custom_1: orderNumber };
  if (shipCarrier === "USPS") options.hazmat = "CLASS_9_USED_LITHIUM";
  const shipment = await ep("shipments", { shipment: {
    to_address: STORE_ADDR,
    from_address: { name: `${customer.first_name} ${customer.last_name}`,
      street1: customer.address1, street2: customer.address2 || undefined,
      city: customer.city, state: customer.state, zip: customer.zip, country: "US",
      phone: customer.phone },
    parcel: { weight: Math.max(Math.round(weightOz), 4) },
    options,
  }});
  if (!shipment.id) throw new Error(shipment.error?.message || "EasyPost shipment failed");
  const rates = shipment.rates || [];
  const rate = (RATE_PICKERS[shipCarrier] || RATE_PICKERS.USPS)(rates) || RATE_PICKERS.USPS(rates);
  if (!rate) throw new Error("No rate returned" +
    (shipment.messages?.length ? `: ${shipment.messages[0].message}` : ""));
  const bought = await ep(`shipments/${shipment.id}/buy`, { rate: { id: rate.id } });
  if (!bought.postage_label) throw new Error(bought.error?.message || "Label purchase failed");
  let qrUrl = null;
  if (rate.carrier.startsWith("USPS")) {
    try {
      const withForm = await ep(`shipments/${shipment.id}/forms`, { form: { type: "label_qr_code" } });
      qrUrl = (withForm.forms || []).find((f) => f.form_type === "label_qr_code")?.form_url || null;
    } catch { /* QR is best-effort; the printable label always works */ }
  }
  return { labelUrl: bought.postage_label.label_url, qrUrl, tracking: bought.tracking_code,
           service: `${rate.carrier} ${rate.service}`, carrier: rate.carrier.startsWith("USPS") ? "USPS" : rate.carrier };
}

const db = (path, init = {}) =>
  fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    ...init,
    headers: {
      apikey: SERVICE_KEY,
      authorization: `Bearer ${SERVICE_KEY}`,
      "content-type": "application/json",
      prefer: "return=representation",
      ...init.headers,
    },
  });

const json = (status, body) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

const PAY_METHODS = { PayPal: "paypal", Check: "check", Zelle: "zelle", Venmo: "venmo", "Cash in store": "cash" };

// derive a clean lead channel from first-touch attribution
const REF_CHANNELS = [
  [/sellcell\./i, "SellCell"], [/swappa\./i, "Swappa"], [/flipsy\./i, "Flipsy"],
  [/bankmycell\./i, "BankMyCell"], [/google\./i, "Google"], [/bing\./i, "Bing"],
  [/duckduckgo\./i, "DuckDuckGo"], [/yahoo\./i, "Yahoo"], [/facebook\.|fb\.com/i, "Facebook"],
  [/instagram\./i, "Instagram"], [/(^|\.)x\.com|twitter\.|t\.co/i, "X"],
  [/reddit\./i, "Reddit"], [/youtube\./i, "YouTube"], [/yelp\./i, "Yelp"],
];
function deriveSource(attrib) {
  if (!attrib) return "Direct";
  if (attrib.us) return attrib.us.charAt(0).toUpperCase() + attrib.us.slice(1);
  if (attrib.r) {
    for (const [re, name] of REF_CHANNELS) if (re.test(attrib.r)) return name;
    try { return "Referral: " + new URL(attrib.r).hostname.replace(/^www\./, ""); }
    catch { return "Referral"; }
  }
  // feed deeplink prefill params with no referrer = price-comparison click-through
  if (/[?&](carrier|cond)=/.test(attrib.l || "")) return "Price comparison";
  return "Direct";
}

export default async (req) => {
  if (req.method !== "POST") return json(405, { error: "POST only" });
  let body;
  try { body = await req.json(); } catch { return json(400, { error: "Invalid JSON" }); }

  const { customer = {}, items = [], payment = {}, promo_code, sms_opt_in, attrib, ship_carrier } = body;

  const method = PAY_METHODS[payment.method] || null;
  if (!method) return json(400, { error: "Invalid payment method" });
  let shipCarrier = ["USPS", "FedEx", "UPS"].includes(ship_carrier) ? ship_carrier : "USPS";

  // -- validate customer fields (cash walk-ins bring the device — no address needed)
  const required = method === "cash"
    ? ["first_name", "last_name", "email", "phone"]
    : ["first_name", "last_name", "email", "phone", "address1", "city", "state", "zip"];
  for (const f of required) {
    if (!String(customer[f] || "").trim()) return json(400, { error: `Missing field: ${f}` });
  }
  if (method !== "cash" && !/^\d{5}(-\d{4})?$/.test(customer.zip)) return json(400, { error: "Invalid ZIP" });
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(customer.email)) return json(400, { error: "Invalid email" });
  customer.email = customer.email.trim().toLowerCase(); // normalized — throttle + track lookups rely on it
  if (method === "cash")  // ignore any half-typed address from before the switch
    customer.address1 = customer.address2 = customer.city = customer.state = customer.zip = null;
  // length caps — oversized junk otherwise surfaces later as Lob/EasyPost failures at payout time
  const CAPS = { first_name: 40, last_name: 40, email: 120, phone: 20, address1: 100, address2: 100, city: 60, state: 2, zip: 10 };
  for (const [f, cap] of Object.entries(CAPS))
    if (customer[f]) customer[f] = String(customer[f]).slice(0, cap);
  if (method !== "cash" && !/^[A-Z]{2}$/i.test(customer.state)) return json(400, { error: "Invalid state" });
  if (payment.detail) payment.detail = String(payment.detail).slice(0, 120);

  // -- throttle: this endpoint sends email and (for mail-in) buys a shipping
  // label, so cap orders per email address per hour
  const recent = await db(`trade_ins?email=eq.${encodeURIComponent(customer.email.toLowerCase())}` +
    `&created_at=gte.${encodeURIComponent(new Date(Date.now() - 36e5).toISOString())}&select=id`);
  if ((await recent.json()).length >= 3)
    return json(429, { error: "Too many orders in the last hour — call us at 657-286-8274 and we'll help directly" });
  if ((method === "paypal" || method === "zelle" || method === "venmo") && !String(payment.detail || "").trim())
    return json(400, { error: `${payment.method} details required` });

  if (!Array.isArray(items) || !items.length || items.length > 25)
    return json(400, { error: "Cart is empty or too large" });

  // -- re-price every item against the catalog (authoritative prices)
  let total = 0;
  const verified = [];
  for (const it of items) {
    const qty = Math.min(Math.max(parseInt(it.qty) || 1, 1), 10);
    const params = new URLSearchParams({
      select: "price,price_enabled,model_enabled,category_enabled,weight_oz",
      category: `eq.${it.cat}`, brand: `eq.${it.brand}`, model: `eq.${it.device}`,
      carrier: `eq.${it.carrier || "-"}`, storage: `eq.${it.storage || "-"}`,
      condition: `eq.${it.cond}`,
    });
    const r = await db(`catalog_flat?${params}`);
    const rows = await r.json();
    const row = rows[0];
    if (!row || !row.price_enabled || !row.model_enabled || !row.category_enabled || !(row.price > 0))
      return json(409, { error: `No current offer for ${it.brand} ${it.device} (${it.cond}). Please re-quote.` });
    total += row.price * qty;
    verified.push({ ...it, qty, price: row.price, weight_oz: Number(row.weight_oz) || 16 });
  }

  // FedEx/UPS is a game-console-only option (Henry's cheaper heavy-parcel
  // rates); anything else in the cart needs the USPS lithium hazmat label
  if (shipCarrier !== "USPS" && !verified.every((i) => i.cat === "Game Console"))
    shipCarrier = "USPS";

  // -- promo code (optional). Strip anything outside [A-Za-z0-9-] BEFORE the
  // ilike lookup: %, _ and * are pattern wildcards in PostgREST, so an
  // unsanitized "%" would match (and redeem) any active code.
  let promoAmount = 0, promoCode = null;
  const promoClean = String(promo_code || "").trim().replace(/[^A-Za-z0-9-]/g, "");
  if (promoClean && promoClean === String(promo_code).trim()) {
    const r = await db(`promo_codes?code=ilike.${encodeURIComponent(promoClean)}&active=eq.true&select=*`);
    const codes = await r.json();
    if (codes[0]) {
      promoAmount = Number(codes[0].amount);
      promoCode = codes[0].code;
      await db(`promo_codes?id=eq.${codes[0].id}`, {
        method: "PATCH", body: JSON.stringify({ times_used: codes[0].times_used + 1 }),
      });
    }
  }

  // -- create the trade-in
  const orderNumber = "OCB-" + Array.from(crypto.getRandomValues(new Uint8Array(6)))
    .map((b) => "ABCDEFGHJKMNPQRSTUVWXYZ23456789"[b % 31]).join("");
  const lockDate = new Date(Date.now() + 14 * 864e5).toISOString().slice(0, 10);

  const tiRes = await db("trade_ins", {
    method: "POST",
    body: JSON.stringify({
      order_number: orderNumber,
      first_name: customer.first_name, last_name: customer.last_name,
      email: customer.email, phone: customer.phone,
      address1: customer.address1, address2: customer.address2 || null,
      city: customer.city, state: customer.state, zip: customer.zip,
      payment_method: method, payment_detail: payment.detail || null,
      sms_opt_in: !!sms_opt_in,
      promo_code: promoCode, promo_amount: promoAmount,
      total_quote: total + promoAmount,
      price_locked_until: lockDate,
      estimated_weight_oz: verified.reduce((a, i) => a + i.weight_oz * i.qty, 0) + 8, // +8oz box/padding
      ship_carrier: method === "cash" ? "USPS" : shipCarrier,
      source: deriveSource(attrib),
      referrer: (attrib?.r || "").slice(0, 500) || null,
      landing_page: (attrib?.l || "").slice(0, 500) || null,
      utm: attrib?.us || attrib?.um || attrib?.uc
        ? { source: attrib.us || null, medium: attrib.um || null, campaign: attrib.uc || null } : null,
    }),
  });
  if (!tiRes.ok) {
    console.error("trade_ins insert failed:", await tiRes.text()); // detail stays server-side
    return json(500, { error: "Could not create order — please try again" });
  }
  const [tradeIn] = await tiRes.json();

  await db("trade_in_items", {
    method: "POST",
    body: JSON.stringify(verified.map((it) => ({
      trade_in_id: tradeIn.id,
      category: it.cat, brand: it.brand, model: it.device,
      carrier: it.carrier || null, storage: it.storage || null,
      condition: it.cond, quoted_price: it.price, qty: it.qty,
    }))),
  });
  // -- buy the return shipping label (skip for walk-in cash orders)
  let label = null;
  if (method !== "cash" && EASYPOST_KEY) {
    try {
      label = await buyReturnLabel(customer,
        verified.reduce((a, i) => a + i.weight_oz * i.qty, 0) + 8, orderNumber, shipCarrier);
      await db(`trade_ins?id=eq.${tradeIn.id}`, { method: "PATCH", body: JSON.stringify({
        label_url: label.labelUrl, label_qr_url: label.qrUrl, tracking_number: label.tracking }) });
    } catch (e) {
      await db("trade_in_events", { method: "POST", body: JSON.stringify({
        trade_in_id: tradeIn.id, status: "initiated",
        note: `⚠️ Shipping label purchase FAILED (${e.message}) — buy manually and email the customer.` }) });
    }
  }

  await db("trade_in_events", {
    method: "POST",
    body: JSON.stringify({
      trade_in_id: tradeIn.id, status: "initiated",
      note: method === "cash" ? "Order created — customer will bring device to the store."
        : label ? `Order created — ${label.service} label bought (${label.tracking})${label.qrUrl ? ", emailed with QR code" : ", emailed"}.`
                : "Order created — label pending.",
    }),
  });

  // -- order confirmation email (label email comes with the carrier integration)
  if (RESEND_KEY) {
    try {
      const lockedPretty = new Date(lockDate + "T12:00:00").toLocaleDateString("en-US", { month: "long", day: "numeric" });
      const { subject, html } = buildOrderConfirmation({
        orderNumber, firstName: customer.first_name, items: verified,
        total: total + promoAmount, lockedUntil: lockedPretty, payMethod: method,
        trackUrl: `${new URL(req.url).origin}/trade-in/track`,
        labelUrl: label?.labelUrl, qrUrl: label?.qrUrl, tracking: label?.tracking,
        shipCarrier: label?.carrier || shipCarrier,
      });
      await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: { authorization: `Bearer ${RESEND_KEY}`, "content-type": "application/json" },
        body: JSON.stringify({ from: FROM, to: customer.email, subject, html,
                               reply_to: "support@ocbuyback.com" }),
      });
    } catch (e) { /* order stands even if the email hiccups */ }
  }
  // TODO: SMS via Twilio when sms_opt_in; label email once carrier account is wired.

  return json(200, {
    order_number: orderNumber,
    total: total + promoAmount,
    locked_until: lockDate,
    payment_method: payment.method,
  });
};

export const config = { path: "/api/create-trade-in" };
