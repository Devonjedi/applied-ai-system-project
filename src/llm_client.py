from __future__ import annotations

import os
from typing import Iterable

from .retrieval import RetrievalMatch, RetrievalResult


def generate_llm_summary(
    query: str,
    matches: Iterable[RetrievalMatch],
    retrieval: RetrievalResult,
) -> tuple[str, str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return "", "OPENAI_API_KEY not set, so the app used its local explanation mode."

    try:
        from openai import OpenAI
    except ImportError:
        return "", "The `openai` package is not installed, so the app used its local explanation mode."

    song_context = []
    for match in matches:
        song_context.append(
            (
                f"{match.song.title} by {match.song.artist} | genre={match.song.genre} | "
                f"energy={match.song.energy} | scene={match.song.scene} | "
                f"tags={', '.join(match.song.tags)} | reasons={', '.join(match.reasons)}"
            )
        )

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    system_prompt = (
        "You are a music recommendation assistant. Use only the retrieved songs and "
        "retrieval evidence that the app provides. Do not invent songs, artists, or facts. "
        "Write a concise recommendation summary in 3 to 5 sentences."
    )
    user_prompt = (
        f"User request: {query}\n"
        f"Detected genres: {', '.join(retrieval.intent.genres) or 'none'}\n"
        f"Detected scenes: {', '.join(retrieval.intent.scenes) or 'none'}\n"
        f"Detected moods: {', '.join(retrieval.intent.moods) or 'none'}\n"
        f"Target energy: {retrieval.intent.target_energy}\n"
        "Retrieved songs:\n"
        + "\n".join(f"- {line}" for line in song_context)
    )

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
            ],
        )
    except Exception as exc:
        return "", f"OpenAI generation failed ({exc}), so the app used its local explanation mode."

    summary = getattr(response, "output_text", "").strip()
    if not summary:
        return "", "OpenAI returned an empty summary, so the app used its local explanation mode."
    return summary, ""
