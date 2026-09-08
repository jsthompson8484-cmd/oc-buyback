-- Fast bulk load. Run from repo root: psql "$CONN" -f supabase/csv/load.sql
begin;
truncate prices, variants, models, brands, categories restart identity cascade;
\copy categories (id,name,slug,display_name,image_dir,q1_label,q2_label,sort,enabled) from 'supabase/csv/categories.csv' csv header
\copy brands (id,name,slug) from 'supabase/csv/brands.csv' csv header
\copy models (id,category_id,brand_id,name,slug,image_url,sort,enabled) from 'supabase/csv/models.csv' csv header
\copy variants (id,model_id,carrier,storage) from 'supabase/csv/variants.csv' csv header
\copy prices (variant_id,condition,price,enabled) from 'supabase/csv/prices.csv' csv header
select setval('categories_id_seq', (select max(id) from categories));
select setval('brands_id_seq', (select max(id) from brands));
select setval('models_id_seq', (select max(id) from models));
select setval('variants_id_seq', (select max(id) from variants));
commit;
