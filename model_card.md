# Model Card

## Project

Project name: `SignalFlow Music Recommender`

Base project: `Playlist Chaos`

The original project grouped songs into mood-based playlists and offered search, stats, and history inside a Streamlit app. This version turns that idea into a retrieval-augmented recommendation system with evaluation and guardrails.

## Engineer's Pitch

### The Problem: What did you solve?

I solved the problem of turning a basic playlist organizer into a recommendation system that can respond to natural-language music requests. Instead of making the user manually browse moods or categories, the app lets them describe what they want, such as "calm piano music for late-night studying" or "high-energy dance pop for a party," and then returns ranked songs from a known catalog.

Technical explanation:

The system loads a structured CSV catalog of songs, where each song has a title, artist, genre, energy score, mood, tags, scene, and description. Those fields become the retrieval database. The recommender does not generate new songs; it searches over the known catalog and ranks existing records, which makes the output easier to inspect and less likely to hallucinate.

### The Logic: How does the AI think?

The system uses a retrieval-augmented recommendation pattern. The "AI thinking" happens in two layers: first, deterministic retrieval finds the best catalog matches; second, an optional LLM summary explains those matches using only the retrieved evidence.

Technical explanation:

The retriever parses the user query into a `QueryIntent` object. It normalizes and tokenizes the prompt, removes weak stopword matches, and detects signals such as genre, scene, mood, and target energy. For example, words like "party" or "dance" push the target toward high energy, while words like "study," "calm," or "piano" push the target toward lower energy.

Each song receives a score from several weighted signals:

- Genre match: strong bonus
- Scene match: strong bonus
- Mood match: medium bonus
- Text overlap with tags, description, title, artist, or metadata: smaller bonus
- Preferred genre from the user profile: bonus
- Energy range and distance from target energy: ranking adjustment

After scoring, the app sorts songs by score, energy closeness, and title. The optional OpenAI layer does not choose the songs. It only receives the retrieved song evidence and writes a concise grounded explanation. If no API key is available or generation fails, the system falls back to a local deterministic summary.

### The Reliability: How do you know it works?

I know it works because the recommendation logic is tested with both unit tests and benchmark-style evaluation cases. The tests check guardrails, expected retrieval behavior, genre filtering, energy matching, and whether the evaluation suite passes.

Technical explanation:

The unit tests in `tests/test_recommender.py` verify core behavior:

- Empty prompts are blocked by a guardrail.
- A study prompt returns calm, low-energy tracks.
- A party prompt returns high-energy pop tracks.
- The evaluation suite passes end to end.

The benchmark in `src/evaluation.py` uses fixed test cases for study focus, party energy, and night driving. Each case defines expected titles, expected genres, an acceptable energy range, and a user preference profile. A case passes only if the top recommendations include at least one expected title, at least two matching genres, and all top songs stay inside the target energy range.

Guardrails also improve reliability:

- Empty prompts are blocked.
- Very short prompts are rejected because they do not provide enough retrieval signal.
- Prompts over 240 characters are rejected to keep retrieval focused.
- The LLM is instructed to use only retrieved songs and evidence.
- The app displays retrieval scores and reasoning so the user can inspect why each result appeared.

### The Reflection: What surprised you?

What surprised me most was that the quality of the recommender depended less on having a large model and more on having clear metadata. Once the catalog descriptions, tags, scenes, and moods used words that matched how people naturally ask for music, the retrieval became much more stable.

Technical reflection:

This showed me that a practical AI system is not just a model call. The surrounding system design matters: data representation, scoring weights, input validation, fallback behavior, and evaluation all shape the final user experience. The optional LLM made the explanations feel more natural, but the actual reliability came from the deterministic retrieval layer and the benchmark tests.

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
