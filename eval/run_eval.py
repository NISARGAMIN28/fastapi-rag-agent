#!/usr/bin/env python3
# Eval: Hit@k, Precision@k, MRR, plus heuristic answer score.

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import get_settings
from src.rag import ask, citations_for_eval, retrieve

DATASET = Path(__file__).parent / "dataset.json"

JUDGE_PROMPT = """Score RAG answer faithfulness 1-5 vs reference and context.
Reply JSON only: {"score": <int>, "reason": "<one sentence>"}"""


def load_dataset() -> list[dict]:
    return json.loads(DATASET.read_text())


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]{3,}", text.lower())
    stop = {"the", "and", "for", "with", "how", "you", "are", "can", "use", "that", "this", "from"}
    return {w for w in words if w not in stop}


def heuristic_faithfulness(reference: str, answer: str, context: str) -> dict:
    ref = _tokenize(reference)
    if not ref:
        return {"score": 0, "reason": "empty reference"}
    ans_cov = len(ref & _tokenize(answer)) / len(ref)
    ctx_cov = len(ref & _tokenize(context)) / len(ref)
    combined = 0.6 * ctx_cov + 0.4 * ans_cov
    if combined >= 0.45:
        score = 5
    elif combined >= 0.3:
        score = 4
    elif combined >= 0.18:
        score = 3
    elif combined >= 0.08:
        score = 2
    else:
        score = 1
    return {
        "score": score,
        "reason": f"context={ctx_cov:.0%} answer={ans_cov:.0%}",
        "context_overlap": round(ctx_cov, 3),
        "answer_overlap": round(ans_cov, 3),
    }


def retrieval_metrics(dataset: list[dict], k: int) -> dict:
    hits, precisions, rr = [], [], []
    per_item = []

    for item in dataset:
        retrieved = retrieve(item["question"], top_k=k)
        m = citations_for_eval(item["expected_urls"], retrieved, k=k)
        rank_score = 0.0
        for i, h in enumerate(retrieved[:k], start=1):
            if h.get("url") in item["expected_urls"]:
                rank_score = 1.0 / i
                break
        rr.append(rank_score)
        hits.append(1.0 if m["hit"] else 0.0)
        precisions.append(m["precision_at_k"])
        per_item.append({"id": item["id"], "question": item["question"], **m})

    return {
        "k": k,
        "hit_at_k": statistics.mean(hits),
        "precision_at_k": statistics.mean(precisions),
        "mrr": statistics.mean(rr),
        "n": len(dataset),
        "items": per_item,
    }


def answer_metrics_heuristic(dataset: list[dict], k: int) -> dict:
    scores, details = [], []
    for item in dataset:
        resp = ask(item["question"], top_k=k, generate=True)
        context = "\n".join(c.snippet for c in resp.citations)
        verdict = heuristic_faithfulness(item["reference_answer"], resp.answer, context)
        scores.append(verdict["score"])
        details.append({"id": item["id"], **verdict})
    return {
        "method": "heuristic_keyword_overlap",
        "mean_faithfulness": statistics.mean(scores) if scores else 0,
        "n": len(scores),
        "details": details,
    }


def llm_judge(dataset: list[dict], sample: int | None, k: int) -> dict:
    settings = get_settings()
    if not settings.anthropic_configured:
        return {"skipped": True, "reason": "ANTHROPIC_API_KEY not set"}

    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    items = dataset[:sample] if sample else dataset
    scores, details = [], []

    for item in items:
        resp = ask(item["question"], top_k=k, generate=True, settings=settings)
        context = "\n".join(c.snippet for c in resp.citations)
        msg = client.messages.create(
            model=settings.chat_model,
            max_tokens=256,
            system=JUDGE_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Q: {item['question']}\nRef: {item['reference_answer']}\n"
                        f"Ans: {resp.answer}\nCtx: {context}"
                    ),
                }
            ],
        )
        text = "".join(b.text for b in msg.content if hasattr(b, "text"))
        try:
            verdict = json.loads(text)
            score = int(verdict.get("score", 0))
        except json.JSONDecodeError:
            score, verdict = 0, {"reason": text[:200]}
        scores.append(score)
        details.append({"id": item["id"], "score": score, **verdict})

    return {
        "method": "llm_judge",
        "mean_faithfulness": statistics.mean(scores) if scores else 0,
        "n": len(scores),
        "details": details,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--skip-answers", action="store_true")
    parser.add_argument("--judge-llm", action="store_true")
    parser.add_argument("--judge-sample", type=int, default=5)
    parser.add_argument("--output", type=str, default="eval/results.json")
    args = parser.parse_args()

    settings = get_settings()
    from src.vector_store import chunk_count

    n = chunk_count(settings)
    if n == 0:
        print("Run: python -m src.ingest", file=sys.stderr)
        sys.exit(1)

    dataset = load_dataset()
    print(f"\nEval: {len(dataset)} questions, k={args.k}, {n} chunks\n")

    retrieval = retrieval_metrics(dataset, k=args.k)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "retrieval": retrieval,
    }

    print(f"Hit@{args.k}: {retrieval['hit_at_k']:.2%}")
    print(f"Precision@{args.k}: {retrieval['precision_at_k']:.2%}")
    print(f"MRR: {retrieval['mrr']:.3f}")

    if not args.skip_answers:
        report["answer_heuristic"] = answer_metrics_heuristic(dataset, k=args.k)
        print(f"Heuristic faithfulness: {report['answer_heuristic']['mean_faithfulness']:.2f}/5")

    if args.judge_llm:
        report["llm_judge"] = llm_judge(dataset, sample=args.judge_sample, k=args.k)

    out = Path(args.output)
    out.write_text(json.dumps(report, indent=2))
    print(f"Wrote {out}\n")


if __name__ == "__main__":
    main()
