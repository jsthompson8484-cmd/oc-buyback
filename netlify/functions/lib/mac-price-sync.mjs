// Shared Mac price-feed sync logic — used by the daily scheduled function
// and the admin "Sync now" button (/api/sync-mac-prices).
//
// Fetches MAC_PRICE_FEED_URL (CSV: model_slug,processor,memory,condition,price
// with optional generated_at), validates rows, and applies them in one
// apply_mac_price_feed RPC call (guards + category scoping live in SQL —
// see supabase/mac_price_feed_rpc.sql). The result summary is stored in
// site_settings.mac_price_sync so the admin panel can show the last run.

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

const CONDITIONS = new Set([
  "Brand New", "Flawless", "Good", "Fair", "Minor Damage", "Broken",
]);

// minimal CSV parser (handles quoted fields + escaped quotes)
function parseCsv(text) {
  const rows = [];
  let row = [], field = "", inQ = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (inQ) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (ch === '"') inQ = false;
      else field += ch;
    } else if (ch === '"') inQ = true;
    else if (ch === ",") { row.push(field); field = ""; }
    else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && text[i + 1] === "\n") i++;
      row.push(field); field = "";
      if (row.some((f) => f !== "")) rows.push(row);
      row = [];
    } else field += ch;
  }
  row.push(field);
  if (row.some((f) => f !== "")) rows.push(row);
  return rows;
}

export async function runMacPriceSync(trigger) {
  if (!process.env.MAC_PRICE_FEED_URL)
    return { error: "MAC_PRICE_FEED_URL is not configured in Netlify env vars yet" };

  const headers = {};
  if (process.env.MAC_PRICE_FEED_TOKEN)
    headers.authorization = `Bearer ${process.env.MAC_PRICE_FEED_TOKEN}`;

  let text;
  try {
    const res = await fetch(process.env.MAC_PRICE_FEED_URL, { headers });
    if (!res.ok) return { error: `Feed returned HTTP ${res.status}` };
    text = await res.text();
  } catch (e) {
    return { error: `Feed unreachable: ${e.message}` };
  }

  const rows = parseCsv(text);
  if (rows.length < 2) return { error: "Feed is empty or has no data rows" };
  const header = rows[0].map((h) => h.trim().toLowerCase());
  const col = Object.fromEntries(
    ["model_slug", "processor", "memory", "condition", "price", "generated_at"]
      .map((c) => [c, header.indexOf(c)]));
  for (const c of ["model_slug", "processor", "memory", "condition", "price"])
    if (col[c] === -1) return { error: `Feed is missing required column "${c}"` };

  const feed = [];
  let bad = 0, generatedAt = null;
  for (const r of rows.slice(1)) {
    const price = Number(r[col.price]);
    const condition = (r[col.condition] || "").trim();
    if (!CONDITIONS.has(condition) || !Number.isFinite(price) || price <= 0) { bad++; continue; }
    feed.push({
      model_slug: (r[col.model_slug] || "").trim(),
      processor: (r[col.processor] || "").trim(),
      memory: (r[col.memory] || "").trim(),
      condition, price,
    });
    if (col.generated_at !== -1 && !generatedAt) generatedAt = r[col.generated_at];
  }
  if (!feed.length) return { error: "No valid rows in feed (check conditions/prices)", bad_rows: bad };

  const rpc = await fetch(`${SUPABASE_URL}/rest/v1/rpc/apply_mac_price_feed`, {
    method: "POST",
    headers: { apikey: SERVICE_KEY, authorization: `Bearer ${SERVICE_KEY}`,
      "content-type": "application/json" },
    body: JSON.stringify({ feed }),
  });
  if (!rpc.ok) return { error: `DB apply failed: ${(await rpc.text()).slice(0, 200)}` };
  const counts = await rpc.json();

  const summary = {
    at: new Date().toISOString(), trigger,
    feed_rows: rows.length - 1, bad_rows: bad,
    feed_generated_at: generatedAt || null,
    ...counts, // total, matched, guarded, updated
    unknown: (counts.total ?? feed.length) - (counts.matched ?? 0),
  };

  await fetch(`${SUPABASE_URL}/rest/v1/site_settings`, {
    method: "POST",
    headers: { apikey: SERVICE_KEY, authorization: `Bearer ${SERVICE_KEY}`,
      "content-type": "application/json",
      prefer: "resolution=merge-duplicates" },
    body: JSON.stringify({ key: "mac_price_sync", value: summary }),
  }).catch(() => {}); // summary is informational; the sync itself already succeeded

  return summary;
}
