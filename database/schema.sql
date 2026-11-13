-- OMAN FOOD AI: run in Supabase SQL Editor.
create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  created_at timestamptz not null default now()
);

create table if not exists public.dishes (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  name_ar text,
  category text,
  region text,
  description text,
  ingredients_summary text,
  cooking_method text,
  cultural_notes text,
  dietary_tags text[] not null default '{}',
  image_url text,
  is_published boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.ingredients (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  description text,
  common_allergens text[] not null default '{}'
);

create table if not exists public.dish_ingredients (
  dish_id uuid not null references public.dishes(id) on delete cascade,
  ingredient_id uuid not null references public.ingredients(id) on delete cascade,
  quantity numeric(10,2),
  unit text,
  primary key (dish_id, ingredient_id)
);

create table if not exists public.nutrition (
  id uuid primary key default gen_random_uuid(),
  dish_id uuid not null unique references public.dishes(id) on delete cascade,
  serving_description text not null default 'per serving',
  serving_grams numeric(10,2),
  calories_kcal numeric(10,2),
  protein_g numeric(10,2),
  carbohydrates_g numeric(10,2),
  fat_g numeric(10,2),
  fiber_g numeric(10,2),
  source_note text,
  verified boolean not null default false
);

create table if not exists public.chat_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  question text not null,
  answer text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.recognition_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  predicted_dish text not null,
  confidence text not null check (confidence in ('high','medium','low')),
  image_path text,
  created_at timestamptz not null default now()
);

create table if not exists public.recommendations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  criteria jsonb not null default '{}',
  result_dish_ids uuid[] not null default '{}',
  created_at timestamptz not null default now()
);

create index if not exists dishes_category_idx on public.dishes(category);
create index if not exists dishes_region_idx on public.dishes(region);
create index if not exists chat_history_user_created_idx on public.chat_history(user_id, created_at desc);
create index if not exists recognition_history_user_created_idx on public.recognition_history(user_id, created_at desc);

-- Enable RLS. Public food catalogue is readable; user activity is private.
alter table public.profiles enable row level security;
alter table public.dishes enable row level security;
alter table public.ingredients enable row level security;
alter table public.dish_ingredients enable row level security;
alter table public.nutrition enable row level security;
alter table public.chat_history enable row level security;
alter table public.recognition_history enable row level security;
alter table public.recommendations enable row level security;

drop policy if exists "profiles read own" on public.profiles;
create policy "profiles read own" on public.profiles for select to authenticated using (auth.uid() = id);
drop policy if exists "profiles update own" on public.profiles;
create policy "profiles update own" on public.profiles for update to authenticated using (auth.uid() = id) with check (auth.uid() = id);

drop policy if exists "published dishes readable" on public.dishes;
create policy "published dishes readable" on public.dishes for select to anon, authenticated using (is_published = true);
drop policy if exists "ingredients readable" on public.ingredients;
create policy "ingredients readable" on public.ingredients for select to anon, authenticated using (true);
drop policy if exists "dish ingredients readable" on public.dish_ingredients;
create policy "dish ingredients readable" on public.dish_ingredients for select to anon, authenticated using (true);
drop policy if exists "nutrition readable" on public.nutrition;
create policy "nutrition readable" on public.nutrition for select to anon, authenticated using (true);

 drop policy if exists "users read own chats" on public.chat_history;
create policy "users read own chats" on public.chat_history for select to authenticated using (auth.uid() = user_id);
drop policy if exists "users add own chats" on public.chat_history;
create policy "users add own chats" on public.chat_history for insert to authenticated with check (auth.uid() = user_id);
drop policy if exists "users read own recognition" on public.recognition_history;
create policy "users read own recognition" on public.recognition_history for select to authenticated using (auth.uid() = user_id);
drop policy if exists "users add own recognition" on public.recognition_history;
create policy "users add own recognition" on public.recognition_history for insert to authenticated with check (auth.uid() = user_id);
drop policy if exists "users read own recommendations" on public.recommendations;
create policy "users read own recommendations" on public.recommendations for select to authenticated using (auth.uid() = user_id);
drop policy if exists "users add own recommendations" on public.recommendations;
create policy "users add own recommendations" on public.recommendations for insert to authenticated with check (auth.uid() = user_id);

-- Private bucket for user-uploaded food photos. Backend signs access URLs.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('food-images', 'food-images', false, 8388608, array['image/jpeg','image/png','image/webp'])
on conflict (id) do nothing;

-- Starter catalogue. Nutrition values are illustrative estimates and are NOT verified.
insert into public.dishes (name, category, region, description, ingredients_summary, cooking_method, cultural_notes, dietary_tags)
values
('Omani Shuwa','Meat','Across Oman','Marinated meat traditionally slow-cooked for many hours in an underground oven.','lamb, garlic, spices, vinegar','Slow-cooked in a sealed underground oven','Often prepared for Eid and family celebrations.','{}'),
('Majboos','Rice','Across Oman','A fragrant spiced rice dish commonly served with chicken, lamb, or fish.','rice, chicken, onion, tomato, baharat, lime','Rice simmered with spiced meat or fish','A much-loved celebratory and family meal.','{}'),
('Harees','Wheat','Across Oman','A comforting dish of wheat and meat cooked until soft and blended.','wheat, chicken, lamb, salt, ghee','Slow-cooked and stirred to a porridge-like texture','Often associated with Ramadan and gatherings.','{}'),
('Omani Halwa','Dessert','Across Oman','A traditional gelatinous sweet often flavoured with rosewater, saffron, and spices.','sugar, starch, rosewater, saffron, nuts','Slow-stirred until thick and glossy','Served to guests with Omani coffee.','{}'),
('Mashuai','Seafood','Coastal Oman','Roasted kingfish served with a tangy lemon rice preparation.','kingfish, rice, lemon, spices','Fish roasted and served with rice','A well-known coastal seafood preparation.','{}')
on conflict (name) do nothing;

insert into public.nutrition (dish_id, serving_description, calories_kcal, protein_g, carbohydrates_g, fat_g, fiber_g, source_note, verified)
select id, 'illustrative serving',
 case name when 'Omani Shuwa' then 560 when 'Majboos' then 520 when 'Harees' then 480 when 'Omani Halwa' then 320 when 'Mashuai' then 430 end,
 case name when 'Omani Shuwa' then 38 when 'Majboos' then 27 when 'Harees' then 22 when 'Omani Halwa' then 3 when 'Mashuai' then 32 end,
 case name when 'Omani Shuwa' then 8 when 'Majboos' then 65 when 'Harees' then 55 when 'Omani Halwa' then 52 when 'Mashuai' then 48 end,
 case name when 'Omani Shuwa' then 38 when 'Majboos' then 16 when 'Harees' then 18 when 'Omani Halwa' then 12 when 'Mashuai' then 12 end,
 2, 'Demo seed values only; replace with values calculated from weighed recipe ingredients.', false
from public.dishes where name in ('Omani Shuwa','Majboos','Harees','Omani Halwa','Mashuai')
on conflict (dish_id) do nothing;
