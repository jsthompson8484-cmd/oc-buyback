begin;

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select c.id, b.id, 'iPhone Duo', 'iphone-duo', '/assets/devices/cell-phones/apple/iphone-duo.webp', 8450, false, 10
from categories c, brands b
where c.name = 'Cell Phone' and b.name = 'Apple'
  and not exists (select 1 from models m where m.slug = 'iphone-duo');
insert into variants (model_id, carrier, storage) select m.id, 'Unlocked', '256GB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Unlocked' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'Unlocked', '512GB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Unlocked' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'Unlocked', '1TB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Unlocked' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'Unlocked', '2TB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Unlocked' and v.storage='2TB');
insert into variants (model_id, carrier, storage) select m.id, 'AT&T', '256GB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='AT&T' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'AT&T', '512GB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='AT&T' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'AT&T', '1TB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='AT&T' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'AT&T', '2TB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='AT&T' and v.storage='2TB');
insert into variants (model_id, carrier, storage) select m.id, 'T-Mobile', '256GB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='T-Mobile' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'T-Mobile', '512GB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='T-Mobile' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'T-Mobile', '1TB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='T-Mobile' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'T-Mobile', '2TB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='T-Mobile' and v.storage='2TB');
insert into variants (model_id, carrier, storage) select m.id, 'Verizon', '256GB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Verizon' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'Verizon', '512GB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Verizon' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'Verizon', '1TB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Verizon' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'Verizon', '2TB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Verizon' and v.storage='2TB');
insert into variants (model_id, carrier, storage) select m.id, 'Other', '256GB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Other' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'Other', '512GB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Other' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'Other', '1TB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Other' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'Other', '2TB' from models m where m.slug='iphone-duo' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Other' and v.storage='2TB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select c.id, b.id, 'iPhone 18 Pro Max', 'iphone-18-pro-max', '/assets/devices/cell-phones/apple/iphone-18-pro-max.webp', 8400, false, 9
from categories c, brands b
where c.name = 'Cell Phone' and b.name = 'Apple'
  and not exists (select 1 from models m where m.slug = 'iphone-18-pro-max');
insert into variants (model_id, carrier, storage) select m.id, 'Unlocked', '256GB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Unlocked' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'Unlocked', '512GB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Unlocked' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'Unlocked', '1TB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Unlocked' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'Unlocked', '2TB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Unlocked' and v.storage='2TB');
insert into variants (model_id, carrier, storage) select m.id, 'AT&T', '256GB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='AT&T' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'AT&T', '512GB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='AT&T' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'AT&T', '1TB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='AT&T' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'AT&T', '2TB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='AT&T' and v.storage='2TB');
insert into variants (model_id, carrier, storage) select m.id, 'T-Mobile', '256GB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='T-Mobile' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'T-Mobile', '512GB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='T-Mobile' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'T-Mobile', '1TB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='T-Mobile' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'T-Mobile', '2TB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='T-Mobile' and v.storage='2TB');
insert into variants (model_id, carrier, storage) select m.id, 'Verizon', '256GB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Verizon' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'Verizon', '512GB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Verizon' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'Verizon', '1TB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Verizon' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'Verizon', '2TB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Verizon' and v.storage='2TB');
insert into variants (model_id, carrier, storage) select m.id, 'Other', '256GB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Other' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'Other', '512GB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Other' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'Other', '1TB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Other' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'Other', '2TB' from models m where m.slug='iphone-18-pro-max' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Other' and v.storage='2TB');

insert into models (category_id, brand_id, name, slug, image_url, sort, enabled, weight_oz)
select c.id, b.id, 'iPhone 18 Pro', 'iphone-18-pro', '/assets/devices/cell-phones/apple/iphone-18-pro.webp', 8350, false, 8
from categories c, brands b
where c.name = 'Cell Phone' and b.name = 'Apple'
  and not exists (select 1 from models m where m.slug = 'iphone-18-pro');
insert into variants (model_id, carrier, storage) select m.id, 'Unlocked', '256GB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Unlocked' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'Unlocked', '512GB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Unlocked' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'Unlocked', '1TB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Unlocked' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'Unlocked', '2TB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Unlocked' and v.storage='2TB');
insert into variants (model_id, carrier, storage) select m.id, 'AT&T', '256GB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='AT&T' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'AT&T', '512GB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='AT&T' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'AT&T', '1TB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='AT&T' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'AT&T', '2TB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='AT&T' and v.storage='2TB');
insert into variants (model_id, carrier, storage) select m.id, 'T-Mobile', '256GB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='T-Mobile' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'T-Mobile', '512GB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='T-Mobile' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'T-Mobile', '1TB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='T-Mobile' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'T-Mobile', '2TB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='T-Mobile' and v.storage='2TB');
insert into variants (model_id, carrier, storage) select m.id, 'Verizon', '256GB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Verizon' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'Verizon', '512GB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Verizon' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'Verizon', '1TB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Verizon' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'Verizon', '2TB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Verizon' and v.storage='2TB');
insert into variants (model_id, carrier, storage) select m.id, 'Other', '256GB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Other' and v.storage='256GB');
insert into variants (model_id, carrier, storage) select m.id, 'Other', '512GB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Other' and v.storage='512GB');
insert into variants (model_id, carrier, storage) select m.id, 'Other', '1TB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Other' and v.storage='1TB');
insert into variants (model_id, carrier, storage) select m.id, 'Other', '2TB' from models m where m.slug='iphone-18-pro' and not exists (select 1 from variants v where v.model_id=m.id and v.carrier='Other' and v.storage='2TB');

insert into prices (variant_id, condition, price, enabled)
select v.id, c.cond, 0, false
from variants v
join models m on m.id = v.model_id and m.slug in ('iphone-duo','iphone-18-pro-max','iphone-18-pro')
cross join (values ('Brand New'),('Flawless'),('Good'),('Fair'),('Minor Damage'),('Broken')) as c(cond)
where not exists (select 1 from prices p where p.variant_id = v.id and p.condition = c.cond);
commit;