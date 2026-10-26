#!/usr/bin/env python3
"""Pull per-model trade statistics into data/trade_stats.json.

Device pages were 81-94% identical to one another -- thin content regardless
of word count, because the only thing that varied was the model name and the
prices inside the quote widget. These statistics are the one thing no
competitor can copy: what OCBuyBack has actually bought.

Reads two aggregate-only views (see supabase/model_trade_stats_oct26.sql).
They expose no order or customer data and apply a 25-trade floor, so the anon
key is sufficient and nothing identifying can reach a public page.

Runs before generate_concept_pages, like the catalog sync.
"""
import json, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONF = (ROOT / "admin" / "config.js").read_text()
url = CONF.split('SUPABASE_URL: "')[1].split('"')[0]
key = CONF.split('SUPABASE_ANON_KEY: "')[1].split('"')[0]

def get(path):
    r = subprocess.run(["curl", "-s", f"{url}/rest/v1/{path}", "-H", f"apikey: {key}"],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return []

models = get("model_trade_stats?select=*")
cats = get("category_trade_stats?select=*")
overall = get("trade_stats_overall?select=*")

if not isinstance(models, list) or not models:
    # Never fail the build over this: the blocks are additive, and a page
    # without them is the page we had yesterday.
    print("WARNING: no trade stats returned - device pages build without them")
    models = []

stats = {m["model"]: m for m in models if m.get("model")}
out = {"models": stats,
       "categories": {c["category"]: c for c in cats if isinstance(cats, list) and c.get("category")},
       "overall": (overall[0] if isinstance(overall, list) and overall else {})}
json.dump(out, open(ROOT / "data" / "trade_stats.json", "w"), indent=1)
print(f"trade stats: {len(stats)} models, {len(out['categories'])} categories, "
      f"site-wide {out['overall'].get('pct_damaged','?')}% damaged")
