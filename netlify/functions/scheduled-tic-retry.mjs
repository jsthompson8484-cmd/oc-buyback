// Hourly: re-send Trade Into Cash conversions that never got recorded.
//
// The inline retry in create-trade-in covers a blip. This covers the rest —
// their endpoint being down for a stretch, or returning 500 {success:false},
// which looks like success from our side but leaves the order uncredited.
// Without this, those orders are silently unbilled forever.
//
// Safe to run repeatedly: Trade Into Cash dedups on (partner, order_id), so a
// conversion they already hold is discarded rather than double-counted.

import { reportConversion, isTicReferral } from "./lib/tic-conversion.mjs";

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

const db = (path, init = {}) =>
  fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    ...init,
    headers: { apikey: SERVICE_KEY, authorization: `Bearer ${SERVICE_KEY}`,
      "content-type": "application/json", prefer: "return=representation", ...init.headers },
  });

export default async () => {
  // anything created in the last 30 days that still isn't confirmed reported
  const since = new Date(Date.now() - 30 * 864e5).toISOString();
  // ONLY orders Trade Into Cash actually referred — a click id OR the
  // tradeintocash referral tag. Without this filter the drain re-sends every
  // organic and Swappa order, which is exactly the over-reporting we caused.
  const referred = "or=(tic_click.not.is.null,referrer.ilike.*tradeintocash*," +
                   "landing_page.ilike.*tradeintocash*,source.ilike.*tradeintocash*)";
  const pending = await db(
    `trade_ins?tic_reported_at=is.null&legacy_id=is.null&${referred}` +
    `&created_at=gte.${encodeURIComponent(since)}` +
    `&select=id,order_number,total_quote,tic_click,referrer,landing_page,source,utm,tic_report_status&limit=50`
  ).then((r) => r.json()).catch(() => []);

  const out = { pending: pending.length, recovered: 0, still_failing: 0, orders: [] };

  for (const t of pending) {
    if (!isTicReferral(t)) { out.orders.push({ order: t.order_number, result: "skipped — not a TIC referral" }); continue; }
    const r = await reportConversion({
      orderNumber: t.order_number, orderTotal: t.total_quote, clickId: t.tic_click });
    await db(`trade_ins?id=eq.${t.id}`, { method: "PATCH", body: JSON.stringify({
      tic_reported_at: r.ok ? new Date().toISOString() : null,
      tic_report_status: r.ok ? "reported (retry)" : r.status,
    }) }).catch(() => {});
    if (r.ok) out.recovered++; else out.still_failing++;
    out.orders.push({ order: t.order_number, result: r.status });
  }

  if (out.recovered || out.still_failing) console.log("tic retry:", JSON.stringify(out));
  return new Response(JSON.stringify(out), { status: 200, headers: { "content-type": "application/json" } });
};

export const config = { schedule: "17 * * * *" };   // hourly, off the hour
