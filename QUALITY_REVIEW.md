# Quality review: evidence, not performance claims

Review provenance: Live AI editorial analysis via Google Gemini 3.1 Flash Lite with deterministic cue-level validation.
Evaluated against cold-audience marketing criteria (0-3s hook, unresolved climax, answer leakage prevention).
No independent human editor labels, unseen evaluation set, footage verification or paid audience ad spend testing.

## First posting hypothesis

1. Episode 33, 02:14.50-02:44.50, 30.0s: coerced perjury framing Juliana for witchcraft. Starts on "My testimony?!", cuts on "Save your tears for the trial." Visceral stakes and unyielding threat (Comparative Rank #1).
2. Episode 45, 01:41.20-02:01.75, 20.6s: invalidated marriage vows. Starts on "These vows were never entered into the Royal Matrimonial Register", cuts on Catherine's vindictive smirk as Juliana's claim collapses (Comparative Rank #2).
3. Episode 46, 01:51.80-02:23.80, 32.0s: a ticking-clock standoff before witnesses. Starts on challenging forged seals, cuts on the High Priest's ominous "Ten days is plenty of time." (Comparative Rank #3).
4. Episode 28, 01:35.00-02:16.70, 41.7s: secret identity exposed, facing impending doom. Cuts on "...before he sends you to the gallows." (Comparative Rank #4).
5. Episode 12, 01:03.20-01:27.21, 24.0s: high-stakes sacrifice ultimatum with a clean cut on defiance. Starts on "Do it, and we withdraw the charges", cuts on freezing on Juliana's resolute eye contact (Comparative Rank #5).

All cut times refer to each episode's local screenplay clock. Footage may differ.

## Why scores bunch: The limits of isolated single-pass ratings

When an AI evaluates each episode in isolation on 0–5 integers, three structural problems cause the results to cluster:
1. **Self-selection bias:** The same model instance that decided to propose a promo clip also rates it. Having already decided the scene is worthy of selection, it naturally assigns high ratings (4 or 5) to its own picks.
2. **Score quantization:** Combining three coarse integer ratings through $8 \times \text{hook} + 8 \times \text{cliff} + 4 \times \text{context}$ leaves only 4 discrete totals among all 20 selected promos: 96 (5 promos), 92 (1 promo), 88 (7 promos), and 80 (7 promos).
3. **Arbitrary tie-breakers:** Because 5 promos tied at 96 and 7 tied at 88, any single-pass ranking within those clusters ends up following arbitrary tie-breakers (such as clip duration or chronological episode order).

### The Solution: 2nd-pass comparative forced ranking tournament & score removal

Large language models struggle with absolute scalar calibration, but excel at pairwise and relative comparison (*"Which of these 20 candidate clips is stronger for a cold audience?"*). 

To eliminate ties and overcome coarse single-pass score quantization, we implemented a second-stage comparative ranking pass (`rank_comparative` in `ai_engine.py`):
This pass is fully wired into the end-to-end pipeline: `ai.analyse()` executes it automatically whenever candidate promos are shortlisted, the Streamlit app triggers it on fresh uploads and interactive cut refinements with live UI badges, and `promo.py` supports it via CLI (`rank` / `--rank`).

1. **Fan-In Comparative Prompt:** After the per-episode screening stage selects the candidate clips, all candidates are bundled into a single second-pass prompt containing each clip's episode ID, duration, opening hook line, closing cliffhanger, open question, and dialogue excerpt (~14k tokens total, costing ~$0.003 on Gemini 3.1 Flash Lite).
2. **Forced Total Ordering:** The model is required to return a strict 1-to-20 ranking with one sentence of comparative editorial justification per candidate. Ties are structurally prohibited.
3. **Order-Bias Mitigation (Dual-Pass Shuffle):** LLMs suffer from position bias (favoring candidates presented early in the prompt). We run the comparative tournament twice with independently permuted candidate orders (Pass A seed 101, Pass B seed 202) and average the resulting positions ($\text{Rank}_{\text{final}} = \frac{\text{Rank}_A + \text{Rank}_B}{2}$).
4. **Empirical Rank Stability Metric:** Comparing the two permuted passes yields a **Spearman rank correlation of $\rho = 0.811$**, confirming high cross-order stability and providing an objective confidence metric for the editor.
5. **Score Removal (No Conflicting Badges):** Because single-pass scores carried almost no discriminative signal (only 4 score totals appeared across all 20 promos, and `context` was 4 for 19 of 20 promos) and produced blatant rank inversions (e.g. Rank 2 is Ep 45 at score 88 while Rank 3 is Ep 46 at score 96), we deliberately removed score badges and rating breakdowns from the UI, the HTML report, and `cuts.csv`. The system exclusively presents the true comparative tournament ranking with qualitative pairwise justification.

**Live Comparative Ranking Results:**
- **Rank 1: Episode 33** (Avg rank: 1.0, ranked #1 in both Pass A and Pass B) — *"Immediate high-stakes life-or-death coercion creates an instantaneous and visceral curiosity gap."*
- **Rank 2: Episode 45** (Avg rank: 2.0, ranked #2 in both Pass A and Pass B) — *"Direct legal invalidation of a marriage creates an urgent, objective narrative threat."*
- **Rank 3: Episode 46** (Avg rank: 4.5, A:4, B:5) — *"Ticking clock of a ten-day deadline paired with direct confrontation with authority sets up a clear conflict."*
- **Rank 4: Episode 28** (Avg rank: 4.5, A:6, B:3) — *"Sudden exposure of a secret identity serves as a classic, high-velocity hook."*
- **Rank 5: Episode 12** (Avg rank: 5.5, A:3, B:8) — *"Immediate blackmail and a brutal physical threat against the husband provides strong narrative momentum."*
- **Episode 16 demoted to Rank 15:** The comparative pass autonomously identified the answer leakage in Episode 16 (*"Gerald Harrington paid us!"*), dropping it from the top tier down to #15.

## Detailed system limitations & deep failure analysis

A critical, transparent audit of the 50-episode run reveals four distinct structural failure modes across the LLM and the validation harness:

### 1. False-negative passes on high-potential episodes (LLM constraint hallucinations)
The model passed several of the most dramatic, high-retention scenes in the entire screenplay collection on completely false grounds, claiming *"no valid 20–60s window exists"* or that cutting would split mid-sentence. When examined against the actual screenplay clock, perfectly valid, continuous windows exist:
- **Episode 41 (The Cathedral Wedding Explosion):**
  - *Model pass rationale:* *"The scene's high-stakes climax occurs at the very end of the episode. A clip meeting the 20-second minimum duration requirement while avoiding internal cuts to dialogue or violating cue timing is not possible for this segment."*
  - *Screenplay reality:* An exceptional ~20.3s window exists from `01:15.80` to `01:36.09` (75.8s to 96.1s). Rupert gloats *"Nothing"* (E041B043), the priest begins *"Shall we?"* (E041B045), and at `01:21.00` an ear-splitting detonation blows the cathedral double doors into flying shrapnel and billowing smoke (E041B047/E041B048). Silhouetted armed figures emerge through the rubble as Juliana stares in shock (E041B053). It meets all cue boundaries and duration requirements without splitting any dialogue.
- **Episode 32 (Branding Rod Frozen Inches from Skin):**
  - *Model pass rationale:* *"Attempting to create a 20-60 second clip ending on the cliffhanger (E032B117) requires starting the clip mid-dialogue in the middle of a sentence, which violates the strict constraint against cutting spoken dialogue."*
  - *Screenplay reality:* An intense ~25.8s window exists from `02:05.40` to `02:31.20` (125.4s to 151.2s). It opens cleanly at the exact start of Juliana's scathing dialogue cue E032B097: *"You want everyone to believe you are powerful... You have to threaten a chained woman to feel powerful!"* Catherine loses control, screaming *"Then let's see how brave you are when it touches your skin!"* (E032B114) and plunges the searing iron poker until it freezes an inch from Juliana's eye. There is zero mid-sentence cutting; the clip starts on an intact sentence boundary and ends on an extreme cliffhanger.
- **Episode 35 (The "Someone Wanted Me Erased" Reveal):**
  - *Model pass rationale:* *"The scene's high-stakes emotional peak (Alexander's revelation) cannot be cut into a 20-60 second segment without either violating cue boundaries, cutting through continuous dialogue sequences, or falling below the 20-second duration requirement."*
  - *Screenplay reality:* A self-contained ~36.8s window exists from `01:54.00` to `01:50.80 / 02:30.80` (114.0s to 150.8s). Alexander starts: *"I crawled away from the battlefield, half dead, alone... Someone ordered my men to die. Someone wanted me erased. The men behind it... are the same men ruling Ashwood now."* (E035B054 through E035B070). The dialogue is continuous, high-stakes, within 20–60s, and snaps to exact cue boundaries.
- *Root cause:* The LLM suffers from arithmetic myopia when estimating elapsed seconds from `MM:SS.SS` screenplay timestamps, combined with over-cautious refusal behavior when prompted with strict negative constraints ("never split dialogue"). These three scenes are likely stronger marketing hooks than several selected promos.

### 2. Mechanical validation failures vs. editorial calls (11 of 30 passes)
Of the 30 recorded passes, **11 were not editorial judgments**, but mechanical code validation failures where the model proposed a promo that tripped a strict formatting or cue-type check and failed the single-turn repair attempt:
- **Sub-second endpoint mismatches (Ep 1, Ep 24):** In Ep 1, the closing cue `E001B027` ended at `00:41.20`, but the segment out-point was listed as `00:41.50` (a 0.3s discrepancy). In Ep 24, the cliff cue ended at `01:29.80` while the segment out-point was `01:32.00`.
- **Micro-duration shortfalls (Ep 5, Ep 43):** In Ep 5, the proposed clip was 19.5s (0.5s below the 20.0s floor). In Ep 43, 18.46s.
- **Camera cues selected for hook or cliff evidence (Ep 13, 18, 23, 27, 31):** The model selected a visual cue (`CAMERA`) as its evidence ID (e.g., `E013B075`, `E018B076`, `E023B049`, `E027B095`, `E031B087`). Because marketing requires spoken dialogue or physical character action in the hook/cliff, the validator rejected camera cues. In a single repair turn, the model failed to switch to the corresponding spoken dialogue or character action cue at the exact same timestamp.
- *Code fixability:* All 11 cases are fixable in code without needing better LLM reasoning:
  1. *Programmatic boundary snapping:* Automatically snapping segment start/end to the cited evidence cue boundary when within a $\pm 0.5\text{s}$ tolerance window.
  2. *Automatic cue remapping:* If the LLM cites a `CAMERA` cue whose timestamp coincides with a `DIALOGUE` or `ACTION` cue, code can automatically remap the evidence ID to the valid spoken/action beat.
  3. *Multi-turn repair or heuristic extension:* Allowing a 2nd repair attempt or automatically expanding a 19.5s cut to the adjacent cue boundary to clear the 20.0s threshold.

### 3. The multi-segment stitching feature never fired (0 of 20 promos)
Although the validator and data schema explicitly support 1 to 3 segments per promo (enabling dramatic montage cuts across separate scenes), **all 20 shortlisted promos are single continuous segments**.
- In several rejected episodes (e.g., Ep 14, Ep 22, Ep 42), the model's explicit pass reason was: *"The only segments with high-stakes tension do not meet the 20-second minimum duration requirement..."* (Ep 14, 22) or *"The only high-intensity dialogue segments are too short (under 20s)"* (Ep 42).
- Stitching two 10–12 second high-stakes beats from within the same episode would have resolved the duration constraint and yielded strong promos.
- *Root cause:* LLMs have an intrinsic inductive bias toward continuous interval extraction. Without explicit few-shot prompting showing multi-segment stitching examples or a dedicated two-stage retrieval pass (finding separate high-stakes beats and joining them), the model never synthesizes non-contiguous segments.

### 4. Coarse single-pass scores and rank contradiction
- Single-pass ratings (0–5 integers for hook, cliff, context) combined via $8H + 8C + 4X$ generated only 4 distinct score totals across the entire run: 80, 88, 92, and 96.
- The `context` metric collapsed to a constant value of 4 for 19 out of 20 promos, providing zero ranking variance.
- When the 2nd-pass comparative tournament evaluated all candidates together, it produced an informed ranking that directly inverted the coarse rubric scores:
  - **Rank 2 is Episode 45 with a single-pass score of 88**, while **Rank 3 is Episode 46 with a single-pass score of 96**.
  - **Rank 5 is Episode 12 with a single-pass score of 80**, while **Rank 6 is Episode 44 with a single-pass score of 88**.
- Presenting single-pass scores alongside comparative ranks creates confusion and gives a false impression of mathematical precision. Consequently, score badges were removed from the user-facing Streamlit app, HTML report, and CSV export.

## The headline failure: Episode 16 answer leakage

In the live Google Gemini API evaluation, the model selected **Episode 16** (`00:41.20 - 01:06.20`, 25.0s, Rank 15 in final comparative ranking / Rank 17 in initial rubric) as an approved promo.
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
- **Atmospheric slow-burns (Episode 40 & Episode 48):** In Episode 40, the model selected an assassination discussion, but the first 12 seconds are atmospheric guard placement without immediate emotional stakes. In Episode 48, the dialogue-heavy villain recruitment takes over 15 seconds to ramp up tension. Both were demoted to ranks #17 and #20 in the comparative pass.
- **Presumed lore context (Episode 7):** The cut ends on Gerald's retreat, which feels like a great victory to someone who knows the story, but to a cold viewer who does not know who Gerald is or why his retreat matters, the emotional climax falls flat.
- **Weak opening in Episode 43:** Episode 43 failed the duration constraint during repair (18.46s < 20s) and was cleanly passed.
- **Mid-sentence pickup in Episode 36:** Episode 36 opens on an action framing Alexander in the doorway. While high-stakes, spoken pickups without breathing room require editor audio crossfades.

## Technical checks and honest denominator

The full pack contains 50 episodes. There are 50 validated decisions: 20 select, 30 pass. All 20
selected cuts satisfy implemented structural checks (20-60s duration, valid cue boundaries, dialogue
not split, hook in 0-3s, cliff ending at final cut point, and camera/sound cues excluded from evidence).
These are compliance counts, not precision or recall. Forty-two unit tests pass, covering core AI logic,
networking, UI integration, 2nd-pass comparative tournament ranking, and known semantic limitations (such as the Episode 16 reveal).
The supplied decisions and exports are not hand-edited after the live run; all 50 live Gemini screening responses and the 2 comparative tournament ranking passes (Spearman rho = 0.811) are preserved in `raw_outputs/api_responses.json` and `raw_outputs/ranking_responses.json` with execution hashes in `raw_outputs/run_audit.json`.

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

All 42 test suite checks pass cleanly on Python 3.12:
- **28 Core & AI tests (`test_ai_engine.py`):** Schema validation, repair loop, cue timing, prompt hashing, end-to-end pipeline comparative tournament execution in `analyse()`, promo validate/finish ranking preservation, 2nd-pass comparative forced ranking with dual-shuffle stability, export structure, and semantic edge cases.
- **5 Network tests (`test_network.py`):** IPv4 priority, IPv6 fallback, bounded timeout retry, and TLS enforcement.
- **9 UI Integration tests (`test_app.py`):** Default sample loading, workspace switching isolation, fresh analysis execution, chat explanation, cut refinement, session reset, DOM key hiding, and missing sample guards.
