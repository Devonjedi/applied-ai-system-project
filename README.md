# SignalFlow Music Recommender

`SignalFlow Music Recommender` is a retrieval-augmented music recommendation app built in Streamlit. A user can describe what they want to hear in plain language, the system retrieves the closest songs from a local catalog, and the app returns grounded recommendations with transparent reasons and evaluation results.

This project builds on my original `Playlist Chaos` project from Modules 1-3. The earlier version grouped songs into mood-based playlists, let users add and search tracks, and surfaced simple listening stats. This final version turns that playlist idea into a more complete applied AI system with retrieval, guardrails, evaluation, and portfolio-ready documentation.

## Why it matters

The app demonstrates a practical AI pattern: use retrieval before generation so the system stays tied to real data. Instead of inventing songs or making vague suggestions, the recommender searches a known catalog, ranks the best matches, and only then produces an explanation.

## Architecture overview

The system follows this flow:

1. A user submits a natural-language prompt and optional preference settings.
2. Guardrails validate the prompt and parse genres, scenes, moods, and target energy.
3. The retriever ranks songs from `data/song_catalog.csv`.
4. The explanation layer returns grounded reasons for each recommendation.
5. The reliability tab and evaluation script test fixed prompts against expected results.

Mermaid source for the system diagram is in [assets/system_architecture.mmd](/Users/admin/ai110/applied-ai-system-project/assets/system_architecture.mmd), and the rendered submission image is already saved as [assets/system_architecture.png](/Users/admin/ai110/applied-ai-system-project/assets/system_architecture.png). If you want to revise the chart later, Mermaid Live Editor is still a convenient way to re-export the PNG.

![System Architecture](assets/system_architecture.png)

## Repository structure

```text
applied-ai-system-project/
├── assets/
├── data/
├── src/
├── tests/
├── app.py
├── model_card.md
├── README.md
└── requirements.txt
```

## Setup instructions

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Optional: add an OpenAI API key if you want the app to generate a short grounded summary on top of the retrieved songs:

   ```bash
   export OPENAI_API_KEY=your_key_here
   ```

3. Start the app:

   ```bash
   streamlit run app.py
   ```

4. Run the automated checks:

   ```bash
   python3 -m unittest discover -s tests
   python3 -m src.evaluation
   ```

## Sample interactions

- Input: `I need calm piano music for late-night studying.`
  Output: `Clair de Lune`, `Gymnopedie No. 1`, and `Lo-fi Rain`.
  Why it worked: the retriever matched low energy, piano, study, and late-night signals.

- Input: `Give me high-energy dance pop for a party.`
  Output: `Uptown Funk`, `Blinding Lights`, and `Levitating`.
  Why it worked: the query strongly matched pop, dance, party, and high-energy cues.

- Input: `Need moody synth music for a night drive.`
  Output: `Night Drive`, `Midnight City`, and `Strobe`.
  Why it worked: the retriever picked up electronic, synth, night, and drive concepts.

## Design decisions

- I chose retrieval-augmented recommendation because it fits a music catalog naturally and keeps the output grounded in real songs.
- The retriever uses a structured CSV catalog plus transparent scoring rules instead of hidden heuristics, which makes testing easier.
- The explanation layer has two modes: a local deterministic summary for reproducibility and an optional OpenAI summary for a more natural response.
- I added an evaluation harness because recommendation systems can feel plausible even when they are wrong, so the repo needed measurable checks.

## Testing summary

- `python3 -m unittest discover -s tests` passed all 4 unit tests.
- `python3 -m src.evaluation` passed 3 out of 3 evaluation cases.
- The local test environment did not exercise a live OpenAI call because no API key was configured, so the LLM explanation path remains lightly tested compared with the retrieval path.

## Reflection

This project taught me that useful AI systems need more than a prompt box. The strongest improvement came from making retrieval, guardrails, and evaluation explicit so the recommender could explain itself and be checked against expected behavior. It also reinforced that a smaller grounded system is often more trustworthy than a bigger system that sounds confident but cannot show where its answer came from.

## Ethics and limitations

The catalog is small, hand-curated, and English-centered, so the system reflects those biases. It can only recommend what exists in the dataset, and its keyword-driven retrieval may miss subtle preferences, newer genres, or culturally specific language. To reduce misuse, the app blocks empty or low-information prompts, keeps recommendations tied to catalog entries, and exposes retrieval evidence rather than pretending the answer came from nowhere.

## Portfolio artifact

This project shows me as an AI engineer who cares about grounded behavior, not just flashy output. I focused on building a system that can explain what it retrieved, expose its confidence, and measure whether it is actually meeting the user request.

## Demo walkthrough

Loom link: `[replace with your Loom walkthrough URL]`

Record the walkthrough in this order:

1. Enter a study-focused prompt and show the retrieved songs plus explanation.
2. Enter a party or night-drive prompt and show how the output changes.
3. Open the retrieval trace so viewers can see why songs were selected.
4. Run the reliability tab evaluation suite and show the pass results.
