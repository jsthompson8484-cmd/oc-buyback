#!/usr/bin/env python3
"""Migrate the 64 live blog posts into data/blog.json + local images.

Fetches each post from www.ocbuyback.com LIVE (the snapshot's image URLs are
signed and expired), extracts title/meta/date/hero/body, downloads images to
concepts/freshair/assets/blog/, and rewrites the body HTML clean.

URL paths are taken verbatim from the sitemap (including the platform's odd
month tokens like /2018/010/12/) — URL parity is the whole point.
"""
import re, html, json, pathlib, subprocess, time, hashlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "concepts" / "freshair" / "assets" / "blog"
ASSETS.mkdir(parents=True, exist_ok=True)

paths = sorted(
    u.strip().replace("https://www.ocbuyback.com/blog/", "")
    for u in open(ROOT / "reference" / "all_urls.txt")
    if "/blog/" in u
)
print(f"{len(paths)} posts to migrate")

def fetch(url):
    r = subprocess.run(["curl", "-s", "--max-time", "30", url], capture_output=True, text=True)
    return r.stdout

def download(url, slug_hint):
    ext = ".jpg"
    m = re.search(r'filename%3D%22([^%"]+)%22', url)
    if m and "." in m.group(1):
        ext = "." + m.group(1).rsplit(".", 1)[1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"): ext = ".jpg"
    name = slug_hint[:60] + "-" + hashlib.md5(url.split("?")[0].encode()).hexdigest()[:6] + ext
    out = ASSETS / name
    if not out.exists():
        subprocess.run(["curl", "-s", "--max-time", "30", "-o", str(out), url])
        if out.stat().st_size < 500:  # error body, not an image
            out.unlink(missing_ok=True); return None
    return name

def balanced_div(t, start_pat):
    m = re.search(start_pat, t)
    if not m: return None
    i = t.index(">", m.start()) + 1
    depth, j = 1, i
    for tag in re.finditer(r"<(/?)div\b", t[i:]):
        depth += -1 if tag.group(1) else 1
        if depth == 0:
            j = i + tag.start(); break
    return t[i:j]

def clean_body(body, slug):
    body = re.sub(r"(?s)<script.*?</script>|<link[^>]*>|<style.*?</style>", "", body)
    # download + rewrite any platform-hosted images inside the body
    def img_repl(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        if not src: return ""
        url = html.unescape(src.group(1))
        if "fliptech" not in url and "amazonaws" not in url: return tag
        name = download(url, slug)
        if not name: return ""
        alt = re.search(r'alt="([^"]*)"', tag)
        return f'<img src="{{ASSET}}/{name}" alt="{alt.group(1) if alt else ""}" loading="lazy">'
    body = re.sub(r"<img[^>]*>", img_repl, body)
    # unwrap divs/spans, drop classes/styles/ids, absolute self-links -> relative
    body = re.sub(r"</?(?:div|span)[^>]*>", "", body)
    body = re.sub(r'\s(?:class|style|id|dir)="[^"]*"', "", body)
    body = body.replace("https://www.ocbuyback.com/", "/")
    body = re.sub(r"<p>\s*(?:<b>\s*</b>|<br\s*/?>)?\s*</p>", "", body)
    return body.strip()

posts, failed = [], []
for p in paths:
    url = f"https://www.ocbuyback.com/blog/{p}"
    t = fetch(url)
    slug = p.rsplit("/", 1)[1]
    try:
        title_tag = html.unescape(re.search(r"<title>([^<]*)", t).group(1)).replace(" | OCBuyBack", "").strip()
        md = re.search(r'<meta name="description" content="([^"]*)"', t)
        desc = html.unescape(md.group(1)) if md else ""
        entry = balanced_div(t, r'<div class="blog-entry py-2">') or t
        am = re.search(r'(?s)class="blog-author[^"]*"[^>]*>(.*?)<', entry)
        date_display = am.group(1).strip() if am else ""
        hm = re.search(r'(?s)class="home-headline blog-title"[^>]*>(.*?)</', entry)
        heading = html.unescape(hm.group(1).strip()) if hm else title_tag
        hero = None
        him = re.search(r'class="blog-entry-image[^"]*"[^>]*style="background-image:url\(&#39;([^&]+)&#39;\)|class="blog-entry-image[^"]*"[^>]*style="background-image:url\(\'([^\']+)\'\)', entry)
        if him:
            hero = download(html.unescape(him.group(1) or him.group(2)), slug)
        body = balanced_div(entry, r'<div class="blog-body')
        if not body: raise ValueError("no body")
        body = clean_body(body, slug)
        # the first <p><b>title</b></p> duplicates the heading — drop it
        body = re.sub(r"^<p><b>" + re.escape(heading[:40]), lambda m: "<p><b\x00>" + heading[:40], body, count=1)
        if "\x00" in body:
            body = re.sub(r"(?s)^<p><b\x00>.*?</p>", "", body, count=1).strip()
        posts.append({"path": p, "slug": slug, "title": title_tag, "heading": heading,
                      "description": desc, "date_display": date_display,
                      "hero": hero, "body": body})
        print(f"ok  {p}  ({len(body)} chars{', hero' if hero else ''})")
    except Exception as e:
        failed.append((p, str(e)))
        print(f"FAIL {p}: {e}")
    time.sleep(0.15)

json.dump(posts, open(ROOT / "data" / "blog.json", "w"), indent=1)
print(f"\n{len(posts)} migrated, {len(failed)} failed -> data/blog.json")
for f in failed: print("  FAILED:", f)
