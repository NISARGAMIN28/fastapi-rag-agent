-- Run this ONCE in Supabase SQL Editor (replaces 1536-dim OpenAI schema with 384-dim local embeddings)
-- Safe if you have 0 chunks or are OK re-running ingest.

drop function if exists match_doc_chunks(vector, int, float);
drop function if exists match_doc_chunks(vector(1536), int, float);
drop table if exists doc_chunks cascade;

create extension if not exists vector;

create table doc_chunks (
  id bigserial primary key,
  url text not null,
  title text,
  section text,
  content text not null,
  chunk_index int not null default 0,
  token_count int,
  embedding vector(384),
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  unique (url, chunk_index)
);

create index doc_chunks_embedding_idx
  on doc_chunks using ivfflat (embedding vector_cosine_ops)
  with (lists = 50);

create index doc_chunks_url_idx on doc_chunks (url);

create or replace function match_doc_chunks(
  query_embedding vector(384),
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
