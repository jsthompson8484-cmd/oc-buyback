-- Legacy (FlipTech) trade-in import — schema additions.
-- Orders carried over from the old platform keep their original identifiers so
-- support can match them to old emails, and are clearly marked in the admin.
-- Safe to re-run.

alter table trade_ins
  add column if not exists legacy_id bigint,
  add column if not exists legacy_status text,
  add column if not exists legacy_data jsonb;

create unique index if not exists trade_ins_legacy_id_key on trade_ins (legacy_id) where legacy_id is not null;
create index if not exists trade_ins_legacy_idx on trade_ins (legacy_id) where legacy_id is not null;

comment on column trade_ins.legacy_id is 'FlipTech trade_ins.id — present only on orders imported from the old platform';
comment on column trade_ins.legacy_status is 'Original FlipTech status string (our status is the closest mapped equivalent)';
comment on column trade_ins.legacy_data is 'Raw FlipTech fields with no home in the new schema (payment/shipping enums, check number, payout tracking)';

-- "expired" = quote issued, customer never shipped. 18k of the legacy rows are
-- this; mapping them to cancelled would misrepresent the history.
alter table trade_ins drop constraint if exists trade_ins_status_check;
alter table trade_ins add constraint trade_ins_status_check check (status = any (array[
  'initiated','shipped','delivered','received','evaluating','adjusted',
  'action_pending','paid','returned','cancelled','expired']));

-- items: keep the original line id so re-runs are idempotent
alter table trade_in_items add column if not exists legacy_id bigint;
create unique index if not exists trade_in_items_legacy_id_key on trade_in_items (legacy_id) where legacy_id is not null;
