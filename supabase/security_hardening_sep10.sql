-- Security hardening — Sep 10 audit findings.
-- Safe to re-run. Also reflected in schema.sql for fresh installs.

-- 1) is_admin(): don't trust the raw JWT email claim alone. Verify the caller
--    is a real, email-confirmed auth user with an allowlisted address. This
--    closes the "sign up as an admin email while Confirm-Email is toggled off"
--    hole and pins search_path (Supabase linter 0011).
create or replace function is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1 from auth.users u
    where u.id = auth.uid()
      and u.email_confirmed_at is not null
      and lower(u.email) in ('js@neartechpartners.com', 'henry@ocbuyback.com')
  );
$$;

-- 2) catalog_flat: run with the caller's privileges so it can never become an
--    RLS bypass channel if catalog policies are ever tightened.
alter view catalog_flat set (security_invoker = true);

-- 3) site_settings: public read only for known-public keys; everything else
--    (any future key) is admin-only by default.
drop policy if exists public_read_settings on site_settings;
create policy public_read_settings on site_settings for select
  using (key in ('contact', 'store_hours', 'quote', 'social', 'conditions', 'mac_price_sync'));

-- 4) storage: make the UPDATE checks explicit, and give admins the missing
--    DELETE on device-images (photos were undeletable through the client).
drop policy if exists "admin update blog images" on storage.objects;
create policy "admin update blog images" on storage.objects for update
  using (bucket_id = 'blog-images' and is_admin())
  with check (bucket_id = 'blog-images' and is_admin());
drop policy if exists "admin update device images" on storage.objects;
create policy "admin update device images" on storage.objects for update
  using (bucket_id = 'device-images' and is_admin())
  with check (bucket_id = 'device-images' and is_admin());
drop policy if exists "admin delete device images" on storage.objects;
create policy "admin delete device images" on storage.objects for delete
  using (bucket_id = 'device-images' and is_admin());

-- 5) mac price feed RPC: include pg_temp explicitly (defense in depth; EXECUTE
--    is already revoked from public/anon/authenticated).
alter function apply_mac_price_feed(jsonb) set search_path = public, pg_temp;
