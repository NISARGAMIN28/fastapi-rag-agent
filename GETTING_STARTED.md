# Getting started — local prototype & Vercel (free)

Everything you need to go from zero → working demo.

---

## What you need (accounts & keys)

### FREE mode (default — no OpenAI / Anthropic)

| Item | Cost | Why |
|------|------|-----|
| Python 3.11+ | Free | Run locally |
| Nothing else | $0 | Local embeddings + local vector file + extractive answers |

Your `.env` should have:
```env
VECTOR_STORE=local
EMBEDDING_PROVIDER=local
LLM_PROVIDER=extractive
```

Data lives in `data/chunks.json` (created by ingest).

### Optional: Supabase + paid LLMs

| Item | Cost | Why |
|------|------|-----|
| [Supabase](https://supabase.com) | Free | Hosted pgvector (`VECTOR_STORE=supabase` + run `sql/migrate_to_local.sql`) |
| [Groq](https://console.groq.com) | Free tier | Better answers: `LLM_PROVIDER=groq` |
| [Ollama](https://ollama.com) | Free | Local LLM: `LLM_PROVIDER=ollama` |
| OpenAI / Anthropic | Paid | Only if you want those providers |

---

## Part A — Local working prototype (~20 min)

### Step 1: Supabase (5 min)

1. Create a project at https://supabase.com/dashboard  
2. **Settings → API** → copy:
   - Project URL → `SUPABASE_URL`
   - **service_role** key (secret) → `SUPABASE_SERVICE_KEY`  
     ⚠️ Never commit this key. Do not use the `anon` key for ingest.
3. **SQL Editor** → paste and run [`sql/schema.sql`](sql/schema.sql)

### Step 2: API keys (2 min)

```bash
cd /Users/shaikmohammadusman/Desktop/William
cp .env.example .env
```

Edit `.env`:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbG...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Step 3: Install & ingest (10 min, one-time)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Loads ~60 FastAPI doc pages into Supabase (~5–10 min)
python -m src.ingest
```

### Step 4: Run & test

```bash
./scripts/start-local.sh
```

Open in browser:

| URL | What |
|-----|------|
| http://127.0.0.1:8000/demo | Chat-style UI |
| http://127.0.0.1:8000/docs | Swagger API |
| http://127.0.0.1:8000/health | Config + chunk count |

Or terminal:

```bash
curl -s http://127.0.0.1:8000/health | python3 -m json.tool

curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I use Depends() for dependency injection?"}' \
  | python3 -m json.tool
```

### Troubleshooting local

```bash
python scripts/check_setup.py
```

| Error | Fix |
|-------|-----|
| `.env missing` | `cp .env.example .env` and fill keys |
| `0 chunks` | `python -m src.ingest` |
| Supabase RPC error | Re-run `sql/schema.sql` |
| `503` on `/ask` | Add `ANTHROPIC_API_KEY` or check “Search only” on demo UI |

**MCP (Cursor)** stays local only — see README. Not required for the web demo.

---

## Part B — Deploy API to Vercel free

Vercel hosts the **API + demo UI**. Supabase stays your database. **Ingest always runs on your laptop** (not on Vercel).

### 1. Install Vercel CLI

```bash
npm i -g vercel
# or: npx vercel
```

### 2. Add env vars in Vercel

Dashboard → your project → **Settings → Environment Variables** (Production + Preview):

| Variable | Value |
|----------|--------|
| `SUPABASE_URL` | same as `.env` |
| `SUPABASE_SERVICE_KEY` | service role key |
| `OPENAI_API_KEY` | your OpenAI key |
| `ANTHROPIC_API_KEY` | your Anthropic key |

### 3. Deploy

```bash
cd /Users/shaikmohammadusman/Desktop/William
vercel          # first time: link project
vercel --prod   # production URL
```

Your live URLs:

- `https://YOUR-PROJECT.vercel.app/demo` — UI  
- `https://YOUR-PROJECT.vercel.app/health`  
- `https://YOUR-PROJECT.vercel.app/ask` — POST JSON  

### Vercel free tier limits (important)

| Limit | Impact | Workaround |
|-------|--------|------------|
| **10s function timeout** (Hobby) | Full Claude answer may timeout | Use **“Search only”** on demo UI, or `include_generation: false` |
| **Cold start** | First request ~2–5s slower | Hit `/health` once before demo |
| **No long jobs** | Cannot run `ingest` on Vercel | Run `python -m src.ingest` locally once |
| **MCP server** | stdio process — not serverless | Use locally in Cursor |

For a Loom demo, **local is more reliable** than Vercel free for full `/ask` with Claude. Vercel is great to show a **public URL** for search/health.

### 4. Verify production

```bash
curl https://YOUR-PROJECT.vercel.app/health
```

`chunks_indexed` should match local (same Supabase).

---

## Cost estimate (demo)

| Action | Approx cost |
|--------|-------------|
| One-time ingest (~500 chunks) | ~$0.05–0.15 OpenAI embeddings |
| Per `/ask` with Claude | ~$0.01–0.03 |
| Supabase + Vercel | $0 on free tier |

---

## Quick reference

```bash
# Check everything is wired
python scripts/check_setup.py

# One-time: fill database
python -m src.ingest

# Local server
./scripts/start-local.sh

# Eval
python eval/run_eval.py --k 5

# Deploy
vercel --prod
```

---

## What runs where

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Your laptop    │     │  Vercel (free)   │     │  Supabase   │
│  python ingest  │────▶│  /ask /search    │────▶│  pgvector   │
│  MCP (Cursor)   │     │  /demo UI        │     │  (free)     │
└─────────────────┘     └──────────────────┘     └─────────────┘
        │                         │
        └──────── same .env keys ─┘
```
