import unittest

from src.catalog import load_catalog
from src.evaluation import run_evaluation_suite
from src.recommender import MusicRecommender
from src.retrieval import PreferenceProfile


class MusicRecommenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.recommender = MusicRecommender(load_catalog())

    def test_empty_query_triggers_guardrail(self) -> None:
        package = self.recommender.recommend(
            "   ",
            profile=PreferenceProfile(),
            allow_llm=False,
        )
        self.assertEqual(package.recommendations, [])
        self.assertIn("Add a music request", package.summary)

    def test_study_query_returns_calm_tracks(self) -> None:
        package = self.recommender.recommend(
            "I need calm piano music for late-night studying.",
            profile=PreferenceProfile(favorite_genre="ambient", energy_min=1, energy_max=4),
            top_k=3,
            allow_llm=False,
        )
        titles = [item.song.title for item in package.recommendations]
        self.assertEqual(titles[:3], ["Clair de Lune", "Gymnopedie No. 1", "Lo-fi Rain"])

    def test_party_query_prefers_high_energy_pop(self) -> None:
        package = self.recommender.recommend(
            "Give me high-energy dance pop for a party.",
            profile=PreferenceProfile(favorite_genre="pop", energy_min=7, energy_max=10),
            top_k=3,
            allow_llm=False,
        )
        genres = [item.song.genre for item in package.recommendations]
        self.assertTrue(all(genre == "pop" for genre in genres))
        self.assertTrue(all(item.song.energy >= 7 for item in package.recommendations))

    def test_evaluation_suite_passes(self) -> None:
        results = run_evaluation_suite()
        self.assertTrue(results)
        self.assertTrue(all(result.passed for result in results))


if __name__ == "__main__":
    unittest.main()
