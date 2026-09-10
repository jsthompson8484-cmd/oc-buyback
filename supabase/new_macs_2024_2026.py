#!/usr/bin/env python3
"""Seed the Mac models released 2024-2026 that FlipTech never had.

Follows the existing catalog convention for Macs: one model per year,
chip (with core counts where confirmed) in the carrier slot, unified
memory in the storage slot. All prices start at $0/disabled and models
start disabled — Henry prices and enables what he wants to buy.

Images live in the repo at concepts/freshair/assets/devices/{slug}.webp
and are referenced by the stable netlify.app URL (swap the prefix to
www.ocbuyback.com at cutover).

Emits supabase/new_macs_2024_2026.sql. Idempotent: skips slugs that exist.
"""
import pathlib

IMG = "https://ocbuyback.netlify.app/assets/devices"
CONDS = ["Brand New", "Flawless", "Good", "Fair", "Minor Damage", "Broken"]

# (category_id, name, slug, sort, weight_oz, {chip: [memory,...]})
MODELS = [
    (9, 'MacBook Pro 14" (2024)', "macbook-pro-14-2024", 21700, 56, {
        "M4 10-Core CPU 10-Core GPU": ["16GB", "24GB", "32GB"],
        "M4 Pro 12-Core CPU 16-Core GPU": ["24GB"],
        "M4 Pro 14-Core CPU 20-Core GPU": ["24GB", "48GB"],
        "M4 Max 14-Core CPU 32-Core GPU": ["36GB"],
        "M4 Max 16-Core CPU 40-Core GPU": ["48GB", "64GB", "128GB"]}),
    (9, 'MacBook Pro 16" (2024)', "macbook-pro-16-2024", 21710, 77, {
        "M4 Pro 14-Core CPU 20-Core GPU": ["24GB", "48GB"],
        "M4 Max 14-Core CPU 32-Core GPU": ["36GB"],
        "M4 Max 16-Core CPU 40-Core GPU": ["48GB", "64GB", "128GB"]}),
    (9, 'MacBook Air 13" (2025)', "macbook-air-13-2025", 21720, 43, {
        "M4 10-Core CPU 8-Core GPU": ["16GB"],
        "M4 10-Core CPU 10-Core GPU": ["16GB", "24GB", "32GB"]}),
    (9, 'MacBook Air 15" (2025)', "macbook-air-15-2025", 21730, 53, {
        "M4 10-Core CPU 10-Core GPU": ["16GB", "24GB", "32GB"]}),
    (9, 'MacBook Pro 14" (2025)', "macbook-pro-14-2025", 21740, 56, {
        "M5 10-Core CPU 10-Core GPU": ["16GB", "24GB", "32GB"]}),
    (9, 'MacBook Air 13" (2026)', "macbook-air-13-2026", 21750, 43, {
        "M5 10-Core CPU 10-Core GPU": ["16GB", "24GB", "32GB"]}),
    (9, 'MacBook Air 15" (2026)', "macbook-air-15-2026", 21760, 53, {
        "M5 10-Core CPU 10-Core GPU": ["16GB", "24GB", "32GB"]}),
    (9, 'MacBook Pro 14" (2026)', "macbook-pro-14-2026", 21770, 56, {
        "M5 Pro": ["24GB", "48GB"],
        "M5 Max": ["36GB", "64GB", "128GB"]}),
    (9, 'MacBook Pro 16" (2026)', "macbook-pro-16-2026", 21780, 77, {
        "M5 Pro": ["24GB", "48GB"],
        "M5 Max": ["36GB", "64GB", "128GB"]}),
    (11, 'iMac 24" (2024)', "imac-24-2024", 18930, 157, {
        "M4 8-Core CPU 8-Core GPU": ["16GB", "24GB"],
        "M4 10-Core CPU 10-Core GPU": ["16GB", "24GB", "32GB"]}),
    (12, "Mac Mini (2024)", "mac-mini-2024", 19000, 26, {
        "M4 10-Core CPU 10-Core GPU": ["16GB", "24GB", "32GB"],
        "M4 Pro 12-Core CPU 16-Core GPU": ["24GB"],
        "M4 Pro 14-Core CPU 20-Core GPU": ["24GB", "48GB", "64GB"]}),
    (12, "Mac Mini (2026)", "mac-mini-2026", 19010, 26, {
        "M5": ["16GB", "24GB", "32GB"],
        "M5 Pro": ["24GB", "48GB", "64GB"]}),
    (13, "Mac Studio (2025)", "mac-studio-2025", 19240, 115, {
        "M4 Max 14-Core CPU 32-Core GPU": ["36GB"],
        "M4 Max 16-Core CPU 40-Core GPU": ["48GB", "64GB", "128GB"],
        "M3 Ultra 28-Core CPU 60-Core GPU": ["96GB", "256GB"],
        "M3 Ultra 32-Core CPU 80-Core GPU": ["96GB", "256GB", "512GB"]}),
    (13, "Mac Studio (2026)", "mac-studio-2026", 19250, 115, {
        "M5 Max": ["36GB", "64GB", "128GB"],
        "M5 Ultra": ["96GB", "256GB", "512GB"]}),
    (14, "Mac Pro (2023)", "mac-pro-2023", 19300, 595, {
        "M2 Ultra 24-Core CPU 60-Core GPU": ["64GB", "128GB", "192GB"],
        "M2 Ultra 24-Core CPU 76-Core GPU": ["64GB", "128GB", "192GB"]}),
]

esc = lambda s: s.replace("'", "''")
out = ["begin;"]
for cat, name, slug, sort, wt, chips in MODELS:
    out.append(f"""
insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select {cat}, 1, '{esc(name)}', '{slug}', '{IMG}/{slug}.webp', {sort}, false, {wt}
where not exists (select 1 from models where slug = '{slug}');""")
    for chip, mems in chips.items():
        for mem in mems:
            out.append(
                f"insert into variants (model_id, carrier, storage) "
                f"select m.id, '{esc(chip)}', '{mem}' from models m where m.slug='{slug}' "
                f"and not exists (select 1 from variants v where v.model_id=m.id "
                f"and v.carrier='{esc(chip)}' and v.storage='{mem}');")
out.append("""
insert into prices (variant_id, condition, price, enabled)
select v.id, c.cond, 0, false
from variants v
join models m on m.id = v.model_id and m.slug in ({slugs})
cross join (values {conds}) as c(cond)
where not exists (select 1 from prices p where p.variant_id = v.id and p.condition = c.cond);
commit;""".replace("{slugs}", ",".join(f"'{m[2]}'" for m in MODELS))
         .replace("{conds}", ",".join(f"('{c}')" for c in CONDS)))

path = pathlib.Path(__file__).parent / "new_macs_2024_2026.sql"
path.write_text("\n".join(out))
print(f"wrote {path.name}: {len(MODELS)} models, "
      f"{sum(len(v) for m in MODELS for v in m[5].values())} variants")
