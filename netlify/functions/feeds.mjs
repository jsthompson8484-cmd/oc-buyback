// GET /admin/catalog/e51ee82a3/export/{swappa|bankmycell|sellcell|flipsy}-csv.csv
//
// Price feeds for the aggregators that send sellers to OCBuyBack. The URLs
// (including the token) are what Flipsy/SellCell/BankMyCell/Swappa already
// have configured — they must never change.
//
// Feeds are generated LIVE from the catalog on every request and cached at
// the CDN for at most 1 hour — so a price change reaches aggregators within
// the hour automatically, and the admin "check feeds" button always sees
// fresh data (it bypasses the cache).
//
// Formats replicate the FlipTech feeds byte-for-byte in structure
// (reference copies: reference/feeds/*.csv):
//  swappa:    partner_ref,product,carrier,memory,storage,processor,
//             price_new,price_mint,price_good,price_fair,price_broken,url
//             (price_new left empty and price_broken = Minor Damage,
//              matching the original feed's semantics)
//  bankmycell: ID,Manufacturer,Model,Capacity,Carrier,Brand New Price,
//              Like New Price,Good Price,Minor Damage Price,Damaged Price,Deeplink
//  sellcell:  Manufacturer,Model,Capacity,Carrier,<5 prices>,<5 per-condition deeplinks>
//  flipsy:    "{Model}_{Storage}_{Carrier}_{Condition}",price,url   (no header)

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const SITE = process.env.SITE_URL || "https://www.ocbuyback.com";
const TOKEN = "e51ee82a3";

const US = { Aluminium: "aluminum" }; // aggregators use US spelling
const seg = (s) => (US[s] || s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
const swappaCarrier = (s) => (US[s] || s).toLowerCase().replace(/&/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
// customer-facing condition slugs used in SellCell deeplinks
const COND_SLUG = { "Brand New": "brand-new", "Flawless": "like-new", "Good": "good-condition",
                    "Fair": "fair", "Minor Damage": "minor-damage", "Broken": "damaged" };
const csv = (v) => { const s = String(v ?? ""); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };

async function loadCatalog() {
  // paginate catalog_flat (enabled rows with a live price)
  const rows = [];
  for (let from = 0; ; from += 1000) {
    const r = await fetch(`${SUPABASE_URL}/rest/v1/catalog_flat?` + new URLSearchParams({
      select: "category_slug,brand,brand_slug,model,model_slug,variant_id,carrier,storage,condition,price",
      price_enabled: "eq.true", model_enabled: "eq.true", category_enabled: "eq.true",
      price: "gt.0", order: "variant_id,condition",
    }), { headers: { apikey: SERVICE_KEY, authorization: `Bearer ${SERVICE_KEY}`,
                     range: `${from}-${from + 999}` } });
    const page = await r.json();
    rows.push(...page);
    if (page.length < 1000) break;
  }
  // group per variant
  const variants = new Map();
  for (const r of rows) {
    const k = r.variant_id;
    if (!variants.has(k)) variants.set(k, { ...r, prices: {} });
    variants.get(k).prices[r.condition] = Number(r.price).toFixed(1);
  }
  return [...variants.values()];
}

const deeplink = (v) => `${SITE}/sell/${v.category_slug}/${v.brand_slug}/${v.model_slug}`;

const BUILDERS = {
  swappa(vs) {
    const out = ["partner_ref,product,carrier,memory,storage,processor,price_new,price_mint,price_good,price_fair,price_broken,url"];
    for (const v of vs) {
      const p = v.prices;
      out.push(["", `${v.brand_slug}-${v.model_slug}`, swappaCarrier(v.carrier), "", v.storage.toLowerCase(), "",
        "", p["Flawless"] ?? "", p["Good"] ?? "", p["Fair"] ?? "", p["Minor Damage"] ?? "", deeplink(v)]
        .map(csv).join(","));
    }
    return out;
  },
  bankmycell(vs) {
    const out = ["ID,Manufacturer,Model,Capacity,Carrier,Brand New Price,Like New Price,Good Price,Minor Damage Price,Damaged Price,Deeplink"];
    for (const v of vs) {
      const p = v.prices;
      out.push([v.variant_id, v.brand, v.model, v.storage, v.carrier,
        p["Brand New"] ?? "", p["Flawless"] ?? "", p["Good"] ?? "", p["Minor Damage"] ?? "", p["Broken"] ?? "",
        deeplink(v)].map(csv).join(","));
    }
    return out;
  },
  sellcell(vs) {
    const out = ["Manufacturer,Model,Capacity,Carrier,Like New Price,Good Price,Fair Price,Minor Damage Price,Damaged Price,Like New Deeplink,Good Deeplink,Fair Deeplink,Minor Damage Deeplink,Damaged Deeplink"];
    for (const v of vs) {
      const p = v.prices;
      const dl = (cond) => `${deeplink(v)}/${seg(v.carrier)}/${seg(v.storage)}/${COND_SLUG[cond]}`;
      out.push([v.brand, v.model, v.storage, v.carrier,
        p["Flawless"] ?? "", p["Good"] ?? "", p["Fair"] ?? "", p["Minor Damage"] ?? "", p["Broken"] ?? "",
        dl("Flawless"), dl("Good"), dl("Fair"), dl("Minor Damage"), dl("Broken")].map(csv).join(","));
    }
    return out;
  },
  flipsy(vs) {
    const out = [];
    for (const v of vs)
      for (const [cond, price] of Object.entries(v.prices))
        out.push([`${v.model}_${v.storage}_${v.carrier}_${cond}`, price, deeplink(v)].map(csv).join(","));
    return out;
  },
};

export default async (req) => {
  const m = new URL(req.url).pathname.match(new RegExp(`/admin/catalog/${TOKEN}/export/(swappa|bankmycell|sellcell|flipsy)-csv\\.csv$`));
  if (!m) return new Response("Not found", { status: 404 });
  const variants = await loadCatalog();
  const lines = BUILDERS[m[1]](variants);
  return new Response(lines.join("\n") + "\n", {
    headers: {
      "content-type": "text/csv; charset=utf-8",
      "cache-control": "public, max-age=0, must-revalidate",
      "netlify-cdn-cache-control": "public, s-maxage=3600, stale-while-revalidate=86400",
      "x-generated-at": new Date().toISOString(),
      "x-row-count": String(lines.length),
    },
  });
};

export const config = { path: "/admin/catalog/e51ee82a3/export/*" };
