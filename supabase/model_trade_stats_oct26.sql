-- Per-model trade statistics for the public device pages.
--
-- The device pages were 81-94% identical to each other, which is thin content
-- regardless of word count. This exposes the one thing no competitor can copy:
-- what we have actually bought. It is the ONLY route by which trade data
-- reaches a public page, so it is deliberately narrow.
--
-- Safe to expose to anon:
--   * aggregates only, never a row that identifies an order or a customer
--   * a 25-trade floor, so no statistic describes a small enough group to
--     single anyone out
--   * paid orders only -- an abandoned quote is not something we "bought"
--
-- The <= 20 items filter excludes cart-spam orders. 130 legacy orders hold
-- 136,808 of the 175,097 item rows; one 2020 incident added the same iPhone
-- 36,537 times for a $29.9m quote. Without this filter one abusive order
-- rewrites a model's entire history.

create or replace view public.model_trade_stats as
with sane as (
  select trade_in_id from trade_in_items group by trade_in_id having count(*) <= 20
),
items as (
  select i.model, i.condition, i.storage, i.carrier, i.quoted_price, t.created_at
  from trade_in_items i
  join sane s on s.trade_in_id = i.trade_in_id
  join trade_ins t on t.id = i.trade_in_id
  where coalesce(t.legacy_status, t.status) = 'paid'
    and i.model is not null and i.model <> '(device removed from catalog)'
)
select
  model,
  count(*)::int                                                          as traded,
  round(avg(quoted_price))::int                                          as avg_quote,
  round(100.0 * count(*) filter (where condition = 'Flawless') / count(*))::int      as pct_flawless,
  round(100.0 * count(*) filter (where condition in ('Minor Damage','Broken'))
        / count(*))::int                                                 as pct_damaged,
  min(created_at)::date                                                  as first_traded,
  max(created_at)::date                                                  as last_traded,
  (select jsonb_agg(jsonb_build_object('k', storage, 'n', n) order by n desc)
     from (select storage, count(*) n from items i2
           where i2.model = i.model and i2.storage is not null
           group by storage) z)                                          as storage_mix,
  (select jsonb_agg(jsonb_build_object('k', carrier, 'n', n) order by n desc)
     from (select carrier, count(*) n from items i3
           where i3.model = i.model and i3.carrier is not null
           group by carrier) z)                                          as carrier_mix
from items i
group by model
having count(*) >= 25;

grant select on public.model_trade_stats to anon, authenticated;

-- site-wide baseline, so a page can say "below average" without us inventing
-- the average. Same filters, one row.
create or replace view public.trade_stats_overall as
with sane as (
  select trade_in_id from trade_in_items group by trade_in_id having count(*) <= 20
)
select
  count(*)::int as traded,
  round(100.0 * count(*) filter (where i.condition in ('Minor Damage','Broken'))
        / count(*))::int as pct_damaged,
  round(100.0 * count(*) filter (where i.condition = 'Flawless') / count(*))::int as pct_flawless
from trade_in_items i
join sane s on s.trade_in_id = i.trade_in_id
join trade_ins t on t.id = i.trade_in_id
where coalesce(t.legacy_status, t.status) = 'paid' and i.model is not null;

grant select on public.trade_stats_overall to anon, authenticated;
