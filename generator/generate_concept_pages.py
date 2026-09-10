#!/usr/bin/env python3
"""Generate Fresh Air concept pages for every enabled model in data/catalog.json.

Outputs under concepts/freshair/:
  sell/index.html                          category hub
  sell/{cat}/index.html                    model grid per category
  sell/{cat}/{brand}/{model}/index.html    quote page with real price matrix
  index.html                               homepage (data-driven top payouts)

URL slugs mirror the live site: lowercase, spaces->dashes.
Copy rules: buyback site (not marketplace), no shipping-insurance mentions.
"""
import json, re, html, pathlib, collections, csv

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "concepts" / "freshair"
TREE = json.load(open(ROOT / "data" / "catalog.json"))

SITE = "https://www.ocbuyback.com"
GA4_ID = ""  # set at launch (e.g. "G-XXXXXXXXXX") and regenerate

# live-site titles/descriptions from the Sep 3 crawl — SEO continuity beats rewriting
BANNED = ("insurance", "paypal")
BASELINE = {}
for r in csv.DictReader(open(ROOT / "reference" / "parity_baseline.csv")):
    t, d = r["title"].strip(), r["meta_description"].strip()
    BASELINE[r["path"]] = {
        "title": t if t and not any(b in t.lower() for b in BANNED) else None,
        "desc": d if d and not any(b in d.lower() for b in BANNED) else None,
    }

SITEMAP = []  # (path, image_url or None), collected during generation

STORE_SCHEMA = {
    "@context": "https://schema.org", "@type": "LocalBusiness", "@id": SITE + "/#store",
    "name": "OCBuyBack", "url": SITE, "telephone": "+1-657-286-8274",
    "email": "support@ocbuyback.com", "image": SITE + "/assets/logo-colored.png",
    "address": {"@type": "PostalAddress", "streetAddress": "1203 W Imperial Hwy, STE 103",
                "addressLocality": "Brea", "addressRegion": "CA", "postalCode": "92821",
                "addressCountry": "US"},
    "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
        "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday"],
        "opens": "10:00", "closes": "18:00"}],
}
ORG_SCHEMA = {
    "@context": "https://schema.org", "@type": "Organization", "@id": SITE + "/#org",
    "name": "OCBuyBack", "legalName": "OCBuyBack", "url": SITE,
    "logo": SITE + "/assets/logo-colored.png", "telephone": "+1-657-286-8274",
    "sameAs": [],
}
def breadcrumbs(items):  # [(name, path or None)]
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n,
                             **({"item": SITE + p} if p else {})}
                            for i, (n, p) in enumerate(items)]}

LIVE_CATS = ["Cell Phone","Tablet","Smartwatch","Game Console","GoPro","VR","Headphones","iPod"]
CAT_SLUG = {"Cell Phone":"cell-phone","Tablet":"tablet","Smartwatch":"smartwatch",
            "Game Console":"game-console","GoPro":"gopro","VR":"vr","Headphones":"headphones","iPod":"ipod"}
CAT_PLURAL_IMG = {"Cell Phone":"cell-phones","Tablet":"tablets","Smartwatch":"smartwatches",
                  "Game Console":"game-consoles","GoPro":"gopros","VR":"vrs","Headphones":"headphones","iPod":"ipods"}
CAT_DISPLAY = {"Cell Phone":"Cell Phones","Tablet":"Tablets","Smartwatch":"Smartwatches",
               "Game Console":"Game Consoles","GoPro":"GoPro","VR":"VR","Headphones":"Headphones","iPod":"iPods"}
SELL_YOUR = {"GoPro":"GoPro","VR":"VR headset","iPod":"iPod"}
# question labels per category: (question-1 label, question-2 label)
CAT_LABELS = {"Smartwatch":("Which case?","What size?"),
              "Game Console":("Which edition?","How much storage?"),
              "GoPro":("Which edition?","Which bundle?"),
              "Cell Phone":("Which carrier?","How much storage?"),
              "Tablet":("Which connectivity?","How much storage?"),
              "VR":("Which edition?","How much storage?"),
              "Headphones":("Which edition?","Which color?"),
              "iPod":("Which generation?","How much storage?")}
COND_ORDER = ["Brand New","Flawless","Good","Fair","Minor Damage","Broken"]
COND_DESC = {"Brand New":"Sealed in box, never activated.",
             "Flawless":"Like new — zero scratches, fully functional.",
             "Good":"Light wear you have to look for. Works perfectly.",
             "Fair":"Visible scratches or dings, fully functional.",
             "Minor Damage":"Cracked screen or other damage, still works.",
             "Broken":"Doesn't power on or has major faults."}
# full grading criteria from the live admin (Sep 8 2026) — shown in the expandable guide
COND_FULL = {
 "Brand New": ("An unopened item in the original packaging/box. All of the following must be true:",
  ["Plastic film still on the device and has not been reapplied.","Device is not activated.",
   "Comes with the original box with matching serial number.","Contains original accessories sealed and untouched.",
   "Paid off and free of any financial obligations."]),
 "Flawless": ("100% perfect condition — like new out of the box and fully functional. All of the following must be true:",
  ["Zero scratches, scuffs, or other marks. Looks like new.",
   "Display is free of defects such as dead pixels, white spots, or burn-in.",
   "Original battery above 90% capacity.","Powers on and functions 100% as intended.",
   "Paid off and free of any financial obligations."]),
 "Good": ("The most common condition — average wear and tear from normal use, 100% fully functional, no water damage. All of the following must be true:",
  ["No major scratches, deep scratches, chips, or dents.",
   "Display is free of defects such as dead pixels, white spots, or burn-in.",
   "Original battery above 85% capacity.","Powers on and functions 100% as intended.",
   "Paid off and free of any financial obligations."]),
 "Fair": ("Moderate to excessive signs of wear — heavy scratching, deep scratches you can feel, or major dents — but fully functional. All of the following must be true:",
  ["Front and back glass is free of any cracks or chips.",
   "Display is free of defects such as dead pixels, white spots, or burn-in.",
   "Powers on and functions 100% as intended.","Paid off and free of any financial obligations."]),
 "Minor Damage": ("The device has only ONE issue, such as a cracked screen without display damage, cracked camera or back glass, or a bad button — and can be fully tested. One of the following is true:",
  ["Cracked front screen without LCD damage, cracked back glass or camera.",
   "Display defects such as white spots or minor LCD burn-in.",
   "Faulty headphone jack or vibrate motor.","Faulty microphone or speaker.","Malfunctioning buttons or switches.",
   "Another functional defect (calls, charging, fingerprint sensor, etc.). Note: water damage counts as Broken even if the device works."]),
 "Broken": ("More than one issue from the Minor Damage list — or water damage, bent/dented housing, or LCD damage (spots, lines). More than one of the following is true:",
  ["Cracked display or damaged housing.","Display defects such as dead pixels, white spots, or burn-in.",
   "Faulty headphone jack or vibrate motor.","Battery is dead or has poor life.","Faulty microphone or speaker.",
   "Malfunctioning buttons or switches.","Another functional defect.","Signs of liquid intrusion or damage."]),
}
SOCIAL = [("X", "https://x.com/buy_oc"), ("Facebook", "https://www.facebook.com/ocbuyback"),
          ("Instagram", "https://www.instagram.com/ocbuyback")]
BATTERY_NOTE = ('<p style="color:var(--muted);font-size:13px;margin:8px 0 0">iPhone battery health shows under '
                'Settings → Battery. <a href="https://support.apple.com/en-us/HT208387" target="_blank" rel="noopener" '
                'style="color:var(--green);font-weight:600">How to check battery health</a></p>')
CARRIER_ORDER = ["Unlocked","AT&T","T-Mobile","Verizon","Sprint","Other"]

# live-site slugs that diverge from the standard pattern (FlipTech's slugger
# changed over the years and old slugs are frozen in Google's index)
SLUG_OVERRIDES = {
    "Series 7 GPS + Cellular": "series-7-gps-cellular",
    "Series 8 GPS + Cellular": "series-8-gps-cellular",
    "Series 9 GPS + Cellular": "series-9-gps-cellular",
    "Series 10 GPS + Cellular": "series-10-gps-cellular",
    "iPad Pro 11 M5 Nano-texture Glass (2025)": "ipad-pro-11-m5-nanominustexture-glass-2025",
    "iPad Pro 13 M5 Nano-texture Glass (2025)": "ipad-pro-13-m5-nanominustexture-glass-2025",
}
def slug(s):
    if s in SLUG_OVERRIDES: return SLUG_OVERRIDES[s]
    s = s.lower().replace("&","and").replace("+","-plus")
    s = re.sub(r"[^a-z0-9]+","-",s)
    return s.strip("-")

def storkey(s):
    m = re.match(r"([\d.]+)\s*(GB|TB|mm)?", s, re.I)
    if not m: return (999999, s)
    v = float(m.group(1)); u = (m.group(2) or "").upper()
    return (v*1024 if u=="TB" else v, s)

def carrier_sort(c):
    return (CARRIER_ORDER.index(c) if c in CARRIER_ORDER else 50, c)

def model_max(m):
    return max((p for c in m["variants"].values() for s in c.values() for p in s.values()), default=0)

def img_url(cat, brand, device):
    try:
        img = TREE[cat][brand][device].get("image")
        if img: return img
    except (KeyError, AttributeError): pass
    return f"https://s3.amazonaws.com/fliptech-assets/images/devices/{CAT_PLURAL_IMG[cat]}/{slug(brand)}/{slug(device)}.webp"

def mslug(m, name):
    """DB slug wins (it carries the legacy overrides); fall back to computed."""
    return (m.get("slug") if isinstance(m, dict) else None) or slug(name)

def money(v):
    return f"${v:,.0f}" if v == int(v) else f"${v:,.2f}"

CSS = """
:root{--ground:#f5f8f4;--surface:#ffffff;--ink:#182420;--muted:#5c6e64;--brand:#2EB835;--green:#2D8631;--deep:#1E6323;
--lime:#DFF3E1;--lime-ink:#1E6323;--line:#e3eae2;--gold:#e8a828}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font:400 16px/1.6 "Figtree",system-ui,sans-serif}
a{color:inherit;text-decoration:none}
.wrap{max-width:1120px;margin:0 auto;padding:0 24px}
header{background:var(--ground);position:sticky;top:0;z-index:10;border-bottom:1px solid var(--line)}
.nav{display:flex;align-items:center;gap:30px;height:68px}
.logo{font:800 19px/1 "Bricolage Grotesque",sans-serif;color:var(--deep)}
.logo i{font-style:normal;color:var(--green)}
.nav .links{display:flex;gap:24px;font-size:14.5px;font-weight:600;color:var(--muted)}
.nav .links a:hover{color:var(--ink)}
.nav .cta{margin-left:auto;background:var(--deep);color:#fff;font-weight:700;font-size:14px;padding:11px 20px;border-radius:99px}
.crumb{font-size:13.5px;color:var(--muted);padding:22px 0}
.crumb b{color:var(--ink)}
h1{font:800 clamp(26px,3.4vw,38px)/1.1 "Bricolage Grotesque",sans-serif;color:var(--deep);margin:0 0 6px}
.sub{color:var(--muted);margin:0 0 28px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:14px;padding-bottom:70px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:20px;text-align:center;
transition:transform .12s,box-shadow .12s}
.card:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(14,61,38,.08)}
.card img{height:96px;width:auto;max-width:100%;object-fit:contain;display:block;margin:0 auto 12px}
.card .name{font-weight:700;font-size:14.5px}
.card .val{color:var(--green);font-weight:800;font-size:16px;margin-top:4px;font-variant-numeric:tabular-nums}
.card .val small{color:var(--muted);font-weight:500;font-size:12px}
.brand-h{font:700 20px "Bricolage Grotesque",sans-serif;color:var(--deep);margin:34px 0 14px}
.back{position:fixed;bottom:18px;right:18px;background:var(--surface);border:1px solid var(--line);color:var(--muted);
font-size:12px;font-weight:700;padding:9px 14px;border-radius:99px;z-index:20;box-shadow:0 2px 10px rgba(14,61,38,.08)}
footer{background:var(--deep);color:#bcd6c4;font-size:13.5px;margin-top:40px}
footer .cols{display:grid;grid-template-columns:1.3fr 1fr 1fr 1fr;gap:36px;padding:44px 0 30px}
footer h4{font:700 13px "Bricolage Grotesque",sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--lime);margin:0 0 12px}
footer a{color:#bcd6c4}
footer a:hover{color:#fff}
footer .flinks{display:grid;gap:7px}
footer .fbrand img{height:34px;margin-bottom:12px}
footer .fbrand p{margin:0 0 10px;line-height:1.6;max-width:34ch}
footer .fbot{border-top:1px solid rgba(255,255,255,.12);padding:16px 0;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;font-size:12.5px;color:#8fa595}
@media(max-width:860px){footer .cols{grid-template-columns:1fr 1fr}}
"""

WIZ_CSS = """
.layout{display:grid;grid-template-columns:1.3fr 1fr;gap:36px;padding-bottom:80px;align-items:start}
.qs{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:24px;margin-bottom:16px}
.qs .label{font-weight:700;font-size:15px;margin-bottom:14px;display:flex;align-items:center;gap:10px}
.qs .label .badge{background:var(--lime);color:var(--lime-ink);font-size:12px;font-weight:800;border-radius:99px;padding:3px 10px}
.pills{display:flex;flex-wrap:wrap;gap:10px}
.pill{background:var(--ground);border:1.5px solid var(--line);border-radius:99px;padding:11px 22px;font-weight:600;
font-size:14.5px;cursor:pointer;color:var(--ink);font-family:inherit}
.pill:hover{border-color:var(--green)}
.pill.on{border-color:var(--brand);background:var(--brand);color:#fff}
.conds{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.cond{background:var(--ground);border:1.5px solid var(--line);border-radius:12px;padding:14px 16px;cursor:pointer}
.cond:hover{border-color:var(--green)}
.cond.on{border-color:var(--green);background:#eaf6ee}
.cond.na{opacity:.45;cursor:not-allowed}
.cond b{font-size:14.5px}
.cond p{margin:3px 0 0;font-size:12.5px;color:var(--muted);line-height:1.45}
.sum{background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:28px;position:sticky;top:88px;
box-shadow:0 8px 28px rgba(14,61,38,.07)}
.sum img{height:130px;display:block;margin:0 auto 16px}
.sum .dev{font:700 18px "Bricolage Grotesque",sans-serif;text-align:center;color:var(--deep)}
.sum .picks{color:var(--muted);font-size:13.5px;text-align:center;margin:4px 0 18px;min-height:20px}
.sum .pricebox{background:var(--ground);border-radius:14px;padding:18px;text-align:center;margin-bottom:16px}
.sum .pl{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:700}
.sum .price{font:800 50px/1.15 "Bricolage Grotesque",sans-serif;color:var(--green);font-variant-numeric:tabular-nums}
.sum .price.dim{color:var(--muted);font-size:26px}
.sum .lock{font-size:12.5px;color:var(--muted);margin-top:2px}
.sum button{width:100%;background:var(--brand);color:#fff;font:700 15px "Figtree",sans-serif;padding:15px;border:0;
border-radius:99px;cursor:pointer}
.sum button:hover:not(:disabled){background:var(--deep)}
.sum button:disabled{background:var(--line);color:var(--muted);cursor:not-allowed}
.sum .trust{display:grid;gap:8px;margin-top:16px;font-size:13px;color:var(--muted)}
.sum .trust span::before{content:"\\2713 ";color:var(--green);font-weight:800}
.toast{margin-top:12px;font-size:13px;color:var(--green);text-align:center;min-height:18px;font-weight:700}
@media(max-width:900px){.layout{grid-template-columns:1fr}.sum{position:static}.conds{grid-template-columns:1fr}}
"""

FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Figtree:wght@400;500;600;700&display=swap">'

def header(depth):
    p = "../" * depth
    return f'''<header><div class="wrap nav">
  <a class="logo" href="{p}index.html">OC<i>BuyBack</i></a>
  <nav class="links"><a href="{p}sell/index.html">Sell</a><a href="{p}trade-in/track/index.html">Track order</a><a href="{p}faq/index.html">FAQ</a><a href="{p}blog/index.html">Blog</a><a href="{p}contact-us/index.html">Contact</a></nav>
  <a class="cta" href="{p}sell/index.html">Get my quote</a>
  <a class="cta" id="cartPill" href="{p}sell/devices/index.html" style="display:none;margin-left:12px;background:var(--lime);color:var(--lime-ink)">Cart · 0</a>
</div></header>'''

CART_JS = '''<script>
const CART_KEY = "ocb_cart";
function cartGet(){ try { return JSON.parse(localStorage.getItem(CART_KEY)) || []; } catch(e) { return []; } }
function cartSave(c){ try { localStorage.setItem(CART_KEY, JSON.stringify(c)); } catch(e) {} }
function cartBadge(){
  const c = cartGet(), n = c.reduce((a,i)=>a+i.qty,0), t = c.reduce((a,i)=>a+i.price*i.qty,0);
  const el = document.getElementById("cartPill");
  if(el){ el.style.display = n ? "" : "none"; el.textContent = "Cart · " + n + " ($" + t.toLocaleString() + ")"; }
}
cartBadge();
// first-touch lead attribution: recorded once per visitor, sent with checkout
(function(){
  try {
    if (localStorage.getItem("ocb_attrib")) return;
    const q = new URLSearchParams(location.search);
    const ref = document.referrer || "";
    const sameSite = ref && new URL(ref).host === location.host;
    localStorage.setItem("ocb_attrib", JSON.stringify({
      r: sameSite ? "" : ref,
      l: location.pathname + location.search,
      us: q.get("utm_source") || "", um: q.get("utm_medium") || "", uc: q.get("utm_campaign") || "",
      t: new Date().toISOString(),
    }));
  } catch(e) {}
})();
</script>'''

def page(title, body, depth, extra_css="", *, path=None, desc="", schema=None,
         og_image=None, noindex=False, in_sitemap=True):
    p = "../" * depth
    head_extra = ""
    if path is not None:
        b = BASELINE.get(path, {})
        if b.get("title"): title = b["title"]
        if b.get("desc"): desc = b["desc"]
        canonical = SITE + (path if path != "/" else "/")
        head_extra += f'<link rel="canonical" href="{canonical}">\n'
        head_extra += f'<meta name="description" content="{html.escape(desc)}">\n'
        head_extra += (f'<meta property="og:title" content="{html.escape(title)}">\n'
                       f'<meta property="og:description" content="{html.escape(desc)}">\n'
                       f'<meta property="og:url" content="{canonical}">\n'
                       f'<meta property="og:type" content="website">\n'
                       f'<meta property="og:site_name" content="OCBuyBack">\n')
        if og_image:
            head_extra += f'<meta property="og:image" content="{html.escape(og_image)}">\n'
        if noindex:
            head_extra += '<meta name="robots" content="noindex,nofollow">\n'
        elif in_sitemap:
            SITEMAP.append((path, og_image))
    for s in (schema or []):
        head_extra += f'<script type="application/ld+json">{json.dumps(s)}</script>\n'
    if GA4_ID:
        head_extra += (f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>'
                       f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}'
                       f'gtag("js",new Date());gtag("config","{GA4_ID}");</script>\n')
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="icon" type="image/png" href="{p}favicon.png">
<link rel="apple-touch-icon" href="{p}apple-touch-icon.png">
{head_extra}{FONTS}
<style>{CSS}{extra_css}</style></head><body>
{header(depth)}
{CART_JS}
{body}
<footer>
<div class="wrap">
  <div class="cols">
    <div class="fbrand">
      <img src="{p}assets/logo-white.png" alt="OCBuyBack">
      <p>Cash for phones, tablets, watches, consoles and more — Brea's local buyback shop. Instant quotes, free shipping, paid within 1 business day.</p>
      <p>1203 W Imperial Hwy, STE 103<br>Brea, CA 92821<br><a href="tel:657-286-8274">657-286-8274</a> · <a href="mailto:support@ocbuyback.com">support@ocbuyback.com</a><br>Mon–Fri 10 AM – 6 PM</p>
    </div>
    <div><h4>Sell your device</h4><div class="flinks">
      <a href="{p}sell/cell-phone/apple/index.html">Apple iPhone</a>
      <a href="{p}sell/cell-phone/samsung/index.html">Samsung Galaxy</a>
      <a href="{p}sell/cell-phone/google/index.html">Google Pixel</a>
      <a href="{p}sell/tablet/apple/index.html">Apple iPad</a>
      <a href="{p}sell/smartwatch/apple/index.html">Apple Watch</a>
      <a href="{p}sell/game-console/index.html">Game Consoles</a>
      <a href="{p}sell/index.html">All devices →</a>
    </div></div>
    <div><h4>OCBuyBack</h4><div class="flinks">
      <a href="{p}trade-in/track/index.html">Track your order</a>
      <a href="{p}faq/index.html">FAQ</a>
      <a href="{p}blog/index.html">Blog</a>
      <a href="{p}locations/brea-ca-92821/index.html">Our Brea store</a>
      <a href="{p}contact-us/index.html">Contact us</a>
    </div></div>
    <div><h4>Follow us</h4><div class="flinks">
      {"".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in SOCIAL)}
    </div>
    <p style="margin-top:14px">★ 4.7 on Google<br>★ 4.8 on Trustpilot</p></div>
  </div>
  <div class="fbot">
    <div>© 2026 OCBuyBack · Brea, CA</div>
    <div><a href="{p}privacy-policy/index.html">Privacy Policy</a> · <a href="{p}terms-of-service/index.html">Terms of Service</a></div>
  </div>
</div></footer>
<a class="back" href="{p}../index.html">← All concepts</a>
</body></html>'''

def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

# ---- collect enabled models ----
models = []  # (cat, brand, device, model)
for cat in LIVE_CATS:
    for brand, devs in sorted(TREE.get(cat, {}).items()):
        for dev, m in devs.items():
            if m["enabled"] and model_max(m) > 0:
                models.append((cat, brand, dev, m))

# ---- device pages ----
count = 0
for cat, brand, dev, m in models:
    cslug, bslug, dslug = CAT_SLUG[cat], slug(brand), mslug(m, dev)
    q1, q2 = CAT_LABELS.get(cat, ("Which option?","Which configuration?"))
    # variants with at least one price
    variants = {c:{s:conds for s,conds in ss.items() if conds} for c,ss in m["variants"].items()}
    variants = {c:ss for c,ss in variants.items() if ss}
    carriers = sorted(variants.keys(), key=carrier_sort)
    single_carrier = len(carriers) == 1
    matrix = json.dumps(variants)
    cond_html = "".join(
        f'<div class="cond" data-v="{c}"><b>{c}</b><p>{COND_DESC[c]}</p></div>' for c in COND_ORDER)
    carrier_html = "".join(f'<button class="pill" data-v="{html.escape(c)}">{html.escape(c) if c != "-" else "Standard"}</button>' for c in carriers)
    q1_block = "" if single_carrier else f'''
      <div class="qs"><div class="label"><span class="badge">1</span> {q1}</div>
        <div class="pills" id="carrier">{carrier_html}</div></div>'''
    n2, n3 = ("1","2") if single_carrier else ("2","3")
    body = f'''
<div class="wrap">
  <div class="crumb"><a href="../../../index.html">Sell</a> → <a href="../../index.html">{cat}</a> → <a href="../index.html">{html.escape(brand)}</a> → <b>{html.escape(dev)}</b></div>
  <div class="layout">
    <div>
      <h1>Sell your {html.escape(dev)}</h1>
      <p class="sub">Answer the quick questions — your price locks for 14 days.</p>
      {q1_block}
      <div class="qs"><div class="label"><span class="badge">{n2}</span> {q2}</div>
        <div class="pills" id="storage"></div></div>
      <div class="qs"><div class="label"><span class="badge">{n3}</span> What condition is it in?</div>
        <div class="conds" id="cond">{cond_html}</div></div>
      <div id="condDetail" style="display:none;margin-top:12px;background:#eaf6ee;border:1.5px solid var(--green);border-radius:12px;padding:16px 18px">
        {"".join(f'<div class="cdet" data-c="{c}" style="display:none"><b style="font-size:14px;color:var(--deep)">{c} — what this means</b><p style="color:var(--muted);font-size:13px;margin:4px 0 6px">{COND_FULL[c][0]}</p><ol style="color:var(--muted);font-size:13px;margin:0;padding-left:20px">{"".join(f"<li>{x}</li>" for x in COND_FULL[c][1])}</ol>{BATTERY_NOTE if cat == "Cell Phone" and c in ("Flawless","Good","Fair") else ""}</div>' for c in COND_ORDER)}
      </div>
      <p style="color:var(--muted);font-size:13px;max-width:60ch;margin-top:10px">Not sure about condition? Pick your best guess — if our inspection differs, you get a new offer to accept, or we ship your device back free.</p>
    </div>
    <aside class="sum">
      <img src="{img_url(cat, brand, dev)}" alt="{html.escape(dev)}" onerror="this.style.display='none'">
      <div class="dev">{html.escape(brand)} {html.escape(dev)}</div>
      <div class="picks" id="picks">Make your picks to see the price</div>
      <div class="pricebox"><div class="pl">Your offer</div><div class="price dim" id="price">— —</div><div class="lock" id="lock"></div></div>
      <button id="go" disabled>Lock my price for 14 days</button>
      <div class="toast" id="toast"></div>
      <div class="trust"><span>Free prepaid USPS shipping label</span><span>Paid within 1 business day of arrival</span><span>PayPal, Zelle, Venmo, check — or cash in store</span></div>
    </aside>
  </div>
</div>
<script>
const M = {matrix};
const SINGLE = {str(single_carrier).lower()};
const state = {{carrier: SINGLE ? Object.keys(M)[0] : null, storage: null, cond: null}};
function storkey(s){{const m=s.match(/([\\d.]+)\\s*(GB|TB|mm)?/i); if(!m) return 1e9; const v=parseFloat(m[1]); return (m[2]||"").toUpperCase()==="TB"?v*1024:v;}}
function renderStorage(){{
  const el = document.getElementById("storage"); el.innerHTML = "";
  if(!state.carrier) {{ el.innerHTML = '<span style="color:var(--muted);font-size:13.5px">Pick an option above first</span>'; return; }}
  Object.keys(M[state.carrier]).sort((a,b)=>storkey(a)-storkey(b)).forEach(s=>{{
    const b = document.createElement("button"); b.className = "pill"+(state.storage===s?" on":""); b.textContent = s; b.dataset.v = s;
    b.onclick = ()=>{{ state.storage = s; state.cond = null; renderStorage(); renderConds(); render(); }};
    el.appendChild(b);
  }});
}}
function renderConds(){{
  const avail = (state.carrier && state.storage) ? M[state.carrier][state.storage] : null;
  document.querySelectorAll("#cond .cond").forEach(c=>{{
    const has = avail && avail[c.dataset.v] > 0;
    c.classList.toggle("na", avail !== null && !has);
    c.classList.toggle("on", state.cond === c.dataset.v);
  }});
  // show the full grading criteria for the selected condition (like the live site)
  document.getElementById("condDetail").style.display = state.cond ? "block" : "none";
  document.querySelectorAll("#condDetail .cdet").forEach(d =>
    d.style.display = d.dataset.c === state.cond ? "block" : "none");
}}
document.querySelectorAll("#carrier .pill").forEach(b=>b.onclick=()=>{{
  state.carrier = b.dataset.v; state.storage = null; state.cond = null;
  document.querySelectorAll("#carrier .pill").forEach(x=>x.classList.toggle("on", x===b));
  renderStorage(); renderConds(); render();
}});
document.getElementById("cond").addEventListener("click", e=>{{
  const t = e.target.closest(".cond"); if(!t || t.classList.contains("na")) return;
  const avail = state.carrier && state.storage; if(!avail) return;
  state.cond = t.dataset.v; renderConds(); render();
}});
function render(){{
  const {{carrier, storage, cond}} = state;
  const parts = [SINGLE?null:carrier, storage, cond].filter(Boolean);
  document.getElementById("picks").textContent = parts.join(" · ") || "Make your picks to see the price";
  const priceEl = document.getElementById("price"), go = document.getElementById("go");
  const p = (carrier && storage && cond) ? M[carrier][storage][cond] : null;
  if(p > 0){{
    priceEl.textContent = "$" + p.toLocaleString(); priceEl.classList.remove("dim");
    document.getElementById("lock").textContent = "Locked through " + new Date(Date.now()+14*864e5).toLocaleDateString("en-US",{{month:"short",day:"numeric"}});
    go.disabled = false;
  }} else {{
    priceEl.textContent = "— —"; priceEl.classList.add("dim"); go.disabled = true;
    document.getElementById("lock").textContent = "";
  }}
}}
document.getElementById("go").onclick = ()=>{{
  const {{carrier, storage, cond}} = state;
  const p = M[carrier][storage][cond];
  const item = {{ id: [{json.dumps(brand)}, {json.dumps(dev)}, carrier, storage, cond].join("|"),
    brand: {json.dumps(brand)}, device: {json.dumps(dev)}, cat: {json.dumps(cat)},
    carrier: SINGLE ? "" : carrier, storage, cond, price: p,
    img: {json.dumps(img_url(cat, brand, dev))}, qty: 1 }};
  const c = cartGet();
  const ex = c.find(x => x.id === item.id);
  if (ex) ex.qty += 1; else c.push(item);
  cartSave(c);
  location.href = "../../../devices/index.html";
}};
renderStorage(); renderConds();
// prefill from feed deeplinks: ?carrier=at-t&storage=128gb&cond=like-new
(function(){{
  const q = new URLSearchParams(location.search);
  if (!q.get("storage") && !q.get("carrier")) return;
  const slug = s => (s === "Aluminium" ? "aluminum" : s).toLowerCase().replace(/&/g,"").replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"");
  const slug2 = s => (s === "Aluminium" ? "aluminum" : s).toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"");
  const CONDS = {{"brand-new":"Brand New","like-new":"Flawless","good-condition":"Good","fair":"Fair","minor-damage":"Minor Damage","damaged":"Broken"}};
  const want = (val, s) => val && (slug(val) === s || slug2(val) === s);
  const c = q.get("carrier");
  if (c && !SINGLE) {{
    const pill = [...document.querySelectorAll("#carrier .pill")].find(b => want(b.dataset.v, c));
    if (pill) pill.click();
  }}
  const st = q.get("storage");
  if (st && state.carrier) {{
    const sp = [...document.querySelectorAll("#storage .pill")].find(b => want(b.dataset.v, st));
    if (sp) sp.click();
  }}
  const co = CONDS[q.get("cond")];
  if (co && state.carrier && state.storage) {{
    const cc = document.querySelector(`#cond .cond[data-v="${{co}}"]`);
    if (cc && !cc.classList.contains("na")) cc.click();
  }}
}})();
</script>'''
    live_path = f"/sell/{cslug}/{bslug}/{dslug}"
    mx = model_max(m)
    product_schema = {
        "@context": "https://schema.org", "@type": "Product",
        "name": f"{brand} {dev}", "image": img_url(cat, brand, dev),
        "brand": {"@type": "Brand", "name": brand},
        "description": f"Sell your {brand} {dev} for cash at OCBuyBack in Brea, CA — instant quote, free shipping, paid within 1 business day.",
        "offers": {"@type": "Offer", "price": f"{mx:.2f}", "priceCurrency": "USD",
                   "availability": "https://schema.org/InStock", "url": SITE + live_path,
                   "seller": {"@id": SITE + "/#org"}},
    }
    crumbs = breadcrumbs([("Sell", "/sell"), (cat, f"/sell/{cslug}"), (brand, f"/sell/{cslug}/{bslug}"), (dev, None)])
    write(OUT/"sell"/cslug/bslug/dslug/"index.html",
          page(f"Sell {dev} Brea, CA | OCBuyBack", body, 4, WIZ_CSS,
               path=live_path,
               desc=f"Cash for {dev} in Brea, CA 92821 — up to {money(mx)}. Instant quote locked for 14 days, free shipping, paid within 1 business day.",
               schema=[product_schema, crumbs], og_image=img_url(cat, brand, dev)))
    count += 1

# ---- category pages: brand picker when multiple brands, else model grid ----
BRAND_LINE = {("Cell Phone","Apple"):"iPhone", ("Cell Phone","Samsung"):"Galaxy", ("Cell Phone","Google"):"Pixel",
  ("Cell Phone","OnePlus"):"OnePlus", ("Cell Phone","Motorola"):"moto & razr", ("Cell Phone","LG"):"LG",
  ("Tablet","Apple"):"iPad", ("Tablet","Samsung"):"Galaxy Tab", ("Tablet","Microsoft"):"Surface",
  ("Smartwatch","Apple"):"Apple Watch", ("Smartwatch","Samsung"):"Galaxy Watch",
  ("Game Console","Sony"):"PlayStation", ("Game Console","Microsoft"):"Xbox",
  ("Game Console","Nintendo"):"Switch, Game Boy & more", ("Game Console","Asus"):"ROG Ally",
  ("Game Console","Valve"):"Steam Deck", ("Game Console","Playstation"):"PlayStation"}

def brand_logo(brand):
    return f"https://s3.amazonaws.com/fliptech-assets/images/brands/{slug(brand)}.webp"

def model_cards(cat, brand, devs, depth_prefix=""):
    return "".join(
        f"""<a class="card" href="{depth_prefix}{slug(brand)}/{mslug(m, d)}/index.html">
<img src="{img_url(cat, brand, d)}" alt="" onerror="this.style.display='none'">
<div class="name">{html.escape(d)}</div><div class="val">{money(model_max(m))} <small>up to</small></div></a>"""
        for d, m in devs)

for cat in LIVE_CATS:
    cslug = CAT_SLUG[cat]
    brands = TREE.get(cat, {})
    # sellable models per brand, newest first
    by_brand = {}
    for brand in brands:
        devs = [(d, m) for d, m in brands[brand].items() if m["enabled"] and model_max(m) > 0]
        if devs:
            devs.sort(key=lambda x: x[1]["sort"], reverse=True)
            by_brand[brand] = devs
    # Apple first (user rule), then by model count
    order = sorted(by_brand, key=lambda b: (b != "Apple", -len(by_brand[b]), b))

    # brand picker page (like the live site) + a page per brand
    tiles = "".join(f"""<a class="card" href="{slug(b)}/index.html" style="padding:28px 20px">
<img src="{brand_logo(b)}" alt="{html.escape(b)} logo" style="height:64px;object-fit:contain" onerror="this.style.display='none'">
<div class="name" style="font-size:17px;margin-top:6px">{html.escape(b)}</div>
<div style="color:var(--green);font-weight:700;font-size:13px">{html.escape(BRAND_LINE.get((cat, b), ""))}</div>
<div class="val" style="font-size:14px">up to {money(max(model_max(m) for _, m in by_brand[b]))}</div>
<div style="color:var(--muted);font-size:12.5px">{len(by_brand[b])} models</div></a>"""
        for b in order)
    body = f"""
<div class="wrap">
  <div class="crumb"><a href="../index.html">Sell</a> → <b>{cat}</b></div>
  <h1>Sell your {SELL_YOUR.get(cat, cat.lower())}</h1>
  <p class="sub">Pick your brand to see every model we buy.</p>
  <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(220px,1fr))">{tiles}</div>
</div>"""
    write(OUT/"sell"/cslug/"index.html",
          page(f"Sell {CAT_DISPLAY[cat]} Near Me Brea, CA | OCBuyBack", body, 2,
               path=f"/sell/{cslug}",
               desc=f"Sell your {SELL_YOUR.get(cat, cat.lower())} for cash near Brea, CA. Pick your brand for an instant quote — locked for 14 days, free shipping, paid within 1 business day.",
               schema=[breadcrumbs([("Sell", "/sell"), (cat, None)])]))
    for b in order:
        line = BRAND_LINE.get((cat, b), "")
        bbody = f"""
<div class="wrap">
  <div class="crumb"><a href="../../index.html">Sell</a> → <a href="../index.html">{cat}</a> → <b>{html.escape(b)}</b></div>
  <h1>Sell your {html.escape(line or b)}</h1>
  <p class="sub">Pick your model for an instant quote — prices lock for 14 days.</p>
  <div class="grid">{model_cards(cat, b, by_brand[b], "../")}</div>
</div>"""
        write(OUT/"sell"/cslug/slug(b)/"index.html",
              page(f"Sell {line or b} Near Me Brea, CA | OCBuyBack", bbody, 3,
                   path=f"/sell/{cslug}/{slug(b)}", in_sitemap=False,
                   desc=f"Sell your {line or b} for cash near Brea, CA — instant quotes on every model, free shipping, paid within 1 business day.",
                   schema=[breadcrumbs([("Sell", "/sell"), (cat, f"/sell/{cslug}"), (b, None)])]))

# ---- sell hub ----
cat_cards = []
for cat in LIVE_CATS:
    devs = [(b,d,m) for b,dd in TREE.get(cat,{}).items() for d,m in dd.items() if m["enabled"] and model_max(m) > 0]
    if not devs: continue
    top = max(devs, key=lambda x: model_max(x[2]))
    n = len(devs)
    cat_cards.append(f'''<a class="card" href="{CAT_SLUG[cat]}/index.html">
<img src="{img_url(cat, top[0], top[1])}" alt="" onerror="this.style.display='none'">
<div class="name">{CAT_DISPLAY[cat]}</div><div class="val">up to {money(model_max(top[2]))}</div>
<div style="color:var(--muted);font-size:12.5px;margin-top:2px">{n} models</div></a>''')
body = f'''
<div class="wrap">
  <div class="crumb"><b>Sell</b></div>
  <h1>What are you selling?</h1>
  <p class="sub">Every price is a real offer, locked for 14 days once you start a trade-in.</p>
  <div class="grid">{"".join(cat_cards)}</div>
</div>'''
write(OUT/"sell"/"index.html",
      page("Sell your device for cash | OCBuyBack", body, 1, path="/sell",
           desc="Sell your cell phone, tablet, smartwatch, game console, GoPro and more for cash. Instant quotes, free shipping, paid within 1 business day."))

# ---- cart + checkout page (/sell/devices/ like the live site) ----
CART_CSS = """
.cartgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px;margin-bottom:8px}
.item{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:20px;text-align:center;position:relative}
.item img{height:96px;width:auto;max-width:100%;object-fit:contain;display:block;margin:0 auto 12px}
.item .name{font-weight:700;font-size:14.5px}
.item .spec{color:var(--muted);font-size:12.5px;margin:2px 0 8px}
.item .price{color:var(--green);font-weight:800;font-size:18px;font-variant-numeric:tabular-nums}
.item .qty{display:flex;align-items:center;justify-content:center;gap:12px;margin:10px 0 4px}
.item .qty button{width:30px;height:30px;border-radius:50%;border:1.5px solid var(--line);background:var(--ground);
font-weight:800;font-size:15px;cursor:pointer;color:var(--ink)}
.item .qty button:hover{border-color:var(--green)}
.item .rm{background:none;border:0;color:var(--muted);font-size:12.5px;font-weight:600;cursor:pointer;
text-decoration:underline;margin-top:6px;font-family:inherit}
.item .rm:hover{color:#b3372b}
.addmore{border:1.5px dashed var(--line);background:var(--ground);border-radius:16px;display:flex;flex-direction:column;
align-items:center;justify-content:center;gap:10px;padding:20px;color:var(--muted);font-weight:600;font-size:14px;min-height:220px}
.addmore:hover{border-color:var(--green);color:var(--green)}
.totalbar{display:flex;justify-content:space-between;align-items:center;background:var(--deep);color:#eaf4ec;
border-radius:16px;padding:20px 26px;margin:18px 0 44px}
.totalbar b{font:800 26px/1 "Bricolage Grotesque",sans-serif;color:var(--lime);font-variant-numeric:tabular-nums}
.totalbar span{font-size:13.5px;color:#bcd6c4}
/* form */
.co{display:grid;grid-template-columns:1.5fr 1fr;gap:36px;align-items:start;padding-bottom:80px}
.fs{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:26px;margin-bottom:16px}
.fs h2{font:700 18px "Bricolage Grotesque",sans-serif;color:var(--deep);margin:0 0 16px}
.frow{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.field{margin-bottom:12px}
.field.full{grid-column:1/-1}
.field label{display:block;font-weight:600;font-size:13px;margin-bottom:5px}
.field input,.field select{width:100%;background:var(--ground);border:1.5px solid var(--line);border-radius:10px;
padding:12px 14px;font:400 15px "Figtree",sans-serif;color:var(--ink)}
.field input:focus,.field select:focus{outline:none;border-color:var(--green)}
.field.err input,.field.err select{border-color:#b3372b}
.field .hint{font-size:12px;color:#b3372b;margin-top:4px;min-height:14px}
.pay{display:grid;gap:10px}
.payopt{border:1.5px solid var(--line);border-radius:12px;padding:14px 16px;cursor:pointer;background:var(--ground)}
.payopt.on{border-color:var(--green);background:#eaf6ee}
.payopt b{font-size:14.5px}
.payopt p{margin:3px 0 0;font-size:12.5px;color:var(--muted)}
.payopt .extra{margin-top:10px;display:none}
.payopt.on .extra{display:block}
.consent{display:flex;gap:10px;align-items:flex-start;font-size:13.5px;color:var(--muted);margin-bottom:10px}
.consent input{margin-top:3px;accent-color:var(--green)}
.side{background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:26px;position:sticky;top:88px;
box-shadow:0 8px 28px rgba(14,61,38,.07)}
.side .row{display:flex;justify-content:space-between;font-size:14px;padding:7px 0;border-bottom:1px solid var(--line)}
.side .row:last-of-type{border-bottom:none}
.side .row b{font-variant-numeric:tabular-nums}
.side .tot{display:flex;justify-content:space-between;align-items:baseline;margin:12px 0 16px}
.side .tot b{font:800 34px/1 "Bricolage Grotesque",sans-serif;color:var(--green);font-variant-numeric:tabular-nums}
.side button{width:100%;background:var(--brand);color:#fff;font:700 15px "Figtree",sans-serif;padding:15px;border:0;
border-radius:99px;cursor:pointer}
.side button:hover:not(:disabled){background:var(--deep)}
.side button:disabled{background:var(--line);color:var(--muted);cursor:not-allowed}
.side .trust{display:grid;gap:8px;margin-top:16px;font-size:13px;color:var(--muted)}
.side .trust span::before{content:"\\2713 ";color:var(--green);font-weight:800}
/* empty + success */
.bigstate{text-align:center;padding:60px 0 90px}
.bigstate .emoji{font-size:44px}
.bigstate h2{font:800 28px "Bricolage Grotesque",sans-serif;color:var(--deep);margin:14px 0 8px}
.bigstate p{color:var(--muted);max-width:52ch;margin:0 auto 24px}
.bigstate .btn{display:inline-block;background:var(--green);color:#fff;font-weight:700;padding:14px 26px;border-radius:99px}
.steps3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;max-width:760px;margin:30px auto 0;text-align:left}
.steps3 .s{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px}
.steps3 .s b{display:block;font-size:14px;margin-bottom:4px}
.steps3 .s p{font-size:13px;color:var(--muted);margin:0}
@media(max-width:900px){.co{grid-template-columns:1fr}.side{position:static}.frow{grid-template-columns:1fr}.steps3{grid-template-columns:1fr}}
"""

STATES = ["AL","AK","AZ","AR","CA","CO","CT","DE","DC","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
"MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX",
"UT","VT","VA","WA","WV","WI","WY","PR"]
state_opts = '<option value="">Select a state</option>' + "".join(f'<option>{s}</option>' for s in STATES)

cart_body = f'''
<div class="wrap">
  <div class="crumb"><a href="../index.html">Sell</a> → <b>Your trade-in</b></div>

  <div id="emptyState" class="bigstate" style="display:none">
    <div class="emoji">📦</div>
    <h2>Nothing here yet</h2>
    <p>Get an instant quote for your device — it takes about 90 seconds and the price locks for 14 days.</p>
    <a class="btn" href="../index.html">Pick a device to sell</a>
  </div>

  <div id="cartState" style="display:none">
    <h1>Your trade-in</h1>
    <p class="sub">Prices are locked for 14 days from the moment you check out.</p>
    <div class="cartgrid" id="items"></div>
    <div class="totalbar"><span>We'll email your free prepaid USPS shipping label right after checkout.</span>
      <div style="text-align:right"><span>Total offer</span><br><b id="barTotal">$0</b></div></div>

    <div class="co">
      <div>
        <div class="fs"><h2>Your details</h2>
          <div class="frow">
            <div class="field"><label for="fn">First name</label><input id="fn" autocomplete="given-name"><div class="hint"></div></div>
            <div class="field"><label for="ln">Last name</label><input id="ln" autocomplete="family-name"><div class="hint"></div></div>
            <div class="field full"><label for="a1">Address</label><input id="a1" autocomplete="address-line1"><div class="hint"></div></div>
            <div class="field full"><label for="a2">Address 2 <span style="color:var(--muted);font-weight:400">(optional)</span></label><input id="a2" autocomplete="address-line2"><div class="hint"></div></div>
            <div class="field"><label for="city">City</label><input id="city" autocomplete="address-level2"><div class="hint"></div></div>
            <div class="field"><label for="st">State</label><select id="st">{state_opts}</select><div class="hint"></div></div>
            <div class="field"><label for="zip">ZIP code</label><input id="zip" inputmode="numeric" autocomplete="postal-code"><div class="hint"></div></div>
            <div class="field"><label for="em">Email</label><input id="em" type="email" autocomplete="email"><div class="hint"></div></div>
            <div class="field full"><label for="ph">Phone</label><input id="ph" inputmode="tel" autocomplete="tel"><div class="hint"></div></div>
          </div>
        </div>
        <div class="fs"><h2>How do you want to get paid?</h2>
          <div class="pay" id="pay">
            <div class="payopt" data-v="PayPal"><b>PayPal</b><p>Sent to your PayPal within 1 business day of arrival.</p>
              <div class="extra field"><label for="paypal">PayPal email</label><input id="paypal"><div class="hint"></div></div></div>
            <div class="payopt" data-v="Check"><b>Check</b><p>Mailed to the address above within 1 business day of your device arriving.</p></div>
            <div class="payopt" data-v="Zelle"><b>Zelle</b><p>Sent within 1 business day of arrival.</p>
              <div class="extra field"><label for="zelle">Zelle email or phone</label><input id="zelle"><div class="hint"></div></div></div>
            <div class="payopt" data-v="Venmo"><b>Venmo</b><p>Sent within 1 business day of arrival.</p>
              <div class="extra field"><label for="venmo">Venmo username</label><input id="venmo" placeholder="@username"><div class="hint"></div></div></div>
            <div class="payopt" data-v="Cash in store"><b>Cash in store</b><p>Skip shipping — bring your device to 1203 W Imperial Hwy, Brea and get paid on the spot.</p></div>
          </div>
        </div>
        <div class="fs">
          <label class="consent"><input type="checkbox" id="tos"><span>I've read and accept the <a href="#" style="color:var(--green)">terms and conditions</a>.</span></label>
          <label class="consent"><input type="checkbox" id="sms"><span>Text me updates about my order (optional).</span></label>
        </div>
      </div>
      <aside class="side">
        <div id="sideRows"></div>
        <div class="tot"><span style="font-weight:700">Total offer</span><b id="sideTotal">$0</b></div>
        <button id="submit">Sell my device(s)</button>
        <div class="toast" id="coToast" style="margin-top:12px;font-size:13px;color:#b3372b;text-align:center;min-height:18px;font-weight:600"></div>
        <div class="trust"><span>Free prepaid USPS shipping label</span><span>Price locked for 14 days</span><span>Paid within 1 business day of arrival</span></div>
      </aside>
    </div>
  </div>

  <div id="doneState" class="bigstate" style="display:none">
    <div class="emoji">🎉</div>
    <h2>You're all set, <span id="doneName"></span>!</h2>
    <p>Order <b id="doneId" style="color:var(--deep)"></b> · total offer <b id="doneTotal" style="color:var(--green)"></b>, locked through <b id="doneLock"></b>.</p>
    <div class="steps3">
      <div class="s"><b>1 · Check your email</b><p>Your free prepaid USPS shipping label and packing instructions are on the way<span id="doneSms"></span>.</p></div>
      <div class="s"><b>2 · Pack and ship</b><p>Any sturdy box works. Drop it at any Post Office or USPS pickup.</p></div>
      <div class="s"><b>3 · Get paid</b><p>Paid by <span id="donePay"></span> within 1 business day of your device arriving.</p></div>
    </div>
    <p style="margin-top:28px"><a class="btn" href="../index.html">Sell another device</a></p>
    <p style="margin-top:10px"><a href="../../trade-in/track/index.html" style="color:var(--green);font-weight:700;font-size:14px">Track this order →</a></p>
  </div>
</div>
<script>
function money(v){{ return "$" + v.toLocaleString(); }}
let payMethod = null;
function renderCart(){{
  const c = cartGet();
  document.getElementById("emptyState").style.display = c.length ? "none" : "";
  document.getElementById("cartState").style.display = c.length ? "" : "none";
  if(!c.length) return;
  const items = document.getElementById("items");
  items.innerHTML = "";
  c.forEach((it,i)=>{{
    const d = document.createElement("div"); d.className = "item";
    const spec = [it.carrier, it.storage, it.cond].filter(Boolean).join(" / ");
    d.innerHTML = `<img src="${{it.img}}" onerror="this.style.display='none'">`+
      `<div class="name">${{it.brand}} ${{it.device}}</div><div class="spec">${{spec}}</div>`+
      `<div class="price">${{money(it.price)}}<small style="color:var(--muted);font-weight:500"> each</small></div>`+
      `<div class="qty"><button data-i="${{i}}" data-d="-1">−</button><b>${{it.qty}}</b><button data-i="${{i}}" data-d="1">+</button></div>`+
      `<button class="rm" data-i="${{i}}">Remove</button>`;
    items.appendChild(d);
  }});
  const add = document.createElement("a"); add.className = "addmore"; add.href = "../index.html";
  add.innerHTML = "<div style='font-size:28px'>+</div>Have another device to sell?";
  items.appendChild(add);
  const total = c.reduce((a,i)=>a+i.price*i.qty,0);
  document.getElementById("barTotal").textContent = money(total);
  document.getElementById("sideTotal").textContent = money(total);
  document.getElementById("sideRows").innerHTML = c.map(it=>
    `<div class="row"><span>${{it.device}} × ${{it.qty}}</span><b>${{money(it.price*it.qty)}}</b></div>`).join("");
  cartBadge();
}}
document.getElementById("items")?.addEventListener("click", e=>{{
  const t = e.target; if(!(t instanceof HTMLButtonElement)) return;
  const c = cartGet(); const i = +t.dataset.i;
  if(t.classList.contains("rm")) c.splice(i,1);
  else {{ c[i].qty += +t.dataset.d; if(c[i].qty < 1) c.splice(i,1); }}
  cartSave(c); renderCart();
}});
document.getElementById("pay").addEventListener("click", e=>{{
  const t = e.target.closest(".payopt");
  if(!t || e.target.closest("input")) return;
  payMethod = t.dataset.v;
  document.querySelectorAll(".payopt").forEach(x=>x.classList.toggle("on", x===t));
}});
function setErr(id, msg){{
  const f = document.getElementById(id).closest(".field");
  f.classList.toggle("err", !!msg); f.querySelector(".hint").textContent = msg || "";
}}
// ZIP -> city/state autofill (prevents typos; fields stay editable)
document.getElementById("zip").addEventListener("input", async (e) => {{
  const z = e.target.value.trim();
  if (!/^\\d{{5}}$/.test(z)) return;
  try {{
    const r = await fetch("https://api.zippopotam.us/us/" + z);
    if (!r.ok) {{ setErr("zip", "That ZIP doesn't look right — double-check it"); return; }}
    const d = await r.json();
    const place = d.places && d.places[0];
    if (place) {{
      const cityEl = document.getElementById("city"), stEl = document.getElementById("st");
      if (!cityEl.value.trim() || cityEl.dataset.auto) {{ cityEl.value = place["place name"]; cityEl.dataset.auto = "1"; }}
      if (!stEl.value || stEl.dataset.auto) {{ stEl.value = place["state abbreviation"]; stEl.dataset.auto = "1"; }}
      setErr("zip", ""); setErr("city", ""); setErr("st", "");
    }}
  }} catch(err) {{}}
}});
function validate(){{
  let ok = true;
  const req = {{fn:"First name", ln:"Last name", a1:"Address", city:"City", st:"State", zip:"ZIP", em:"Email", ph:"Phone"}};
  for(const [id,label] of Object.entries(req)){{
    const v = document.getElementById(id).value.trim();
    let msg = v ? "" : label + " is required";
    if(!msg && id==="zip" && !/^\\d{{5}}(-\\d{{4}})?$/.test(v)) msg = "Enter a 5-digit ZIP";
    if(!msg && id==="em" && !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(v)) msg = "Enter a valid email";
    if(!msg && id==="ph" && v.replace(/\\D/g,"").length < 10) msg = "Enter a 10-digit phone number";
    setErr(id, msg); if(msg) ok = false;
  }}
  if(payMethod === "PayPal"){{ const v = document.getElementById("paypal").value.trim(); setErr("paypal", v?"":"Required for PayPal"); if(!v) ok=false; }}
  if(payMethod === "Zelle"){{ const v = document.getElementById("zelle").value.trim(); setErr("zelle", v?"":"Required for Zelle"); if(!v) ok=false; }}
  if(payMethod === "Venmo"){{ const v = document.getElementById("venmo").value.trim(); setErr("venmo", v?"":"Required for Venmo"); if(!v) ok=false; }}
  const toast = document.getElementById("coToast");
  if(!payMethod){{ toast.textContent = "Pick how you'd like to get paid."; ok = false; }}
  else if(!document.getElementById("tos").checked){{ toast.textContent = "Please accept the terms and conditions."; ok = false; }}
  else if(!ok) toast.textContent = "A few fields need attention above.";
  else toast.textContent = "";
  return ok;
}}
document.getElementById("submit").addEventListener("click", async ()=>{{
  if(!validate()) return;
  const c = cartGet();
  let total = c.reduce((a,i)=>a+i.price*i.qty,0);
  let id = "OCB-" + Math.random().toString(36).slice(2,8).toUpperCase();
  let lockDate = new Date(Date.now()+14*864e5);
  // submit to the real API when deployed; static preview falls back to demo mode
  const btn = document.getElementById("submit");
  btn.disabled = true; btn.textContent = "Submitting…";
  try {{
    const val = x => document.getElementById(x).value.trim();
    const r = await fetch("/api/create-trade-in", {{ method: "POST",
      headers: {{ "content-type": "application/json" }},
      body: JSON.stringify({{
        customer: {{ first_name: val("fn"), last_name: val("ln"), address1: val("a1"),
          address2: val("a2"), city: val("city"), state: val("st"), zip: val("zip"),
          email: val("em"), phone: val("ph") }},
        items: c,
        payment: {{ method: payMethod,
          detail: payMethod === "PayPal" ? val("paypal") : payMethod === "Zelle" ? val("zelle") : payMethod === "Venmo" ? val("venmo") : null }},
        sms_opt_in: document.getElementById("sms").checked,
        attrib: (()=>{{ try {{ return JSON.parse(localStorage.getItem("ocb_attrib")); }} catch(e) {{ return null; }} }})(),
      }}) }});
    if (r.ok) {{
      const d = await r.json();
      id = d.order_number; total = d.total; lockDate = new Date(d.locked_until + "T12:00:00");
    }} else if ((r.headers.get("content-type") || "").includes("json")) {{
      // a real API answered with an error — show it; non-JSON = static preview, demo mode
      const d = await r.json().catch(()=>({{}}));
      document.getElementById("coToast").textContent = d.error || "Something went wrong — please try again.";
      btn.disabled = false; btn.textContent = "Sell my device(s)";
      return;
    }}
  }} catch(e) {{ /* static preview / offline: demo mode */ }}
  btn.disabled = false; btn.textContent = "Sell my device(s)";
  document.getElementById("doneName").textContent = document.getElementById("fn").value.trim();
  document.getElementById("doneId").textContent = id;
  document.getElementById("doneTotal").textContent = money(total);
  document.getElementById("doneLock").textContent = lockDate.toLocaleDateString("en-US",{{month:"long",day:"numeric"}});
  document.getElementById("donePay").textContent = ({{"Check":"check","Cash in store":"cash in store"}})[payMethod] || payMethod;
  document.getElementById("doneSms").textContent = document.getElementById("sms").checked ? ", plus text updates" : "";
  if(payMethod === "Cash in store"){{
    document.querySelector(".steps3").innerHTML = "<div class='s'><b>1 · Check your email</b><p>Your order confirmation is on the way.</p></div>"+
      "<div class='s'><b>2 · Come by the shop</b><p>1203 W Imperial Hwy, STE 103, Brea — Mon–Fri 10 AM to 6 PM.</p></div>"+
      "<div class='s'><b>3 · Get paid</b><p>We evaluate while you wait (about 10 minutes) and pay cash on the spot.</p></div>";
  }}
  cartSave([]); cartBadge();
  document.getElementById("cartState").style.display = "none";
  document.getElementById("doneState").style.display = "";
  window.scrollTo(0,0);
}});
renderCart();
</script>'''

write(OUT/"sell"/"devices"/"index.html",
      page("Your trade-in | OCBuyBack", cart_body, 2, WIZ_CSS + CART_CSS,
           path="/sell/devices", desc="Review your trade-in and check out.", noindex=True))

# ---- track order page (/trade-in/track like the live site) ----
TRACK_CSS = """
.lookup{max-width:520px;margin:40px auto 80px;background:var(--surface);border:1px solid var(--line);
border-radius:20px;padding:34px;box-shadow:0 8px 28px rgba(14,61,38,.07);text-align:center}
.lookup h1{margin-bottom:6px}
.lookup p{color:var(--muted);margin:0 0 22px}
.lookup .field{text-align:left;margin-bottom:12px}
.lookup label{display:block;font-weight:600;font-size:13px;margin-bottom:5px}
.lookup input{width:100%;background:var(--ground);border:1.5px solid var(--line);border-radius:10px;
padding:13px 14px;font:400 15px "Figtree",sans-serif;color:var(--ink)}
.lookup input:focus{outline:none;border-color:var(--green)}
.lookup button{width:100%;background:var(--brand);color:#fff;font:700 15px "Figtree",sans-serif;
padding:15px;border:0;border-radius:99px;cursor:pointer;margin-top:6px}
.lookup button:hover{background:var(--deep)}
.lookup .err{color:#b3372b;font-size:13.5px;font-weight:600;min-height:18px;margin-top:10px}
/* result */
.result{max-width:720px;margin:34px auto 80px;display:none}
.shead{background:var(--deep);color:#eaf4ec;border-radius:20px;padding:28px 30px;margin-bottom:16px}
.shead .on{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#bcd6c4;font-weight:700}
.shead h1{color:#fff;font-size:24px;margin:6px 0 4px}
.shead .sub2{color:#bcd6c4;font-size:14px}
.prog{display:flex;margin:22px 0 4px;gap:6px}
.prog .p{flex:1;text-align:center;font-size:12px;font-weight:700;color:#7fa38a}
.prog .p .bar{height:6px;border-radius:99px;background:rgba(255,255,255,.15);margin-bottom:8px}
.prog .p.done .bar{background:var(--lime)}
.prog .p.done{color:var(--lime)}
.banner{border-radius:14px;padding:14px 18px;font-size:14.5px;font-weight:600;margin-bottom:16px}
.banner.warn{background:#faf0e2;color:#b45d0e}
.banner.crit{background:#f9e9e6;color:#b3372b}
.rcard{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:22px 24px;margin-bottom:16px}
.rcard h2{font:700 16px "Bricolage Grotesque",sans-serif;color:var(--deep);margin:0 0 12px}
.ritem{display:flex;justify-content:space-between;gap:14px;padding:9px 0;border-bottom:1px solid var(--line);font-size:14.5px}
.ritem:last-child{border-bottom:none}
.ritem .money{font-weight:700}
.ritem .fin{color:var(--green);font-size:12.5px;font-weight:700}
.tl{list-style:none;margin:0;padding:0}
.tl li{position:relative;padding:0 0 18px 26px;font-size:14px}
.tl li::before{content:"";position:absolute;left:6px;top:5px;width:9px;height:9px;border-radius:50%;
background:var(--green)}
.tl li::after{content:"";position:absolute;left:10px;top:16px;bottom:-2px;width:1.5px;background:var(--line)}
.tl li:last-child::after{display:none}
.tl .when{color:var(--muted);font-size:12.5px}
.again{text-align:center;margin-top:6px}
.again button{background:none;border:0;color:var(--green);font:600 14px "Figtree",sans-serif;cursor:pointer;text-decoration:underline}
.demo-note{background:var(--lime);color:var(--lime-ink);border-radius:10px;padding:8px 14px;font-size:12.5px;
font-weight:700;text-align:center;margin-bottom:16px;display:none}
"""

track_body = '''
<div class="wrap">
  <div class="lookup" id="lookup">
    <h1>Track your order</h1>
    <p>Enter your order number and the email you used at checkout.</p>
    <div class="field"><label for="tOrder">Order number</label><input id="tOrder" placeholder="OCB-XXXXXX" autocomplete="off"></div>
    <div class="field"><label for="tEmail">Email</label><input id="tEmail" type="email" placeholder="you@example.com"></div>
    <button id="tGo">Track my order</button>
    <div class="err" id="tErr"></div>
  </div>

  <div class="result" id="result">
    <div class="demo-note" id="demoNote">Sample data — live tracking connects when the site is deployed.</div>
    <div class="shead">
      <div class="on">Order <span id="rOrder"></span></div>
      <h1 id="rLabel"></h1>
      <div class="sub2" id="rMeta"></div>
      <div class="prog" id="rProg"></div>
    </div>
    <div id="rBanner"></div>
    <div class="rcard"><h2>Your devices</h2><div id="rItems"></div></div>
    <div class="rcard"><h2>History</h2><ul class="tl" id="rHist"></ul></div>
    <div class="again"><button id="tAgain">Track a different order</button></div>
  </div>
</div>
<script>
const STEPS = ["Order placed","Shipped","Received","Evaluating","Paid"];
const STEP_OF = { initiated:0, shipped:1, delivered:1, received:2, evaluating:3, adjusted:3, action_pending:3, paid:4 };
const money = v => "$" + Number(v).toLocaleString();
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function demoData(order){
  const d = 864e5, now = Date.now();
  return { order_number: order || "OCB-DEMO42", status: "evaluating",
    status_label: "Device being evaluated",
    total_quote: 905, total_paid: null, tracking_number: "9400 1234 5678 9012 3456 78",
    created_at: new Date(now - 3*d).toISOString(),
    items: [{ brand:"Apple", model:"iPhone 17 Pro Max", condition:"Flawless", quoted_price:905, qty:1 }],
    history: [
      { status:"initiated", note:"Order created — shipping label emailed.", created_at:new Date(now-3*d).toISOString() },
      { status:"received", note:"Package arrived at our Brea location.", created_at:new Date(now-1*d).toISOString() },
      { status:"evaluating", note:"Diagnostics in progress.", created_at:new Date(now-3600e3).toISOString() } ] };
}
function render(d){
  document.getElementById("lookup").style.display = "none";
  document.getElementById("result").style.display = "block";
  document.getElementById("rOrder").textContent = d.order_number;
  document.getElementById("rLabel").textContent = d.status_label || d.status;
  const meta = [];
  meta.push("Placed " + new Date(d.created_at).toLocaleDateString("en-US",{month:"long",day:"numeric"}));
  meta.push("Quote " + money(d.total_quote));
  if (d.total_paid != null) meta.push("Paid " + money(d.total_paid));
  if (d.tracking_number) meta.push("USPS " + d.tracking_number);
  document.getElementById("rMeta").textContent = meta.join(" · ");
  const stepIdx = STEP_OF[d.status];
  document.getElementById("rProg").innerHTML = stepIdx == null ? "" :
    STEPS.map((s,i)=>`<div class="p ${i<=stepIdx?"done":""}"><div class="bar"></div>${s}</div>`).join("");
  const banner = document.getElementById("rBanner");
  banner.innerHTML = d.status === "adjusted"
    ? '<div class="banner warn">We sent you a revised offer by email — check your inbox to accept or decline.</div>'
    : d.status === "action_pending" ? '<div class="banner warn">We emailed you — a quick action on your end keeps things moving.</div>'
    : d.status === "returned" ? '<div class="banner warn">Your device has been shipped back to you.</div>'
    : d.status === "cancelled" ? '<div class="banner crit">This order was cancelled.</div>' : "";
  document.getElementById("rItems").innerHTML = (d.items || []).map(it => `
    <div class="ritem"><span><b>${esc(it.brand)} ${esc(it.model)}</b> × ${it.qty}
      <span style="color:var(--muted)">· ${esc(it.condition)}</span>
      ${it.final_price != null ? `<span class="fin"> → final ${money(it.final_price)}${it.final_condition ? " (" + esc(it.final_condition) + ")" : ""}</span>` : ""}</span>
      <span class="money">${money(it.quoted_price * it.qty)}</span></div>`).join("");
  document.getElementById("rHist").innerHTML = (d.history || []).map(h => `
    <li><b>${esc(h.note || h.status)}</b><div class="when">${new Date(h.created_at).toLocaleString("en-US",
      {month:"short",day:"numeric",hour:"numeric",minute:"2-digit"})}</div></li>`).join("");
}
document.getElementById("tGo").onclick = async () => {
  const order = document.getElementById("tOrder").value.trim().toUpperCase();
  const email = document.getElementById("tEmail").value.trim();
  const err = document.getElementById("tErr");
  if (!order || !email) { err.textContent = "Both fields are required."; return; }
  err.textContent = "";
  const btn = document.getElementById("tGo");
  btn.disabled = true; btn.textContent = "Looking up…";
  try {
    const r = await fetch(`/api/track-order?order=${encodeURIComponent(order)}&email=${encodeURIComponent(email)}`);
    if ((r.headers.get("content-type") || "").includes("json")) {
      const d = await r.json();
      if (!r.ok) { err.textContent = d.error || "Order not found."; }
      else render(d);
    } else {
      document.getElementById("demoNote").style.display = "block";
      render(demoData(order));
    }
  } catch(e) {
    document.getElementById("demoNote").style.display = "block";
    render(demoData(order));
  }
  btn.disabled = false; btn.textContent = "Track my order";
};
document.getElementById("tEmail").addEventListener("keydown", e => { if (e.key === "Enter") document.getElementById("tGo").click(); });
document.getElementById("tAgain").onclick = () => {
  document.getElementById("result").style.display = "none";
  document.getElementById("lookup").style.display = "block";
};
</script>'''

write(OUT/"trade-in"/"track"/"index.html",
      page("Track your order | OCBuyBack", track_body, 2, TRACK_CSS,
           path="/trade-in/track", in_sitemap=False,
           desc="Track your OCBuyBack trade-in from shipment through payment with your order number and email."))

# ---- static pages: /faq, /contact-us, /privacy-policy, /terms-of-service ----
STATIC_CSS = """
.narrow{max-width:760px;margin:0 auto;padding-bottom:80px}
details{border:1px solid var(--line);border-radius:12px;margin-bottom:10px;background:var(--surface)}
summary{padding:16px 20px;font-weight:700;font-size:15px;cursor:pointer;list-style:none}
summary::before{content:"+";color:var(--green);margin-right:12px;font-weight:800}
details[open] summary::before{content:"–"}
details p{padding:0 20px 16px;margin:0;color:var(--muted);font-size:14.5px;max-width:65ch}
.legal p{color:var(--muted);font-size:14.5px;line-height:1.7;margin:0 0 14px}
.legal h2{font:700 19px "Bricolage Grotesque",sans-serif;color:var(--deep);margin:30px 0 10px}
.contact-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:8px}
.ccard{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:26px}
.ccard h2{font:700 18px "Bricolage Grotesque",sans-serif;color:var(--deep);margin:0 0 12px}
.ccard p{margin:0 0 8px;font-size:15px}
.ccard a{color:var(--green);font-weight:700}
.ccard .hours{display:grid;grid-template-columns:auto 1fr;gap:6px 22px;font-size:14.5px;color:var(--muted);margin-top:8px}
.ccard .hours b{color:var(--ink)}
.ccard .btn{display:inline-block;background:var(--brand);color:#fff;font-weight:700;font-size:14px;
padding:12px 22px;border-radius:99px;margin-top:12px}
.ccard .btn:hover{background:var(--deep)}
@media(max-width:760px){.contact-grid{grid-template-columns:1fr}}
"""

FAQS = [
    ("How long is my offer good for?",
     "The offer is good for 14 days beginning the day the order is submitted to us. If an item arrives after the 14-day mark, the current offer for the device will be given."),
    ("How do I ship an item?",
     "After checkout we email you a free prepaid USPS shipping label. Pack your device in any sturdy box and drop it at any Post Office or USPS pickup location."),
    ("How do I track my package?",
     "Use the Track Order page with your order number and email — you can follow your trade-in from shipment through payment."),
    ("How are the electronics evaluated?",
     "Devices are evaluated with diagnostic software that verifies the model and tests all functionality, then manually inspected for physical condition, authenticity, water damage, and account locks. If your self-assessment was accurate, payment is sent in the method you selected. If not, we send a revised offer you can accept — or we ship your item back free."),
    ("What do I need to send in to get the quoted offer amount?",
     "Just the device itself unless noted otherwise. Include chargers or accessories only when the quote page asks for them."),
    ("What if I'm not sure about the condition of my product?",
     "Pick your best guess — every device is checked on arrival. If our grade differs you'll get a new offer to accept, or we return your device free."),
    ("How and when will I get paid?",
     "Within 1 business day of your device arriving — by PayPal, Zelle, Venmo, or check. Locals can choose cash on the spot at our Brea store."),
    ("Is there a limit on the number of items I can sell?",
     "No — sell one device or a whole drawer full. Bulk trade-ins welcome."),
    ("What if I do not agree with the evaluation of my phone?",
     "You can reject the revised offer and we'll ship your device back to you at no cost."),
    ("My package weighs more than the weight shown on the shipping label. What should I do?",
     "That's okay — USPS bills us for any difference in weight, not you. Just ship it."),
]

faq_body = f'''
<div class="wrap narrow">
  <div class="crumb"><a href="../index.html">Home</a> → <b>FAQ</b></div>
  <h1>Frequently asked questions</h1>
  <p class="sub">Everything sellers usually ask — and if we missed something, <a href="../contact-us/index.html" style="color:var(--green);font-weight:700">get in touch</a>.</p>
  {"".join(f"<details{' open' if i == 0 else ''}><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>" for i, (q, a) in enumerate(FAQS))}
</div>'''
faq_schema = {"@context": "https://schema.org", "@type": "FAQPage",
    "mainEntity": [{"@type": "Question", "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQS]}
write(OUT/"faq"/"index.html",
      page("Questions about selling your device at OCBuyBack", faq_body, 1, STATIC_CSS,
           path="/faq",
           desc="How long is my offer good for? How do I ship? How and when will I get paid? Answers to every question about selling your device to OCBuyBack.",
           schema=[faq_schema]))

contact_body = '''
<div class="wrap" style="max-width:920px;margin:0 auto;padding-bottom:80px">
  <div class="crumb"><a href="../index.html">Home</a> → <b>Contact us</b></div>
  <h1>Come by the shop, or say hello</h1>
  <p class="sub">Real people, real support — usually within a business day by email, instantly by phone during store hours.</p>
  <div class="contact-grid">
    <div class="ccard">
      <h2>The shop in Brea</h2>
      <p><b>1203 W Imperial Hwy, STE 103<br>Brea, CA 92821</b></p>
      <div class="hours">
        <b>Mon–Fri</b><span>10:00 AM – 6:00 PM</span>
        <b>Sat–Sun</b><span>Closed</span>
      </div>
      <a class="btn" href="https://www.google.com/maps/search/?api=1&query=OCBuyBack%201203%20W%20Imperial%20Hwy%20STE%20103%20Brea%20CA" target="_blank" rel="noopener">Get directions</a>
    </div>
    <div class="ccard">
      <h2>Reach us directly</h2>
      <p>Phone · <a href="tel:657-286-8274">657-286-8274</a></p>
      <p>Email · <a href="mailto:support@ocbuyback.com">support@ocbuyback.com</a></p>
      <p style="color:var(--muted);font-size:14px;margin-top:14px">Already sold to us? Have your order number handy — or check <a href="../trade-in/track/index.html" style="color:var(--green);font-weight:700">Track Order</a> first, it answers most questions.</p>
    </div>
  </div>
</div>'''
write(OUT/"contact-us"/"index.html",
      page("Contact OCBuyBack — Brea, CA", contact_body, 1, STATIC_CSS,
           path="/contact-us",
           desc="Visit OCBuyBack at 1203 W Imperial Hwy STE 103, Brea, CA 92821, call 657-286-8274, or email support@ocbuyback.com. Open Mon–Fri 10 AM to 6 PM.",
           schema=[STORE_SCHEMA]))

# privacy + terms from the live-site extraction (data/policies.json),
# payment methods updated to the new lineup
policies = json.load(open(ROOT/"data"/"policies.json"))
def legal_page(name, title):
    blocks = policies[name]
    out_html = []
    for b in blocks:
        txt = b["text"]
        if txt.strip() == title: continue
        txt = txt.replace("PayPal, check or cash(local pickup only for cash)",
                          "check, Zelle, Venmo, or cash (local pickup only for cash)")
        txt = re.sub(r"\bPayPal, check or cash\b", "check, Zelle, Venmo, or cash", txt)
        txt = txt.replace("126 Viking Ave", "1203 W Imperial Hwy, STE 103")  # old address in policy contact block
        txt = txt.replace("Chancellor Communications", "OCBuyBack")  # legal entity is OCBuyBack (user, Sep 8 2026)
        # question headings (privacy) and numbered sections (terms)
        if b["tag"] == "h" or (len(txt) < 120 and txt.endswith("?")):
            out_html.append(f"<h2>{html.escape(txt)}</h2>"); continue
        m2 = re.match(r"^(\d+\.\s+[^.]{3,70})\.\s+(.+)$", txt, re.S)
        if m2:
            out_html.append(f"<h2>{html.escape(m2.group(1))}</h2><p>{html.escape(m2.group(2))}</p>"); continue
        out_html.append(f"<p>{html.escape(txt)}</p>")
    return f'''
<div class="wrap narrow legal">
  <div class="crumb"><a href="../index.html">Home</a> → <b>{title}</b></div>
  <h1>{title}</h1>
  {"".join(out_html)}
</div>'''
write(OUT/"privacy-policy"/"index.html",
      page("Privacy Policy | OCBuyBack", legal_page("privacy-policy", "Privacy Policy"), 1, STATIC_CSS,
           path="/privacy-policy", desc="How OCBuyBack collects, uses, and protects your personal information."))
write(OUT/"terms-of-service"/"index.html",
      page("Terms of Service | OCBuyBack", legal_page("terms-of-service", "Terms of Service"), 1, STATIC_CSS,
           path="/terms-of-service", desc="The terms governing device trade-ins and use of ocbuyback.com."))

# ---- blog: /blog index + /blog/{y}/{m}/{d}/{slug} posts (paths verbatim) ----
BLOG_CSS = """
.bloggrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px;padding-bottom:70px}
.bpost{background:var(--surface);border:1px solid var(--line);border-radius:16px;overflow:hidden;
transition:transform .12s,box-shadow .12s;display:flex;flex-direction:column}
.bpost:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(14,61,38,.08)}
.bpost .thumb{height:170px;background:var(--ground) center/cover no-repeat}
.bpost .pad{padding:18px 20px 20px;display:flex;flex-direction:column;gap:6px;flex:1}
.bpost .date{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:700}
.bpost h2{font:700 16.5px/1.35 "Bricolage Grotesque",sans-serif;color:var(--deep);margin:0;text-wrap:balance}
.bpost p{color:var(--muted);font-size:13.5px;margin:0;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
/* post page */
.post{max-width:720px;margin:0 auto;padding-bottom:80px}
.post .date{font-size:12.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:700}
.post h1{margin:8px 0 18px}
.post .hero{width:100%;border-radius:20px;border:1px solid var(--line);margin-bottom:26px}
.post .body p{color:#33413a;font-size:16px;line-height:1.75;margin:0 0 16px;max-width:68ch}
.post .body h4,.post .body h5{font:700 20px "Bricolage Grotesque",sans-serif;color:var(--deep);margin:28px 0 10px}
.post .body a{color:var(--green);font-weight:600}
.post .body img{max-width:100%;border-radius:14px;margin:8px 0}
.post .body ul,.post .body ol{color:#33413a;font-size:16px;line-height:1.7;padding-left:22px}
.postcta{background:var(--deep);color:#eaf4ec;border-radius:20px;padding:30px;text-align:center;margin-top:36px}
.postcta b{font:800 20px "Bricolage Grotesque",sans-serif;color:#fff;display:block;margin-bottom:6px}
.postcta a{display:inline-block;background:var(--lime);color:var(--lime-ink);font-weight:800;font-size:14.5px;
padding:13px 26px;border-radius:99px;margin-top:14px}
"""

blog_posts = json.load(open(ROOT/"data"/"blog.json"))
def post_key(p):
    y, mo, d = p["path"].split("/")[:3]
    return (int(y), int(mo.lstrip("0") or 0), int(d))
blog_posts.sort(key=post_key, reverse=True)

def hero_src(bp, depth):
    """Migrated posts store a local asset filename; admin-created posts store a full URL."""
    h = bp["hero"]
    if not h: return None
    return h if h.startswith("http") else "../" * depth + "assets/blog/" + h

for bp in blog_posts:
    depth = 5  # blog/y/m/d/slug/
    hs = hero_src(bp, depth)
    hero_html = f'<img class="hero" src="{hs}" alt="{html.escape(bp["heading"])}">' if hs else ""
    body = bp["body"].replace("{ASSET}", "../"*depth + "assets/blog")
    post_body = f'''
<div class="wrap post">
  <div class="crumb"><a href="{"../"*depth}index.html">Home</a> → <a href="{"../"*depth}blog/index.html">Blog</a> → <b>{html.escape(bp["heading"][:48])}…</b></div>
  <div class="date">{html.escape(bp["date_display"])}</div>
  <h1>{html.escape(bp["heading"])}</h1>
  {hero_html}
  <div class="body">{body}</div>
  <div class="postcta"><b>Ready to turn your device into cash?</b>
    Get an instant offer — locked for 14 days, free shipping, paid within 1 business day.
    <br><a href="{"../"*depth}sell/index.html">Get my instant quote</a></div>
</div>'''
    y, mo, d = bp["path"].split("/")[:3]
    post_schema = {"@context": "https://schema.org", "@type": "BlogPosting",
        "headline": bp["heading"], "description": bp["description"],
        "datePublished": f"{y}-{(mo.lstrip('0') or '0').zfill(2)}-{d.zfill(2)}",
        "author": {"@id": SITE + "/#org"}, "publisher": {"@id": SITE + "/#org"},
        **({"image": bp["hero"] if bp["hero"].startswith("http") else SITE + "/assets/blog/" + bp["hero"]} if bp["hero"] else {}),
        "mainEntityOfPage": SITE + "/blog/" + bp["path"]}
    write(OUT/"blog"/bp["path"]/"index.html",
          page(f'{bp["title"]} | OCBuyBack', post_body, depth, BLOG_CSS,
               path="/blog/" + bp["path"], desc=bp["description"],
               schema=[post_schema, breadcrumbs([("Blog", "/blog"), (bp["heading"], None)])],
               og_image=(bp["hero"] if bp["hero"].startswith("http") else SITE + "/assets/blog/" + bp["hero"]) if bp["hero"] else None))

cards = "".join(f'''<a class="bpost" href="{bp["path"]}/index.html">
  <div class="thumb" style="background-image:url('{hero_src(bp, 0) if bp["hero"] and bp["hero"].startswith("http") else "../assets/blog/" + (bp["hero"] or "")}')"></div>
  <div class="pad"><div class="date">{html.escape(bp["date_display"])}</div>
  <h2>{html.escape(bp["heading"])}</h2>
  <p>{html.escape(bp["description"])}</p></div></a>''' for bp in blog_posts)
blog_index = f'''
<div class="wrap">
  <div class="crumb"><a href="../index.html">Home</a> → <b>Blog</b></div>
  <h1>The OCBuyBack blog</h1>
  <p class="sub">Selling tips, trade-in news, and what your devices are worth — since 2018.</p>
  <div class="bloggrid">{cards}</div>
</div>'''
write(OUT/"blog"/"index.html",
      page("The OCBuyBack Blog — selling tips & trade-in news", blog_index, 1, BLOG_CSS,
           path="/blog",
           desc="Selling tips, trade-in news, and what your devices are worth — from OCBuyBack in Brea, CA."))

# ---- location page (/locations/brea-ca-92821) ----
LOC_BLURBS = [
    ("Cash for iPhone", "We'll buy your iPhone in Brea, CA 92821. Our trade-in process is quick, reliable, and professional — come see us today."),
    ("Cash for Samsung phones", "If you're in Brea, CA, OCBuyBack pays cash for your Samsung Galaxy. Stop by and see us."),
    ("Cash for Google Pixel", "Selling your Google Pixel in Brea, CA today? We'll give you fast cash for it."),
    ("Cash for iPad", "Turn your Apple iPad into cash in Brea, CA — instant quote online or in store."),
    ("Cash for any device", "iPhone, Pixel, Galaxy, consoles, watches — whatever it is, get cash for your trade-in today in Brea, CA 92821."),
]
loc_body = f'''
<div class="wrap" style="max-width:920px;margin:0 auto;padding-bottom:80px">
  <div class="crumb"><a href="../../index.html">Home</a> → <b>Brea, CA 92821</b></div>
  <h1>OCBuyBack — Brea, CA</h1>
  <p class="sub">Trade in your device today at our Brea shop, or get an instant quote online and ship it free.</p>
  <div class="contact-grid">
    <div class="ccard">
      <h2>The shop</h2>
      <p><b>1203 W Imperial Hwy, STE 103<br>Brea, CA 92821</b></p>
      <p><a href="tel:657-286-8274">657-286-8274</a> · <a href="mailto:support@ocbuyback.com">support@ocbuyback.com</a></p>
      <div class="hours"><b>Mon–Fri</b><span>10:00 AM – 6:00 PM</span><b>Sat–Sun</b><span>Closed</span></div>
      <a class="btn" href="https://www.google.com/maps/search/?api=1&query=OCBuyBack%201203%20W%20Imperial%20Hwy%20STE%20103%20Brea%20CA" target="_blank" rel="noopener">Get directions</a>
    </div>
    <div class="ccard">
      <h2>Cash on the spot</h2>
      <p style="color:var(--muted)">Same price online and in store. Devices are evaluated while you wait — about 10 minutes — and locals get paid in cash.</p>
      <a class="btn" href="../../sell/index.html">Get an instant quote</a>
    </div>
  </div>
  <h2 style="font:700 22px 'Bricolage Grotesque',sans-serif;color:var(--deep);margin:44px 0 16px">Trade in your device today in Brea, CA 92821</h2>
  <div class="contact-grid">
    {"".join(f'<div class="ccard"><h2>{t}</h2><p style="color:var(--muted)">{b}</p></div>' for t, b in LOC_BLURBS)}
  </div>
</div>'''
write(OUT/"locations"/"brea-ca-92821"/"index.html",
      page("Sell your device in Brea, CA 92821 | OCBuyBack", loc_body, 2, STATIC_CSS,
           path="/locations/brea-ca-92821",
           desc="OCBuyBack at 1203 W Imperial Hwy STE 103, Brea, CA 92821. Cash for iPhones, Samsung, Pixel, iPads and more — evaluated in about 10 minutes, cash on the spot.",
           schema=[STORE_SCHEMA]))

# ---- sitemap.xml + robots.txt ----
urls = []
for path, img in [("/", None)] + SITEMAP:
    entry = f"  <url>\n    <loc>{SITE}{path if path != '/' else ''}/</loc>\n  </url>" if path == "/" else \
            f"  <url>\n    <loc>{SITE}{path}</loc>\n" + \
            (f"    <image:image><image:loc>{html.escape(img)}</image:loc></image:image>\n" if img else "") + "  </url>"
    urls.append(entry)
(OUT/"sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
    'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + "\n".join(urls) + "\n</urlset>\n")
(OUT/"robots.txt").write_text(f"User-Agent: *\nAllow: /\nDisallow: /admin\nSitemap: {SITE}/sitemap.xml\n")

print(f"generated {count} device pages, {len(LIVE_CATS)} category pages, 1 hub, 1 cart/checkout, 1 track, 4 static, {len(blog_posts)+1} blog, 1 location; sitemap: {len(SITEMAP)+1} urls")
