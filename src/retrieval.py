from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from .catalog import Song

TOKEN_RE = re.compile(r"[a-z0-9']+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "give",
    "i",
    "im",
    "i'm",
    "me",
    "music",
    "need",
    "playlist",
    "please",
    "something",
    "song",
    "songs",
    "that",
    "the",
    "to",
    "want",
    "with",
}

GENRE_ALIASES = {
    "ambient": {"ambient"},
    "electronic": {"electronic", "edm", "synth"},
    "jazz": {"jazz"},
    "lofi": {"lofi", "lo-fi"},
    "pop": {"pop"},
    "rock": {"rock", "guitar", "grunge"},
}

SCENE_SYNONYMS = {
    "drive": {"drive", "driving", "roadtrip", "cruise", "highway"},
    "dinner": {"dinner", "meal", "lounge"},
    "late-night": {"late-night", "midnight", "night", "after-hours"},
    "morning": {"morning", "sunrise", "wake-up"},
    "party": {"party", "club", "dance-floor", "celebration"},
    "relax": {"relax", "wind", "reset", "unwind", "decompress"},
    "sleep": {"sleep", "bedtime", "rest"},
    "study": {"study", "focus", "homework", "reading", "read"},
    "workout": {"workout", "gym", "run", "running", "lift", "lifting"},
}

MOOD_SYNONYMS = {
    "chill": {"calm", "chill", "gentle", "quiet", "soft", "sleepy"},
    "hype": {"adrenaline", "energetic", "hype", "intense", "loud", "upbeat"},
    "mixed": {"balanced", "cruise", "midtempo", "steady"},
}

ENERGY_HINTS = {
    3: {"ambient", "calm", "focus", "gentle", "piano", "relax", "sleep", "soft", "study"},
    6: {"cool", "cruise", "indie", "late-night", "moody", "night", "steady"},
    9: {"dance", "energetic", "festival", "hype", "party", "power", "upbeat", "workout"},
}


@dataclass(frozen=True)
class PreferenceProfile:
    favorite_genre: str = "any"
    energy_min: int = 1
    energy_max: int = 10


@dataclass(frozen=True)
class QueryIntent:
    raw_query: str
    tokens: tuple[str, ...]
    matched_keywords: tuple[str, ...]
    genres: tuple[str, ...]
    scenes: tuple[str, ...]
    moods: tuple[str, ...]
    target_energy: int


@dataclass(frozen=True)
class RetrievalMatch:
    song: Song
    score: float
    matched_terms: tuple[str, ...]
    reasons: tuple[str, ...]


@dataclass
class RetrievalResult:
    query: str
    intent: QueryIntent
    matches: list[RetrievalMatch]
    confidence: float
    warnings: list[str] = field(default_factory=list)

    @property
    def confidence_label(self) -> str:
        if self.confidence >= 0.75:
            return "high"
        if self.confidence >= 0.5:
            return "medium"
        return "low"

    @classmethod
    def empty(cls, query: str, target_energy: int = 5) -> "RetrievalResult":
        intent = QueryIntent(
            raw_query=query,
            tokens=(),
            matched_keywords=(),
            genres=(),
            scenes=(),
            moods=(),
            target_energy=target_energy,
        )
        return cls(query=query, intent=intent, matches=[], confidence=0.0, warnings=[])


def retrieve_songs(
    songs: Iterable[Song],
    query: str,
    profile: PreferenceProfile,
    top_k: int = 5,
) -> RetrievalResult:
    catalog = list(songs)
    intent = extract_intent(query, profile)
    ranked: list[RetrievalMatch] = []

    for song in catalog:
        ranked.append(score_song(song, intent, profile))

    ranked = [match for match in ranked if match.score > 0]

    if not ranked:
        ranked = [fallback_match(song, intent, profile) for song in catalog]

    ranked.sort(
        key=lambda match: (
            -match.score,
            abs(match.song.energy - intent.target_energy),
            match.song.title.lower(),
        )
    )

    matches = ranked[:top_k]
    warnings: list[str] = []

    if not intent.genres and not intent.scenes and not intent.moods:
        warnings.append(
            "Broad query detected, so retrieval leaned more on tags, text overlap, and energy."
        )
    if matches and compute_confidence(matches[0].score) < 0.5:
        warnings.append(
            "Low-confidence retrieval: consider adding a genre, activity, or mood for sharper recommendations."
        )

    return RetrievalResult(
        query=query,
        intent=intent,
        matches=matches,
        confidence=compute_confidence(matches[0].score if matches else 0.0),
        warnings=warnings,
    )


def extract_intent(query: str, profile: PreferenceProfile) -> QueryIntent:
    lowered = normalize_text(query)
    tokens = tuple(tokenize(lowered))
    matched_keywords = set(tokens)
    genres = {
        genre
        for genre, aliases in GENRE_ALIASES.items()
        if any(alias in lowered for alias in aliases)
    }
    scenes = {
        scene
        for scene, aliases in SCENE_SYNONYMS.items()
        if any(alias in lowered for alias in aliases)
    }
    moods = {
        mood
        for mood, aliases in MOOD_SYNONYMS.items()
        if any(alias in lowered for alias in aliases)
    }

    target_energy = round((profile.energy_min + profile.energy_max) / 2)
    best_hint_score = -1
    for energy, hints in ENERGY_HINTS.items():
        score = sum(1 for hint in hints if hint in lowered)
        if score > best_hint_score:
            best_hint_score = score
            if score > 0:
                target_energy = energy

    return QueryIntent(
        raw_query=query,
        tokens=tokens,
        matched_keywords=tuple(sorted(matched_keywords)),
        genres=tuple(sorted(genres)),
        scenes=tuple(sorted(scenes)),
        moods=tuple(sorted(moods)),
        target_energy=target_energy,
    )


def score_song(song: Song, intent: QueryIntent, profile: PreferenceProfile) -> RetrievalMatch:
    text = song.searchable_text()
    matched_terms: set[str] = set()
    reasons: list[str] = []
    score = 0.0

    if intent.genres and song.genre in intent.genres:
        score += 5.0
        matched_terms.add(song.genre)
        reasons.append(f"genre match: {song.genre}")

    if profile.favorite_genre != "any" and song.genre == profile.favorite_genre:
        score += 2.0
        reasons.append("matches favorite genre")

    if intent.scenes and song.scene in intent.scenes:
        score += 4.0
        matched_terms.add(song.scene)
        reasons.append(f"scene match: {song.scene}")

    if intent.moods and song.mood in intent.moods:
        score += 3.0
        matched_terms.add(song.mood)
        reasons.append(f"mood match: {song.mood}")

    for token in intent.tokens:
        if token in STOPWORDS:
            continue
        if token in text:
            score += 1.4
            matched_terms.add(token)

    if profile.energy_min <= song.energy <= profile.energy_max:
        score += 2.0
        reasons.append("inside preferred energy range")

    energy_gap = abs(song.energy - intent.target_energy)
    score += max(0.0, 4.0 - energy_gap)

    if not reasons and matched_terms:
        reasons.append("text overlap with query")

    return RetrievalMatch(
        song=song,
        score=round(score, 2),
        matched_terms=tuple(sorted(matched_terms)),
        reasons=tuple(reasons),
    )


def fallback_match(song: Song, intent: QueryIntent, profile: PreferenceProfile) -> RetrievalMatch:
    score = max(0.5, 4.0 - abs(song.energy - intent.target_energy))
    reasons = ["fallback energy match"]
    if profile.favorite_genre != "any" and song.genre == profile.favorite_genre:
        score += 1.5
        reasons.append("favorite genre bonus")
    return RetrievalMatch(
        song=song,
        score=round(score, 2),
        matched_terms=(),
        reasons=tuple(reasons),
    )


def normalize_text(text: str) -> str:
    return text.lower().replace("-", " ")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(normalize_text(text))


def compute_confidence(top_score: float) -> float:
    return round(min(1.0, top_score / 18.0), 2)
