-- OCBuyBack rebuild — Supabase schema
-- Run in the Supabase SQL editor (or psql) on a fresh project, then run seed.sql.

-- ============ CATALOG ============

create table categories (
  id           serial primary key,
  name         text unique not null,          -- "Cell Phone"
  slug         text unique not null,          -- "cell-phone" (must match live URL slugs)
  display_name text not null,                 -- "Cell Phones"
  image_dir    text not null,                 -- S3/asset folder: "cell-phones"
  q1_label     text not null default 'Which carrier?',
  q2_label     text not null default 'How much storage?',
  sort         int not null default 0,
  enabled      boolean not null default false, -- category shown on site
  default_weight_oz numeric not null default 16 -- shipping-weight estimate for the category
);

create table brands (
  id   serial primary key,
  name text unique not null,
  slug text not null
);

create table models (
  id          serial primary key,
  category_id int not null references categories,
  brand_id    int not null references brands,
  name        text not null,
  slug        text not null,                  -- must match live URL slugs
  image_url   text,
  sort        int not null default 0,
  enabled     boolean not null default false, -- model page generated when enabled AND has a price
  weight_oz   numeric,                        -- per-model shipping-weight override
  unique (category_id, brand_id, slug)
);

-- one row per carrier × storage combination ("carrier" holds case material for
-- smartwatches, "-" for consoles etc. — mirrors the FlipTech catalog exactly)
create table variants (
  id       serial primary key,
  model_id int not null references models on delete cascade,
  carrier  text not null default '-',
  storage  text not null default '-',
  unique (model_id, carrier, storage)
);

-- one row per variant × condition. Disabled rows keep price 0 (kept in DB so
-- the shop can start buying that config later — user rule from Sep 8 2026).
create table prices (
  variant_id int not null references variants on delete cascade,
  condition  text not null check (condition in
    ('Brand New','Flawless','Good','Fair','Minor Damage','Broken')),
  price      numeric(10,2) not null default 0,
  enabled    boolean not null default false,
  primary key (variant_id, condition)
);

-- flat read model for the site generator + quote API
create view catalog_flat as
select c.name as category, c.slug as category_slug, c.enabled as category_enabled,
       b.name as brand, b.slug as brand_slug,
       m.name as model, m.slug as model_slug, m.image_url, m.sort, m.enabled as model_enabled,
       v.id as variant_id, v.carrier, v.storage,
       p.condition, p.price, p.enabled as price_enabled,
       coalesce(m.weight_oz, c.default_weight_oz) as weight_oz
from prices p
join variants v on v.id = p.variant_id
join models m   on m.id = v.model_id
join brands b   on b.id = m.brand_id
join categories c on c.id = m.category_id;

-- ============ TRADE-INS ============

create table trade_ins (
  id                uuid primary key default gen_random_uuid(),
  order_number      text unique not null,               -- "OCB-XXXXXX"
  status            text not null default 'initiated' check (status in
    ('initiated',   -- order created, label emailed
     'shipped',     -- label scanned / in transit (set by carrier webhook later)
     'delivered',   -- carrier says delivered, not yet checked in
     'received','evaluating','adjusted',
     'action_pending', -- issue email sent, waiting on the customer
     'paid','returned','cancelled')),
  first_name        text not null,
  last_name         text not null,
  email             text not null,
  phone             text not null,
  address1          text not null,
  address2          text,
  city              text not null,
  state             text not null,
  zip               text not null,
  payment_method    text not null check (payment_method in ('paypal','check','zelle','venmo','cash')),
  payment_detail    text,                               -- zelle contact / venmo handle
  sms_opt_in        boolean not null default false,
  promo_code        text,
  promo_amount      numeric(10,2) not null default 0,
  total_quote       numeric(10,2) not null,
  total_paid        numeric(10,2),
  price_locked_until date not null,
  source            text,                               -- derived lead channel (SellCell, Google, Direct...)
  referrer          text,                               -- first-touch referrer URL
  landing_page      text,                               -- first page the visitor hit
  utm               jsonb,                              -- utm_source/medium/campaign if present
  estimated_weight_oz numeric,                        -- for the shipping label
  label_url         text,
  label_qr_url      text,                               -- USPS Label Broker QR code image
  tracking_number   text,
  admin_notes       text,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

create table trade_in_items (
  id              serial primary key,
  trade_in_id     uuid not null references trade_ins on delete cascade,
  category        text not null,
  brand           text not null,
  model           text not null,
  carrier         text,
  storage         text,
  condition       text not null,
  quoted_price    numeric(10,2) not null,
  qty             int not null default 1,
  final_condition text,                                 -- set during evaluation
  final_price     numeric(10,2)
);

-- issues raised during evaluation that need a customer response by email:
-- iCloud/Google locks, carrier financing, condition requotes, or anything custom.
-- The email carries tokenized links; the customer's click resolves the issue.
create table trade_in_issues (
  id            uuid primary key default gen_random_uuid(),
  trade_in_id   uuid not null references trade_ins on delete cascade,
  item_id       int references trade_in_items on delete set null,
  type          text not null check (type in
    ('icloud_lock','google_lock','financing','requote','other')),
  status        text not null default 'pending' check (status in
    ('pending',            -- email sent, waiting on customer
     'resolved',           -- customer clicked "I've done it"
     'cannot_complete',    -- customer clicked "I'm not able to"
     'accepted',           -- customer accepted the revised offer
     'declined',           -- customer declined the revised offer
     'cancelled')),        -- admin withdrew the issue
  message       text,                    -- admin's note shown in the email
  new_condition text,                    -- requote: the re-graded condition
  new_price     numeric(10,2),           -- requote/other: revised offer (per unit)
  token         text unique not null,    -- secures the email links
  email_sent_at timestamptz,
  responded_at  timestamptz,
  created_at    timestamptz not null default now()
);
create index on trade_in_issues (trade_in_id);
create index on trade_in_issues (token);

-- status history / audit trail (one row per change, powers Track Order)
create table trade_in_events (
  id          serial primary key,
  trade_in_id uuid not null references trade_ins on delete cascade,
  status      text not null,
  note        text,
  created_at  timestamptz not null default now()
);

create index on trade_ins (status, created_at desc);
create index on trade_in_items (trade_in_id);
create index on trade_in_events (trade_in_id, created_at);

-- ============ CONTENT ============

create table faqs (
  id       serial primary key,
  question text not null,
  answer   text not null,
  sort     int not null default 0,
  enabled  boolean not null default true
);

create table blog_posts (
  id               serial primary key,
  published_on     date not null,           -- URL: /blog/{yyyy}/{mm}/{d}/{slug}
  slug             text not null,
  title            text not null,
  meta_description text,
  image_url        text,
  html             text not null,
  enabled          boolean not null default true,
  unique (published_on, slug)
);

create table promo_codes (
  id         serial primary key,
  code       text not null,
  amount     numeric(10,2) not null,        -- added to the total quote
  active     boolean not null default true,
  times_used int not null default 0,
  created_at timestamptz not null default now()
);
create unique index promo_codes_active_code on promo_codes (upper(code)) where active;

create table site_settings (
  key   text primary key,                   -- 'store_hours', 'contact', 'colors', ...
  value jsonb not null
);

-- ============ ROW LEVEL SECURITY ============
-- Catalog + content: public read. Trade-ins: no anon access at all —
-- created and read only through Netlify functions using the service-role key,
-- and through the admin panel by allow-listed authenticated users.

alter table categories      enable row level security;
alter table brands          enable row level security;
alter table models          enable row level security;
alter table variants        enable row level security;
alter table prices          enable row level security;
alter table faqs            enable row level security;
alter table blog_posts      enable row level security;
alter table promo_codes     enable row level security;
alter table site_settings   enable row level security;
alter table trade_ins       enable row level security;
alter table trade_in_items  enable row level security;
alter table trade_in_events enable row level security;
alter table trade_in_issues enable row level security;

create policy public_read_categories on categories    for select using (true);
create policy public_read_brands     on brands        for select using (true);
create policy public_read_models     on models        for select using (true);
create policy public_read_variants   on variants      for select using (true);
create policy public_read_prices     on prices        for select using (true);
create policy public_read_faqs       on faqs          for select using (enabled);
create policy public_read_blog       on blog_posts    for select using (enabled);
create policy public_read_settings   on site_settings for select using (true);
-- promo_codes: NOT publicly readable (codes validated server-side in the function)

-- admin allowlist: update these emails before going live
create or replace function is_admin() returns boolean
language sql stable security definer as $$
  select coalesce(auth.jwt()->>'email','') in (
    'js@neartechpartners.com',
    'henry@ocbuyback.com'
  );
$$;

create policy admin_all_categories on categories    for all using (is_admin()) with check (is_admin());
create policy admin_all_brands     on brands        for all using (is_admin()) with check (is_admin());
create policy admin_all_models     on models        for all using (is_admin()) with check (is_admin());
create policy admin_all_variants   on variants      for all using (is_admin()) with check (is_admin());
create policy admin_all_prices     on prices        for all using (is_admin()) with check (is_admin());
create policy admin_all_faqs       on faqs          for all using (is_admin()) with check (is_admin());
create policy admin_all_blog       on blog_posts    for all using (is_admin()) with check (is_admin());
create policy admin_all_promos     on promo_codes   for all using (is_admin()) with check (is_admin());
create policy admin_all_settings   on site_settings for all using (is_admin()) with check (is_admin());
create policy admin_all_tradeins   on trade_ins       for all using (is_admin()) with check (is_admin());
create policy admin_all_items      on trade_in_items  for all using (is_admin()) with check (is_admin());
create policy admin_all_events     on trade_in_events for all using (is_admin()) with check (is_admin());
create policy admin_all_issues     on trade_in_issues for all using (is_admin()) with check (is_admin());

-- ============ STORAGE ============
-- blog hero images uploaded from the admin
insert into storage.buckets (id, name, public) values ('blog-images', 'blog-images', true)
on conflict (id) do nothing;
create policy "public read blog images" on storage.objects
  for select using (bucket_id = 'blog-images');
create policy "admin insert blog images" on storage.objects
  for insert with check (bucket_id = 'blog-images' and public.is_admin());
create policy "admin update blog images" on storage.objects
  for update using (bucket_id = 'blog-images' and public.is_admin());
create policy "admin delete blog images" on storage.objects
  for delete using (bucket_id = 'blog-images' and public.is_admin());

-- keep updated_at fresh
create or replace function touch_updated_at() returns trigger
language plpgsql as $$ begin new.updated_at := now(); return new; end; $$;
create trigger trade_ins_touch before update on trade_ins
  for each row execute function touch_updated_at();
