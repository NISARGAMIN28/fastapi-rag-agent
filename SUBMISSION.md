# Submission checklist (Ovidius take-home)

## Deliverables

- [ ] **GitHub repo** — push this folder; share with `tech@ovidius.ai` or make public
- [ ] **README** — already in repo root
- [ ] **Loom (5–10 min)** — follow script in README § "Loom walkthrough"
- [ ] **"What next"** — README § "What I'd build next"

## Before recording Loom

1. Create Supabase project + run `sql/schema.sql`
2. Fill `.env` from `.env.example`
3. `python -m src.ingest`
4. `uvicorn src.api:app --reload`
5. `python eval/run_eval.py --k 5` (note Hit@5 / MRR on screen)
6. Configure MCP in Cursor → demo `ask_docs`

## Suggested Loom title

*"FastAPI Docs RAG — Supabase pgvector, eval harness, MCP server"*

## One-liner for email

Built a cited RAG agent over FastAPI docs with Supabase/pgvector ingestion, FastAPI `/ask` endpoint, 15-question eval (Hit@k, MRR, LLM judge), and an MCP server for Cursor/Claude — repo + Loom linked.
