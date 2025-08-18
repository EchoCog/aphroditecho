-- Memories table
create table if not exists public.memories (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  title text not null,
  content text not null,
  tags text[] default '{}',
  embedding vector(1536),
  type text default 'memory',
  context text,
  metadata jsonb default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Useful index on user and created_at
create index if not exists idx_memories_user_created_at on public.memories (user_id, created_at desc);

-- Ensure pgvector extension exists
create extension if not exists vector;

-- RPC: match_memories
create or replace function public.match_memories(
  query_embedding vector(1536),
  match_threshold float,
  match_count int,
  user_id text,
  filter_type text default null
)
returns table (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
language sql stable as $$
  select m.id,
         m.content,
         m.metadata,
         1 - (m.embedding <=> query_embedding) as similarity
  from public.memories m
  where m.user_id = match_memories.user_id
    and (filter_type is null or m.type = filter_type)
    and m.embedding is not null
    and 1 - (m.embedding <=> query_embedding) >= match_threshold
  order by m.embedding <=> query_embedding asc
  limit match_count;
$$;

-- Permissions (adjust to your auth model)
grant select, insert, update, delete on table public.memories to anon, authenticated;
grant execute on function public.match_memories(vector, float, int, text, text) to anon, authenticated;