# Continue DOOMSDAY Zero: mimic the strongest teams' gameplay

You are continuing work for me in `Infosuii/neural-networkk-battlecode`.

Actual Windows checkout: `C:\projects\cambridge battlecode\work\neural-full-stack`.
The parent workspace is `C:\projects\cambridge battlecode`. Use the actual checkout for Git and project commands.

## Mission and current decision

The user's overall objective is to build a very strong bot that **copies how the top teams actually play, follows their meta, and has strategies optimised for every map**. Treat observed successful opponent behaviour as the primary design target: drafting, opening routes, farm selection, team allocation, ability sequences, purchases, banking, recovery and fights. Implement those behaviours directly where practical; theoretical novelty is secondary to reproducing effective play.

Use DZ and legacy components to achieve that target. A coherent legacy gameplay package is a promising implementation route, not the ultimate objective or proof that it matches the top teams. Preserve useful DZ architecture while adapting it to execute the observed policy. You may selectively reuse/adapt old source. The former prohibition on legacy code reuse is superseded. The existing pure-algorithm restriction remains: behavioural imitation here does not itself authorise importing trained weights or learned policies.

The previous agent investigated many weak candidates but did **not** achieve a competitive improvement. Do not assume its experiments are validated. We are explicitly changing the development approach: establish a complete productive lifecycle, then let advanced planning improve that working incumbent. Do not start with another forecasting feature or a series of fuel-threshold tweaks.

Keep DZ's kernel, observation boundaries, `Goal`/memory interfaces, Actuator legality checks and advanced economy/combat/coordination implementations. Preserve opportunities for their later use. Do not wholesale copy v76's controller or create two competing controllers. Each task transition and each game action must have one owner.

Work autonomously and implement code. Use the existing evidence before running games. Prioritise productive play and complete-game conversion over feature count, isolated tests and elaborate reports.

## Read these first, in this order

1. `research/dz/legacy-execution-2026-11-01/REVIEW.md` — current evidence, rejected approaches and recommended change of method.
2. `research/dz/legacy-execution-2026-11-01/session-results.json` and `opponent-early-economy.json` — exact run metrics, hashes and settings.
3. `research/dz/architecture-2026-11-01/README.md`, `FOLLOWUP.json`, and the current top of `research/dz/BACKLOG.md` — what the advanced architecture actually implements and what already failed.
4. Relevant source listed below. Read other historical documents only when needed; do not spend the session rereading the entire handoff archive.

Check applicable repository instructions and current Git status before editing. A prior search found no AGENTS.md; verify if circumstances changed.

## Source/checkpoint facts

- Advanced base: `886313f4b32a04479c377d702c27c06d0f8106f4`, branch `build/pure-algorithm-zero`; architecture implementation `069775d891b414af1e2e1834191c5549e4e1b78d`.
- Local no-Varg cherry-pick: `0a4ff7e245712819bf7f01232e1fb767901403c2`, originally remote `experiment/dz-no-varg-draft-2026-11-01` at `9ab0abb2f29047d839a1897bf528ccf77e74006e`. PR #3 was open/draft when checked, not merged remotely. There may now be a later local closeout commit containing this prompt, evidence and trace diagnostics; inspect the log.
- `DZ_ECONOMY_V2=1` enables the current advanced development architecture. The selected default/release remains off; a default compile alone does not exercise the development bot.
- Exact lab v76 source is `bots/v76lab/src`, extracted from `origin/lab/box` commit `8866d3a344817007d77aefdc8485758b456f91fe`. `bots/v76/src` is a different version. File hashes are in `legacy-sources.json`.
- `bots/v81hl/src` matches the supplied archive byte-for-byte. Archive: `C:\Users\omdha\Downloads\v81_home_ladder_hybrid.zip`.
- Stale-foundation work is quarantined at branch `checkpoint/legacy-pre-refresh-2026-11-01`, commit `175bf8c3a63fa8d99c46e0eb2dccef9dd2ac6786`. Do not cherry-pick its old controller or attribute its numbers to the advanced base. It contains a useful preprocessor inventory/audit, not an accepted gameplay implementation.
- `build/z-plan` is not an automatically better replacement. Earlier gold-price and combat changes there lacked successful integrated validation; B1 had fuel failures. Do not blindly merge branches.

## Current performance: take this seriously

Final untraced collision games using the flag-off current-equivalent advanced policy:

- Against exact v76lab: DZ lost both sides, earned zero gold, collected zero gems and banked zero; opponents banked 1021/1001, ending rounds 925/993.
- Against v81hl: same zero DZ productivity; opponents banked 1021/1004, ending rounds 925/1005.
- DZ had zero deaths, faults and fuel-outs in all four games. Runtime safety is not the bottleneck that these results justify optimising first.
- At round 250 opponents had earned 1345–1480 gold, spent 1170–1350, collected 68–87 gems and banked 46–60. DZ was still at zero.

Exact runs: `dz-hybrid-current-v76lab-final-01` and `dz-hybrid-current-v81hl-final-01`. Same DZ binary across those opponents. Do not describe four losing development cells as a broad win-rate estimate; they are enough to reject claims that the bot is nearly competitive.

The untraced idle reference `dz-hybrid-current-baseline-release-idle-01` banks 0/0 on collision and 88/72 on corners (mean40). Legacy solo-seed improved collection but mean banking was39; later variants fell to29.5,8,33 and26. All unsuccessful gameplay changes were reverted. The older architecture's excellent controlled fixtures also coexisted with failed contested screens and layered-B0. Do not use fixture gains as strength acceptance.

## Concrete diagnosis already established

The retained `DZ_FRONTIER` trace line counts candidates and actual solo quotes, with fuel entering discovery/pricing. `dz-hybrid-frontier-diagnostic-01` shows the original policy repeatedly entering discovery at about37k fuel while `tc.allow(30000)` requires more than42k, because `allow` adds the12k reserve. Thus it makes zero candidates/quotes. A smaller frontier experiment moved the stall: it discovered3–6 candidates but reached pricing at30–31k, below that stage's34k requirement. Further lowering thresholds did not improve integrated banking.

This proves a specific stage starvation problem, not that one smaller threshold solves the bot. Investigate the complete turn schedule and the ownership of an executable task. Avoid constructing every speculative prerequisite before doing useful work.

Read the chain:

- `main.cpp`: memory, requested fields, bank fields, crew planning/fields, then `safe_goal`, executor and background work.
- `safemode.cpp`: neutral recovery, engagement, bank/access forecasts, openings, economy, then budget-protected old fallback.
- `economy.cpp`: current contract and delivery handling, actor/inventory decoding, participants, frontier discovery, pricing, allocation, macro decisions.
- `actions.cpp`: live action legality, camp wake admission, crew/siege focus, movement, spells/attacks, banking.
- `siege.cpp`: physical access, bank forecasts/routes, current admission, neutral recovery.

Also investigate the complete collection-to-delivery handoff: unknown bank access can make economic gem value zero; a small initial bag can be acquired without creating a deliverable route; selected solo work is still subject to executor admission. A raw solo bid alone already failed.

Do not repeat these disproved explanations: `threat_revision` does not change merely on a refreshed observation date, and ordinary singleton tasks are not held behind the managed multi-worker handshake.

## Proposed implementation sequence

### 0. Establish a small, concrete top-team behaviour reference

Find the available top-team replay/analysis data in this repository and connected project context before asking for more data. Verify the team, bot version, match date, map and opponent; distinguish current evidence from old meta. Do not invent unavailable replay paths or assume every legacy behaviour represents the current leaders.

Inspect a small representative set, especially the first250 rounds and the first completed farm/bank/purchase cycles. Record concrete state-to-action examples: who goes where after spawning, which camp they choose, how many bodies they commit, attack/cast/movement ordering, capture ownership, actual purchase order, bag size and conditions when they bank, and what triggers withdrawal or a fight. Include the relevant map/lineup/nearby threats so a situational behaviour does not become a universal rule. Separate directly observed actions from inferred motives.

Produce a compact behaviour-to-code mapping: observed top-team behaviour → DZ's current divergence → legacy component that can implement it → required dependencies → complete-game metric. Choose the largest clear productivity gap and implement its coherent lifecycle using the steps below. This is a short engineering reference, not a new research campaign or training project. Reuse existing analyses and stop collecting examples once there is enough evidence for the first change.

Validate both behavioural fidelity and competitive effect. A bot that takes the same route but fails to capture, bank or purchase has not reproduced the useful behaviour. Judge improvements against real opponents as well as the reference traces. Keep the user's no-Varg preference as an explicit constraint when adapting top-team drafts.

### 1. Identify the first failed lifecycle transition from existing evidence

Use one collision replay/trace and the corresponding legacy source, especially rounds1–250. For each relevant body, identify its actual task, selected target, distance/field readiness, action taken, veto/defer reason and remaining fuel. Locate the earliest transition where legacy progresses and DZ stops.

Read existing summaries/replays before launching another whole match. If a fact is missing, add one compact reason/counter to the existing trace or construct one focused native replay/fixture. Trace changes fuel; do not use traced strength numbers as the final comparison.

Choose an implementable causal failure, not a plausible theory. State what action legacy takes, why it is legal/productive, why DZ cannot take it and which dependent behaviours must move with it.

### 2. Adapt one coherent productive lifecycle inside DZ

Start with reachable harmless/resource jobs and genuinely affordable small damaging jobs where a complete cycle is possible. The integrated unit should include:

1. Bounded discovery of a feasible real job with an incumbent that survives optional planning.
2. Sticky ownership and executable navigation to it, with finite failure deadlines.
3. Target selection, live retargeting after kills, move-compatible attacks/resets and actual kit usage.
4. Capture ownership/standing and observed payout before counting future gold or gems.
5. A real delivery task for the carried bag, including safe movement, current channel admission, retention through deferred work and recovery when actually unsafe.
6. Funded equipment purchases and a return to productive farming, preserving near-finish/capture work where justified.

Port interacting behaviours together. Keep advanced planning as a potential improvement to that cycle; retain its code and interfaces. Do not merely inject another gold-only bid into the same starved pipeline. Do not disable all safety or treat unknown hazards as safe. Distinguish `Deferred` from `Infeasible` and from an actionable task. Optional planner failure must not automatically replace safe progress with Home.

Use a clear owner table for farm selection, capture, delivery, shopping/recovery, crew commitments and combat interruption. Legacy adapters should return decisions through the existing architecture, not issue a second set of SDK commands. Never let a singleton reset override a managed crew focus or siege withdrawal.

Use one explicit development feature switch or a frozen candidate. Keep the existing baseline playable and preserve a rollback checkpoint. Do not add several overlapping fallback controllers.

### 3. Validate the whole cycle, then a small contested comparison

First prove actual execution of collect → capture → bank → purchase/return, including fuel and legality. Existing host references already cover a great deal of arithmetic; only add tests for genuinely new invariants and observed failure cases.

Use collision both sides as a known development failure, not a holdout. Avoid testing already-disproved variants. Once it performs a real cycle, run the smallest untraced matched screen against v76lab and v81hl and the exact frozen DZ control. Add a few representative maps only after material progress. Preserve designated holdouts.

Report R100/R250 gold, collection and banking; actual completion/capture count; spent gold/gear; deaths; task/idle or Home rounds; own/opponent score and outcome; runtime faults/fuel-outs. Mark unmeasured metrics explicitly. A collected-bag increase with zero submission is an unfinished cycle.

Reject decisive regressions promptly. If one repair moves the stall to the next stage, fix the complete dependency/ownership problem instead of continuing a threshold sweep. Keep positive interactions testable: this lifecycle is a coherent package, not six artificial isolated feature gates.

### 4. Reintroduce planning authority on evidence

After the cycle works, test whether the existing auction improves allocation over the real incumbent, whether crews complete more valuable jobs, and whether advanced gear/combat choices improve the same integrated games. Give each planner a bounded budget and preserve a feasible current action. Prefer the proven executor whenever the more sophisticated replacement has not improved complete-game performance.

Avoid speculative universal-value redesign and broad calibration campaigns. Map-conditioned drafts, routes and role choices belong in the initial lifecycle whenever the observed strategy needs them; do not force one generic opening onto incompatible maps. Add specialised rules for a concrete observed map need, then validate the complete strategy.

### 5. Build and optimise a strategy for every map

Maintain a map strategy registry covering the full supported map inventory. For each map, record its exact identity/version, both spawn sides, known top-team references, chosen no-Varg draft, roles, first250-round opening, farm/respawn circuit, capture ownership, bank access and rhythm, equipment progression, contested objectives and recovery/blocked-route contingencies. Include evidence links, exact candidate hash and status: unstudied, proposed, implemented, measured or independently confirmed. Never label an untested plan optimised.

Begin with the worst demonstrated failure and a few structurally different development maps. Build reusable execution primitives, then compose them into plans adapted to each map's actual terrain, camp economy and altar access. Explicit map-specific plans are authorised and desirable when supported by evidence; terrain-derived plans can cover unfamiliar maps. Preserve a playable fallback. A map name alone is not evidence that a historical hardcoded plan remains good for the current source, draft and opponent meta.

Optimise the complete combination on each map: draft + opening + worker allocation + farm/capture cycle + bank route/timing + gear + threat response. Copy the strong teams' map-specific division of labour where it works. Do not simply use the same champion order and farming policy everywhere, or assume one scalar setting can compensate for incompatible geography. Let the plan adapt when enemies contest a route or an intended camp is unavailable.

Evaluate side-specific failures explicitly. A good mean across maps must not hide a map/side that produces nothing. Maintain a per-map scoreboard of early economy, completed cycles, banking, deaths and outcomes against real opponents. Iterate on the weakest map strategies in small batches; expand only after a material fix. Map coverage is an explicit completion requirement, but broad repeated sweeps of a decisively failing candidate are wasteful.

Preserve designated holdout games/opponents/seeds and any reserved maps. Do not inspect or tune against a sealed holdout to populate the strategy registry. Mark that coverage pending until the final confirmation stage. The goal is strong map-specific play with evidence, rather than a claim of universal optimality from a small screen.

## Legacy source priorities and traps

In `bots/v76lab/src/bot.cpp`, inspect `fight_camps` (~4820), `go_home_if_needed` (~4462), `tribute_if_needed` (~4576), the `V58_ITEM_PLAN` purchases near the beginning, and job selection ~5580–5938. Check actual switches/preprocessed code before adapting a behaviour.

Active known settings include `V58_ITEM_PLAN=1`, `V58_FINISH_RESET=1`, `V58_CAPTURE_STAND=2`, `V58_ACT=12`, `HOME_SIDE=1`; v81hl adds `LADDER_HOME=1`. `A2_RESETFIX=0` and `APEX_PLAN=0` are inactive experiments, not proven transfers. Existing `fight_camps` already refreshes the target before a reset. The legacy builds also use learned camp/draft components; do not copy those into pure-algorithm DZ or infer that every surrounding rule is independently validated.

Do not revive `DZ_PRODUCTIVE_EXECUTION`, `DZ_LEGACY_FARM`, the early-snapshot solo incumbent, the frontier-budget policies, or the earlier root-arrival/resource-prefetch bundle as accepted code. Their sources/results are preserved for diagnosis. A new coherent replacement needs a causal reason it differs.

## No-Varg requirement

Keep Varg excluded from every lineup and the optional portfolio. Preferred base orders:

- Three: Vendetta, Marcella, Vesper Vale.
- Four: add Heart of Ruin.
- Five: add Ryth.

Map-aware complementary choices may remain available. These are preferences, not validated universal optimal drafts. The final source has compile-time checks for unique non-Varg lineup entries; all eight compiled successfully. Do not confuse good picks with correct execution.

## Operational details and safeguards

- Python: `C:\Users\omdha\AppData\Local\Programs\Python\Python313\python.exe`. The Windows `python` alias and `py` are unusable here.
- Native compiler: `C:\msys64\ucrt64\bin\g++.exe`.
- Local CLI: `tools/vendor/cambc.exe`, SDK4.0.0/engine2.0.0. Builds access `%LOCALAPPDATA%\cambc`; use the normal tool approval mechanism if needed. No manual engine patching.
- Example development run: `& '<python path>' tools/dz.py smoke --name <fresh-unique-name> --maps 00collision --opponent v76lab --set DZ_ECONOMY_V2=1 --workers 2`.
- `--trace --set DZ_TRACE_TO=0` supplies compact diagnostic traces; trace is not fuel-neutral.
- `tools/dz.py host`; `-m unittest discover -s tests/dz -p 'test_*.py'`; `tools/dz.py verify --names <only relevant new runs>`.
- Complete experiments are immutable. Use fresh names; inspect `provenance.json` for source, binary, map and opponent hashes. `tools/dz_extract_replay.py` and `tools/dz_scene.mjs` read existing native evidence without new games.
- At closeout24 host suites passed;58 Python tests passed; all17 current-session capsules/58cells verified. These checks do not establish competitive strength. The changed frontier policy/test extension was then reverted; only draft checks and trace diagnostics remain.
- `config/paths.json` was already user-modified; preserve it. Many unrelated old binaries, `compile_commands.json` files and `bots/v81home` were untracked. Do not stage or delete them. Do not use a broad clean/reset.
- Do not overwrite releases, push/merge remotely, submit, activate a bot or run online ladder games without explicit authorisation. Preserve reserved holdouts. Local reversible development and checkpoints are authorised.

Start by reading the review, existing failing replay and available top-team behaviour evidence. Choose the first coherent lifecycle gap, implement the observed successful behaviour through DZ's interfaces and verify it efficiently. End with exact source/evidence provenance and candid remaining weaknesses. Do not stop at another plan or claim success from clean runtime and idle wins.
