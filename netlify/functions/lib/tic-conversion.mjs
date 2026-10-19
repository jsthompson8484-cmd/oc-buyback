// Report a conversion to Trade Into Cash (partner referral billing).
//
// Server-side by design: their browser snippet loses orders to ad blockers,
// JS errors and closed tabs, and each loss is an unbilled sale.
//
// Two things their integration notes call out, both handled here:
//   * Authenticate — the shared secret goes in the body as "t". Kept in
//     site_settings (service-role only), never in page source or client JS.
//   * Retry — their endpoint can return 500 {success:false}, meaning the
//     request arrived but was not recorded. That's the dangerous shape: the
//     call looks like it went through while the order stays uncredited. We
//     retry with backoff, and anything still failing is left marked so the
//     scheduled drain can re-send it. Retries are safe: they dedup on
//     (partner, order_id).

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const ENDPOINT = "https://tradeintocash.com/.netlify/functions/conversion-pixel";
const PARTNER = "ocbuyback";          // must match their records byte for byte
const CLICK_RE = /^[0-9a-f-]{10,40}$/i;

/**
 * Is this order actually a Trade Into Cash referral?
 *
 * The referral tag is the source of truth, NOT the absence of a click id:
 * a missing click id only means we couldn't join the order back to a specific
 * click (cleared cookies, device switch, weeks elapsed) — it never means
 * "assume it's theirs". Reporting unreferred orders would have OCBuyBack
 * paying 3% on its own organic and Swappa traffic.
 */
export function isTicReferral(t = {}) {
  if (CLICK_RE.test(String(t.tic_click || ""))) return true;
  const hay = [t.referrer, t.landing_page, t.source, t.utm && t.utm.source]
    .filter(Boolean).join(" ").toLowerCase();
  return hay.includes("tradeintocash");
}

let cachedSecret;
async function secret() {
  if (cachedSecret !== undefined) return cachedSecret;
  try {
    const [row] = await fetch(
      `${SUPABASE_URL}/rest/v1/site_settings?key=eq.tic_pixel_secret&select=value`,
      { headers: { apikey: SERVICE_KEY, authorization: `Bearer ${SERVICE_KEY}` } },
    ).then((r) => r.json());
    cachedSecret = typeof row?.value === "string" ? row.value : null;
  } catch { cachedSecret = null; }
  return cachedSecret;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * POST one conversion, retrying on any non-200 and on {success:false}.
 * Returns { ok, status } — never throws, so partner billing can't break an order.
 */
export async function reportConversion({ orderNumber, orderTotal, clickId }, { attempts = 3 } = {}) {
  const t = await secret();
  const body = JSON.stringify({
    partner: PARTNER,
    click_id: CLICK_RE.test(String(clickId || "")) ? clickId : null,
    order_id: orderNumber,
    order_total: Number(Number(orderTotal).toFixed(2)),
    currency: "USD",
    referral_source: "tradeintocash",
    ...(t ? { t } : {}),
  });

  let last = "no attempt";
  for (let i = 0; i < attempts; i++) {
    if (i) await sleep(400 * 2 ** (i - 1));            // 400ms, 800ms
    try {
      const res = await fetch(ENDPOINT, {
        method: "POST", headers: { "content-type": "application/json" }, body,
      });
      // a 200 that says success:false is still a failure to record
      const payload = await res.json().catch(() => ({}));
      if (res.ok && payload.success !== false) return { ok: true, status: "reported" };
      last = `HTTP ${res.status}${payload.success === false ? " success:false" : ""}`;
    } catch (e) {
      last = `network: ${String(e.message).slice(0, 60)}`;
    }
  }
  return { ok: false, status: `failed ${last}`.slice(0, 120) };
}
