# DOOMSDAY: 12-hour implementation mission

You are the implementation and testing agent on the team's strongest available machine. Build a substantially stronger Cambridge Battlecode 2026 bot for team DOOMSDAY. Deliver running C++/WASM, measured improvements, a fuel-safe path for the lightly trained RL policy, and reproducible supporting infrastructure. Do not finish with a research report, an architecture proposal, or an untested training script. Start implementing within the first hour; reserve the final two hours for integration and validation. Stop no later than 12 hours after your recorded start time.

The ambition is leaderboard dominance; the standard of proof is actual game performance. Never assert that dominance, an upgrade over v92, or a fuel fit has been achieved without measurements. Retain v92 when no candidate is proven stronger. A sound runtime and training pipeline plus a qualified candidate are valuable deliverables even if the early RL checkpoint is not yet competitive.

## 1. Authority, roles, branches, and coordination

Repository: https://github.com/Infosuii/neural-networkk-battlecode

The user explicitly wants building, experiments, current-game data collection/training and, when coordinated, site games. Your research can extend beyond the ideas below. Pick the highest-value implementable ideas rather than treating this prompt as an exhaustive list of permitted strategies. Spend at least 80% of the run on code, builds, data generation, training, experiments, and verification. Reading existing results is cheaper than repeating failed experiments.

JOHNDOE and Claude on R1shik123's machine are ideation/review collaborators with limited hardware. You are the compute owner. Do not ask them to run heavy training or duplicate your match batches. Agent 2's RL branch is a real existing source of work; it is not Claude's branch. The user's latest clarification is that RL is **only lightly trained**. Historical reports of older networks are context, not the current model's proven strength.

Coordination starts at https://github.com/Infosuii/neural-networkk-battlecode/issues/5 and the linked builder-dispatch issue. Read both descriptions and latest comments. Issue #5 has a strict existing two-party format: JOHNDOE/CLAUDE, per-sender increasing numbers, `re #n` for replies. Do not impersonate either collaborator. Post builder updates in the builder-dispatch issue, using `[BUILDER <unique-run-id>] <sequence> <topic>`; ask a collaborator to relay into #5 when necessary.

At startup post: start time in UTC, 12-hour deadline, hardware, branch, baseline SHA, intended file ownership, and first experiment. Use a unique branch `johndoe/qualifier-builder-<run-id>` from the pinned handover below, or a newer explicitly agreed baseline. Do not push to `main`, `build/z-plan`, `r1shik/z-plan-handover`, `agent2-neural`, or the prompt branch. Preserve submitted/frozen bots. Put your candidate in `bots/jd-<run-id>/src`; your tools in `tools/jd_<run-id>/`; small evidence in `research/jd-<run-id>/`. Import selected upstream changes into your branch; do not modify another worker's tree.

Post a `CLAIM <track> <paths> <base-SHA>` before taking a workstream. The dispatch issue is the ownership ledger. Check existing claims first. Only the accepted compute owner writes the candidate and runs its integration suite. Others offer patches/commit SHAs on their own branches. An overlapping claim requires an explicit handoff/ACK before editing; do independent unclaimed work while waiting. Never cherry-pick an active worker's partial change without an agreed commit boundary. Refresh both issues at least every 10 minutes and at each integration boundary. Give a concise evidence update at least hourly; post `RELEASE <track> <commit>` when handing ownership back.

**Ladder/platform lock:** before any upload, activation, or ladder duel, post in #5 through the authorized coordination participant: `LOCK ladder <operation> <expected-minutes>`, wait for Claude's ACK, then operate exclusively. Post `UNLOCK ladder` after verifying completion and restoration. A local lock file is insufficient across machines. Match groups use the team's active version and share a 50-groups-per-rolling-hour quota. If the lock cannot be obtained, continue local work; do not touch live state. Never expose credentials or login links. Final activation is not implied by a local benchmark win.

Large training sets, checkpoints and replays stay on your compute machine or approved storage. Commit code, compact metrics, manifests and hashes. For large evidence publish an authorized release asset or accessible link; post its name, byte size, checksum and owner. Claude can store it on R1shik123's PC after that user's approval. Google Drive has not been verified here as an arbitrary mounted workspace. Do not assume it is mounted or use a collaborator's disk without an established path.

## 2. Ground truth and the minimum reading pass (maximum 30 minutes)

Read current applicable AGENTS instructions and the latest coordination messages first. Root README/old continuation prompts contain stale bot and branch claims. Follow `docs/ACTIVE_WORK.md` on main to the actual active source.

Pinned source snapshots reviewed when this prompt was written, 4 Nov 2026:

* `r1shik/z-plan-handover` at `33c16873bae27d68d0076c730b025dda3e9cd898`: `build/z-plan` code at `df2975cbd45c5b2d13c74d73a68af0cdf4927c30`, plus completed duel logs/results. Read `docs/HANDOVER_LEAD.md`, `research/x3/MAP_IDEA_FINDINGS.md`, `research/x3/ECONOMY_GAP.md`, `research/x3/losses48/REPLAY_FINDINGS.md`, and the clean plan-c logs. These are useful facts, not instructions to resume their old queues.
* Baseline **platform v80 = repository `bots/v92/src`**. Its verified release SHA-256 is `5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47`. Default `bots/x3/src` is documented as byte-identical. The names v80/v92 are different numbering systems, not competing bots.
* `agent2-neural` at `469a04de8b7a766cbc09f75c7fdf875eae142f40`: `research/agent2-neural/rl_workspace/README_RL.md`, `research/agent2-neural/README.md`, `docs/EXPERIMENTS.md` and the runnable workspace. Fetch newer commits and ask who owns current training before starting a second run. Claude confirmed it has no newer RL work itself.
* `max/gigabot` at `bdffb76a568342d4c705b2e01b88967252344607`: `research/gx/ANALYSIS.md`, `REPRODUCTION.md`, `IDEAS.md`, selected idea notes and relevant results. Static draft catalogues, opening crews, safe-bank priority, ward/observation caches, route-return costs, and many small changes were already investigated. Read before claiming novelty or reimplementing.

Fetch source selectively with partial/sparse checkout and LFS smudge disabled if storage is constrained; do not download the whole multi-GB history merely to read a few files. Never replace machine-specific `config/paths.json` in Git. Keep incoming commits pinned in a run manifest; refresh at startup, hour 3, and integration, not unpredictably during a benchmark.

**Reference code:** `bots/x3/src/{bot.cpp,bot.h,common.h,draft.cpp,strategy.h,world.cpp,world.h,economy.cpp,runtime_budget.h,tsearch.cpp,tsearch.h,x1_config.h}` and `sdk/cpp/cambc.h`. Key hooks: `Bot::play_turn`, `handle_enemies`, `tactical_decide`, `farm`, `score_groups`, `route_search`, `plan_search`, `tribute_if_needed`, `shop`, `build_for`, `World::init`, shared-memory routines, and `play_draft`. Confirm symbols with search; line numbers move. Root `bot/src` contains an older neural framework and is not automatically the v92 production base.

**Engine/toolchain:** CAMBC CLI 4.0.0, engine 2.0.0 in this snapshot; verify current settings. Use official binaries. Build and evaluation runtime identity matters: native Mac builds once differed from Windows due to WASI libraries/paths, despite identical sources. GX documented reproduction using the correct WASI SDK 33 sysroot. Prefer the canonical baseline WASM; record compiler, sysroot, flags and source digest. If your local baseline hash differs, explain and establish a new measured control before comparing changes. Do not disguise a toolchain change as strategy gain.

## 3. What the evidence actually says

### Established baseline and failed shortcuts

On the clean pinned 120-game plan-c suite, v92 won 57; pack opening pf10 52; early bank pf4 51; progressive expansion pf9 51; audit bundle 47; blanket pack play pf13 29. The Vesper-only draft arm was stopped and regressed locally. Earlier vision/raid/stat-fighter results included startup-fuel defects; some older arms were contaminated by concurrent uploads. Keep those evidence classes separate.

Local counter x3ctr won 171/172 against v92 but did not show a decisive ladder improvement. Map-fit x3mf2 likewise did not beat the paired ladder baseline. A no-op code change can flip 4–7 of 172 games because fuel affects later decisions. More repeated deterministic games are not more independent evidence. Repeating one pairing with invented seeds is not a confidence boost unless the engine or bot actually consumes that seed.

Agent 2 E108 found baseline v92 already as efficient as or better than its simplified solo-farm scheduling model. E109's coarse combat model recommended some wrong policies. E111's promising learned lineup model lost in real games. Therefore do not build a new large approximate simulator, blindly copy top-team lineups, or perform an enormous knob search against one familiar bot. Reuse the actual engine for labels and validation.

### Map features, routes, movement and harvesting

The bot-side atlas matches 86/86 recorded pool maps. It measures dimensions, physical bodies, resource distribution, obstacles, reachable groups, walking distances, own/contested/enemy-side shares, harmless versus dangerous camps, jackpot concentration and altar access. The 7 category rules are coarse summaries (silhouette about 0.15), not seven proven optimal strategies. The older offline mirroring approximation disagrees on 21 maps; use bot/engine-derived features. Maps may store an authored half; verify symmetry, mirrored overlaps, connectivity and dash-only routes.

Geometric shortest paths are not optimal farming routes. A route must account for live/respawning camps, clear time, incoming camp damage, capture, allies' opportunity cost, enemy interception, carried gems, banking and purchases. A greedy-looking path can earn more while a safer-looking banked/collected ratio hides less total income. Optimize match wins and time to 1,000 banked gems, with diagnostic economics underneath.

The current-loss replay study shows winners' first camp was often **later**, and we sometimes cleared more camps early. Do not optimize first capture alone. In the 898-loss study, winners vs us: opening grouping 68% vs 57%; workers per camp 1.72 vs 1.44; allies at first contact 2.14 vs 1.74; first-contact health 89% vs 85%; late clears 17.39 vs 11.09. They gradually expand from 83% to 70% own-half time; we remain around 86% to 83%. On C1 late clears were 22.49 vs 9.79; on C4 23.43 vs 7.30. C6 is an instructive exception: we farmed more and still lost. Diagnose per category and opponent, not a universal pack rule.

In one separate early duel-loss comparison, gold at round 150 was 440 vs 591 before deaths. In a 234-game economy analysis, loss-side gold earned at round 600 was 1,530 vs 2,367, and at 1,000 2,282 vs 3,904. Do not confuse gold held from the replay tables with gold earned in these tables.

Top opponents in our loss sample ward 2–3 times as much, bank 50–290 rounds earlier in several categories, buy more Bruiser/Treasure, recall more, and take our camps later. Vesper appears in 66–84% of winners' lineups. These are **conditional observations from games we lost**, not causal proof or an unbiased census of all elite play. Blanket item swaps, grouping, early bank, invading and Vesper drafting have all failed. Find the mechanism and compatibility with our policy.

### Fights and knowledge limits

46% of our deaths in a duel sample had no hit back, versus 36% for opponents. Agent 2's small 64-scenario staged micro pilot found v92's selected move no better than the average legal option. That supports a tractable micro improvement, not a claim that every real fight is random. Older notes saying micro is not the gap are hypotheses contradicted in part by this newer pilot; check actual trajectories.

A death loses uptime and can transfer the whole bag plus gold. Evaluate fighting as its effect on future team economy, territory, and race time, not damage dealt alone. Melee and ranged action ordering differ; stuns interrupt channels; some champions are stun immune; movement-exclusive abilities and dashes need exact engine semantics. Do not use Lanchester's law as an exact fight simulator.

## 4. Mandatory first deliverable: production fuel contract

The user specifically wants smart use of **10,000,000 fuel initially** and **200,000 on the first gameplay turn**. The SDK comment at `cambc.h:5409` says first **draft** turn is 100x and each champion's first turn 2x. With the documented 100,000 base, that means:

| Phase | Nominal fuel | Use |
|---|---:|---|
| First draft turn | 10,000,000 | Public static analysis, bounded draft/opening planning, compact plan serialization |
| Later draft turns | 100,000 | Update roster/picks and compact plan without recomputing everything |
| Each physical champion's first play turn | 200,000 | Decode plan, essential local world state, useful first action, bounded initialization |
| Ordinary play turn | 100,000 | Observe, choose and execute; optional work only behind measured admission |

The 10M allowance is not 10M for every body or every turn. Older handovers say 10x; verify actual phase-entry fuel in the current engine using a tiny diagnostic. Also verify the lifetime of draft instances, memory across picks, first-turn semantics after respawn, and host-call charges. Record findings in a small machine-readable contract. If the runtime differs, adapt using observed settings and report it.

Build a governor around **whole-turn worst-case reservations**, not only neural matrix cost. Account for observation extraction, claim decoding, inference, fight/move execution, world refresh, distance fields and tail work. Reuse/extend `runtime_budget.h`; it already exists. Admission checks use unsigned-safe arithmetic and retain a legal, coherent fallback. Chunk/cap expensive loops. Publish caches only when complete; never label a partially built field as unreachable or valid. End the turn deliberately before fuel suspension.

Measure stage p50/p95/p99/max by map size, group size, body, contact state and phase; in-game WASM fuel is the constraint, not host milliseconds. Sample diagnostic logging outside hot decisions and compile it out of the scored build. Report the profiler's perturbation. Use matched executable/data controls where feasible; a neutral hook changing fuel is not identical to v92.

Aim for no new fuel-outs and zero faults. The baseline itself already suspends on some maps (Claude reports 160/172 in one self-play run; other opponent suites differ). Never impose or fabricate a zero baseline. Record baseline events and demand no additional candidate-induced suspensions, especially startup/contact/channel turns; eliminate old ones when practical. Final promotion also depends on wins, not fuel counts alone. Fuel savings are enabling infrastructure, not a proven strategy advantage.

Precompute what is static in draft, reuse it at runtime, and build other static local fields on calm/dead turns. A 1,024-byte draft buffer cannot carry all-pairs paths or a full 100x100 distance field. Encode useful summaries, route landmarks, roster roles, compact opening assignments, a group dictionary if needed, and model-context features. Validate each cache and keep native fallback on overflow/unknown maps. Do not assume initial static WASM globals transfer from the draft VM into gameplay VMs.

## 5. Mandatory memory work: make 8 shared bytes and 1,024 draft bytes useful

Audit actual compiled configurations and every reader/writer before designing a protocol. Add a schema document and executable round-trip/transition fixtures. Preserve the baseline schema until the replacement proves useful.

**Current shared layout, from `bot.h` and `bot.cpp`:** six 7-bit claim slots, bits 0–41; sighting x bits 42–48; y bits 49–55; round modulo 64 bits 56–61; distress bit 62; event discriminator bit 63. Cassi + Issac can create a sixth physical body, so a nominal 5-pick team does not imply a spare slot. Idle=127, dead=126; low-group on-site encodings start at 64 for at most 48 groups; fight orders also occupy special codes. Respawn events reuse the mailbox with a 7-bit group and an 8-bit modulo-ready round. A nearby comment wrongly says 8-bit claims; the compiled constants are 7.

Answer with code/tests: What is a claim promising—heading there, fighting, capturing, or merely remembering it? When fleeing, banking, recalling, dead, respawned, displaced, or reassigned, is that promise still valid? What happens to an unchanged stale claim? Do off-screen intentions mean actual presence? Is modulo-64 sighting age ever mistaken after inactivity; can modulo-256 events become phantom future respawns? Do group IDs collide with reserved codes on the largest maps? Are read-modify-writes based on the latest host word? Does turn order or dynamic priority invalidate slot-based coordination? Preserve unrelated fields on every write. Never clear the whole word to send one message.

Prefer a compact decentralized protocol over a per-turn centralized global planner. Use draft data for shared static role/job dictionaries; shared memory for current intent, urgency, completions or a high-value short-lived event. Only consider multiplexing spare slots after proving the actual body count and active schema. If introducing epochs, leases or intention codes, specify bit allocation, representable IDs, TTL/wrap rules, reader fallback and cost. If all desired bits do not fit, drop low-value information or use a versioned dictionary; never silently alias an unrepresentable group to another claim.

**Current draft uses:** `strategy.h` brain header at bytes 0–5 (magic 0xA5, team size, enemy casters, map class, max-group gems and flags); optional ML plan byte 7; optional A2_DPLAN starts at byte 8; optional economy roster occupies 1008–1015. Inventory all other consumers. `A2_DPLAN` exists, defaults off, and its simple model was not a demonstrated upgrade. Certain draft paths pick and return before the later plan/header block—test every active path before claiming your precomputation runs.

SDK `draft_memory` is a **startup snapshot**. Assignment submits a prefix to the host but does not mutate that snapshot; shorter writes preserve remaining host bytes and oversized writes truncate. Later merging from a stale local snapshot can overwrite another section. `economy_record_roster` already demonstrates reading current host bytes to preserve this turn's plan. Use an explicit versioned buffer owner/merge routine with reserved regions, lengths and validity checks; do not independently write a 1,024-byte zeroed buffer from multiple paths. Test first/last picks, all team sizes, Cassi/Issac roster expansion, absent/corrupt/truncated payloads and map mismatches.

Production policy receives only legally available information. No shared vision means no omniscient ally positions/health or enemy inventory inferred as fact. Carry explicit missing/stale masks. Draft-visible champion types can remove avoidable unknown-ally type guesses; verify mapping from draft picks to gameplay body slots in the engine. Training critics may see privileged state, but exported actor features and deployment must not.

## 6. Main build track: make the lightly trained RL implementation usable

Do not restart an entire neural project. Inspect Agent 2's runnable workspace, current branch updates, checkpoint/config, feature version and actual training owner. The historical workspace supports 500-feature layout 2 and 828-feature layout 3, target/bank/options, PPO, DAgger and distillation. These are historical interfaces until confirmed against current code. Save the lightly trained checkpoint unchanged and produce an initial behavior/fuel benchmark. No checkpoint is accepted merely because a README calls it best.

Historical teacher (~186k parameters) used about 2M fuel/turn; smaller student (~28.6k parameters) and `A2_NN_FAST` were the proposed runtime path. Reports used `--fuel-quantum 20000000` for both sides. Such results are not deployable results. `A2_NN_FAST` being present is not proof it compiled, ran, or met fuel. Build it, inspect WASM instructions, test it at official fuel. Avoid running the expensive teacher every turn merely to obtain a fallback choice before overriding it.

Implement a clean model adapter with these contracts:

1. **Feature ABI:** version, order, normalization, clipping, missingness, entity masks, camp-slot-to-group mapping, stable handles/roster slots, history reset rules and cached static features. Golden observations exported from C++ must agree with training preprocessing. Never silently attach a layout-3 header to layout-2 code.
2. **Action ABI:** legal candidate masks; KEEP_BASELINE plus camp target, BANK, HOME, REGROUP and other supported options. Model intents flow through legal v92 executors; they do not bypass channel, combat or movement constraints. Default/disabled models reproduce the agreed control behavior. Unknown model versions disable themselves cleanly.
3. **Decision events:** infer on completion, invalidation, meaningful threat change or bounded periodic replanning—not blindly every round. Maintain commitment, progress and maximum duration; interrupt immediately for safety or a race-winning bank. Measure target thrashing and option durations. Preserve baseline combat during first macro integration.
4. **Compute envelope:** static encoding cached once; dynamic features built once per observation only for relevant entities; dead/masked entities cost little. Evaluate only used heads. Try int8/int16 quantization, WASM SIMD where supported, compact encoders, lookup/cheap activations, reduced top-K and sparse invocation. Choose by measured end-to-end fuel and held-out policy quality, not a preferred technology. Quantization must test overflow, saturation, output agreement and changed actions, not only average logit error.
5. **Fallback:** illegal target, stale observation, low fuel, OOD/missing context, untrusted model version, failed confidence gate or interrupted commitment returns to a valid cached/cheap baseline path. Do not compute the full teacher and full student plus every v92 scoring layer on the same turn by accident. Confidence gating needs calibration; entropy alone is not a safety certificate.
6. **Export pipeline:** checkpoint -> architecture manifest -> deterministic weights/header -> clean release WASM -> real-fuel test. Record model/source/compiler/engine hashes and exact enabled heads. Zero lab control, sampling or debug exports may change release behavior unnoticed.

Provide a one-command smoke path and a resumable training/evaluation driver. Reuse Agent 2 scripts before writing replacements. Remove Windows-only assumptions only where needed; do not spend half the run porting a whole lab. Calibrate CPU workers, RAM, GPU and I/O for this machine, keep resource headroom, batch data/rollouts, and avoid builds racing over the same output directory.

**Current-game data is authorized:** use current engine 2.0.0 official/generated-map games, available current replays, and local states. Historical 1.0.3 data must be labeled and cannot substitute for current rule labels. Treat authentic ranked/unranked version provenance carefully; listings may not identify our bot. Split by match/map/opponent/update-time so adjacent turns from one game do not leak across train/test. Store data lineage, feature/model versions, masks, options, durations, rewards, terminal flags and behavior-policy probabilities for PPO.

Prefer DAgger/on-policy aggregation to pure offline cloning when the actor visits new states; training accuracy was previously high while deployed targeting collapsed. Use team terminal win as the final objective, with conservative shaped economics and potential differences if needed. Do not reward endless camping, gold hoarding, recall loops, fabricated deaths avoidance or collectible gems that never bank. Respect semi-Markov option durations in returns/discounting. Centralized privileged critics are training-only; the actor stays decentralized. Validate action masks, log-probabilities, stale rollout versions, truncation/termination and checkpoint resume before a long PPO run.

Coordinate with the existing training owner. If they are training, give them the fuel-safe actor/export path, feature fixtures and evaluation runner; do not launch a competing rewrite. You may train/distill on your hardware when ownership is clear. Keep relaxed-fuel teacher data generation separate from official-fuel deployment evaluation. Training data must include the *deployed* inference cadence/fallback state distribution; a successful every-turn teacher need not remain successful when invoked every ten turns. Lightly trained policies start as small residuals, with KEEP initially dominant; release trained heads only after their individual gates pass.

## 7. Independent strategy track: practical improvements beyond RL

Work on at most two major new mechanisms concurrently. Default priorities are contact-action quality and contested harvesting; change priority if fresh evidence shows a larger tractable defect. These are hypotheses, not commands to enable another unproven bundle.

### A. Contact movement and action ordering, using real-engine labels

Reuse Agent 2 `micro_lab.js` / fight counterfactual tooling. Collect representative current-engine contacts from actual games: solo and outnumbered fights, heavy camps, carriers, altar approaches, bushes, choke points and each played champion kit. Include raider/contested opponents, not just v92 mirrors. Preserve realistic HP, items, cooldowns and visibility.

For each state, compare a small legal action set in the real engine: v92's action, hold/attack, approach, retreat, lateral step, useful cast timings and targets. Branch short 5–15-turn continuations, with a longer sample for deaths/escape/territory consequences; vary opponent continuation policies and small state perturbations to reject a brittle one-opponent trick. If exact state restore is unavailable, reuse/replay a validated prefix; first prove branch reconstruction matches the reference continuation. Never invent accurate simulation semantics.

Fit a tiny action-value/ranking residual or small rules from these labels. Include body counts *and reachable arrival times*, escape route, bag value, current kit, cooldowns, camp aggro and support. Penalize giving away a carrier and lost 60-turn uptime. Prefer a conservative advantage over KEEP rather than a full replacement. Check hit-before-retreat where legal, ranged walk-or-hit, stuns/channel interruptions, dashes and cast exclusivity. Counterfactuals may use full state as an offline oracle; the actor cannot.

First deliverable: a compiled, bounded contact selector with held-out counterfactual regret, lethal/illegal-action tests, and whole-game comparisons. Require it to change the intended behavior. Lower deaths alone is insufficient if the team gives away all camps. Keep it off if it does not improve games under official fuel.

### B. Harvesting as a contested delivery problem, not fixed grouping

Model a small shortlist of **jobs**: clear/capture a camp, help a high-value nearby crew, finish/escort a valuable deposit, heal/shop, intercept or deny when clearly profitable, or move to a safe reachable resource. Retain v92's exact movement and executors initially. Rank incremental *team* value above each participant's alternative, including travel, wait, fight/clear time, capture, health/heal trip, purchase spike and expected safe banking. Do not count a reward twice across helpers or hand off a capture before a recipient arrives.

The new mechanism must add what E108's failed solo scheduler lacked: enemy pressure, interruption, local safety, useful timing and opportunity cost. A helper joins only when synchronized extra throughput/survival exceeds the farm it abandons; it leaves once no longer useful. Learn/measure actual service time and survival from the real engine, not a uniform DPS constant. Camps hit nearest targets: test tank/DPS spacing and safe rotation as mechanics, without dragging a tank out of its better job. Preserve ongoing captures, recall/tribute commitments, and a high-value safe plan when optional replan is skipped.

Compute cheap route landmarks and reachable jobs in draft/initialization. In play, update only affected costs and shortlists when camps finish, claims change or threats appear. Use a bounded receding horizon for a few options, or a learned value of the option, not full-map combinatorial search every turn. Gold value depends on time to purchase/use before the race ends; gems depend on delivery probability and race urgency. A bag transfers on a kill: avoid treating death as just lost carried value without the opponent's gain. Calibrate terms offline rather than asserting an exact universal conversion rate.

Bank at an already safe altar or for a genuine team finish when beneficial; do not blindly lower every bag threshold. A team-win estimate based on off-screen ally bags may be illegal/stale: use legal confirmed data, uncertainty and existing memory constraints. For defense, respond to observed invasion/style rather than guessing a team name from a common lineup. Routing through enemy camps should be conditional on actual safety/opportunity, since removing the home discount previously lost 16 local games.

### C. Opportunistic smaller mechanisms

Use targeted probes if cheap: camp area-cast geometry/multi-hit, wake-up side effects, capture ownership/payout and Prospector interactions, camp-timer age, ward value without duplicate world refresh, static siege cache completion, recall/teleport purchase economics, finish-bank priority, champion-specific drafting combined with correct items/micro. Read GX and audit notes first; many exist already. A complete audit-fix bundle lost, so test defects separately. Do not add all switches because their prose sounds correct.

Draft experiments should be small conditional alternatives with the relevant champion executor/item support, not a universal Vesper priority. Map identity may be an input for known maps, but use continuous geometry/resource features and a conservative unknown-map fallback. Do not mistake trajectory memorization on one opponent for a robust counterstrategy. Public replay analysis is valid; no platform exploits or hidden information in the actor.

## 8. Experiment infrastructure and promotion gates

Build a single experiment runner around existing tools, with isolated builds, immutable candidates, manifests, timeouts, resume and machine resource limits. Reuse `tools/dz.py smoke`, `tools/x1_gate.sh`, `tools/mapatlas/behaviour_check.py`, `tools/replay/*` as appropriate; read `--help` before assuming old wrappers' default opponents/maps are current. A historically named gate may still point at x2 and obsolete maps. Do not silently skip missing suites and call the gate complete.

For each run record: git source SHA, diff/flags, candidate/opponent WASM hashes, engine/SDK/toolchain, fuel quantum, map bytes/hash, side, true randomness inputs, duration, winner/tiebreak, banked/collected/stolen/lost gems, gold earned versus held, deaths, camp clears/timings, invalid actions, faults, fuel-out counts and rounds. Count played, missing, failed and excluded games. Use fresh output names and reject stale result files. Build once, freeze the artifact, then evaluate it. Compare baseline and candidate against the same opponents/maps/sides.

Use three levels:

1. **Conformance and behavior:** small mechanical fixtures plus 12–20 varied heavy/current maps, both sides. Verify memory/policy ABI, action legality, changed behavior and phase fuel before wide scoring. If the mechanism never triggers, a win fluctuation is not evidence for it.
2. **Screen and selection:** a declared development map set and diverse frozen opponent set, including v92, the invader x3inv, other lineages/archetypes and the available b5_c3/v61_c3 held-out resources. v81/x1 are inflated in familiar v92 fits. Rotate discovery opponents without contaminating the final set. Measure intended diagnostics, but select on matched wins/race performance and catastrophic regressions. Stop a mechanism after two sound revisions without a credible gain; switch to the next tractable one. Do not optimize a fixed 20-map screen for ten hours.
3. **Frozen confirmation:** unseen generated maps from fresh seeds, held-out opponents and all current official maps with both sides. Respect any previously locked final partitions; do not reuse a final set to tune then call it unseen. Use several hundred unique matched map-side/opponent cells at minimum; on a strong machine target at least 1,000 matched baseline/candidate cells across the diverse suite for finalists if throughput allows. Report exact counts, map/opponent strata, paired deltas, draws and map-clustered uncertainty. Related bots and maps are correlated. Small C6/C7 samples do not justify aggressive category-specific policies.

Freeze no more than three finalists for the final holdout. Compare v92, runtime-only, RL-only, micro-only, relevant macro-only, and chosen combinations where actually implemented. Rebuild every final package from clean source and repeat a small reproduction sample. A strict zero-weight/data-only control is useful; measure if it really preserves actions/outcomes instead of declaring it neutral.

Candidate promotion requires zero new faults/illegal actions, a safe measured fuel envelope with no newly introduced suspension failure mode, a positive broad paired improvement with reported uncertainty, and no unexplained severe opponent/map collapse. A 55% win rate directly against v92 is an aspiration, not sufficient proof or a reason to reject a general ladder improvement. If an aggregate suggests gain but the independent holdout is inconclusive, label experimental and keep v92 recommended. Never claim leaderboard superiority from self-play.

If a platform duel is authorized and the ladder lock ACK is obtained, use clean pinned opponents (`--source-group`), one upload pipeline, active-version checks before/during/after arms, shared quota accounting and a pinned v92 rerun for drift. Claude flagged `finished_groups()` only paginates 20x100 groups: inspect/fix pagination before trusting the report. Discard contaminated arms. Read-only platform downloads do not consume the ladder lock, but authenticate normally and obey rate limits. Restore the agreed live baseline before unlocking unless an explicit handoff says otherwise. Do not bypass a platform submission pause.

## 9. Twelve-hour execution clock

Use measured throughput to scale batch sizes. These are maximum time allocations, not excuses to idle:

* **0:00–0:30:** claim role/files; read compact evidence; pin baseline/engine/latest RL; measure machine; start real baseline games; probe phase fuel and memory semantics. Publish the run manifest and a short chosen implementation list.
* **0:30–1:00:** compile the first functioning change and run conformance. Ship the initial adapter/governor/memory fixtures or a targeted contact improvement. No more broad reading. Establish RL owner and model ABI.
* **1:00–3:00:** implement the fuel-safe RL actor path and export/golden fixtures; start representative current-engine data generation and the first independent strategy experiment. Verify student inference under real fuel before treating a training run as deployment progress.
* **3:00–6:00:** improve the best mechanisms from measured failures; do bounded distillation/training if you own it, otherwise supply the trainer with the runtime/data contract. Run diverse screens and compare behavior. Integrate upstream only at a frozen boundary. Keep one strong fallback.
* **6:00–8:00:** spend compute on the strongest two ideas, model compression/cadence and robustness, not a new major architecture. Create a short finalist list. Queue a coordinated paired platform trial only if allowed and time/quota permit; local evaluation continues otherwise.
* **8:00–10:00:** ablate, fix concrete defects, freeze final candidates and begin independent confirmation. Stop tuning on the final data. Save checkpoints before long tests and leave enough time for clean rebuilds.
* **10:00–12:00:** official-fuel full validation, evidence capsule, code cleanup only when needed, source/WASM/package hashes, concise handoff, pushes and ownership/ladder release. Hard stop at 12 hours. A large unfinished training job is not the final deliverable.

If setup or credentials are blocked, finish unaffected local source/runtime work. If exact legacy reproduction needs more than 30 minutes, freeze and document the canonical artifact/new control and proceed with a valid comparison rather than silently changing conditions. If no candidate is stronger, provide the functioning infrastructure, tested candidates and negative results; recommend preserving v92 honestly.

## 10. Required outputs and definition of done

Push to your unique branch:

* A buildable candidate under `bots/jd-<run-id>/src`, with useful changes enabled only where validated; immutable v92 retained.
* Fuel/memory/model contracts, fixtures and a real-budget benchmark. Include shared/draft layouts and a demonstration that all body slots can recover their correct role/intent without hidden state.
* A reproducible record/train/distill/export/build/evaluate path; preserve the lightly trained checkpoint and publish any new checkpoint's lineage. Mark `working`, `measured`, `untrained/lightly-trained`, `experimental`, and `release-qualified` accurately for each component.
* `research/jd-<run-id>/RESULTS.json`, a compact experiment ledger, exact run/reproduction commands and artifact manifests. Summarize rejected ideas to prevent future repetition.
* A source-only submission archive made by the correct official packaging procedure, within the current upload size limit, with no secrets, caches or accidental training dumps. Produce it if a candidate is ready; do not claim it was uploaded if it was not.
* `HANDOFF.md`: strongest tested bot, baseline and model hashes, measured improvements and limitations, completed tests, whether ladder-tested, live version/lock state, outstanding work and one exact next command. Post links and hashes to the dispatch issue; relay key findings to #5.

Begin now: check the coordination ledger and claim your branch, reproduce one baseline build/game, and write the first implementation. Use strong offline compute to discover and learn good decisions, then deploy them through a cheap, legal, bounded runtime. Build, measure, revise, integrate, and leave the team with something it can actually run.

## Evidence and reference index

Repository evidence (paths above are pinned to these snapshots):

* Handover/duels/code: https://github.com/Infosuii/neural-networkk-battlecode/tree/33c16873bae27d68d0076c730b025dda3e9cd898
* Agent 2 RL workspace: https://github.com/Infosuii/neural-networkk-battlecode/blob/469a04de8b7a766cbc09f75c7fdf875eae142f40/research/agent2-neural/rl_workspace/README_RL.md
* GX reproduction and failed experiments: https://github.com/Infosuii/neural-networkk-battlecode/tree/bdffb76a568342d4c705b2e01b88967252344607/research/gx
* Current official platform/docs entry: https://2026a.battlecode.co.uk/game/docs (consult accessible current rules/settings; this prompt's site recheck was unavailable, so its detailed semantics are grounded in the repository SDK and engine experiments).
* DAgger primary paper: https://proceedings.mlr.press/v15/ross11a.html — use on-policy state aggregation to address compounding imitation errors, not as a promise of game gains.
* PPO primary paper: https://arxiv.org/abs/1707.06347 — reuse the existing PPO implementation and validate its data/likelihood contracts before extending it. No new literature survey is needed.
