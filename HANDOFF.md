# Paused botx3 continuation — 3 November 2026

Development is paused at the user's request. No experiment processes remain running. The latest complete full-feature release is `bots/botx3_11`; the strongest measured broad version is `bots/botx3_1`. Do not claim the latest integration is a universal upgrade. No version 12 exists.

Start with `SETUP_FRESH_MACHINE.md`, then `NEXT_AGENT_PROMPT.md`. `PAUSED_STATE.json` identifies releases; `MANIFEST.json` verifies portable files. `handoff-botx3-latest/BOTX3_CONTINUATION_LATEST.zip` is an overlay capsule for this repository, with its SHA-256 alongside. Older `handoff-botx3/` files are historical, not current instructions.

Git branch: `dev/botx3-team-economy-20261102` in https://github.com/Infosuii/neural-networkk-battlecode . Original development checkout: `C:/projects/cambridge battlecode/work/botx3-team-economy`. Do not touch other checkouts. Local development/testing and Git pushes are authorized; official ladder submission, publication and activation are forbidden. No login is needed for local work. Older documentation about ladder login or live versions is stale for this task.

## User intent and failure protocol

Build actual numbered improved bot versions, restore previously implemented features, use draft fuel for substantially richer map analysis, and fix bugs. Spend most time improving the bot after a short audit. Preserve frozen versions rather than replacing them with vaguely named tested candidates. Start the next version from full version 11; retain version 1 as a useful performance reference. `bots/botx3/src` is a flag-controlled integration source with defaults OFF: building it without overrides yields original x1, not the latest full bot. Each numbered version has explicit `features.json`, `release.json`, `src/` and exact runnable `bot.wasm`.

Follow AGENTS.md: never reject an idea solely on its first losing benchmark. Verify compilation/configuration/activation/inputs; inspect shared state, dependencies and order; examine failed native replays; make 2–3 motivated focused repairs where warranted; test plausible interactions and map/opponent/state scope. Classify Accepted, Retry required, Conditionally useful, Parked or Rejected. A failed gate is not Rejected. Record mechanism, evidence, repair hypothesis, attempts and uncertainty. Do not rescue weak ideas with arbitrary configurations.

## Results and version history

All following completed development matrices use 14 already-spent maps, four opponents (x1, x2, v86h, v92), both sides: 112 games per arm. Broad matrices use 46 already-spent maps: 368 per arm. These are not untouched holdouts. Fuel counts are reported by historical summaries; they count fuel-out events, not games. Report faults separately; all listed matrices had zero own/opponent faults.

| Version | Change | Dev wins /112 | Broad wins /368 |
|---|---|---:|---:|
| frozen original x1 | feature defaults off |56|173|
| parent x1c1 | earlier planner |57|171|
| 1 | independent rich draft summary/path matrix |60|189|
| 2 | restored implemented features, team mode14 and rolling planning |49|not run|
| 3 | capture/regroup/flee/banking arbitration |55|112|
| 4 | initial finite banking lease |55|not run|
| 5 | non-renewing banking commitment and public delivery marker |55|119|
| 6 | mastery substitution alias correction |56|119|
| 7 | native planner cost/value restoration |65|136|
| 8 | protect only healer in frontline-heavy draft |65|not run|
| 9 | unique projected roster and safe-siege admission |61|135|
| 10 | chip fallback and complete camp exposure tiles |58|131|
| 11 | exact death window, net-loss anti-feed |56|not run|

Use exact same-code controls, not only cross-version differences: code/data-layout changes alter deterministic play. Dev treatment/control wins: v3 55/50; v4 55/59; v5 55/51; v6 56/55; v7 65/57; v8 65/65; v9 61/54; v10 58/58; v11 56/61 (net-only also56). Broad treatment/control: v5 119/116, v6 119/119, v7 136/116, v9 135/127, v10 131/131. Proofs and exact controls are in each campaign's `same-code-proof.json`, manifests and builds. Tagged volatile runtime initializers preserve code sections; values stored as +1 prevent zero/BSS layout changes.

Dev fuel events original120, parent122, v1 116, full v2/v3/v5/v6/v7/v8/v9/v10 65–66, v4 61; v11 52. Broad original58, parent54, v1 86, v3/v5 142, v6 140, v7 150, v9 157, v10 152. Fuel remains unresolved; zero faults does not imply zero fuel exhaustion.

Earlier draft-summary evidence: full path candidate broad160/304 versus same-code control154, original147, parent142. Fresh-at-the-time 8-map set:29/64 versus control21, original26, parent29; no fuel/faults. Map-cluster intervals span zero. Those maps are now spent. Bank-only mode14: dev60/112 versus control57; 26-map broad102/208 versus96; next12 maps37/96 versus37, original50, parent42. No transfer established. Earlier expiry repair broad95/208 versus never99 (original97,parent100); earlier narrow gain did not hold.

## Implemented mechanisms and evidence

Source and scripts live under `bots/botx3/src` and `research/botx3-20261102`. Every version snapshots the exact enabled flags. `restored-features.json` records the full restored set. Previously implemented mastery, bush preprocessing, siege, resource walk, isolation, secure capture, solo hunting, anti-feed, heartbeat, soak, prune/flee/teamwin, strict siege, bag/drop risk, economy, cover, burst/target visibility, locks/disengage/beliefs, rolling planner, banking cycle and team mode14 are included in full versions. This does not mean every speculative historical retry-queue idea was implemented. Mutually exclusive superseded modes cannot all be active together.

Mode12 admitted proposals through native score_groups; mode13 fixed the leader reading its own ordinary claims as planner commands and preserved productive commitments; mode14 waits for complete field cache (the first trace had only2/15 jobs ready on round1). Coarse auction models remain Parked, not disproven by a single run.

`draft_paths.cpp` spends draft-only fuel on actual static inter-camp shortest paths, spawn/bank access and a geometric banking-route width proxy. Draft allowance is10m fuel; shared memory1KB. Bytes0–7 preserve brain/ML,8–1007 summary,1008+ roster. Up to38 groups: compressed triangular matrix plus7 metadata bytes/group;39–44 matrix only;45–126 rich metadata only. Bridges invalidate imported static paths. Native routing and territory consume the summary. `X3_DRAFT_USE`:0 compute-only,1 both consumers,2 routes,3 territory,4 lazy native-timing cache. Native diagnostic gold:348542 draft fuel,15groups105pairs218bytes,3readers,285 comparisons,zero path mismatches; perimeter864798fuel,22groups231pairs393bytes,6readers,572 comparisons,zero mismatches. These are instrumented traces, not exact release fuel. `draft-paths-v3-diagnostics` stores evidence. First losing greatwall run collected484 versus392 but banked159 versus223 with no early death: collection alone is insufficient.

`bank_commit.h`: deadline round+2*distance+ceil(bag/10)+10 without renewal, public marker125; delivering actors excluded from fresh farm jobs. Completion/death/blocked/cooldown/expiry clear state; contact/low-health safety retains priority, healthy committed trip precedes gold-only shopping. Native legal small-bag conformance:5 probes,98 delivery steps,5 completed empty bags with public125. Diagnostic `X3_BANK_PROBE` is not a release feature.

`draft_alias.h`: accepted mastery substitution consumes its original slot once, in both fixed and ML paths, only after engine acceptance. Original7 had repeatedly become1,10,5; repaired native trace substitutes original7 once. Projection padding also deduplicated. Version8 preserves only healer when projected frontline count>=3.

Native rolling planner previously mixed wall-clock duration with person-turn cost and raw value; v7 restores `c.cost` and effective `c.score*c.cost/sticky` while preserving timing for respawns. Siege checks safe admission before pruning required crew>team; safe siege has no hypothetical tanking health cost. Chip fallback models one-person persistent damage when no safe full clear is possible. `camp_exposure.h` expands32 slots to256: radius7 requires225 unique tiles; host example49wolves980 versus old truncated640. Conformance proves36 chip and24 siege admissions, not competitive strength. Version10 had zero outcome changes against its exact control in112/368 pools. Diagnostic `X1_FUEL_PROBE=1` bypasses shortcuts; never enable it in a normal release.

`feed_control.h`: bounded exact death-window deque, both teams' public alive transitions, net-loss trigger instead of balanced trades; choose strongest safety modifier rather than multiply duplicate modifiers. `X3_FEED_CONTROL=1`, runtime USE0 raw,1 net-only,2 net/noncompounding. Version11's first development test regressed56 versus61. Net-only and combined produced identical results. Activation and failed native replay diagnosis remain unfinished: Retry required, not Rejected.

Host tests cover cycle, scheduler, banking commitment, draft aliases/projection, exposure and feed windows. Individual tests passed during implementation, but the complete suite was not rerun after all final edits/pause. `tools/botx3_resume.py host-tests` runs the six tests on a fresh C++20 toolchain. Do not claim final whole-suite validation until run. Screen JSON writes now use temporary-file replacement; screen original-hash guard checks full hash; `team_contract.py` tolerates absent optional historical campaign rows.

## Next work, in order

1. Short setup/identity audit; then create actual numbered version12 from full11. No large re-audit or giant matrix before a concrete repair.
2. Investigate v11 anti-feed activation, equal/net trade semantics, plan4 timing and lost/gained native replays. Determine why net-only equals combined. Make only mechanism-driven variants and matched controls; inspect fuel before attributing strategy effects.
3. Repair draft summary fallback when a pair distance>=255 or asymmetry currently drops the entire payload: preserve valid rich metadata instead. Add explicit old/new memory-format dispatch: legacy `team_economic_init` still reads old header byte480 while rich memory starts8. Header collision is a plausible unresolved risk, not a reproduced bug.
4. Investigate full-feature broad regression and fuel by relevant interactions (base/A/B/A+B where plausible). Keep all restored systems in the development line; do not silently discard them after first negative results. Version1 remains a strong comparator, not proof full integration cannot work.
5. Check rolling next-camp forecasts against executor banking after the first camp. This horizon repair is not yet implemented. Audit soak-cache keys (totalHP/state can alias redistributed damage or unseen respawn); suspicion only, not a reproduced defect. The suspected exponential ECON multiplier was checked and NOT found: A2_LAB resets baseline knobs each turn before X1_ECON; do not erase learned knobs as a speculative fix.
6. Prove chip mechanism's real competitive scope on relevant large maps/states before judging it. New truly unseen maps are necessary for transfer claims. Avoid unnecessary matrices; preserve exact maps, binaries, sources, effective config, engine, fuel, faults and native replay evidence.

## Portable evidence and exclusions

Exact original x1 Wasm SHA256:1746f2bb7fa341530f41bd8c8c4896b35172783f35eacee8e4a4b6ac0ceea183. Parent:22e6067a423356e29e6738438f47b22d05b554767757717e58bf350392e16b13. Frozen original source ZIP remains `research/botx3-20261102/original-x1-source.zip`. Version11 Wasm:84e34809200ea41b6ccb3ee13c9504e0bbcefc9742de2ea80ceecb91cfed1cce. Each release and all capsule files are hash-verified.

Campaigns retain manifests, rows, aggregate summaries, source snapshots, exact control/release binaries and build logs. Maps and four frozen opponents are included. Compact per-game receipts, screen results, runner logs and candidate output are compressed under `handoff-botx3-latest/game-receipts`, with an index. Selected native replay/diagnostic evidence is included. Bulk generated native per-game summaries/replays (many GB), installed toolchains, build caches and host executables stay local; regenerate targeted games using supplied exact inputs. The capsule overlays a normal repository clone; it is not a replacement for the base repository. Historical absolute paths are provenance, not paths to recreate on a new machine. The portable helper remaps map/research paths.
