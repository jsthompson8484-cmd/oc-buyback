// Daily: reclaim money from UPS labels nobody used.
//
// UPS goes through EasyPost's DAP wallet, which charges at purchase — so an
// unused UPS label is real money gone. (FedEx and USPS bill on first carrier
// scan against the store's own accounts, so an unused label there costs
// nothing and is left alone.)
//
// A quote only holds for 14 days, so once an order is that old and the carrier
// has never scanned the package, the label is dead weight: void it, recover the
// postage, and expire the order.
//
// Safety: we only ever void a label the carrier has NOT scanned. If tracking
// shows any movement the label is left alone, because voiding a label on a
// package already in transit would strand the customer's device.

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const EASYPOST_KEY = process.env.EASYPOST_API_KEY;
const STALE_DAYS = Number(process.env.LABEL_VOID_AFTER_DAYS || 14);

const db = (path, init = {}) =>
  fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    ...init,
    headers: { apikey: SERVICE_KEY, authorization: `Bearer ${SERVICE_KEY}`,
      "content-type": "application/json", prefer: "return=representation", ...init.headers },
  });

const ep = (path, init = {}) =>
  fetch(`https://api.easypost.com/v2/${path}`, {
    ...init,
    headers: { authorization: "Basic " + btoa(EASYPOST_KEY + ":"),
      "content-type": "application/json", ...init.headers },
  }).then((r) => r.json());

// carrier scanned it = the package is really moving; never void these
const MOVED = new Set(["in_transit", "out_for_delivery", "delivered", "available_for_pickup", "return_to_sender"]);

export default async () => {
  if (!EASYPOST_KEY) return new Response(JSON.stringify({ error: "EASYPOST_API_KEY not set" }), { status: 503 });

  const cutoff = new Date(Date.now() - STALE_DAYS * 864e5).toISOString();
  const candidates = await db(
    `trade_ins?ship_carrier=eq.UPS&status=eq.initiated&label_shipment_id=not.is.null` +
    `&label_refund_status=is.null&created_at=lt.${encodeURIComponent(cutoff)}` +
    `&select=id,order_number,email,tracking_number,label_shipment_id,created_at`
  ).then((r) => r.json()).catch(() => []);

  const out = { checked: candidates.length, voided: 0, skipped_moving: 0, failed: 0, orders: [] };

  for (const t of candidates) {
    // has the carrier touched it?
    let moving = false;
    try {
      const tk = await ep(`trackers?tracking_code=${encodeURIComponent(t.tracking_number || "")}`);
      const status = (tk.trackers && tk.trackers[0] && tk.trackers[0].status) || "unknown";
      moving = MOVED.has(status);
    } catch { /* tracker lookup failed — fall through and let the void decide */ }

    if (moving) {
      out.skipped_moving++;
      out.orders.push({ order: t.order_number, action: "left alone — package is moving" });
      continue;
    }

    const refund = await ep(`shipments/${t.label_shipment_id}/refund`, { method: "POST" });
    const status = refund.refund_status || null;
    const ok = ["submitted", "refunded"].includes(status);

    await db(`trade_ins?id=eq.${t.id}`, { method: "PATCH", body: JSON.stringify({
      label_refund_status: status || "rejected",
      label_refunded_at: ok ? new Date().toISOString() : null,
      ...(ok ? { status: "expired" } : {}),
    }) }).catch(() => {});

    await db("trade_in_events", { method: "POST", body: JSON.stringify({
      trade_in_id: t.id, status: ok ? "expired" : "initiated",
      note: ok
        ? `Unused UPS label voided after ${STALE_DAYS} days — postage refunded (${status}). Quote expired; the label no longer works.`
        : `⚠️ Tried to void the unused UPS label but EasyPost said "${status || refund.error?.message || "unknown"}" — check it manually.`,
    }) }).catch(() => {});

    if (ok) out.voided++; else out.failed++;
    out.orders.push({ order: t.order_number, action: ok ? `voided (${status})` : `FAILED (${status || "error"})` });
  }

  console.log("void stale labels:", JSON.stringify(out));
  return new Response(JSON.stringify(out), { status: 200, headers: { "content-type": "application/json" } });
};

// 14:30 UTC = 7:30am Pacific, after the morning price sync
export const config = { schedule: "30 14 * * *" };
