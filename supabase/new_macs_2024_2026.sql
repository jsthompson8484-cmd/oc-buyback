begin;

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 9, 1, 'MacBook Pro 14" (2024)', 'macbook-pro-14-2024', 'https://ocbuyback.netlify.app/assets/devices/macbook-pro-14-2024.webp', 21700, false, 56
where not exists (select 1 from models where slug = 'macbook-pro-14-2024');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '16GB' from models m where m.slug='macbook-pro-14-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='16GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '24GB' from models m where m.slug='macbook-pro-14-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '32GB' from models m where m.slug='macbook-pro-14-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='32GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Pro 12-Core CPU 16-Core GPU', '24GB' from models m where m.slug='macbook-pro-14-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Pro 12-Core CPU 16-Core GPU' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Pro 14-Core CPU 20-Core GPU', '24GB' from models m where m.slug='macbook-pro-14-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Pro 14-Core CPU 20-Core GPU' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Pro 14-Core CPU 20-Core GPU', '48GB' from models m where m.slug='macbook-pro-14-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Pro 14-Core CPU 20-Core GPU' and v.storage='48GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Max 14-Core CPU 32-Core GPU', '36GB' from models m where m.slug='macbook-pro-14-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Max 14-Core CPU 32-Core GPU' and v.storage='36GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Max 16-Core CPU 40-Core GPU', '48GB' from models m where m.slug='macbook-pro-14-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Max 16-Core CPU 40-Core GPU' and v.storage='48GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Max 16-Core CPU 40-Core GPU', '64GB' from models m where m.slug='macbook-pro-14-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Max 16-Core CPU 40-Core GPU' and v.storage='64GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Max 16-Core CPU 40-Core GPU', '128GB' from models m where m.slug='macbook-pro-14-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Max 16-Core CPU 40-Core GPU' and v.storage='128GB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 9, 1, 'MacBook Pro 16" (2024)', 'macbook-pro-16-2024', 'https://ocbuyback.netlify.app/assets/devices/macbook-pro-16-2024.webp', 21710, false, 77
where not exists (select 1 from models where slug = 'macbook-pro-16-2024');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Pro 14-Core CPU 20-Core GPU', '24GB' from models m where m.slug='macbook-pro-16-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Pro 14-Core CPU 20-Core GPU' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Pro 14-Core CPU 20-Core GPU', '48GB' from models m where m.slug='macbook-pro-16-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Pro 14-Core CPU 20-Core GPU' and v.storage='48GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Max 14-Core CPU 32-Core GPU', '36GB' from models m where m.slug='macbook-pro-16-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Max 14-Core CPU 32-Core GPU' and v.storage='36GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Max 16-Core CPU 40-Core GPU', '48GB' from models m where m.slug='macbook-pro-16-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Max 16-Core CPU 40-Core GPU' and v.storage='48GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Max 16-Core CPU 40-Core GPU', '64GB' from models m where m.slug='macbook-pro-16-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Max 16-Core CPU 40-Core GPU' and v.storage='64GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Max 16-Core CPU 40-Core GPU', '128GB' from models m where m.slug='macbook-pro-16-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Max 16-Core CPU 40-Core GPU' and v.storage='128GB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 9, 1, 'MacBook Air 13" (2025)', 'macbook-air-13-2025', 'https://ocbuyback.netlify.app/assets/devices/macbook-air-13-2025.webp', 21720, false, 43
where not exists (select 1 from models where slug = 'macbook-air-13-2025');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 8-Core GPU', '16GB' from models m where m.slug='macbook-air-13-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 8-Core GPU' and v.storage='16GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '16GB' from models m where m.slug='macbook-air-13-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='16GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '24GB' from models m where m.slug='macbook-air-13-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '32GB' from models m where m.slug='macbook-air-13-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='32GB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 9, 1, 'MacBook Air 15" (2025)', 'macbook-air-15-2025', 'https://ocbuyback.netlify.app/assets/devices/macbook-air-15-2025.webp', 21730, false, 53
where not exists (select 1 from models where slug = 'macbook-air-15-2025');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '16GB' from models m where m.slug='macbook-air-15-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='16GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '24GB' from models m where m.slug='macbook-air-15-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '32GB' from models m where m.slug='macbook-air-15-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='32GB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 9, 1, 'MacBook Pro 14" (2025)', 'macbook-pro-14-2025', 'https://ocbuyback.netlify.app/assets/devices/macbook-pro-14-2025.webp', 21740, false, 56
where not exists (select 1 from models where slug = 'macbook-pro-14-2025');
insert into variants (model_id, carrier, storage) select m.id, 'M5 10-Core CPU 10-Core GPU', '16GB' from models m where m.slug='macbook-pro-14-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 10-Core CPU 10-Core GPU' and v.storage='16GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 10-Core CPU 10-Core GPU', '24GB' from models m where m.slug='macbook-pro-14-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 10-Core CPU 10-Core GPU' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 10-Core CPU 10-Core GPU', '32GB' from models m where m.slug='macbook-pro-14-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 10-Core CPU 10-Core GPU' and v.storage='32GB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 9, 1, 'MacBook Air 13" (2026)', 'macbook-air-13-2026', 'https://ocbuyback.netlify.app/assets/devices/macbook-air-13-2026.webp', 21750, false, 43
where not exists (select 1 from models where slug = 'macbook-air-13-2026');
insert into variants (model_id, carrier, storage) select m.id, 'M5 10-Core CPU 10-Core GPU', '16GB' from models m where m.slug='macbook-air-13-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 10-Core CPU 10-Core GPU' and v.storage='16GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 10-Core CPU 10-Core GPU', '24GB' from models m where m.slug='macbook-air-13-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 10-Core CPU 10-Core GPU' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 10-Core CPU 10-Core GPU', '32GB' from models m where m.slug='macbook-air-13-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 10-Core CPU 10-Core GPU' and v.storage='32GB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 9, 1, 'MacBook Air 15" (2026)', 'macbook-air-15-2026', 'https://ocbuyback.netlify.app/assets/devices/macbook-air-15-2026.webp', 21760, false, 53
where not exists (select 1 from models where slug = 'macbook-air-15-2026');
insert into variants (model_id, carrier, storage) select m.id, 'M5 10-Core CPU 10-Core GPU', '16GB' from models m where m.slug='macbook-air-15-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 10-Core CPU 10-Core GPU' and v.storage='16GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 10-Core CPU 10-Core GPU', '24GB' from models m where m.slug='macbook-air-15-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 10-Core CPU 10-Core GPU' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 10-Core CPU 10-Core GPU', '32GB' from models m where m.slug='macbook-air-15-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 10-Core CPU 10-Core GPU' and v.storage='32GB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 9, 1, 'MacBook Pro 14" (2026)', 'macbook-pro-14-2026', 'https://ocbuyback.netlify.app/assets/devices/macbook-pro-14-2026.webp', 21770, false, 56
where not exists (select 1 from models where slug = 'macbook-pro-14-2026');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Pro', '24GB' from models m where m.slug='macbook-pro-14-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Pro' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Pro', '48GB' from models m where m.slug='macbook-pro-14-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Pro' and v.storage='48GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Max', '36GB' from models m where m.slug='macbook-pro-14-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Max' and v.storage='36GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Max', '64GB' from models m where m.slug='macbook-pro-14-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Max' and v.storage='64GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Max', '128GB' from models m where m.slug='macbook-pro-14-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Max' and v.storage='128GB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 9, 1, 'MacBook Pro 16" (2026)', 'macbook-pro-16-2026', 'https://ocbuyback.netlify.app/assets/devices/macbook-pro-16-2026.webp', 21780, false, 77
where not exists (select 1 from models where slug = 'macbook-pro-16-2026');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Pro', '24GB' from models m where m.slug='macbook-pro-16-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Pro' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Pro', '48GB' from models m where m.slug='macbook-pro-16-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Pro' and v.storage='48GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Max', '36GB' from models m where m.slug='macbook-pro-16-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Max' and v.storage='36GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Max', '64GB' from models m where m.slug='macbook-pro-16-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Max' and v.storage='64GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Max', '128GB' from models m where m.slug='macbook-pro-16-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Max' and v.storage='128GB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 11, 1, 'iMac 24" (2024)', 'imac-24-2024', 'https://ocbuyback.netlify.app/assets/devices/imac-24-2024.webp', 18930, false, 157
where not exists (select 1 from models where slug = 'imac-24-2024');
insert into variants (model_id, carrier, storage) select m.id, 'M4 8-Core CPU 8-Core GPU', '16GB' from models m where m.slug='imac-24-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 8-Core CPU 8-Core GPU' and v.storage='16GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 8-Core CPU 8-Core GPU', '24GB' from models m where m.slug='imac-24-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 8-Core CPU 8-Core GPU' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '16GB' from models m where m.slug='imac-24-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='16GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '24GB' from models m where m.slug='imac-24-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '32GB' from models m where m.slug='imac-24-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='32GB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 12, 1, 'Mac Mini (2024)', 'mac-mini-2024', 'https://ocbuyback.netlify.app/assets/devices/mac-mini-2024.webp', 19000, false, 26
where not exists (select 1 from models where slug = 'mac-mini-2024');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '16GB' from models m where m.slug='mac-mini-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='16GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '24GB' from models m where m.slug='mac-mini-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 10-Core CPU 10-Core GPU', '32GB' from models m where m.slug='mac-mini-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 10-Core CPU 10-Core GPU' and v.storage='32GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Pro 12-Core CPU 16-Core GPU', '24GB' from models m where m.slug='mac-mini-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Pro 12-Core CPU 16-Core GPU' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Pro 14-Core CPU 20-Core GPU', '24GB' from models m where m.slug='mac-mini-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Pro 14-Core CPU 20-Core GPU' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Pro 14-Core CPU 20-Core GPU', '48GB' from models m where m.slug='mac-mini-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Pro 14-Core CPU 20-Core GPU' and v.storage='48GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Pro 14-Core CPU 20-Core GPU', '64GB' from models m where m.slug='mac-mini-2024' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Pro 14-Core CPU 20-Core GPU' and v.storage='64GB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 12, 1, 'Mac Mini (2026)', 'mac-mini-2026', 'https://ocbuyback.netlify.app/assets/devices/mac-mini-2026.webp', 19010, false, 26
where not exists (select 1 from models where slug = 'mac-mini-2026');
insert into variants (model_id, carrier, storage) select m.id, 'M5', '16GB' from models m where m.slug='mac-mini-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5' and v.storage='16GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5', '24GB' from models m where m.slug='mac-mini-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5', '32GB' from models m where m.slug='mac-mini-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5' and v.storage='32GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Pro', '24GB' from models m where m.slug='mac-mini-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Pro' and v.storage='24GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Pro', '48GB' from models m where m.slug='mac-mini-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Pro' and v.storage='48GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Pro', '64GB' from models m where m.slug='mac-mini-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Pro' and v.storage='64GB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 13, 1, 'Mac Studio (2025)', 'mac-studio-2025', 'https://ocbuyback.netlify.app/assets/devices/mac-studio-2025.webp', 19240, false, 115
where not exists (select 1 from models where slug = 'mac-studio-2025');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Max 14-Core CPU 32-Core GPU', '36GB' from models m where m.slug='mac-studio-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Max 14-Core CPU 32-Core GPU' and v.storage='36GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Max 16-Core CPU 40-Core GPU', '48GB' from models m where m.slug='mac-studio-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Max 16-Core CPU 40-Core GPU' and v.storage='48GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Max 16-Core CPU 40-Core GPU', '64GB' from models m where m.slug='mac-studio-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Max 16-Core CPU 40-Core GPU' and v.storage='64GB');
insert into variants (model_id, carrier, storage) select m.id, 'M4 Max 16-Core CPU 40-Core GPU', '128GB' from models m where m.slug='mac-studio-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M4 Max 16-Core CPU 40-Core GPU' and v.storage='128GB');
insert into variants (model_id, carrier, storage) select m.id, 'M3 Ultra 28-Core CPU 60-Core GPU', '96GB' from models m where m.slug='mac-studio-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M3 Ultra 28-Core CPU 60-Core GPU' and v.storage='96GB');
insert into variants (model_id, carrier, storage) select m.id, 'M3 Ultra 28-Core CPU 60-Core GPU', '256GB' from models m where m.slug='mac-studio-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M3 Ultra 28-Core CPU 60-Core GPU' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'M3 Ultra 32-Core CPU 80-Core GPU', '96GB' from models m where m.slug='mac-studio-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M3 Ultra 32-Core CPU 80-Core GPU' and v.storage='96GB');
insert into variants (model_id, carrier, storage) select m.id, 'M3 Ultra 32-Core CPU 80-Core GPU', '256GB' from models m where m.slug='mac-studio-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M3 Ultra 32-Core CPU 80-Core GPU' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'M3 Ultra 32-Core CPU 80-Core GPU', '512GB' from models m where m.slug='mac-studio-2025' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M3 Ultra 32-Core CPU 80-Core GPU' and v.storage='512GB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 13, 1, 'Mac Studio (2026)', 'mac-studio-2026', 'https://ocbuyback.netlify.app/assets/devices/mac-studio-2026.webp', 19250, false, 115
where not exists (select 1 from models where slug = 'mac-studio-2026');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Max', '36GB' from models m where m.slug='mac-studio-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Max' and v.storage='36GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Max', '64GB' from models m where m.slug='mac-studio-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Max' and v.storage='64GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Max', '128GB' from models m where m.slug='mac-studio-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Max' and v.storage='128GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Ultra', '96GB' from models m where m.slug='mac-studio-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Ultra' and v.storage='96GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Ultra', '256GB' from models m where m.slug='mac-studio-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Ultra' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'M5 Ultra', '512GB' from models m where m.slug='mac-studio-2026' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M5 Ultra' and v.storage='512GB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select 14, 1, 'Mac Pro (2023)', 'mac-pro-2023', 'https://ocbuyback.netlify.app/assets/devices/mac-pro-2023.webp', 19300, false, 595
where not exists (select 1 from models where slug = 'mac-pro-2023');
insert into variants (model_id, carrier, storage) select m.id, 'M2 Ultra 24-Core CPU 60-Core GPU', '64GB' from models m where m.slug='mac-pro-2023' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M2 Ultra 24-Core CPU 60-Core GPU' and v.storage='64GB');
insert into variants (model_id, carrier, storage) select m.id, 'M2 Ultra 24-Core CPU 60-Core GPU', '128GB' from models m where m.slug='mac-pro-2023' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M2 Ultra 24-Core CPU 60-Core GPU' and v.storage='128GB');
insert into variants (model_id, carrier, storage) select m.id, 'M2 Ultra 24-Core CPU 60-Core GPU', '192GB' from models m where m.slug='mac-pro-2023' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M2 Ultra 24-Core CPU 60-Core GPU' and v.storage='192GB');
insert into variants (model_id, carrier, storage) select m.id, 'M2 Ultra 24-Core CPU 76-Core GPU', '64GB' from models m where m.slug='mac-pro-2023' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M2 Ultra 24-Core CPU 76-Core GPU' and v.storage='64GB');
insert into variants (model_id, carrier, storage) select m.id, 'M2 Ultra 24-Core CPU 76-Core GPU', '128GB' from models m where m.slug='mac-pro-2023' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M2 Ultra 24-Core CPU 76-Core GPU' and v.storage='128GB');
insert into variants (model_id, carrier, storage) select m.id, 'M2 Ultra 24-Core CPU 76-Core GPU', '192GB' from models m where m.slug='mac-pro-2023' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='M2 Ultra 24-Core CPU 76-Core GPU' and v.storage='192GB');

insert into prices (variant_id, condition, price, enabled)
select v.id, c.cond, 0, false
from variants v
join models m on m.id = v.model_id and m.slug in ('macbook-pro-14-2024','macbook-pro-16-2024','macbook-air-13-2025','macbook-air-15-2025','macbook-pro-14-2025','macbook-air-13-2026','macbook-air-15-2026','macbook-pro-14-2026','macbook-pro-16-2026','imac-24-2024','mac-mini-2024','mac-mini-2026','mac-studio-2025','mac-studio-2026','mac-pro-2023')
cross join (values ('Brand New'),('Flawless'),('Good'),('Fair'),('Minor Damage'),('Broken')) as c(cond)
where not exists (select 1 from prices p where p.variant_id = v.id and p.condition = c.cond);
commit;