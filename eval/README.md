# RAG Evaluation

## What we measure

| Metric | Type | API keys? |
|--------|------|-----------|
| **Hit@k** | Retrieval | No |
| **Precision@k** | Retrieval | No |
| **MRR** | Retrieval | No |
| **Heuristic faithfulness** | Answer (1–5) | No |
| **LLM-as-judge** | Answer (optional) | Anthropic |

We use **golden URLs** per question (not generated answers) for retrieval — the right way to eval RAG retrieval without label leakage.

**Not included:** RAGAS library (heavy deps). Heuristic + optional LLM judge show the same intent: *does retrieval find the right docs, and does the answer align with the reference?*

## Run

```bash
# From project root (needs ingest done first)
python eval/run_eval.py --k 5

# Retrieval only (fast)
python eval/run_eval.py --k 5 --skip-answers

# + Anthropic LLM judge on 5 samples
python eval/run_eval.py --k 5 --judge-llm --judge-sample 5
```

Output: `eval/results.json`

## Targets (FastAPI docs, local embeddings)

- Hit@5 ≥ **70%** — good prototype
- Hit@5 ≥ **85%** — strong
- MRR ≥ **0.5**
- Heuristic faithfulness ≥ **3.5/5**

## Dataset

`dataset.json` — 15 questions with `expected_urls` + `reference_answer` each.
