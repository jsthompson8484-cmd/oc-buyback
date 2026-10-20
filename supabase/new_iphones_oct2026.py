#!/usr/bin/env python3
"""Seed the iPhones Apple announced on 9 Sep 2026.

Only three models exist: iPhone 18 Pro, iPhone 18 Pro Max, and iPhone Duo —
the foldable, which Apple named "Duo", not "Fold". There is no base iPhone 18,
no 18e and no Air 2 as of this writing; don't add them until Apple ships them.

Storage tiers (256GB / 512GB / 1TB / 2TB) are from Apple's own pricing page,
not guessed. Carriers mirror the existing iPhone rows.

Prices start at $0 and disabled, per the standing rule that only enabled rows
carry prices — Henry prices and enables what he wants to buy.

Emits new_iphones_oct2026.sql. Idempotent: skips slugs that already exist.
"""
import pathlib

IMG = "/assets/devices/cell-phones/apple"
CONDS = ["Brand New", "Flawless", "Good", "Fair", "Minor Damage", "Broken"]
CARRIERS = ["Unlocked", "AT&T", "T-Mobile", "Verizon", "Other"]
STORAGE = ["256GB", "512GB", "1TB", "2TB"]

# (name, slug, sort, weight_oz)
MODELS = [
    ("iPhone Duo",        "iphone-duo",        8450, 10),   # book-style foldable
    ("iPhone 18 Pro Max", "iphone-18-pro-max", 8400, 9),
    ("iPhone 18 Pro",     "iphone-18-pro",     8350, 8),
]

esc = lambda s: s.replace("'", "''")
out = ["begin;"]
for name, slug, sort, wt in MODELS:
    out.append(f"""
insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select c.id, b.id, '{esc(name)}', '{slug}', '{IMG}/{slug}.webp', {sort}, false, {wt}
from categories c, brands b
where c.name = 'Cell Phone' and b.name = 'Apple'
  and not exists (select 1 from models m where m.slug = '{slug}');""")
    for carrier in CARRIERS:
        for storage in STORAGE:
            out.append(
                f"insert into variants (model_id, carrier, storage) "
                f"select m.id, '{esc(carrier)}', '{storage}' from models m where m.slug='{slug}' "
                f"and not exists (select 1 from variants v where v.model_id=m.id "
                f"and v.carrier='{esc(carrier)}' and v.storage='{storage}');")

out.append("""
insert into prices (variant_id, condition, price, enabled)
select v.id, c.cond, 0, false
from variants v
join models m on m.id = v.model_id and m.slug in ({slugs})
cross join (values {conds}) as c(cond)
where not exists (select 1 from prices p where p.variant_id = v.id and p.condition = c.cond);
commit;""".replace("{slugs}", ",".join(f"'{m[1]}'" for m in MODELS))
         .replace("{conds}", ",".join(f"('{c}')" for c in CONDS)))

path = pathlib.Path(__file__).parent / "new_iphones_oct2026.sql"
path.write_text("\n".join(out))
print(f"wrote {path.name}: {len(MODELS)} models, "
      f"{len(MODELS) * len(CARRIERS) * len(STORAGE)} variants")
