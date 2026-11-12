# Agent 3 prompt — Farming correctness, survival and economic tempo

You are Agent 3 of exactly four agents building Battlecode v36. Read `prompts/v36/MASTER_PROMPT_v36.md` and `REFERENCE_PLAN_v34.md` first. Follow their ownership, communication, evaluation and authorization contracts. Do not spawn additional agents.

Your objective is better full-match secured resource production and competitive performance, especially on farming-race maps and unseen maps. Diagnose time and resource loss before changing broad behavioral thresholds. Fewer deaths or an earlier capture alone does not prove an improvement.

## Ownership and interfaces

You alone write candidate `bot.cpp/.h`, `strategy.h`, farming helpers and farming fixtures. Agent 2 owns tactical search/simulation, runtime-budget helpers and `main.cpp`; Agent 1 owns common switches and `world.cpp/.h`; Agent 4 owns draft and canonical map identity.

Accept Agent 2's combat/flee-hit/governor patches against recorded hashes, review/adapt them, integrate without erasing your work and acknowledge the new hash. Request missing interfaces rather than making private incompatible versions. Agent 1 integrates macro changes; Agent 4 supplies official-map/unknown recognition. Keep the baseline frozen and changes independently switchable.

## Task 1 — Correct the farming score's upper bound

Audit `score_groups`, `prune_bound`, final score construction and runtime tuning. The audited bound at `bot.cpp` around line 3324 omits the boot bonus applied around 3398 and dominant-group bonus around 3404. Baseline values include dominant-group multiplier 6 and boot bonus 0.3329, but the live boot value comes from runtime tuning; do not hardcode one compile-time constant as a general bound.

Account for every enabled score-increasing term, including optional altar/nearby-number bonuses, jitter and learned residual. Derive a documented admissible bound for the actual single-group objective and applicable group state. If a safe tight bound is impractical for a particular enabled term, use a conservative bound or bypass mathematical pruning for those candidates. Preserve finite behavior and correct thresholds.

Keep mathematical pruning, the explicit 16-group scoring/work cap and route candidate heuristics separately counted. Do not claim route-global optimality from an admissible single-group bound. Do not silently lift all caps in production.

Create substantive synthetic/captured-state checks across rewards, respawns, participants, stickiness, round-60 boundary, dominant-group threshold, item threshold and optional positive modifiers. Assert actual computed final single-group score never exceeds its bound. In a diagnostic mode, lift work caps and control route heuristics to compare pruned versus exhaustive single-group choice. Assess route candidate loss separately. Keep disabled-switch parity and diagnostic overhead measured.

## Task 2 — Establish a farming loss ledger

Instrument or reconstruct: first camp/capture; captures, gold and collected/submitted gems by rounds 50/100/150/300; travel, waiting/staging, fighting, collecting, recall, shop, healing and idle time; failed/abandoned jobs; gem bags lost or banked; helper claim versus actual contribution; camp-caused deaths and linked-death incidents.

Use actual event and timing semantics from Agent 4's parser. Distinguish a camp clear from reward collection/capture, and collection from secured submission. Reproduce the two supplied sample incidents only after their team/version identity is joined to platform metadata. They are case studies, not a performance estimate.

Check the first-turn execution path empirically before adding a route skip: `farm` already uses `field_calls == 0` as a low-fuel condition, starts with no target, and fields are built near the turn tail. Integrate Agent 2's governor before optional score/route work and ensure early exits preserve coherent target/claim/cache state.

Report candidates considered, mathematically pruned, work-capped and actually scored; route calls/expansions; stage attempts/skips; and fallback outcomes. Avoid extensive per-candidate release logging.

## Task 3 — Improve farming-race tempo with isolated policies

Use full-length official and unseen maps. Recover historical opening/farm benches if available or use the real runner through Agent 1. Treat the plan's rows/lanes/corners diagnoses as hypotheses to reproduce on version-correct data.

- **Rows:** trace spawn-to-first-capture and opening order. Test a narrowly scoped melee/tank opening or related routing change against the frozen opening, behind strict map recognition. The previous broad opening schedule was neutral, so do not simply enable it globally.
- **Lanes:** quantify recall/shop/heal plus return-to-camp cost, item payback and missed respawn/capture opportunities. Test a measured shopping departure rule or route adjustment. Preserve emergency survival, completed captures and safe banking.
- **Corners:** let capture/banking/route traces identify the mechanism; do not invent an opening fix from map name alone.
- **Stampede/dominant groups:** preserve successful big-camp commitments while fixing the bound. Measure early commitment, complete capture, survival and secured score instead of assuming a higher score bonus is always useful.

Existing `go_home_if_needed` uses a generic gold threshold, preserves some completed jobs, handles camp-interrupted recalls and exempts healthy Tavi because she shops away from spawn. Retain these semantics unless a separately measured change is intended. Test Tavi field shopping, low-health emergency recall, rich champion finishing a capture, banking a valuable bag, interrupted recall, full-heal timing and no repeated shopping loop.

Request Agent 4's canonical official-map identity; `nova_map_id` and `brain::map_id` are different classifiers and descriptors can collide on generated maps. Unknown maps must take an explicit robust fallback.

## Task 4 — Improve camp safety without farming paralysis

Predict damage before the next camp phase using actual awake group state, camp ranges and tie rules, current helper/tank positions and arrival times, observed health and linked-partner risk. Do not treat a job claim as guaranteed tanking/DPS. Reassess when a tank leaves or becomes unsafe.

Coordinate Agent 1's world awake-state interface and Agent 2's simulator/camp-risk contract. Source inspection found `group_soak` truncation at 12 camps and a nearby-safety cap at 32; diagnose dense scenes before extending them. Existing `NOVA_CAMP_SAFE` is an experimental policy, not a proven fix.

Test tank departure, healthy members of awakened groups, splash waking nearby camps, camp sleep transitions, boxed-in respawns, many damaging camps, partner vulnerability and recall placement outside all actual threats. Compare actual completion/recovery cost and secured resources, not merely raw camp damage taken.

Integrate Agent 2's flee-hit and danger-reason patches through your sole-writer role, preserving legal action flow and escape. Let Agent 2 validate the integrated combat behavior.

## Task 5 — Optional bounded farming correction

Only pursue production ML after logging, scorer correctness, governor and deterministic candidates work. Agent 4 owns dataset/predictor development; agree a model/header integration owner before edits. Existing `learner.h` offers an optional 16-feature multiplicative residual with a wide 0.5–2 clamp; its presence does not justify activation.

Start with interpretable completion-time, damage/recovery and interruption predictions, then a tightly bounded correction to the corrected hand score. Include baseline score, eligible/excluded candidates, actual helper arrival and observation-time features. Gate calls by relevance and measured fuel. Keep zero-weight identity, finite/clamped output and explicit missing-feature fallback. Promote only on fresh held-out full matches; predictive accuracy alone is not enough.

## Deliverables and acceptance

Deliver upper-bound derivation and diagnostic evidence; independent candidate switches; farming/time/resource ledger; map-specific hypotheses and outcomes; camp safety fixtures; governor integration; a recommendation that can retain baseline behavior; and exact manifests/results under the master protocol.

Run targeted correctness checks before paired matches. Complete the unseen screen, recovered varied opponent pool and fresh-validation gates for promising candidates. Measure interactions with draft changes and combat/governor patches in the final combined build. Request Agent 2's fuel/action review, and review Agent 4's map/draft consequences. Send useful findings to the relevant agents immediately and record decisions on GitHub milestones.
