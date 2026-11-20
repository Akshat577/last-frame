# Quality review: evidence, not performance claims

Review provenance: Codex self-review of script cues and saved decisions. No independent human
editor labels, unseen evaluation set, footage verification, audience test or live API run.

## First posting hypothesis

1. Episode 12, 00:44.00-01:09.20, 25.2s: a sister makes bodily sacrifice the price of saving a husband. Strong immediate cruelty and explicit unresolved choice. Start here.
2. Episode 27, 00:03.40-00:46.40, 43.0s: her supposedly penniless husband's ring belonged to a lost noble son. Tests identity mystery against cruelty.
3. Episode 28, 00:15.30-00:47.00, 31.7s: the poisoning victim defends the maid, then cannot finish her accusation. Tests an interrupted witness.
4. Episode 45, 01:14.80-01:53.00, 38.2s: declared Duchess, then told she is not lawfully married. Tests a status reversal. Tied rubric scores use earlier episode, not proven superiority.
5. Episode 3, 00:58.30-01:23.90, 25.6s: guards drag a woman away; a stranger demands her release. The fight and identity stay outside the cut.

All cut times refer to each episode's local screenplay clock. Footage may differ.

## Actual mistakes and weak picks

- AI boundary mistake during authoring: episode 18 was initially set to end at 01:24.00,
  the START of her scream, rather than its END at 01:26.20. Source lookup caught that the
  proposed cliff evidence did not end there. The supplied decisions use 01:26.20, before
  the rescue at 01:26.50. This is the concrete example of where the AI got it wrong.
- Episode 18 remains context-fragile: it opens on "Leave it!" and assumes the book is visible.
  If the actual first frame does not show the ledger, reject this pick or expand the setup
  and rerun validation. Its context rating is only 3/5. It is ranked tenth, not launch-first.
- Episode 43 has a credible open loop (the betrayers' names), but a report being presented
  is a weak first-three-second hook. It scores 3/5 on hook and ranks fourteenth. Structural
  validity cannot rescue exposition-heavy creative.
- Episode 36 starts on a conjunction ("...and killing my wife afterward"). It states stakes
  immediately, but the spoken pickup may feel abrupt. Keep the flag until footage review.

## Counterexample: exciting does not mean unresolved

Episode 16, 00:19.20-00:58.50 (39.3s) has a fight, an interrogation and retreat. It is an
attractive naive action pick, but it includes "Harrington! Gerald Harrington paid us!" at
00:49.80-00:52.20. Ending after that cannot be sold as "Who sent the thugs?". The episode
is passed over in favor of episode 15, which ends before the fight and confession.
This is a self-reviewed negative example, not an empirical comparison to a baseline system.

The synthetic test `test_resolved_answer_is_semantic_blind_spot` deliberately demonstrates
that the validator accepts a structurally correct clip containing its answer. AI/editor
review must catch this; no claim of automatic narrative correctness is made.

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
