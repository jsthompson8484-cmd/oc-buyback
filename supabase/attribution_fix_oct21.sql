-- Attribution fixes, 2026-10-21.
--
-- Context: "Direct" was 48% of all orders, but at least 10 of those 26 orders
-- landed on a deep device page nobody types by hand, and 8 of those matched a
-- price-feed deeplink exactly. Root cause: the four feeds emitted untagged
-- URLs, and comparison sites strip the referrer — so Flipsy, SellCell and
-- BankMyCell had sent ZERO attributed orders ever, despite being live feeds.

begin;

-- 1. First-touch timestamp. The browser already captured it; the API dropped
--    it. Needed to join an order to the right day of Search Console data,
--    since a seller may click days before checking out.
alter table trade_ins add column if not exists first_touch_at timestamptz;

comment on column trade_ins.first_touch_at is
  'When the visitor first landed (browser-supplied, validated server-side). '
  'Join key to GSC daily query data; NOT the order date.';

-- 2. Relabel the historical bucket to match what the code now writes. Same
--    meaning, honest name: most of it is stripped referrers, not people
--    typing the domain.
update trade_ins set source = 'Direct / unknown'
 where source = 'Direct';

-- 3. Backfill first_touch_at where we can defend a value. We never stored the
--    real first touch, so the only honest fill is for orders whose attribution
--    we know began at checkout time anyway -- i.e. none. Left NULL on purpose:
--    a guessed timestamp would silently corrupt the GSC join later.

commit;

-- verify
select source, count(*) from trade_ins where legacy_id is null group by 1 order by 2 desc;
