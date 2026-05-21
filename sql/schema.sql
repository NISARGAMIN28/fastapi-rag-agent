-- Run in Supabase SQL Editor (Dashboard → SQL)
create extension if not exists vector;

create table if not exists doc_chunks (
  id bigserial primary key,
  url text not null,
  title text,
  section text,
  content text not null,
  chunk_index int not null default 0,
  token_count int,
  embedding vector(1536),
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  unique (url, chunk_index)
);

create index if not exists doc_chunks_embedding_idx
  on doc_chunks using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

create index if not exists doc_chunks_url_idx on doc_chunks (url);

-- Semantic search RPC (cosine distance; lower = more similar)
create or replace function match_doc_chunks(
  query_embedding vector(1536),
  match_count int default 5,
  match_threshold float default 0.0
)
returns table (
  id bigint,
  url text,
  title text,
  section text,
  content text,
  chunk_index int,
  metadata jsonb,
  similarity float
)
language sql stable
as $$
  select
    dc.id,
    dc.url,
    dc.title,
    dc.section,
    dc.content,
    dc.chunk_index,
    dc.metadata,
    1 - (dc.embedding <=> query_embedding) as similarity
  from doc_chunks dc
  where dc.embedding is not null
    and 1 - (dc.embedding <=> query_embedding) > match_threshold
  order by dc.embedding <=> query_embedding
  limit match_count;
$$;
