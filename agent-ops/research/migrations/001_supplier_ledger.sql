-- V2 plugin migration: additive/idempotent; backup before deployment.
CREATE TABLE IF NOT EXISTS public.yuyan_supplier_cases (
 case_id text PRIMARY KEY, owner_id text NOT NULL, version integer NOT NULL,
 payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS yuyan_supplier_owner ON public.yuyan_supplier_cases(owner_id);
CREATE TABLE IF NOT EXISTS public.yuyan_supplier_commands (
 owner_id text NOT NULL, idempotency_key text NOT NULL, payload_hash text NOT NULL,
 response jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(owner_id,idempotency_key));
