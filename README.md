# Last Frame - AI Promo Finder

Two workspaces, with **Sample results** selected by default:

- **Sample results · 50 episodes:** immediately browse the validated assignment output:
  50 decisions, 20 ranked promos and 30 explicit passes. No upload, API key or new model
  call is needed to review results and inspect grounded source evidence.
- **New analysis:** upload another set of timestamped scripts, connect your own AI model,
  and find new promos. The result, cache and editor conversation are independent of the
  fixed sample. Switching workspaces never replaces new-analysis results with sample data.

There is no previous-runs workspace or run-history feature.

## Run locally

Python 3.10+; tested with Python 3.12 and Streamlit 1.45.1. From this directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows activation: `.venv\Scripts\activate`. Use `python` instead of `python3` if needed.
The local URL is normally `http://localhost:8501`.

The private submission bundle includes the 50-episode sample in `raw_outputs/`.
The public code-only ZIP deliberately omits confidential Kuku story excerpts; that copy
shows a clear message in Sample results and still supports New analysis. It does not
substitute an unrelated synthetic story for the assignment's 50-episode sample.

## Start a new analysis

1. Select **New analysis**.
2. Choose OpenAI or Google Gemini in the sidebar. Enter an available model ID and your
   own API key. The OpenAI preset is `gpt-4.1-mini`; choose your Gemini model ID from your
   provider account. App hosting and model usage are separate.
3. Upload a ZIP or one/more TXT episodes from one show.
4. Optionally choose a 20-60 second duration range and an editorial preference.
5. Click **Find promos / resume analysis**. Errors remain explicit; valid decisions are
   cached within the current session so unchanged inputs/settings do not repeat calls.
6. Inspect exact source evidence. In **Talk to your AI editor**, ask about a cut or choose
   **Refine cut** to replace one episode's decision after validation.
7. Download the run's JSON, CSV, HTML, original AI responses and audit in one ZIP.

Sample results has ranked cards and an all-episodes/download view. Its saved decisions
are read-only; live AI chat and refinement belong to New analysis.

## Input format

Use UTF-8 TXT in the supplied timestamp-block screenplay format, with one unique
`EPISODE NUMBER: Episode N` header per file and `MM:SS.cc` cue times. See
`examples/synthetic_episode.txt` for an original format example. That file is an input
template, not the 50-episode sample result. Audio/video and untimestamped prose are not
supported. The web app accepts up to 100 episodes and 10 MB of expanded text.

## AI and validation

Each episode is read in full by the chosen model. It returns select/pass, cue IDs, cuts,
an unresolved question, ratings and reasons. Code verifies source hashes, existing
boundaries, 20-60s duration, no split dialogue, hook evidence starting in the first three
seconds and cliff evidence ending at the final out point. One invalid response gets one
repair attempt. There is no silent heuristic fallback.

Rank = 8 x hook + 8 x cliff + 4 x standalone context, each rated 0-5. Ties use the earlier
episode. Scores are editorial judgments, not predicted CTR. One promo per episode,
with up to three chronological segments within that episode. No cross-episode montage.
An editor must check narrative truth, standalone clarity and the actual footage.

The network client prefers IPv4 per request, with IPv6 fallback and bounded TCP attempts;
TLS certificate verification stays enabled. A provider/connection failure stops the batch
and marks the remaining episodes unattempted. Resume after correcting the reported issue.

## Data handling

The API key reaches the app server and selected provider. Use a deployment you trust.
Keys, uploads and new-analysis results stay in the Streamlit session; they are not written
to disk or cached globally. Clear session and key removes that state. Restarting the app
can clear it. The fixed sample is read from the separately supplied `raw_outputs/` files.

The new-analysis key is never included in downloads. Sample and new-run downloads contain
story excerpts; share them only with authorized recipients. Never publish the original
Kuku scripts or confidential sample results in a public repository or public app.

## Deploy

Upload the code-only files to a GitHub repository (or use [Akshat577/last-frame](https://github.com/Akshat577/last-frame)),
connect it to Streamlit Community Cloud, choose `app.py` as entrypoint and Python 3.12, then deploy.
Keep `ui.css`, `sample_data.py`, `network.py`, `ai_engine.py`, `promo.py`, `JUDGE_PROMPT.txt`,
`requirements.txt`, `examples/` and `.streamlit/config.toml` beside the app.

### Setting up Secrets (Streamlit Cloud)
To allow evaluators to run fresh analyses without manually entering an API key:
1. In your Streamlit Cloud app dashboard, go to **Settings** $\rightarrow$ **Secrets**.
2. Add your provider key:
   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"
   ```
3. The app dynamically detects this key at runtime (`default_key_for`). When present, the frontend
   hides the key value entirely from the browser DOM, displaying `"Using pre-configured server key"`
   and seamlessly using it behind the scenes.
4. If an evaluator provides their own key in the sidebar, input sanitization automatically strips
   any accidental quotes (`"`, `'`), extra whitespace, or `Bearer ` prefixes.

## Checks

```sh
python3 -m unittest discover -s tests -v
```

38 tests pass: 24 core/AI, five networking and nine UI checks. API tests use controlled
responses and integration mocks. All 50 episodes have been evaluated and verified end-to-end
against the live Google Gemini API (20 selected, 30 explicit passes).

## CLI

Replay the original saved decisions without a key:

```sh
python3 promo.py finish '/path/to/original-pack.zip' --decisions raw_outputs/ai_decisions.json --out rerun
```

`promo.py prepare` still exports prompts for a manual AI-chat workflow; `promo.py judge`
supports a compatible endpoint configured with `PROMO_API_URL`, `PROMO_MODEL` and
`PROMO_API_KEY`. The web workflow adds repair, caching and interactive editing.

