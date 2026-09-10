// POST /api/easypost-webhook — EasyPost tracker events auto-advance orders.
//
// EasyPost fires tracker.created / tracker.updated for every label we buy.
// Mapping (forward-only, never downgrades a status an admin already set):
//   in_transit, out_for_delivery  -> shipped    (only from initiated)
//   delivered                     -> delivered  (only from initiated/shipped)
//   return_to_sender, failure     -> event logged for admin attention only
//
// Auth: HMAC-SHA256 signature over the raw body (X-Hmac-Signature:
// "hmac-sha256-hex=<hex>"), keyed by the secret in
// site_settings.easypost_webhook_secret — the same secret the webhook was
// registered with. That key is NOT in the public-read whitelist.
// Unknown tracking numbers return 200 so EasyPost doesn't retry forever.

import { createHmac, timingSafeEqual } from "node:crypto";

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

const db = (path, init = {}) =>
  fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    ...init,
    headers: { apikey: SERVICE_KEY, authorization: `Bearer ${SERVICE_KEY}`,
      "content-type": "application/json", prefer: "return=representation", ...init.headers },
  });

const json = (status, body) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

// tracker status -> (our status, which current statuses may advance)
const ADVANCE = {
  in_transit: { to: "shipped", from: ["initiated"] },
  out_for_delivery: { to: "shipped", from: ["initiated"] },
  delivered: { to: "delivered", from: ["initiated", "shipped"] },
};
const ATTENTION = new Set(["return_to_sender", "failure", "error", "cancelled"]);

export default async (req) => {
  if (req.method !== "POST") return json(405, { error: "POST only" });
  const raw = await req.text();

  // -- verify the EasyPost signature
  const [row] = await db("site_settings?key=eq.easypost_webhook_secret&select=value")
    .then((r) => r.json()).catch(() => []);
  const secret = typeof row?.value === "string" ? row.value : null;
  if (!secret) return json(503, { error: "Webhook secret not configured" });
  const given = (req.headers.get("x-hmac-signature") || "").replace(/^hmac-sha256-hex=/, "");
  const want = createHmac("sha256", secret).update(raw, "utf8").digest("hex");
  const a = Buffer.from(given, "utf8"), b = Buffer.from(want, "utf8");
  if (a.length !== b.length || !timingSafeEqual(a, b))
    return json(401, { error: "Bad signature" });

  let event;
  try { event = JSON.parse(raw); } catch { return json(400, { error: "Invalid JSON" }); }
  const kind = event?.description || "";
  const tracker = event?.result;
  if (!kind.startsWith("tracker.") || tracker?.object !== "Tracker")
    return json(200, { ok: true, ignored: kind || "not a tracker event" });

  const code = String(tracker.tracking_code || "");
  const tStatus = String(tracker.status || "");
  if (!code) return json(200, { ok: true, ignored: "no tracking code" });

  const [ti] = await db(`trade_ins?tracking_number=eq.${encodeURIComponent(code)}&select=id,order_number,status`)
    .then((r) => r.json());
  if (!ti) return json(200, { ok: true, ignored: "unknown tracking number" });

  const adv = ADVANCE[tStatus];
  if (adv && adv.from.includes(ti.status)) {
    // conditional on current status so replayed/re-ordered events can't
    // regress an order an admin has already moved along
    const upd = await db(
      `trade_ins?id=eq.${ti.id}&status=in.(${adv.from.join(",")})`,
      { method: "PATCH", body: JSON.stringify({ status: adv.to }) });
    const changed = upd.ok ? await upd.json() : [];
    if (changed.length) {
      await db("trade_in_events", { method: "POST", body: JSON.stringify({
        trade_in_id: ti.id, status: adv.to,
        note: `USPS ${tStatus.replace(/_/g, " ")} — auto-updated by tracking` }) });
      return json(200, { ok: true, order: ti.order_number, status: adv.to });
    }
    return json(200, { ok: true, ignored: "already past this status" });
  }

  if (ATTENTION.has(tStatus)) {
    await db("trade_in_events", { method: "POST", body: JSON.stringify({
      trade_in_id: ti.id, status: ti.status,
      note: `Tracking ATTENTION: USPS reports ${tStatus.replace(/_/g, " ")} for ${code} — check the shipment` }) });
    return json(200, { ok: true, order: ti.order_number, flagged: tStatus });
  }

  return json(200, { ok: true, ignored: `no action for ${tStatus}` });
};

export const config = { path: "/api/easypost-webhook" };
