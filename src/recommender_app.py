from __future__ import annotations

import os

import streamlit as st

from .catalog import Song, available_genres, load_catalog
from .evaluation import format_evaluation_summary, run_evaluation_suite
from .recommender import MusicRecommender, RecommendationPackage
from .retrieval import PreferenceProfile

EXAMPLE_QUERIES = (
    "I need calm piano music for late-night studying.",
    "Give me high-energy dance pop for a party.",
    "Need moody synth music for a night drive.",
)


def init_state() -> None:
    if "catalog" not in st.session_state:
        st.session_state.catalog = load_catalog()
    if "recommender" not in st.session_state:
        st.session_state.recommender = MusicRecommender(st.session_state.catalog)
    if "query" not in st.session_state:
        st.session_state.query = EXAMPLE_QUERIES[0]
    if "last_package" not in st.session_state:
        st.session_state.last_package = None
    if "history" not in st.session_state:
        st.session_state.history = []
    if "evaluation_results" not in st.session_state:
        st.session_state.evaluation_results = []


def sidebar_controls(catalog: list[Song]) -> tuple[PreferenceProfile, int, bool]:
    st.sidebar.header("Retriever settings")

    genre_options = ["any", *available_genres(catalog)]
    favorite_genre = st.sidebar.selectbox("Preferred genre", options=genre_options, index=0)
    energy_min, energy_max = st.sidebar.slider(
        "Preferred energy range",
        min_value=1,
        max_value=10,
        value=(3, 8),
    )
    top_k = st.sidebar.slider("Recommendations to retrieve", min_value=3, max_value=5, value=4)
    allow_llm = st.sidebar.checkbox("Use OpenAI summary when available", value=True)

    if os.getenv("OPENAI_API_KEY"):
        st.sidebar.caption("OpenAI key detected. The app can generate a short grounded summary.")
    else:
        st.sidebar.caption("No OpenAI key detected. The app will stay in local explanation mode.")

    profile = PreferenceProfile(
        favorite_genre=favorite_genre,
        energy_min=energy_min,
        energy_max=energy_max,
    )
    return profile, top_k, allow_llm


def recommender_tab(profile: PreferenceProfile, top_k: int, allow_llm: bool) -> None:
    st.subheader("Ask for music in plain language")
    selected_example = st.selectbox("Example prompt", options=EXAMPLE_QUERIES, index=0)
    col1, col2 = st.columns([1, 2])
    if col1.button("Load example"):
        st.session_state.query = selected_example
    with col2:
        st.caption("Describe a mood, genre, activity, or energy level to steer retrieval.")

    st.session_state.query = st.text_area(
        "Prompt",
        value=st.session_state.query,
        height=110,
        placeholder="Example: upbeat electronic music for a late-night coding session",
    )

    if st.button("Recommend songs", type="primary"):
        package = st.session_state.recommender.recommend(
            st.session_state.query,
            profile=profile,
            top_k=top_k,
            allow_llm=allow_llm,
        )
        st.session_state.last_package = package
        if package.recommendations:
            st.session_state.history = [package, *st.session_state.history][:5]

    package = st.session_state.last_package
    if package is not None:
        render_package(package)

    with st.expander("Recent recommendation history", expanded=False):
        if not st.session_state.history:
            st.write("No recommendation history yet.")
        else:
            for previous in st.session_state.history:
                titles = ", ".join(item.song.title for item in previous.recommendations[:3])
                st.write(f"- `{previous.query}` -> {titles}")


def render_package(package: RecommendationPackage) -> None:
    for warning in package.warnings:
        st.warning(warning)

    if not package.recommendations:
        st.info(package.summary)
        return

    st.markdown("### Recommendation summary")
    st.write(package.summary)

    metrics = st.columns(3)
    metrics[0].metric("Retrieved songs", len(package.recommendations))
    metrics[1].metric("Retrieval confidence", package.retrieval.confidence_label.title())
    metrics[2].metric("Explanation mode", "OpenAI" if package.used_llm else "Local")

    st.markdown("### Top matches")
    for item in package.recommendations:
        with st.container(border=True):
            st.markdown(f"**{item.song.title}** by {item.song.artist}")
            st.caption(
                f"{item.song.genre.title()} | energy {item.song.energy}/10 | "
                f"scene {item.song.scene} | mood {item.song.mood}"
            )
            st.write(item.reason)
            st.caption(
                f"Retrieval score: {item.score} | matched terms: "
                f"{', '.join(item.matched_terms) or 'broad profile match'}"
            )

    with st.expander("Retrieval trace", expanded=False):
        st.write(f"Detected genres: {', '.join(package.retrieval.intent.genres) or 'none'}")
        st.write(f"Detected scenes: {', '.join(package.retrieval.intent.scenes) or 'none'}")
        st.write(f"Detected moods: {', '.join(package.retrieval.intent.moods) or 'none'}")
        st.write(f"Target energy: {package.retrieval.intent.target_energy}/10")
        for match in package.retrieval.matches:
            st.write(
                f"- {match.song.title}: score {match.score}, reasons: "
                f"{', '.join(match.reasons) or 'broad retrieval fallback'}"
            )


def catalog_tab(catalog: list[Song]) -> None:
    st.subheader("Catalog browser")
    genre_options = ["all", *available_genres(catalog)]
    genre_filter = st.selectbox("Filter by genre", options=genre_options, index=0, key="catalog_genre")
    search_text = st.text_input("Search catalog text", key="catalog_search")
    min_energy, max_energy = st.slider(
        "Catalog energy range",
        min_value=1,
        max_value=10,
        value=(1, 10),
        key="catalog_energy",
    )

    filtered = []
    for song in catalog:
        if genre_filter != "all" and song.genre != genre_filter:
            continue
        if not (min_energy <= song.energy <= max_energy):
            continue
        if search_text and search_text.lower() not in song.searchable_text():
            continue
        filtered.append(song.to_dict())

    st.write(f"{len(filtered)} songs match the current filters.")
    st.dataframe(filtered, width="stretch", hide_index=True)


def reliability_tab() -> None:
    st.subheader("Reliability and evaluation")
    st.write(
        "The evaluation suite runs fixed prompts against the retriever and checks whether the "
        "top results match expected titles, genres, and energy bands."
    )
    st.write(
        "Guardrails currently block empty or overly short prompts and keep generated explanations "
        "grounded in songs that already exist in the catalog."
    )

    if st.button("Run evaluation suite"):
        st.session_state.evaluation_results = run_evaluation_suite()

    results = st.session_state.evaluation_results
    if results:
        st.info(format_evaluation_summary(results))
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            st.write(
                f"{status} | {result.case.name} | top titles: {', '.join(result.top_titles)} | "
                f"title hits: {result.title_hits} | genre hits: {result.genre_hits} | "
                f"energy ok: {result.energy_passed}"
            )


def main() -> None:
    st.set_page_config(page_title="SignalFlow Music Recommender", layout="wide")
    init_state()

    catalog = st.session_state.catalog
    profile, top_k, allow_llm = sidebar_controls(catalog)

    st.title("SignalFlow Music Recommender")
    st.write(
        "A retrieval-augmented music recommender that turns plain-language requests into "
        "catalog matches, grounded explanations, and reliability checks."
    )

    recommend_tab, browse_tab, reliability_view = st.tabs(
        ["AI Recommender", "Catalog", "Reliability"]
    )

    with recommend_tab:
        recommender_tab(profile, top_k, allow_llm)
    with browse_tab:
        catalog_tab(catalog)
    with reliability_view:
        reliability_tab()


if __name__ == "__main__":
    main()
