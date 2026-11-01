# DZ legacy integration: evidence review and change of approach

Date: 2026-11-01. Development work only; no submission, ladder action or release promotion.

## Decision

User clarification after this review: the overall target is a bot that mimics the strongest teams, follows their observed meta, and has strategies optimised for every map. Their actual drafts, openings, farming, equipment, banking and fight decisions should guide implementation in each map's context. Legacy transfers and DZ's advanced architecture are means to reproduce effective play. The recommendation below to repair a complete lifecycle should therefore be grounded in concrete top-team behaviour examples and map-specific plans. Maintain explicit coverage and performance records for each map and both sides, while preserving sealed holdouts. This is not a request to preserve an elegant architecture at the expense of the target. No new top-team replay research was performed as part of this clarification.

Change the development approach. Keep DZ's kernel, legal observations, action boundary and advanced algorithms, but establish a productive **complete gameplay cycle** before extending their planning authority. The next implementation should adapt a coherent legacy farm/capture/delivery/recovery package to those interfaces. Adding another model, isolated reset improvement or budget threshold is not the priority.

This session did **not** demonstrate competitive improvement. Several candidates improved early collection while degrading banking. All unsuccessful gameplay changes have been removed from the working source; their exact candidates and evidence remain available. The retained changes are the user's no-Varg draft integration, compile-time lineup checks and trace-only discovery/pricing diagnostics.

## Which source was actually investigated

- Current advanced architecture: `origin/build/pure-algorithm-zero` at `886313f4b32a04479c377d702c27c06d0f8106f4`; retained architecture implementation `069775d891b414af1e2e1834191c5549e4e1b78d`.
- Local no-Varg cherry-pick: `0a4ff7e245712819bf7f01232e1fb767901403c2`, from remote experiment `9ab0abb2f29047d839a1897bf528ccf77e74006e`. PR #3 was open/draft when checked; it was not merged remotely.
- Exact lab opponent: `origin/lab/box` at `8866d3a344817007d77aefdc8485758b456f91fe`, extracted to `bots/v76lab/src`. The existing local `bots/v76/src` differs and is not interchangeable with it.
- `bots/v81hl/src` was checked against the user-supplied `v81_home_ladder_hybrid.zip`: zero source mismatches. Per-file lab hashes are in `legacy-sources.json`.
- `build/z-plan` was inspected rather than merged. Its early-gold correlation is not a validated policy; its B1 combat followup was rejected with fuel failures. No reason was established to replace the current architecture with it.

The checkout initially contained a stale `0160ec7` foundation. That earlier work is preserved separately at `checkpoint/legacy-pre-refresh-2026-11-01`, commit `175bf8c3a63fa8d99c46e0eb2dccef9dd2ac6786`. Its measurements must not be attributed to the current architecture. Fetching and refreshing the source corrected that mistake, but consumed substantial effort.

## Decisive complete-game evidence

These are local deterministic development games, not independent strength estimates. `session-results.json` contains all current-architecture run summaries and exact candidate hashes. Every named run has frozen source, binaries, native summaries and replays under `research/dz/runs/<name>/evidence.zip`.

Untraced four-cell idle screen: `00collision` and `00corners`, both sides, advanced architecture enabled. Idle wins are not useful strength evidence.

| Run suffix (all prefixed `dz-hybrid-`) | Mean collected | Mean banked | Decision |
|---|---:|---:|---|
| current-baseline-release-idle-01 | 48.5 | 40 | Reference; itself extremely weak |
| legacy-seed-idle-01 | 71.5 | 39 | Collection gain did not become banking gain |
| playable-idle-01 | 41 | 29.5 | Reject |
| anytime-idle-02 | 30 | 8 | Reject decisively |
| frontier-idle-01 | 54.75 | 33 | Reject as integrated improvement |
| frontier-idle-02 | 46.25 | 26 | Reject; stop threshold tuning |

All these rows had zero reported faults and fuel-outs. On collision the reference earned **zero gold and collected/banked zero gems over 2,000 rounds on both sides**. Some experimental candidates collected 19–67 gems there but still banked zero. This is an acquisition-to-delivery failure as well as a discovery failure.

The final untraced contested screen used the flag-off current-equivalent architecture, not a promising new candidate:

| Opponent/run | DZ side | End round | DZ gold / collected / banked | Opponent banked |
|---|---|---:|---|---:|
| v76lab / current-v76lab-final-01 | A | 925 | 0 / 0 / 0 | 1021 |
| v76lab / current-v76lab-final-01 | B | 993 | 0 / 0 / 0 | 1001 |
| v81hl / current-v81hl-final-01 | A | 925 | 0 / 0 / 0 | 1021 |
| v81hl / current-v81hl-final-01 | B | 1005 | 0 / 0 / 0 | 1004 |

DZ lost all four games with **zero own deaths, faults and fuel-outs**. The two opponent capsules use the same DZ Wasm hash `f81b101c7df04cc6fb3a6f3f18b2bea49165b5eb139aa4b2dd4bdc41b9b0d0c5`. The older idle reference has a different hash; do not pretend all controls are byte-identical. The final opponent source included a disabled frontier experiment, with the original policies selected; its exact provenance is retained.

At round 250, DZ still had zero gold and gems in all four games. Opponents had:

| Opponent / DZ side | Earned gold | Spent gold | Collected gems | Banked gems |
|---|---:|---:|---:|---:|
| v76lab / A | 1480 | 1350 | 87 | 52 |
| v76lab / B | 1358 | 1200 | 68 | 46 |
| v81hl / A | 1480 | 1350 | 87 | 52 |
| v81hl / B | 1345 | 1170 | 80 | 60 |

These values were read from native summary timelines, without running new matches; see `opponent-early-economy.json`. The combination of earning, spending, collection and submission is the benchmark to reproduce. Low deaths alone clearly do not measure useful safety.

Earlier architecture evidence already warned about this: `architecture-2026-11-01/README.md` records excellent controlled opening fixtures but a failed v65 screen (10.5 mean banked, zero wins) and persistent layered-B failure. Its four root-arrival/prefetch followups were rejected. This session's results reinforce that warning rather than supersede it with a successful candidate.

## What is established, and what remains a hypothesis

**Established budget stall.** In `frontier-diagnostic-01`, slot 0 repeatedly entered discovery with roughly 37,000 fuel and produced zero candidates and zero quotes. The discovery guard is `tc.allow(30000)`; `TurnContext::allow` adds the 12,000 reserve, so it requires more than 42,000. This is one concrete liveness failure, not a complete explanation of every champion or map.

**A local fix simply moved the stall.** In diagnostic-02, smaller discovery/participant work produced 3–6 candidates, but pricing still produced zero quotes with roughly 30,000–31,000 fuel. Its outer guard needed more than 34,000. Lowering that guard increased activity in some games but reduced aggregate banking. Independent admission floors cannot substitute for a complete turn budget.

**The execution path has many prerequisites.** `main.cpp` runs memory, requested fields, bank fields and optional crew progress before `safe_goal`. `safemode.cpp` then considers neutral recovery, engagement, access/routes, delivery quotes and opening work before the economy auction. `economic_goal` performs inventory/participant work, frontier discovery, solo/crew pricing and allocation. The old fallback runs later and can be unreachable after a failed expensive auction. Some safety and task owners can independently veto an otherwise selected action.

**Income and delivery are coupled.** Economic gem value requires an accessible altar and a zero-loss bank quote. Unknown access can make collectible gem value zero. The initial small-bag fallback helps acquisition, but a nonempty bag does not itself supply a feasible delivery plan. Repairing only the acquisition bid therefore need not produce more score.

**Model conservatism may suppress useful work.** `objective_model.h` charges worst member order, full incoming exposure to each actor, repositioning and a reserve. Those choices are deliberate bounds, not proof of good decisions in the real executor. This is a hypothesis to check against specific feasible legacy actions; do not simply loosen health thresholds.

**Banking needs its own causal diagnosis.** Root enumeration, paid access, renewals, budgets and executor route ownership interact. No complete causal explanation for collision banking was established here. In particular, do not claim that direct-root ordering, a global cache, or skipping unknown hazards is already proven to fix it.

Two attractive theories were checked and discarded: `threat_revision` does not increase merely because `member_seen` refreshes; it changes when strength changes. Also, ordinary singleton jobs are not held behind the managed multi-worker crew handshake. Do not spend the next turn rediscovering these as proposed fixes.

## What legacy code is worth transferring

The earlier preprocessor audit, preserved in the stale-foundation checkpoint, established active switches rather than relying on comments: `V58_ITEM_PLAN=1`, `V58_FINISH_RESET=1`, `V58_CAPTURE_STAND=2`, `V58_ACT=12`, `HOME_SIDE=1` on lab v76; v81hl also has `LADDER_HOME=1`. `A2_RESETFIX=0` and `APEX_PLAN=0` are not active successes. The active reset refresh is in `fight_camps`, not the inactive reset-fix experiment.

Read these coherent behaviours together in `bots/v76lab/src/bot.cpp`:

- `fight_camps` (about line 4820): damaging targets first, live target refresh after kills, move-compatible attacks/resets, approach failure handling, local danger and staging. Its success depends on reaching a real job with enough executor fuel.
- `go_home_if_needed` (about line 4462): healing/recovery ownership, recall cancellation avoidance, bounded near-finish deferral, capture preservation and stopping gold-only trips after the build is complete.
- `tribute_if_needed` (about line 4576): real carried bag, reachable altar, threat-aware routes, finish/late/rhythm triggers and capture-aware banking. Transfer the cycle, not every historical exception.
- `V58_ITEM_PLAN` and the purchase helper near the start of the file: a funded progression path connected to farming and subsequent visits.
- Group selection around lines 5580–5938: retains the best executable candidate when time runs low; accounts for incumbency and staffing. Extract algorithmic logic without its learned inputs.

Important qualification: the successful legacy builds also enable `A2_CAMPNET` and `A2_MLDRAFT`. Their performance is not evidence that every surrounding hand-written heuristic works independently. The pure-algorithm DZ restriction still excludes learned weights/policies. Legacy opponent wins also do not establish no-Varg parity or isolate draft strength. Do not port a learned score disguised as a formula.

## Recommended engineering method

Use **one minimum productive lifecycle as the integrated unit**: choose a reachable affordable camp, travel, legally use the actual kit, finish, elect the capturer, observe the payout, deliver an actual bag, fund purchases, and recover/return. Implement it inside DZ's existing observations, memory, `Goal` and `Actuator`; do not run a second controller with independent commands.

Keep the advanced auction and planning code. Initially require optional planners to improve an executable lifecycle incumbent within an explicit bounded budget. They must return `Complete`, `Infeasible` or `Deferred`; an incomplete optional search cannot cancel real safe work. Danger/legality gates remain authoritative, with one documented owner for each task transition. This is a proposed design, not a validated solution; the failed raw solo-bid experiment demonstrates that merely inserting another bid is insufficient.

Measure and repair the full lifecycle before returning to drafting, map tables, large lookahead, learned-value substitutions or broad calibration. Diagnose the first divergence using an existing replay. Do not collect a campaign of full matches to answer a question visible in one turn.

A practical next stopping point is a reproducible first complete collect-and-bank cycle on collision from both sides, with purchase/return progress, followed by a small untraced matched opponent screen. A fixture-only increase or more idle gold is insufficient. If the lifecycle is still decisively worse, explain the failed transition and repair/revert it; do not tune ten budget constants.

## Closeout and limitations

- All unsuccessful source policies are reverted. `rejected-experiments.patch`, `rejected-*.h`, `rejected-frontier.patch` and immutable run capsules preserve them. Do not re-enable them as accepted transfers.
- 24 native host suites passed at closeout, including the temporary reduced-frontier coverage checks. That unsuccessful frontier policy and test extension were subsequently restored to the prior implementation. The retained gameplay policy is unchanged.
- All 58 Python tests from `unittest discover -s tests/dz -p test_*.py` passed.
- Final source compiled with all eight lineup variants enabled; the no-Varg/uniqueness static assertions passed. See `novarg-all-eight-build.json`. This is compile validation, not draft strength validation.
- All 17 current-session capsules, containing 58 cells, were verified at closeout; see `CAPSULE_VERIFICATION.txt`. This includes rejected candidates and both real-opponent runs.
- Camp completion counts, per-stage wasted rounds and equipment timelines were not fully extracted for this session. Do not fill them with guesses; the native summaries/replays are available.
- Tracing changes fuel/decisions. Use traces for diagnosis and untraced matched builds for performance.
- Preserve the selected releases, user-owned `config/paths.json`, unrelated untracked files and registered holdouts. No remote merge, push, submission or ladder activation occurred.

Read `NEXT_AGENT_PROMPT.md` for the executable continuation brief.
