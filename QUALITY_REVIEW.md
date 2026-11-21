# Quality review: evidence, not performance claims

Review provenance: Live AI editorial analysis via Google Gemini 3.1 Flash Lite with deterministic cue-level validation.
Evaluated against cold-audience marketing criteria (0-3s hook, unresolved climax, answer leakage prevention).
No independent human editor labels, unseen evaluation set, footage verification or paid audience ad spend testing.

## First posting hypothesis

1. Episode 33, 02:14.50-02:44.50, 30.0s: coerced perjury framing Juliana for witchcraft. Starts on "My testimony?!", cuts on "Save your tears for the trial." Visceral stakes and unyielding threat.
2. Episode 46, 01:51.80-02:23.80, 32.0s: a ticking-clock standoff before witnesses. Starts on challenging forged seals, cuts on the High Priest's ominous "Ten days is plenty of time."
3. Episode 39, 01:05.60-01:38.41, 32.8s: declaration of war upon returning from exile. Starts on "Today, he comes home", cuts on Alexander's burning, resolute stare into the camera.
4. Episode 34, 02:31.80-03:10.00, 38.2s: courtroom drama with a life-or-death ultimatum. Cuts on the judge's raised hand before pronouncing sentence.
5. Episode 28, 01:35.00-02:16.70, 41.7s: secret identity exposed, facing impending doom. Cuts on "...before he sends you to the gallows."

All cut times refer to each episode's local screenplay clock. Footage may differ.

## Why scores bunch: The limits of isolated single-pass ratings

When an AI evaluates each episode in isolation on 0–5 integers, three structural problems cause the results to cluster:
1. **Self-selection bias:** The same model instance that decided to propose a promo clip also rates it. Having already decided the scene is worthy of selection, it naturally assigns high ratings (4 or 5) to its own picks.
2. **Score quantization:** Combining three coarse integer ratings through $8 \times \text{hook} + 8 \times \text{cliff} + 4 \times \text{context}$ leaves only 4 discrete totals among all 20 selected promos: 96 (5 promos), 92 (1 promo), 88 (7 promos), and 80 (7 promos).
3. **Arbitrary tie-breakers:** Because 5 promos tied at 96 and 7 tied at 88, any single-pass ranking within those clusters ends up following arbitrary tie-breakers (such as clip duration or chronological episode order).

### The Solution: 2nd-pass comparative forced ranking tournament

Large language models struggle with absolute scalar calibration, but excel at pairwise and relative comparison (*"Which of these 20 candidate clips is stronger for a cold audience?"*). 

To eliminate ties without arbitrary heuristics, we implemented a second-stage comparative ranking pass (`rank_comparative` in `ai_engine.py`):
1. **Fan-In Comparative Prompt:** After the per-episode screening stage selects the 20 candidate clips, all 20 are bundled into a single second-pass prompt containing each clip's episode ID, duration, opening hook line, closing cliffhanger, open question, and dialogue excerpt (~14k tokens total, costing ~$0.003 on Gemini 3.1 Flash Lite).
2. **Forced Total Ordering:** The model is required to return a strict 1-to-20 ranking with one sentence of comparative editorial justification per candidate. Ties are structurally prohibited.
3. **Order-Bias Mitigation (Dual-Pass Shuffle):** LLMs suffer from position bias (favoring candidates presented early in the prompt). We run the comparative tournament twice with independently permuted candidate orders (Pass A seed 101, Pass B seed 202) and average the resulting positions ($\text{Rank}_{\text{final}} = \frac{\text{Rank}_A + \text{Rank}_B}{2}$).
4. **Empirical Rank Stability Metric:** Comparing the two permuted passes yields a **Spearman rank correlation of $\rho = 0.811$**, confirming high cross-order stability and providing an objective confidence metric for the editor.

**Live Comparative Ranking Results:**
- **Rank 1: Episode 33** (Avg rank: 1.0, ranked #1 in both Pass A and Pass B) — *"Immediate high-stakes life-or-death coercion creates an instantaneous and visceral curiosity gap."*
- **Rank 2: Episode 45** (Avg rank: 2.0, ranked #2 in both Pass A and Pass B) — *"Direct legal invalidation of a marriage creates an urgent, objective narrative threat."*
- **Rank 3: Episode 46** (Avg rank: 4.5, A:4, B:5) — *"Ticking clock of a ten-day deadline paired with direct confrontation with authority sets up a clear conflict."*
- **Rank 4: Episode 28** (Avg rank: 4.5, A:6, B:3) — *"Sudden exposure of a secret identity serves as a classic, high-velocity hook."*
- **Rank 5: Episode 12** (Avg rank: 5.5, A:3, B:8) — *"Immediate blackmail and a brutal physical threat against the husband provides strong narrative momentum."*
- **Episode 16 demoted to Rank 15:** The comparative pass autonomously identified the answer leakage in Episode 16 (*"Gerald Harrington paid us!"*), dropping it from the top tier down to #15.

## The headline failure: Episode 16 answer leakage

In the live Google Gemini API evaluation, the model selected **Episode 16** (`00:41.20 - 01:06.20`, 25.0s, Rank 17) as an approved promo.
- At `00:42.50`, Alexander violently interrogates a captured attacker against the stone wall: *"Who sent you?!"*
- At `00:49.80 - 00:52.20`, the thug breaks under his grip and screams: *"Harrington! Gerald Harrington paid us!"*
- The cut then captures the thugs fleeing and Alexander flexing his knuckles.

**Why this is a severe failure of the AI model:**
Ending after the thug screams the culprit's name destroys the central tension of the scene. It cannot sell the mystery of *"Who sent the thugs?"* because the answer was just shouted aloud.
Yet, Gemini rated the cliffhanger 4/5, rationalizing the spoiled resolution with an invented open loop:
> *"What will Juliana do now that she knows Gerald betrayed her, and what is Alexander's full history?"*

**Why deterministic code passed it:**
The cut snapped to valid cue timestamps, the duration was 25.0s (within 20–60s), dialogue was not split, and the closing cue was a character line (`E016B053`). Python verified the structure and emitted zero errors.

This is the primary semantic blind spot of automated tools: code checks timestamps and syntax; it cannot prove narrative suspense. The LLM readily justifies resolved plotlines as cliffhangers. This failure is why an editor must review every cut before ad spend is committed. The synthetic unit test `test_resolved_answer_is_semantic_blind_spot` deliberately verifies that the code accepts such clips, ensuring developers never falsely believe structural validity equals marketing quality.

## Additional failure modes and weak picks

- **Context fragility in Episode 18:** Episode 18 opened on a camera cue before repair, requiring fallback when visual cues are excluded. When cut on dialogue, opening on shouting without visible props creates cold context fragility.
- **Delayed hooks (Episode 26 & Episode 15):** The model previously rated scenes 5/5 for hook even when dialogue was delayed by 5.2 seconds of silent reaction (Episode 26) or 8.5 seconds of physical approach (Episode 15). For TikTok/Reels ads, 5 seconds of silence causes heavy swipe-away. Our updated validator excludes camera/sound cues from hook evidence, enforcing spoken dialogue or visceral action in seconds 0–3 and correctly passing Episode 26.
- **Weak opening in Episode 43:** Episode 43 failed the duration constraint during repair (18.46s < 20s) and was cleanly passed.
- **Mid-sentence pickup in Episode 36:** Episode 36 opens on an action framing Alexander in the doorway. While high-stakes, spoken pickups without breathing room require editor audio crossfades.

## Technical checks and honest denominator

The full pack contains 50 episodes. There are 50 validated decisions: 20 select, 30 pass. All 20
selected cuts satisfy implemented structural checks (20-60s duration, valid cue boundaries, dialogue
not split, hook in 0-3s, cliff ending at final cut point, and camera/sound cues excluded from evidence).
These are compliance counts, not precision or recall. Thirty-eight unit tests pass, covering core AI logic,
networking, UI integration, and known semantic limitations (such as the Episode 16 reveal).
The supplied decisions and exports are not hand-edited after the live run; all 50 live Gemini responses
are preserved in `raw_outputs/api_responses.json` with execution hashes in `raw_outputs/run_audit.json`.

## Small next experiment

Have one editor blind-review the top five plus five rejected episodes, then label hook,
cliff and standalone clarity separately, record accepted boundary adjustments, and time
review versus the current workflow. This checks rejection mistakes as well as top-rank quality.
For approved creatives, run an equal-budget audience test with matched targeting; track
three-second hold and story-start conversion, and compare cost per story start. No uplift
or production volume assumption has been invented here.

## Interactive prototype & dual-workspace architecture

The Streamlit app provides two distinct, fully isolated workspaces:

1. **Sample results · 50 episodes (Default):**
   Immediately loads the 50 validated decisions (20 ranked promos, 30 passes) from the live Gemini run.
   Evaluators can explore interactive promo cards, verify cue-by-cue source evidence, search by hook or
   open question, and download the full run bundle (JSON + CSV + HTML + API traces) without uploading files
   or providing an API key.

2. **New analysis:**
   Accepts uploaded screenplay files (individual TXT or ZIP packs up to 100 episodes / 10 MB) and executes
   fresh AI analysis against Google Gemini or OpenAI. Evaluators can customize the creative brief and
   duration range (20–60s), chat with the AI editor about decisions, or request refined cuts on specific episodes.
   Session-scoped caching (`st.session_state['cache']`) ensures valid decisions are preserved, allowing seamless
   resumption after any connection or rate limit interruption.

## Deployment, credential safety & error resilience

1. **Frontend Credential Protection:**
   Pre-configured server keys (set via Streamlit Community Cloud Secrets or local `.streamlit/secrets.toml`)
   are never rendered into the browser DOM (`value=''`). The UI displays `"Using pre-configured server key"`,
   and falls back to the server secret automatically behind the scenes.
2. **Dynamic Secret Detection (`default_key_for`):**
   Secrets are resolved dynamically on every rerun across common environment and TOML aliases (`GEMINI_API_KEY`,
   `gemini_api_key`, `GOOGLE_API_KEY`, `API_KEY`). Adding a secret in Streamlit Cloud takes effect instantly
   without requiring container restarts.
3. **Defensive Input Sanitization:**
   Outer quotes (`"`, `'`), extraneous whitespace, and accidental `Bearer ` prefixes are stripped automatically
   before sending requests to provider endpoints, eliminating common HTTP 400 Bad Request errors.
4. **Transparent Error Mapping:**
   Provider HTTP error codes are translated into actionable diagnostic guidance (e.g. rate limit resets for 429,
   authentication warnings for 401/400 key rejections), while network errors halt the batch explicitly without
   inventing synthetic cuts or leaving orphaned unattempted states.

## Test verification summary

All 40 test suite checks pass cleanly on Python 3.12:
- **26 Core & AI tests (`test_ai_engine.py`):** Schema validation, repair loop, cue timing, prompt hashing, 2nd-pass comparative forced ranking with dual-shuffle stability, export structure, and semantic edge cases.
- **5 Network tests (`test_network.py`):** IPv4 priority, IPv6 fallback, bounded timeout retry, and TLS enforcement.
- **9 UI Integration tests (`test_app.py`):** Default sample loading, workspace switching isolation, fresh analysis execution, chat explanation, cut refinement, session reset, DOM key hiding, and missing sample guards.
