# OCBuyBack

Device buyback site for Henry Galeano's shop in Brea, CA. Live on
**www.ocbuyback.com** since 14 Oct 2026, rebuilt off the FlipTech platform onto
Netlify + Supabase. Roughly 145 orders/month, about a quarter of which become
paid devices; 74% of the historical business is out-of-state mail-in.

## The one rule that matters most

**The generator is the source of truth. Never hand-edit a built page.**

`generator/generate_concept_pages.py` writes everything under
`concepts/freshair/`. Editing a built file looks like it works and is silently
reverted by the next build. If a page needs changing, change the generator.

The single exception: `concepts/freshair/index.html` is a **static source file**
that the generator patches in place (hero payout figures, and the canonical
attribution script). It is tracked in git and edited by hand. It used to carry
its own fork of the attribution code, missing gclid capture entirely, so paid
ad clicks landing on the homepage recorded as organic. The generator now
injects `ATTRIB_JS` into it and **raises** if the injection does not land.

## Build and deploy

```
python3 generator/sync_blog_from_db.py
python3 generator/sync_catalog_from_db.py
python3 generator/sync_trade_stats_from_db.py
python3 generator/generate_concept_pages.py
rm -rf concepts/freshair/admin && cp -r admin concepts/freshair/admin
```

That is the netlify.toml build command. Run it locally before pushing.

- **Push to `main` deploys.** No separate staging branch.
- **Netlify runs Python 3.11** — compile with `python3.11 -m py_compile` before
  pushing. No backslashes inside f-string expressions.
- **Build output is committed.** Sync `admin/` into `concepts/freshair/admin`
  in the same commit or the deployed admin lags the source.
- Deploys land in roughly 30–45 seconds.

### Verifying a deploy

Poll production for a string that **did not exist in the previous build**. A
check against an already-present string passes instantly against the stale
build — this happened twice, and once let a test order through that bought a
real, billable UPS label. A new function name or CSS rule works; a generic
word does not.

## Data

The database is authoritative; the site is a render of it.

- `catalog_flat` → `data/catalog.json` (prices, enabled flags, images)
- `model_trade_stats` / `trade_stats_overall` → `data/trade_stats.json`
  (aggregate-only views, safe for the anon key, 25-trade floor)
- `data/published_urls.json` is a **committed manifest of every device URL ever
  published**. It is the only record of what Google has seen, and it drives the
  retired-model redirects. CI checks out clean, so anything keyed off local
  files alone silently produces nothing.

A device needs **both** `models.enabled` and per-price `enabled` to appear.
Henry has ticked 120 price boxes and seen nothing happen because the model flag
was off. Check the model flag first.

### Legacy data gotchas

- `trade_in_items` holds 175k rows for ~27k orders. **130 orders contain 136,808
  of them** — cart-spam incidents, including one 2020 order with the same iPhone
  added 36,537 times for a $29.9m quote. Always filter
  `having count(*) <= 20` before aggregating. The views above already do.
- Only **26.4%** of quotes ever become paid devices. A quote is not a sale.
- Legacy orders carry their original FlipTech dates, so date-windowed queries
  mix both systems. Oct 11–13 2026 is missing entirely (never imported).
- `legacy.ocbuyback.com` is the old FlipTech instance, still live for rollback.

## SEO invariants

These were each a real bug. Don't reintroduce them.

- **Canonicals and sitemap URLs must return 200, not 301.** Netlify serves pages
  as directories, so `/x/` is the 200 and `/x` redirects. Use `canon_path()`.
- **Redirect targets must not themselves redirect.** Check for chains.
- **Device pages must stay differentiated.** They were 81–94% identical, which
  is thin content regardless of length. `device_data_blocks()` renders a price
  matrix and real trade statistics per model to break that up. Anything added to
  the template uniformly makes the problem worse, not better.
- **Never show a historical average beside live prices.** The iPhone 13 Pro Max
  averaged $555 across 2021–26 while its live top price is $375; next to a
  current price table that reads as a promise.

## Secrets

- Never commit keys. They live in Netlify env vars or the `site_settings` table.
- `reference/site-snapshot-2026-09-03/` is gitignored — it contains FlipTech AWS
  key IDs that trip GitHub push protection.
- The FlipTech dump holds **ten other businesses' customer data**. Only
  `shop_id = 3` is OCBuyBack's.
- `CREATE TABLE AS` in Supabase produces a table with no RLS, readable by anon.

## Integrations

- **EasyPost** — never set `is_return`. Addresses are already in return
  orientation; the flag swaps them a second time and prints labels addressed to
  the customer. This shipped five of them.
- **Trade Into Cash** — conversions are reported server-side. The referral tag
  is the source of truth; a missing click id never means the order is theirs. A
  `200 {success:false}` is a failure, not a success.
- **Price feeds** (Flipsy / SellCell / BankMyCell / Swappa) render live from the
  database and need no publish, unlike the website. Every deeplink carries a
  `utm_source` — comparison sites strip referrers, so the tag is the only signal
  that survives. SellCell's tag lives in the `netlify.toml` redirect, because
  that rule's destination replaces the incoming query string.

## Working style

- **Show changes locally before pushing.** Serve the build and verify in a
  browser; screenshot anything visual.
- **Measure, don't eyeball.** Layout claims should come from
  `getBoundingClientRect`, not from looking at it.
- **Test with the full real dataset.** A 10-row sample hid the two columns that
  actually overflow the orders table, and a 10-page sample produced the wrong
  diagnosis of the device pages entirely.
- **Verify a URL exists before reasoning about it.** A page measured at "48
  words" turned out to be a 404 for a URL that was never real.
