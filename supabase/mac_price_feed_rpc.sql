-- apply_mac_price_feed(feed jsonb) — bulk-apply a Mac trade-in price feed.
--
-- Called by the sync-mac-prices Netlify function (service role only) with
-- [{model_slug, processor, memory, condition, price}, ...]. Keys must match
-- the catalog byte-for-byte (see data/mac_price_feed_keys.csv — the contract
-- given to the feed provider).
--
-- Safety rails:
--   * scoped to the Mac categories (9,11,12,13,14) — a bad feed can never
--     touch phones/tablets/etc.
--   * rows with price <= 0 or > 20000 are ignored
--   * jump guard: if a row already has a nonzero price and the new price
--     moves more than 40%, the row is skipped (counted as "guarded") so one
--     bad feed day can't publish nonsense
--   * only price + price.enabled are written; model/category enabled flags
--     stay under Henry's control, so nothing appears on the site until he
--     enables the model/category
--   * unknown keys are simply not matched (reported as total - matched)

create or replace function apply_mac_price_feed(feed jsonb)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  n_total   int;
  n_matched int;
  n_guarded int;
  n_updated int;
begin
  n_total := jsonb_array_length(feed);

  create temp table _feed on commit drop as
  select distinct on (x.model_slug, x.processor, x.memory, x.condition)
         p.variant_id, p.condition, x.price::numeric as new_price, p.price as old_price
  from jsonb_to_recordset(feed)
       as x(model_slug text, processor text, memory text, condition text, price numeric)
  join models m   on m.slug = x.model_slug and m.category_id in (9, 11, 12, 13, 14)
  join variants v on v.model_id = m.id and v.carrier = x.processor and v.storage = x.memory
  join prices p   on p.variant_id = v.id and p.condition = x.condition
  where x.price > 0 and x.price <= 20000
  order by x.model_slug, x.processor, x.memory, x.condition;

  select count(*) into n_matched from _feed;
  select count(*) into n_guarded from _feed
   where old_price > 0 and abs(new_price - old_price) / old_price > 0.4;

  update prices p
     set price = f.new_price, enabled = true
    from _feed f
   where p.variant_id = f.variant_id and p.condition = f.condition
     and not (f.old_price > 0 and abs(f.new_price - f.old_price) / f.old_price > 0.4)
     and (p.price is distinct from f.new_price or p.enabled = false);
  get diagnostics n_updated = row_count;

  return jsonb_build_object(
    'total', n_total, 'matched', n_matched,
    'guarded', n_guarded, 'updated', n_updated);
end
$$;

revoke all on function apply_mac_price_feed(jsonb) from public;
revoke all on function apply_mac_price_feed(jsonb) from anon;
revoke all on function apply_mac_price_feed(jsonb) from authenticated;
