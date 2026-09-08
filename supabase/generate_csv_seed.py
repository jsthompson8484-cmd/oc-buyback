#!/usr/bin/env python3
"""Fast bulk seed: emit CSVs with explicit IDs + a load.sql that \\copy's them.

Loads in seconds over the network vs ~1h for the row-by-row seed.sql.
Run: psql "$CONN" -v ON_ERROR_STOP=1 -f supabase/csv/load.sql   (from repo root)
"""
import csv, re, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTD = ROOT / "supabase" / "csv"
OUTD.mkdir(exist_ok=True)
rows = list(csv.DictReader(open(ROOT / "data" / "catalog_clean.csv")))

LIVE = ["Cell Phone","Tablet","Smartwatch","Game Console","GoPro","VR","Headphones","iPod"]
DORMANT = ["Macbook","Laptop","iMac","Mac Mini","Mac Studio","Mac Pro","Apple TV","Drone"]
CAT_SLUG = {"Cell Phone":"cell-phone","Tablet":"tablet","Smartwatch":"smartwatch","Game Console":"game-console",
            "GoPro":"gopro","VR":"vr","Headphones":"headphones","iPod":"ipod","Macbook":"macbook","Laptop":"laptop",
            "iMac":"imac","Mac Mini":"mac-mini","Mac Studio":"mac-studio","Mac Pro":"mac-pro","Apple TV":"apple-tv",
            "Drone":"drone"}
CAT_DISPLAY = {"Cell Phone":"Cell Phones","Tablet":"Tablets","Smartwatch":"Smartwatches","Game Console":"Game Consoles",
               "GoPro":"GoPro","VR":"VR","Headphones":"Headphones","iPod":"iPods","Macbook":"MacBooks","Laptop":"Laptops",
               "iMac":"iMacs","Mac Mini":"Mac Minis","Mac Studio":"Mac Studios","Mac Pro":"Mac Pros",
               "Apple TV":"Apple TV","Drone":"Drones"}
CAT_IMGDIR = {"Cell Phone":"cell-phones","Tablet":"tablets","Smartwatch":"smartwatches","Game Console":"game-consoles",
              "GoPro":"gopros","VR":"vrs","Headphones":"headphones","iPod":"ipods","Macbook":"macbooks","Laptop":"laptops",
              "iMac":"imacs","Mac Mini":"mac-minis","Mac Studio":"mac-studios","Mac Pro":"mac-pros",
              "Apple TV":"apple-tvs","Drone":"drones"}
CAT_LABELS = {"Smartwatch":("Which case?","What size?"),"Game Console":("Which edition?","How much storage?"),
              "GoPro":("Which edition?","Which bundle?"),"Tablet":("Which connectivity?","How much storage?"),
              "VR":("Which edition?","How much storage?"),"Headphones":("Which edition?","Which color?"),
              "iPod":("Which generation?","How much storage?")}
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
    return re.sub(r"[^a-z0-9]+","-",s).strip("-")

def w(name, header, data):
    with open(OUTD / name, "w", newline="") as f:
        wr = csv.writer(f); wr.writerow(header); wr.writerows(data)

# categories
cats = LIVE + DORMANT
w("categories.csv", ["id","name","slug","display_name","image_dir","q1_label","q2_label","sort","enabled"],
  [[i+1, c, CAT_SLUG[c], CAT_DISPLAY[c], CAT_IMGDIR[c],
    *CAT_LABELS.get(c, ("Which carrier?","How much storage?")), i, c in LIVE] for i, c in enumerate(cats)])
cat_id = {c: i+1 for i, c in enumerate(cats)}

# brands
brands = sorted(set(r["Brand"] for r in rows))
w("brands.csv", ["id","name","slug"], [[i+1, b, slug(b)] for i, b in enumerate(brands)])
brand_id = {b: i+1 for i, b in enumerate(brands)}

# models
models = {}
for r in rows:
    k = (r["Category"], r["Brand"], r["Device"])
    m = models.setdefault(k, {"sort": 10**9, "enabled": False})
    m["sort"] = min(m["sort"], int(r["Sort Order"] or 10**9))
    m["enabled"] = m["enabled"] or r["Enabled"] == "true"
model_rows, model_id = [], {}
for i, ((cat, brand, dev), m) in enumerate(models.items()):
    model_id[(cat, brand, dev)] = i + 1
    img = f"https://s3.amazonaws.com/fliptech-assets/images/devices/{CAT_IMGDIR[cat]}/{slug(brand)}/{slug(dev)}.webp"
    model_rows.append([i+1, cat_id[cat], brand_id[brand], dev, slug(dev), img, m["sort"], m["enabled"]])
w("models.csv", ["id","category_id","brand_id","name","slug","image_url","sort","enabled"], model_rows)

# variants + prices
variants, var_rows, price_rows = {}, [], []
for r in rows:
    vk = (r["Category"], r["Brand"], r["Device"], r["Carrier"] or "-", r["Storage Capacity"] or "-")
    if vk not in variants:
        variants[vk] = len(variants) + 1
        var_rows.append([variants[vk], model_id[(r["Category"], r["Brand"], r["Device"])], vk[3], vk[4]])
    price_rows.append([variants[vk], r["Condition"], float(r["Price"] or 0), r["Enabled"] == "true"])
w("variants.csv", ["id","model_id","carrier","storage"], var_rows)
w("prices.csv", ["variant_id","condition","price","enabled"], price_rows)

# load script (faqs + settings reuse the statements from seed.sql tail)
load = f"""-- Fast bulk load. Run from repo root: psql "$CONN" -f supabase/csv/load.sql
begin;
truncate prices, variants, models, brands, categories restart identity cascade;
\\copy categories (id,name,slug,display_name,image_dir,q1_label,q2_label,sort,enabled) from 'supabase/csv/categories.csv' csv header
\\copy brands (id,name,slug) from 'supabase/csv/brands.csv' csv header
\\copy models (id,category_id,brand_id,name,slug,image_url,sort,enabled) from 'supabase/csv/models.csv' csv header
\\copy variants (id,model_id,carrier,storage) from 'supabase/csv/variants.csv' csv header
\\copy prices (variant_id,condition,price,enabled) from 'supabase/csv/prices.csv' csv header
select setval('categories_id_seq', (select max(id) from categories));
select setval('brands_id_seq', (select max(id) from brands));
select setval('models_id_seq', (select max(id) from models));
select setval('variants_id_seq', (select max(id) from variants));
commit;
"""
(OUTD / "load.sql").write_text(load)
print(f"csv seed: {len(cats)} categories, {len(brands)} brands, {len(model_rows)} models, "
      f"{len(var_rows)} variants, {len(price_rows)} prices -> supabase/csv/")
