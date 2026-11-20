-- Exécuter dans l'éditeur SQL d'un projet Supabase neuf.
create extension if not exists pgcrypto with schema extensions;
create table if not exists public.members (
 id uuid primary key default gen_random_uuid(),
 name text not null unique check (length(trim(name)) between 1 and 80),
 code_hash text not null unique,
 created_at timestamptz not null default now()
);
create table if not exists public.wishes (
 id uuid primary key default gen_random_uuid(),
 owner_id uuid not null references public.members(id) on delete cascade,
 title text not null check (length(trim(title)) between 1 and 180),
 details text not null default '' check (length(details)<=1500),
 price numeric(10,2) check (price is null or price>=0),
 url text not null default '' check (length(url)<=1000),
 priority text not null default 'Ça me ferait plaisir'
 check (priority in ('J’en rêve','Ça me ferait plaisir','Si le Père Noël est riche')),
 created_at timestamptz not null default now()
);
create table if not exists public.reservations (
 wish_id uuid primary key references public.wishes(id) on delete cascade,
 member_id uuid not null references public.members(id) on delete cascade,
 status text not null default 'Réservé' check (status in ('Réservé','Acheté')),
 created_at timestamptz not null default now()
);
alter table public.members enable row level security;
alter table public.wishes enable row level security;
alter table public.reservations enable row level security;
revoke all on public.members,public.wishes,public.reservations from anon,authenticated;

create or replace function public.lutin_identity(p_code text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare m public.members%rowtype;
begin
 select * into m from public.members
 where code_hash=encode(extensions.digest(coalesce(p_code,''),'sha256'),'hex');
 if not found then return null; end if;
 return jsonb_build_object('id',m.id,'name',m.name);
end; $$;

create or replace function public.lutin_board(p_code text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare me_id uuid; mm jsonb; ww jsonb; rr jsonb;
begin
 select id into me_id from public.members
 where code_hash=encode(extensions.digest(coalesce(p_code,''),'sha256'),'hex');
 if me_id is null then raise exception 'Code invalide'; end if;
 select coalesce(jsonb_agg(jsonb_build_object('id',id,'name',name) order by name),'[]'::jsonb)
 into mm from public.members;
 select coalesce(jsonb_agg(jsonb_build_object('id',w.id,'owner_id',w.owner_id,
 'title',w.title,'details',w.details,'price',w.price,'url',w.url,'priority',w.priority,
 'reservation',case when w.owner_id=me_id then null else
 (select jsonb_build_object('member_id',r.member_id,'status',r.status)
 from public.reservations r where r.wish_id=w.id) end)
 order by w.created_at desc),'[]'::jsonb) into ww from public.wishes w;
 select coalesce(jsonb_agg(jsonb_build_object('wish_id',r.wish_id,
 'title',w.title,'owner_name',m.name,'status',r.status)
 order by r.created_at desc),'[]'::jsonb) into rr
 from public.reservations r join public.wishes w on w.id=r.wish_id
 join public.members m on m.id=w.owner_id where r.member_id=me_id;
 return jsonb_build_object('me',me_id,'members',mm,'wishes',ww,'my_reservations',rr);
end; $$;

create or replace function public.lutin_save_wish(
 p_code text,p_title text,p_details text default '',p_price numeric default null,
 p_url text default '',p_priority text default 'Ça me ferait plaisir',p_id uuid default null)
returns void language plpgsql security definer set search_path='' as $$
declare me_id uuid;
begin
 select id into me_id from public.members
 where code_hash=encode(extensions.digest(coalesce(p_code,''),'sha256'),'hex');
 if me_id is null then raise exception 'Code invalide'; end if;
 if p_id is null then
 insert into public.wishes(owner_id,title,details,price,url,priority)
 values(me_id,trim(p_title),coalesce(p_details,''),p_price,coalesce(p_url,''),p_priority);
 else
 update public.wishes set title=trim(p_title),details=coalesce(p_details,''),
 price=p_price,url=coalesce(p_url,''),priority=p_priority
 where id=p_id and owner_id=me_id;
 if not found then raise exception 'Cadeau introuvable ou non autorisé'; end if;
 end if;
end; $$;

create or replace function public.lutin_delete_wish(p_code text,p_id uuid)
returns void language plpgsql security definer set search_path='' as $$
declare me_id uuid;
begin
 select id into me_id from public.members
 where code_hash=encode(extensions.digest(coalesce(p_code,''),'sha256'),'hex');
 if me_id is null then raise exception 'Code invalide'; end if;
 delete from public.wishes where id=p_id and owner_id=me_id;
 if not found then raise exception 'Cadeau introuvable ou non autorisé'; end if;
end; $$;

create or replace function public.lutin_reserve(p_code text,p_wish_id uuid,p_action text)
returns void language plpgsql security definer set search_path='' as $$
declare me_id uuid; gift_owner uuid;
begin
 select id into me_id from public.members
 where code_hash=encode(extensions.digest(coalesce(p_code,''),'sha256'),'hex');
 if me_id is null then raise exception 'Code invalide'; end if;
 select owner_id into gift_owner from public.wishes where id=p_wish_id;
 if gift_owner is null then raise exception 'Cadeau introuvable'; end if;
 if gift_owner=me_id then raise exception 'Impossible de réserver son propre cadeau'; end if;
 if p_action='reserve' then
 insert into public.reservations(wish_id,member_id) values(p_wish_id,me_id)
 on conflict (wish_id) do nothing;
 if not found then raise exception 'Un autre lutin a déjà réservé ce cadeau'; end if;
 elsif p_action='release' then
 delete from public.reservations where wish_id=p_wish_id and member_id=me_id;
 if not found then raise exception 'Réservation introuvable ou non autorisée'; end if;
 elsif p_action='buy' then
 update public.reservations set status='Acheté'
 where wish_id=p_wish_id and member_id=me_id;
 if not found then raise exception 'Réservation introuvable ou non autorisée'; end if;
 else raise exception 'Action inconnue'; end if;
end; $$;

revoke all on function public.lutin_identity(text) from public;
revoke all on function public.lutin_board(text) from public;
revoke all on function public.lutin_save_wish(text,text,text,numeric,text,text,uuid) from public;
revoke all on function public.lutin_delete_wish(text,uuid) from public;
revoke all on function public.lutin_reserve(text,uuid,text) from public;
grant execute on function public.lutin_identity(text) to anon,authenticated;
grant execute on function public.lutin_board(text) to anon,authenticated;
grant execute on function public.lutin_save_wish(text,text,text,numeric,text,text,uuid) to anon,authenticated;
grant execute on function public.lutin_delete_wish(text,uuid) to anon,authenticated;
grant execute on function public.lutin_reserve(text,uuid,text) to anon,authenticated;
