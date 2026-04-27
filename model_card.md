# Model Card

## Project

Project name: `SignalFlow Music Recommender`

Base project: `Playlist Chaos`

The original project grouped songs into mood-based playlists and offered search, stats, and history inside a Streamlit app. This version turns that idea into a retrieval-augmented recommendation system with evaluation and guardrails.

## Intended use

This system is meant for lightweight music discovery and playlist inspiration. It is designed for users who want grounded recommendations from a known catalog, not for making claims about a person's identity, health, or emotional state.

## Model or AI feature

The main AI feature is retrieval-augmented recommendation. The app parses a user's prompt, retrieves the best matches from a structured song catalog, and then explains the results using either a deterministic local summary or an optional OpenAI-generated grounded summary.

## Inputs and outputs

Inputs:

- Natural-language recommendation prompt
- Preferred genre
- Preferred energy range
- Optional OpenAI API key for the summary layer

Outputs:

- Ranked song recommendations
- Grounded explanation summary
- Per-song reasoning and retrieval scores
- Evaluation results from fixed benchmark prompts

## Reliability and testing

The app includes two reliability layers:

- Unit tests in [tests/test_recommender.py](/Users/admin/ai110/applied-ai-system-project/tests/test_recommender.py)
- A benchmark script in [src/evaluation.py](/Users/admin/ai110/applied-ai-system-project/src/evaluation.py)

Verified results from local testing:

- `python3 -m unittest discover -s tests`: 4 tests passed
- `python3 -m src.evaluation`: 3 out of 3 benchmark cases passed

What surprised me while testing reliability was how much better the system became once the catalog descriptions and tags were made more explicit. The retriever was much more stable when the dataset carried the same vocabulary that users naturally typed into prompts.

## Limitations and biases

The dataset is small and hand-selected, so it reflects my own choices about genres, artists, moods, and descriptive language. The retriever is keyword and metadata driven, which means it may over-reward songs whose tags are more descriptive and under-reward songs that are stylistically similar but described differently. The system also does not cover regional genres, non-English prompt phrasing, or a large modern catalog.

## Misuse and guardrails

Possible misuse:

- Treating the recommendations as authoritative rather than exploratory
- Assuming the system understands all music styles equally well
- Using vague prompts and over-interpreting the result quality

Guardrails:

- Empty, overly short, and overly long prompts are blocked
- Recommendations are limited to songs already stored in the catalog
- Retrieval evidence is shown so the user can inspect why a song appeared
- The evaluation tab makes it easier to notice weak retrieval behavior

## AI collaboration reflection

Helpful suggestion:

An AI assistant helped me choose retrieval-augmented recommendation as the core feature and suggested pairing it with an evaluation harness. That was useful because it turned the project from a basic playlist app into a system with a clear architecture and measurable behavior.

Flawed or incorrect suggestion:

Early in the process, the AI assistant inspected the wrong repo folder and started from the module starter context instead of `applied-ai-system-project`. Catching that mistake early mattered because it could have sent the implementation and documentation into the wrong codebase.
