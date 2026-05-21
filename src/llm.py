# Answer generation: extractive (default), ollama, groq, gemini, anthropic, openai.

from __future__ import annotations

import httpx

from src.config import Settings, get_settings


def _system_prompt(settings: Settings) -> str:
    kb = settings.knowledge_base_name
    return (
        f"You answer from {kb} using only the provided context. "
        "Cite as [1], [2]. End with Sources: [n] Title — URL."
    )


def generate_answer(
    question: str,
    context: str,
    settings: Settings | None = None,
) -> str:
    settings = settings or get_settings()
    provider = settings.llm_provider.lower()

    if provider == "extractive":
        return _extractive_answer(question, context, settings)
    if provider == "ollama":
        return _ollama_answer(question, context, settings)
    if provider == "groq":
        return _groq_answer(question, context, settings)
    if provider == "gemini":
        return _gemini_answer(question, context, settings)
    if provider == "anthropic":
        return _anthropic_answer(question, context, settings)
    if provider == "openai":
        return _openai_answer(question, context, settings)

    raise RuntimeError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")


def _extractive_answer(question: str, context: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    lines = [
        "## Answer\n",
        f"From **{settings.knowledge_base_name}**, here is what applies to: **{question}**\n",
    ]
    parts = context.split("\n\n")
    used = 0
    for part in parts:
        if part.strip().startswith("[") and "---" in part:
            header, _, body = part.partition("\n---\n")
            snippet = body.strip()[:700]
            if snippet:
                lines.append(f"{header.strip()}\n{snippet}\n")
                used += 1
            if used >= 3:
                break

    if used == 0:
        lines.append("_No snippets matched._\n")

    lines.append("\n## Sources\n")
    for part in parts:
        if "URL:" in part and part.strip().startswith("["):
            first_line = part.split("\n")[0]
            url_line = next((ln for ln in part.split("\n") if ln.startswith("URL:")), "")
            if url_line:
                lines.append(f"- {first_line} — {url_line.replace('URL:', '').strip()}")

    return "\n".join(lines)


def _ollama_answer(question: str, context: str, settings: Settings) -> str:
    prompt = f"{_system_prompt(settings)}\n\nContext:\n{context}\n\nQuestion: {question}"
    url = f"{settings.ollama_host.rstrip('/')}/api/generate"
    try:
        with httpx.Client(timeout=120.0) as client:
            r = client.post(
                url,
                json={"model": settings.chat_model, "prompt": prompt, "stream": False},
            )
            r.raise_for_status()
            return r.json().get("response", "")
    except httpx.ConnectError:
        raise RuntimeError("Ollama not running. Install from ollama.com and pull a model.") from None


def _groq_answer(question: str, context: str, settings: Settings) -> str:
    if not settings.groq_configured:
        raise RuntimeError("GROQ_API_KEY required")
    prompt = f"Context:\n{context}\n\nQuestion: {question}"
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.chat_model or "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": _system_prompt(settings)},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 1024,
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def _gemini_answer(question: str, context: str, settings: Settings) -> str:
    if not settings.gemini_configured:
        raise RuntimeError("GEMINI_API_KEY required")
    prompt = f"{_system_prompt(settings)}\n\nContext:\n{context}\n\nQuestion: {question}"
    model = settings.chat_model or "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            url,
            params={"key": settings.gemini_api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def _anthropic_answer(question: str, context: str, settings: Settings) -> str:
    if not settings.anthropic_configured:
        raise RuntimeError("ANTHROPIC_API_KEY required")
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model=settings.chat_model,
        max_tokens=1024,
        system=_system_prompt(settings),
        messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}],
    )
    return "".join(b.text for b in msg.content if hasattr(b, "text"))


def _openai_answer(question: str, context: str, settings: Settings) -> str:
    if not settings.openai_configured:
        raise RuntimeError("OPENAI_API_KEY required")
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    resp = client.chat.completions.create(
        model=settings.chat_model or "gpt-4o-mini",
        messages=[
            {"role": "system", "content": _system_prompt(settings)},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        max_tokens=1024,
    )
    return resp.choices[0].message.content or ""
