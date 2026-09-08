# OCBuyBack Rebuild

Rebuild of ocbuyback.com off the FlipTech platform. Netlify + Supabase, preserving the
live site's URL structure exactly (see `reference/parity_baseline.csv`).

## Layout

- `data/` — cleaned catalog (`catalog_clean.csv` re-importable, `catalog.json` nested)
- `generator/generate_concept_pages.py` — builds the Fresh Air site into `concepts/freshair/`
- `supabase/schema.sql` — full DDL + RLS (run first in the SQL editor)
- `supabase/generate_seed.py` → `seed.sql` — catalog + FAQs + settings seed (run second)
- `netlify/functions/` — `create-trade-in.mjs` (checkout, server-side re-pricing),
  `track-order.mjs` (public tracking by order # + email)
- `admin/` — admin panel (Trade-Ins, Catalog price grid, Promo Codes, FAQs)
- `reference/` — full snapshot of the old site (Sep 3 2026) + parity baseline
- `concepts/` — clickable design concepts; `freshair/` is the chosen direction
  (preview: `cd concepts && python3 -m http.server 8791`)

## Supabase setup (one time)

1. Create a project at supabase.com (region: us-west).
2. SQL editor → run `supabase/schema.sql`.
3. Run `supabase/seed.sql` (large — use `psql` if the editor times out:
   `psql "$SUPABASE_DB_URL" -f supabase/seed.sql`).
4. Update the admin allowlist in **two places**: `is_admin()` in schema.sql (re-run the
   `create or replace function` block) and `admin/config.js`.
5. Fill `admin/config.js` with the project URL + anon key (Settings → API).
6. Netlify env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (service-role key).
7. Auth → providers: enable Email (magic link / OTP). Add the deployed `/admin/` URL to
   the redirect allowlist.

## Business rules (do not regress)

- Only `enabled=true` catalog rows carry prices; disabled rows stay at $0 in the DB.
- Payment methods: PayPal (auto payout), check (auto via Lob), Zelle, Venmo, cash in store.
  (PayPal re-added Sep 8 per user for automated payouts — no processing fee shown.)
- Payout env vars: `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` (developer.paypal.com → live app),
  `LOB_API_KEY`, `LOB_BANK_ACCOUNT_ID`, `LOB_FROM_ADDRESS_ID` (dashboard.lob.com — bank account
  must be added + verified in Lob before checks can send).
- Never mention shipping insurance anywhere on the site.
- Buyback site, not a marketplace. No `/buy` store (301 → `/sell`).
- 14-day price lock; paid within 1 business day of arrival; free prepaid USPS label.

## Still pending

- Shipping label purchase (waiting on the customer's carrier account details)
- Resend (email) + Twilio (SMS) keys and templates
- Blog migration (64 posts in `reference/site-snapshot-2026-09-03/blog/`)
- Track Order page, FAQ page, static pages in the generator
- DNS access for cutover
