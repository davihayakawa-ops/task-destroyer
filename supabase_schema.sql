-- Task Destroyer Supabase schema
-- Run this in Supabase SQL Editor.

create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  display_name text,
  role text not null default 'member' check (role in ('admin', 'member')),
  plan text not null default 'free',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.workspaces (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  slug text not null unique,
  name text not null,
  plan text not null default 'free',
  monthly_call_limit integer not null default 100,
  stripe_customer_id text,
  stripe_subscription_id text,
  subscription_status text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.workspaces add column if not exists stripe_customer_id text;
alter table public.workspaces add column if not exists stripe_subscription_id text;
alter table public.workspaces add column if not exists subscription_status text;

create table if not exists public.workspace_members (
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null default 'owner' check (role in ('owner', 'admin', 'member')),
  created_at timestamptz not null default now(),
  primary key (workspace_id, user_id)
);

create table if not exists public.products (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  local_id text not null,
  name text,
  data jsonb not null default '{}'::jsonb,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, local_id)
);

create table if not exists public.cores (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  product_id uuid references public.products(id) on delete cascade,
  local_product_id text not null,
  version_label text,
  status text not null default 'ai_generated',
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.generated_contents (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  product_id uuid references public.products(id) on delete cascade,
  local_product_id text not null,
  content_type text not null,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.api_usage (
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  period text not null,
  used_calls integer not null default 0,
  updated_at timestamptz not null default now(),
  primary key (workspace_id, period)
);

create table if not exists public.consents (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  terms_version text not null,
  accepted boolean not null default true,
  accepted_at timestamptz not null default now(),
  unique (user_id, terms_version)
);

create table if not exists public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  actor_id uuid references auth.users(id) on delete set null,
  actor_email text,
  event_type text not null,
  action text not null,
  status text not null default 'ok',
  product_id uuid references public.products(id) on delete set null,
  local_product_id text,
  detail jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;
alter table public.workspaces enable row level security;
alter table public.workspace_members enable row level security;
alter table public.products enable row level security;
alter table public.cores enable row level security;
alter table public.generated_contents enable row level security;
alter table public.api_usage enable row level security;
alter table public.consents enable row level security;
alter table public.audit_logs enable row level security;

create policy "profiles_select_own" on public.profiles
  for select using (id = auth.uid());

create policy "workspace_members_select_own" on public.workspace_members
  for select using (user_id = auth.uid());

create policy "workspaces_select_member" on public.workspaces
  for select using (
    exists (
      select 1 from public.workspace_members wm
      where wm.workspace_id = id and wm.user_id = auth.uid()
    )
  );

create policy "products_member_all" on public.products
  for all using (
    exists (
      select 1 from public.workspace_members wm
      where wm.workspace_id = products.workspace_id and wm.user_id = auth.uid()
    )
  );

create policy "cores_member_all" on public.cores
  for all using (
    exists (
      select 1 from public.workspace_members wm
      where wm.workspace_id = cores.workspace_id and wm.user_id = auth.uid()
    )
  );

create policy "generated_member_all" on public.generated_contents
  for all using (
    exists (
      select 1 from public.workspace_members wm
      where wm.workspace_id = generated_contents.workspace_id and wm.user_id = auth.uid()
    )
  );

create policy "usage_member_select" on public.api_usage
  for select using (
    exists (
      select 1 from public.workspace_members wm
      where wm.workspace_id = api_usage.workspace_id and wm.user_id = auth.uid()
    )
  );

create policy "consents_own_select" on public.consents
  for select using (user_id = auth.uid());

create policy "audit_member_select" on public.audit_logs
  for select using (
    exists (
      select 1 from public.workspace_members wm
      where wm.workspace_id = audit_logs.workspace_id and wm.user_id = auth.uid()
    )
  );
