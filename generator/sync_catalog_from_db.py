#!/usr/bin/env python3
"""Pull the catalog from Supabase into data/catalog.json.

The database is the source of truth: admin price edits, enable/disable
toggles, weight changes, and newly added devices (with uploaded images) all
flow to the static site on the next build. Runs before generate_concept_pages.
"""
import json, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONF = (ROOT / "admin" / "config.js").read_text()
url = CONF.split('SUPABASE_URL: "')[1].split('"')[0]
key = CONF.split('SUPABASE_ANON_KEY: "')[1].split('"')[0]

rows = []
offset = 0
while True:
    r = subprocess.run(["curl", "-s",
        f"{url}/rest/v1/catalog_flat?select=category,brand,model,model_slug,image_url,sort,model_enabled,category_enabled,carrier,storage,condition,price,price_enabled"
        f"&order=category,brand,model,carrier,storage,condition&limit=1000&offset={offset}",
        "-H", f"apikey: {key}"], capture_output=True, text=True)
    page = json.loads(r.stdout)
    rows.extend(page)
    if len(page) < 1000: break
    offset += 1000

tree = {}
for r in rows:
    m = tree.setdefault(r["category"], {}).setdefault(r["brand"], {}).setdefault(r["model"], {
        "enabled": False, "sort": 10**9, "variants": {}, "image": None, "slug": None})
    m["enabled"] = bool(r["model_enabled"] and r["category_enabled"])
    m["sort"] = min(m["sort"], r["sort"] if r["sort"] is not None else 10**9)
    m["image"] = r.get("image_url") or m["image"]
    m["slug"] = r.get("model_slug") or m["slug"]
    v = m["variants"].setdefault(r["carrier"], {}).setdefault(r["storage"], {})
    if r["price_enabled"] and (r["price"] or 0) > 0:
        v[r["condition"]] = float(r["price"])

json.dump(tree, open(ROOT / "data" / "catalog.json", "w"), indent=1)

# condition copy (short card text + expanded criteria), editable in the admin
r = subprocess.run(["curl", "-s", f"{url}/rest/v1/site_settings?key=eq.conditions&select=value",
                    "-H", f"apikey: {key}"], capture_output=True, text=True)
try:
    conds = json.loads(r.stdout)[0]["value"]
    json.dump(conds, open(ROOT / "data" / "conditions.json", "w"), indent=1)
    print(f"synced condition copy for {len(conds)} conditions")
except (IndexError, KeyError, ValueError):
    print("condition copy not in DB - generator falls back to built-ins")
models = sum(len(b) for c in tree.values() for b in c.values())
sellable = sum(1 for c in tree.values() for b in c.values() for m in b.values()
               if m["enabled"] and any(p for cr in m["variants"].values() for s in cr.values() for p in s.values()))
print(f"synced catalog from db: {len(rows)} price rows, {models} models, {sellable} sellable")
