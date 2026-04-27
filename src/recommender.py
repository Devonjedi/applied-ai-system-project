from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable

from .catalog import Song, load_catalog
from .llm_client import generate_llm_summary
from .retrieval import PreferenceProfile, RetrievalMatch, RetrievalResult, retrieve_songs

LOGGER = logging.getLogger("applied_ai_music_recommender")
if not LOGGER.handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


@dataclass(frozen=True)
class Recommendation:
    song: Song
    reason: str
    score: float
    matched_terms: tuple[str, ...]


@dataclass
class RecommendationPackage:
    query: str
    summary: str
    recommendations: list[Recommendation]
    retrieval: RetrievalResult
    warnings: list[str] = field(default_factory=list)
    used_llm: bool = False


class MusicRecommender:
    def __init__(self, catalog: Iterable[Song] | None = None):
        self.catalog = list(catalog) if catalog is not None else load_catalog()

    def recommend(
        self,
        query: str,
        profile: PreferenceProfile,
        top_k: int = 5,
        allow_llm: bool = True,
    ) -> RecommendationPackage:
        guardrail_message = validate_query(query)
        if guardrail_message:
            LOGGER.warning("Blocked invalid query: %s", guardrail_message)
            return RecommendationPackage(
                query=query,
                summary=guardrail_message,
                recommendations=[],
                retrieval=RetrievalResult.empty(query),
                warnings=[guardrail_message],
                used_llm=False,
            )

        retrieval = retrieve_songs(self.catalog, query, profile, top_k=top_k)
        recommendations = [
            Recommendation(
                song=match.song,
                reason=build_song_reason(match, retrieval),
                score=match.score,
                matched_terms=match.matched_terms,
            )
            for match in retrieval.matches
        ]

        warnings = list(retrieval.warnings)
        summary = build_local_summary(query, retrieval)
        used_llm = False

        if allow_llm and recommendations:
            llm_summary, llm_warning = generate_llm_summary(query, retrieval.matches, retrieval)
            if llm_warning:
                warnings.append(llm_warning)
            if llm_summary:
                summary = llm_summary
                used_llm = True

        LOGGER.info(
            "Query=%r retrieved=%s confidence=%s llm=%s",
            query,
            [item.song.title for item in recommendations],
            retrieval.confidence_label,
            used_llm,
        )

        return RecommendationPackage(
            query=query,
            summary=summary,
            recommendations=recommendations,
            retrieval=retrieval,
            warnings=warnings,
            used_llm=used_llm,
        )


def validate_query(query: str) -> str:
    cleaned = query.strip()
    if not cleaned:
        return "Add a music request before asking for recommendations."
    if len(cleaned) < 8:
        return "Be a little more specific so the recommender can retrieve useful songs."
    if len(cleaned) > 240:
        return "Please shorten the request to under 240 characters so retrieval stays reliable."
    return ""


def build_local_summary(query: str, retrieval: RetrievalResult) -> str:
    if not retrieval.matches:
        return (
            "I could not find strong matches in the catalog yet. Try naming a mood, "
            "genre, activity, or target energy."
        )

    titles = ", ".join(match.song.title for match in retrieval.matches[:3])
    genre_text = ", ".join(retrieval.intent.genres) or "mixed genres"
    scene_text = ", ".join(retrieval.intent.scenes) or "general listening"
    return (
        f"For `{query}`, I retrieved songs centered on {genre_text} and {scene_text} patterns. "
        f"The strongest matches are {titles}. The system kept the results close to an energy "
        f"target of {retrieval.intent.target_energy}/10 and only recommends songs already in the catalog."
    )


def build_song_reason(match: RetrievalMatch, retrieval: RetrievalResult) -> str:
    descriptors: list[str] = []
    if match.song.genre in retrieval.intent.genres:
        descriptors.append(f"it matches the {match.song.genre} genre you asked for")
    if match.song.scene in retrieval.intent.scenes:
        descriptors.append(f"its scene tag lines up with {match.song.scene}")
    if match.song.mood in retrieval.intent.moods:
        descriptors.append(f"its mood lands in the {match.song.mood} range")
    if match.matched_terms:
        descriptors.append(f"it overlaps with query terms like {', '.join(match.matched_terms[:4])}")
    descriptors.append(f"its energy sits at {match.song.energy}/10")

    return (
        f"{match.song.title} works because "
        + "; ".join(descriptors)
        + "."
    )
