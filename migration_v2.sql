-- Bureau des Lutins : migration V2 sur la base existante.
-- Préserve les codes personnels, les listes et les réservations.

update public.members
set name = case name
  when 'Lutin 1' then 'Cécile'
  when 'Lutin 2' then 'Emmanuelle'
  when 'Lutin 3' then 'Aurélie'
  when 'Lutin 4' then 'Samuel'
  when 'Lutin 5' then 'Shayra'
  when 'Lutin 6' then 'Zakia'
  when 'Lutin 7' then 'Isidore'
  else name end
where name in ('Lutin 1','Lutin 2','Lutin 3','Lutin 4','Lutin 5','Lutin 6','Lutin 7');

create table if not exists public.contributions (
 wish_id uuid not null references public.reservations(wish_id) on delete cascade,
 member_id uuid not null references public.members(id) on delete cascade,
 amount numeric(10,2) check (amount is null or amount > 0),
 created_at timestamptz not null default now(),
 primary key(wish_id, member_id)
);
alter table public.contributions enable row level security;
revoke all on public.contributions from anon, authenticated;

-- Ne renvoie jamais les contributions d'une personne sur ses propres envies.
create or replace function public.lutin_collectives(p_code text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare me_id uuid; data jsonb;
begin
 select id into me_id from public.members
 where code_hash=encode(extensions.digest(coalesce(p_code,''),'sha256'),'hex');
 if me_id is null then raise exception 'Code invalide'; end if;
 select coalesce(jsonb_agg(jsonb_build_object(
    'wish_id', r.wish_id, 'organizer_id',r.member_id,
    'participants', (select coalesce(jsonb_agg(jsonb_build_object(
        'member_id',c.member_id,'amount',c.amount) order by c.created_at),'[]'::jsonb)
        from public.contributions c where c.wish_id=r.wish_id)
    ) order by r.created_at),'[]'::jsonb) into data
 from public.reservations r
 join public.wishes w on w.id=r.wish_id
 where w.owner_id <> me_id;
 return data;
end; $$;

-- Inscription à un cadeau déjà réservé, ou retrait de sa participation.
create or replace function public.lutin_contribute(
 p_code text,p_wish_id uuid,p_action text,p_amount numeric default null)
returns void language plpgsql security definer set search_path='' as $$
declare me_id uuid; owner_id uuid; organizer_id uuid;
begin
 select id into me_id from public.members
 where code_hash=encode(extensions.digest(coalesce(p_code,''),'sha256'),'hex');
 if me_id is null then raise exception 'Code invalide'; end if;
 select w.owner_id,r.member_id into owner_id,organizer_id
 from public.wishes w join public.reservations r on r.wish_id=w.id
 where w.id=p_wish_id for update of r;
 if owner_id is null then raise exception 'Ce cadeau n''est pas réservé'; end if;
 if owner_id=me_id then raise exception 'Surprise ! Impossible de participer à son propre cadeau'; end if;
 if organizer_id=me_id then raise exception 'Tu coordonnes déjà ce cadeau'; end if;
 if p_action='join' then
   if p_amount is not null and (p_amount<=0 or p_amount>99999999) then
     raise exception 'Montant invalide';
   end if;
   insert into public.contributions(wish_id,member_id,amount)
   values(p_wish_id,me_id,p_amount)
   on conflict(wish_id,member_id) do update set amount=excluded.amount;
 elsif p_action='leave' then
   delete from public.contributions where wish_id=p_wish_id and member_id=me_id;
 else raise exception 'Action inconnue'; end if;
end; $$;

-- Un organisateur ne peut pas libérer un cadeau tant que d'autres y participent.
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
   on conflict(wish_id) do nothing;
   if not found then raise exception 'Un autre lutin a déjà réservé ce cadeau'; end if;
 elsif p_action='release' then
   if exists (select 1 from public.contributions
       where wish_id=p_wish_id) then
     raise exception 'Demande aux participants de se retirer avant de libérer le cadeau';
   end if;
   delete from public.reservations where wish_id=p_wish_id and member_id=me_id;
   if not found then raise exception 'Réservation introuvable ou non autorisée'; end if;
 elsif p_action='buy' then
   update public.reservations set status='Acheté'
   where wish_id=p_wish_id and member_id=me_id;
   if not found then raise exception 'Réservation introuvable ou non autorisée'; end if;
 else raise exception 'Action inconnue'; end if;
end; $$;

revoke all on function public.lutin_collectives(text) from public;
revoke all on function public.lutin_contribute(text,uuid,text,numeric) from public;
grant execute on function public.lutin_collectives(text) to anon,authenticated;
grant execute on function public.lutin_contribute(text,uuid,text,numeric) to anon,authenticated;
