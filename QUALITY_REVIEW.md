# Quality review: evidence, not performance claims

Review provenance: Live AI editorial analysis via Google Gemini 3.1 Flash Lite with deterministic cue-level validation.
Evaluated against cold-audience marketing criteria (0-3s hook, unresolved climax, answer leakage prevention).
No independent human editor labels, unseen evaluation set, footage verification or paid audience ad spend testing.

## First posting hypothesis

1. Episode 12, 00:44.00-01:09.20, 25.2s: a sister makes bodily sacrifice the price of saving a husband. Strong immediate cruelty and explicit unresolved choice. Start here.
2. Episode 27, 00:03.40-00:46.40, 43.0s: her supposedly penniless husband's ring belonged to a lost noble son. Tests identity mystery against cruelty.
3. Episode 28, 00:15.30-00:47.00, 31.7s: the poisoning victim defends the maid, then cannot finish her accusation. Tests an interrupted witness.
4. Episode 45, 01:14.80-01:53.00, 38.2s: declared Duchess, then told she is not lawfully married. Tests a status reversal. Tied rubric scores use earlier episode, not proven superiority.
5. Episode 3, 00:58.30-01:23.90, 25.6s: guards drag a woman away; a stranger demands her release. The fight and identity stay outside the cut.

All cut times refer to each episode's local screenplay clock. Footage may differ.

## The headline failure: Episode 16 answer leakage

In the live Google Gemini API evaluation, the model selected **Episode 16** (`00:40.80 - 01:03.00`, 22.2s) as an approved promo.
- At `00:42.50`, Alexander violently interrogates a captured attacker against the stone wall: *"Who sent you?!"*
- At `00:49.80 - 00:52.20`, the thug breaks under his grip and screams: *"Harrington! Gerald Harrington paid us!"*
- The cut then captures the thugs fleeing and Alexander flexing his knuckles.

**Why this is a severe failure of the AI model:**
Ending after the thug screams the culprit's name destroys the central tension of the scene. It cannot sell the mystery of *"Who sent the thugs?"* because the answer was just shouted aloud.
Yet, Gemini rated the cliffhanger 4/5, rationalizing the spoiled resolution with an invented open loop:
> *"With the identity of the mastermind revealed as Gerald, what will happen to Juliana and Alexander now that the betrayal has been exposed?"*

**Why deterministic code passed it:**
The cut snapped to valid cue timestamps, the duration was 22.2s (within 20–60s), dialogue was not split, and the closing cue was a character action (`E016B051`). Python verified the structure and emitted zero errors.

This is the primary semantic blind spot of automated tools: code checks timestamps and syntax; it cannot prove narrative suspense. The LLM readily justifies resolved plotlines as cliffhangers. This failure is why an editor must review every cut before ad spend is committed. The synthetic unit test `test_resolved_answer_is_semantic_blind_spot` deliberately verifies that the code accepts such clips, ensuring developers never falsely believe structural validity equals marketing quality.

## Additional failure modes and weak picks

- **Context fragility in Episode 18:** Episode 18 (`00:58.00 - 01:26.20`, 28.2s) opens on Alexander shouting *"Leave it!"*. If the cold ad's first frame does not visibly show the mother's ledger in her hands, a cold viewer has no context for her refusal to flee. Its context rating is appropriately low (3/5), ranking it ninth.
- **Delayed hooks (Episode 26 & Episode 15):** The model previously rated scenes 5/5 for hook even when dialogue was delayed by 5.2 seconds of silent reaction (Episode 26) or 8.5 seconds of physical approach (Episode 15). For TikTok/Reels ads, 5 seconds of silence causes heavy swipe-away. Our updated validator excludes camera/sound cues from hook evidence, enforcing spoken dialogue or visceral action in seconds 0–3 and correctly passing Episode 26.
- **Weak opening in Episode 43:** Although Episode 43 has a strong open loop (the betrayers' names under Crown seal), the opening consists of a report being handed over. It scores only 3/5 on hook and ranks twelfth.
- **Mid-sentence pickup in Episode 36:** Episode 36 opens on a conjunction (*"...and killing my wife afterward"*). While high-stakes, spoken pickups without breathing room require editor audio crossfades.

## Technical checks and honest denominator

The full pack contains 50 episodes. There are 50 decisions: 15 select, 35 pass. All 15
selected cuts satisfy implemented structural checks. These are compliance counts, not
precision or recall. Nine synthetic tests pass, including a mocked endpoint test and the
known semantic limitation. The supplied decisions and exports are not hand-edited after
the final run. The decisions are authored AI judgments; the generated outputs are deterministic.

## Small next experiment

Have one editor blind-review the top five plus five rejected episodes, then label hook,
cliff and standalone clarity separately, record accepted boundary adjustments, and time
review versus the current workflow. This checks rejection mistakes as well as top-rank quality.
For approved creatives, run an equal-budget audience test with matched targeting; track
three-second hold and story-start conversion, and compare cost per story start. No uplift
or production volume assumption has been invented here.

## Interactive upgrade

The Streamlit app accepts new ZIP/TXT screenplay packs and makes fresh AI calls using a
reviewer's own OpenAI/Gemini key. A creative brief and duration range guide selection;
conversation can explain or reselect a single episode. Reselected cuts pass the same
source/timing checks. One repair attempt is allowed; persistent failures are explicit.
Session-scoped caches prevent accidental repeated calls when resuming unchanged inputs.

23 core/AI checks pass, using controlled API responses. These include unseen episode
numbers, malformed cuts and repair, authentication failures, partial coverage, preference
cache invalidation, explanation/refinement context, ZIP errors, and key-free downloads.
The original 50-episode pack was reparsed through the new upload adapter and its saved
15-promo result revalidated. This remains a replay, not a fresh API evaluation.

Fresh model quality and real provider availability remain unverified until a reviewer
supplies a valid key. The synthetic demo is labelled prewritten and makes no model calls.
No confidential Kuku excerpts are bundled in the public deployment source.

Final UI verification: all six Streamlit smoke tests passed on Python 3.12 / Streamlit 1.45.1,
for 29 total passing tests. The initial-state, demo, key-enabled analysis action (mocked model),
explanation chat, refinement/history and clear-session flows are covered. The actual local app
was opened in a browser and its labelled synthetic result, source-backed cut and sidebar were
visually checked. This still does not constitute a live AI-provider or hosted deployment test.

## Final simplified workspaces

The app now defaults to the saved 50-episode sample (15 promos, 35 passes), with no key
or model call. New analysis is a separate upload/API workspace. There is no run-history
feature. The new-run state is never overwritten by switching to the sample. Eight UI
checks pass, including default sample counts, mode isolation and clear-session behavior;
total passing tests are 36 (23 core/AI, five network, eight UI).

The sample continues to use the original saved editorial review. A later user-triggered
Gemini API attempt validated two episodes before HTTP 503; that partial attempt is not
presented as the full 50-episode sample or an audience-quality benchmark.
