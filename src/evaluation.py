from __future__ import annotations

from dataclasses import dataclass

from .catalog import load_catalog
from .recommender import MusicRecommender
from .retrieval import PreferenceProfile


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    query: str
    expected_titles: tuple[str, ...]
    expected_genres: tuple[str, ...]
    energy_range: tuple[int, int]
    profile: PreferenceProfile


@dataclass(frozen=True)
class EvaluationResult:
    case: EvaluationCase
    passed: bool
    title_hits: int
    genre_hits: int
    energy_passed: bool
    top_titles: tuple[str, ...]


EVALUATION_CASES = (
    EvaluationCase(
        name="Study focus",
        query="I need calm piano music for late-night studying.",
        expected_titles=("Gymnopedie No. 1", "Clair de Lune", "Lo-fi Rain"),
        expected_genres=("ambient", "lofi"),
        energy_range=(1, 4),
        profile=PreferenceProfile(favorite_genre="ambient", energy_min=1, energy_max=4),
    ),
    EvaluationCase(
        name="Party energy",
        query="Give me high-energy dance pop for a party.",
        expected_titles=("Levitating", "Uptown Funk", "Blinding Lights", "Titanium"),
        expected_genres=("pop",),
        energy_range=(7, 10),
        profile=PreferenceProfile(favorite_genre="pop", energy_min=7, energy_max=10),
    ),
    EvaluationCase(
        name="Night drive",
        query="Need moody synth music for a night drive.",
        expected_titles=("Night Drive", "Midnight City", "On Hold", "Strobe"),
        expected_genres=("electronic",),
        energy_range=(4, 8),
        profile=PreferenceProfile(favorite_genre="electronic", energy_min=4, energy_max=8),
    ),
)


def run_evaluation_suite() -> list[EvaluationResult]:
    recommender = MusicRecommender(load_catalog())
    results: list[EvaluationResult] = []

    for case in EVALUATION_CASES:
        package = recommender.recommend(
            case.query,
            profile=case.profile,
            top_k=3,
            allow_llm=False,
        )
        top_titles = tuple(item.song.title for item in package.recommendations[:3])
        title_hits = sum(1 for title in top_titles if title in case.expected_titles)
        genre_hits = sum(
            1 for item in package.recommendations[:3] if item.song.genre in case.expected_genres
        )
        energy_passed = all(
            case.energy_range[0] <= item.song.energy <= case.energy_range[1]
            for item in package.recommendations[:3]
        )
        passed = title_hits >= 1 and genre_hits >= 2 and energy_passed
        results.append(
            EvaluationResult(
                case=case,
                passed=passed,
                title_hits=title_hits,
                genre_hits=genre_hits,
                energy_passed=energy_passed,
                top_titles=top_titles,
            )
        )

    return results


def format_evaluation_summary(results: list[EvaluationResult]) -> str:
    passed = sum(1 for result in results if result.passed)
    total = len(results)
    return f"{passed}/{total} evaluation cases passed."


def main() -> None:
    results = run_evaluation_suite()
    print(format_evaluation_summary(results))
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(
            f"{status} | {result.case.name} | titles={result.top_titles} | "
            f"title_hits={result.title_hits} | genre_hits={result.genre_hits} | "
            f"energy_ok={result.energy_passed}"
        )


if __name__ == "__main__":
    main()
