#!/usr/bin/env python3
"""Pull live (enabled) blog posts from Supabase into data/blog.json.

The database is the source of truth once the customer edits posts in the
admin — run this, then generate_concept_pages.py, to publish their changes.
Anon key only sees enabled posts (RLS), which is exactly what the site shows.
"""
import json, urllib.request, pathlib, subprocess, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONF = (ROOT / "admin" / "config.js").read_text()
url = CONF.split('SUPABASE_URL: "')[1].split('"')[0]
key = CONF.split('SUPABASE_ANON_KEY: "')[1].split('"')[0]

r = subprocess.run(["curl", "-s",
    f"{url}/rest/v1/blog_posts?select=path,published_on,slug,title,meta_description,image_url,html&order=published_on.desc&limit=1000",
    "-H", f"apikey: {key}"], capture_output=True, text=True)
rows = json.loads(r.stdout)

posts = []
for p in rows:
    d = datetime.date.fromisoformat(p["published_on"])
    posts.append({
        "path": p["path"],
        "slug": p["slug"],
        "title": p["title"],
        "heading": p["title"],
        "description": p["meta_description"] or "",
        "date_display": d.strftime("%B %d, %Y"),
        "hero": p["image_url"] or None,
        "body": p["html"],
    })
json.dump(posts, open(ROOT / "data" / "blog.json", "w"), indent=1)
print(f"synced {len(posts)} posts from the database -> data/blog.json")
