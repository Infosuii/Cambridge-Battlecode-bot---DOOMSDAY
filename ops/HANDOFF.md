# Handoff: bot development from v52 onward (read this first)

Written by Claude Code on 2026-10-25, when development was paused at v53. The next agent (GPT/Codex) works on **another device** and should set it up with `ops/SETUP.md`. Everything needed to build, test, analyse and submit is in this repository. Only bulk training data stays on the original laptop, the "training box" (§7), and none of the next steps need it.

## 1. Goal and standing approvals

- **Goal:** the user wants an "unbeatable" bot. The measurable target is ladder top 25; team **DOOMSDAY** (team id `fcf5f666-ea55-4da0-b8d4-97c64bb37236`). Original snapshot: rank 87, rating 1834. Latest saved 2026-10-25 13:34 UTC snapshot: rank 78, rating 1848.9; this is not attributed causally to v53.
- **Approved by the user (2026-10-25):**
  - queueing unranked match groups against top teams;
  - multi-hour CPU/GPU training runs;
  - submitting a new version **once it passes the gate** (§4).
- **Credentials:** never log in or enter them. The user logs the CLI in on each device (`ops/SETUP.md` §2).

## 2. Versions

Sources are in `bots/`; `src/` is exactly what `cambc submit` uploads. Each version's `CHANGES.md` has its measurements.

| Version | Platform | Content |
|---|---|---|
| v48 | - | heuristic lineage; draft net and danger net on |
| v50 | version 50 | v48 lineage plus a camp net (321 parameters, about 3 hours of PPO; `training/v50-campnet/`); danger net off |
| v51 | version 51, submitted 2026-10-25 11:29 UTC | v50 plus the moated-island fix (champions froze at camps behind two-tile hole moats: big_world, islands) |
| v52 | version 52, submitted 12:02 UTC | v51 plus the sole-gem-camp rule (stampede) |
| **v53** | **version 53, submitted 13:08:26 UTC, live** | v52 plus once-per-call open-job scan hoist; `A2_GATE_JOB 0`, `A2_SOLE_FROM 500`. Development 87/168, -2.1; aggregate holdout 39/72, +5.3; zero faults. |
| **v54** | **version 54, submitted 16:24:00 UTC, live** | v53 plus crew-job coordination, item milestones, lead lock, teleport shortcuts (§12). vs v53: development 109/168, +149.0; 12 seeds 443/672, +187.1; holdout 41/72, +30.8; zero faults. |

`artifacts/baselines/heuristic-v1` is the frozen local baseline from the same lineage; do not modify it.

## 3. Findings (do not relearn)

1. **One heuristic codebase.** v48, v50, v51, v52 and heuristic-v1 differ by only a few hundred lines. Neural parts:
   - draft net (`A2_MLDRAFT`);
   - camp net (`A2_CAMPNET`; its extra 2 hours of training gave no reliable gain);
   - danger net (v48, `UB_DANGER`).

   In 56-game local A/B tests none had a measurable effect. The policy-v2 network, trained by behaviour cloning on 7.3M top-team decisions (`tools/policy_bc.py`, `artifacts/claude_ops/NIGHT_REPORT.md`), learned nothing useful in games: 0 gems, 0-12 against heuristic-v1. Do not revive it.
2. **The bot runs at its fuel limit, and that dominates evaluation.** The engine is deterministic.
   - A behaviour-identical change that added a few instructions in hot code (`open_call_by_lower` and the group-scoring loop) lost **70-98 with a -85 gem margin over 168 games**.
   - The same no-op in a cold path played identical games.
   - Fuel is also charged for memory fills (1 per byte, per a comment in `bot.cpp`).

   Rules that follow:
   - Put new logic behind a check that runs once per call or once per turn, never inside per-group or per-camp loops.
   - Making hot paths cheaper is probably the strongest untried lever.
3. **Ladder losses are map-specific.** These are the 800 ranked games before v51 (`data/ladder/doomsday_ranked_800_20261025.json`, analysed with `tools/replay/ladder_report.py`); overall 51%.

   | Map | Record | Status |
   |---|---|---|
   | stampede | 0/28 | v52 fix |
   | big_world | 0/26 | v51 fix |
   | boss_battle | 1/16 | open |
   | islands | 3/25 | v51 fix |
   | concentrated_wealth | 3/21 | open |
   | elkring | 7/24 | open |
   | swirl | 6/19 | open |
   | monolith (holdout) | 6/18 | open |
   | fracture (holdout) | 5/13 | open |
   | yellow_brick_road | 9/23 | open |

   Most other maps are at 50-86%. Early ladder after v51: 14/20 (70%), with none yet on the target maps.
4. **stampede (fixed in v52).** One group holds every gem (20 monsters, 16,080 HP, 160 gems). Big-job calls never filled, so the camp was never attacked.
   - Fix: `A2_SOLE_GEM` at the top of `score_groups`.
   - Result: stampede 6-0 locally at every tested start round, banking about 870 gems against v51's 100.
5. **boss_battle (open).**
   - The altars' only access tiles are monolith camp tiles: group 16 at (24,20), 2 members, 400 gems, 600 gold, strength 200, range 5, 20,000 HP. Banking opens only while that group is dead. See `A2_ALTARFIX`, `no_bank`, `altar_gated`, `gate_camps` and `World::update_altar_gates`.
   - Our carriers hold 170-570 gems each from round ~900 and never bank. Even v52 against v52 collects about 2,500 gems but banks only about 300. Top teams bank first at rounds 645-1,100.
   - Rushing the gate with the whole team (v53 `A2_GATE_JOB`) gets the team killed.

   Next ideas:
   - decode top teams' winning boss_battle replays to see when and how they kill group 16 (draft, items, timing);
   - take the gate only late, with full items, as a whole-team job;
   - change the boss_battle draft, which is fixed to types 3, 5, 9, 11 (`APEX_MAPDRAFT`, `draft.cpp`).
6. **Methodology for map bugs** (it found the v51 and v52 bugs in about an hour each). Reproduce the bug with a logging build (§5), look for champions whose position or mode never changes, find the code path, and fix it cheaply.

## 4. Measuring and the gate

- **bench v3:** `bash artifacts/claude_ops/bench3.sh <abs cand dir> <abs opp dir> <abs out prefix> [seeds]`.
  - It plays the 28 development maps × both sides × `NOVA_SEED` 1-3, rebuilding both bots per seed (the shipped bots use seed 1): 168 games.
  - Single maps: `MAPS_OVERRIDE="00stampede" bench3.sh ...`.
- A non-zero exit, any faults, or fewer than `2 × maps × seeds` games invalidates a run.
- Compare candidates with `python tools/bench_compare.py <prefix A> <prefix B>`. Retain a mechanism only when its map-clustered 95% interval is above zero against the base it modifies; do not use the naive per-game standard error.
- **Gate** for a new version against the live one:
  - (a) Every target map is won on both sides across seeds, by a clear margin.
  - (b) Overall win rate ≥ 0.47 and margin ≥ -30. This is the noise floor: the behaviour-identical control scored 0.417 and -85.
  - (c) No regression on the 12 holdout maps (`HOLDOUT=1 MAPS_OVERRIDE="<the 12 final maps>" bench3.sh ...`). Run them once per release.
  - A map whose six games mirror the opponent's exactly (A-side margins = -B-side margins) is untouched by the change.
- **Other tools:**
  - `tools/bot_match.py`: any two bots; the default opponent is heuristic-v1.
  - `artifacts/claude_ops/bench3.sh`.
  - `tools/match_stats.py` and `tools/bench_summary.py`.
- **Results so far** are in `artifacts/claude_ops/results/*.txt`:
  - `b2-v52a-vs-v51`: 83-85, +6.7;
  - `b2-holdout-v52-vs-v51`: 36-36, +29.6;
  - `b2-noop-vs-v51`: the noise floor;
  - `bb-gate*`: the rejected gate rule;
  - `st-sole*`: the stampede sweeps.

## 5. Diagnosing a map (logging build)

1. Copy the bot and prepend `#define APEX_LOG 1` to `src/common.h`.
2. In `src/world.cpp`, change the per-turn GROUP dump's `if (APEX_LOG)` (near line 179) to `if (0)`. Leave it on and run 2 rounds when you want the camp-group list.
3. Build with `engine.official_build(dir, out.wasm)` (python `nfs.engine`) or `cambc build`.
4. Run `cambc run <a.wasm> <b.wasm> --map maps/local-benchmarks/<map>.map26a --rounds 600 --release --log-limit 16000000 --out-dir <dir>`.
5. The `.repl26a` output is a ZIP. Unzip it and run `strings` on `team-a.stdout` / `team-b.stdout`.

Champion lines look like `R<round> <type> p(x,y) hp g<gems> $<gold> <mode> G<group>`. There are also `BIG`, `DUO` and `MODES`/`DIAG` lines every 50 rounds.

## 6. Ladder and platform (needs the user's CLI login on your device)

- **Recent games:**
  - `cambc matches list --team me --kind ranked --json` (paginate with `--cursor`);
  - `tools/replay/ladder_report.py --matches <json> --ladder <ladder json>`;
  - `tools/replay/track_submission.py --since 2026-10-25T12:05:00Z --maps 00stampede 01big_world 01islands` for results since v52.
- **Replays:** `cambc matches download <match id> -o <file>` gives a ZIP with the replay and our team's logs. Decode it with `node tools/replay/decode_replays.mjs --out <x.jsonl> <replay.repl26a>`. Local replays are also ZIPs; extract `replay.repl26a` first.
- **Standings:** `cambc ladder --json --limit 100 --page N` (snapshot: `data/ladder/ladder_top400_20261025.json`).
- **Match groups** were queued 2026-10-25 around 12:15 UTC with v52 on stampede, big_world, islands, concentrated_wealth and elkring, against Hidden Altar Keepers (#80) and meow (#25). Their ids are in `data/ladder/match_groups_20261025.json`. Read them with `cambc match-groups show <group id> --json` or `cambc match-groups download <group id>`. New groups: `cambc match-groups create <team uuid> --maps a,b,c,d,e --sides a,b,a,b,a`. Match groups play our **currently submitted** bot.
- **Submit:** `cambc submit bots/vNN --note "..."`, only after the gate passes.

## 7. Data

- **In the repo** (`data/ladder/`, see its README):
  - top-400 ladder snapshot;
  - our last 800 ranked games, and our games since v51;
  - compact Bradley-Terry ratings (743 teams, 244,981 matches);
  - 46 decoded bad-map losses (gz) with metadata, and 30 user-supplied decoded losses (gz);
  - the queued match groups.

  The 40 maps are in `maps/local-benchmarks`.
- **On the training box only** (too large, gitignored):
  - `artifacts/local-only/replays-20261023`: the decoded 23 Oct archive, 244,981 matches, with per-replay team ids in `team_ratings.json`;
  - `artifacts/local-only/bc-top12k`: the behaviour-cloning dataset;
  - downloaded match ZIPs;
  - the original archive ZIPs in `C:\projects\cambridge battlecode\match summaries 23102026`.

  You can rebuild the archive analysis from fresh downloads with `tools/replay/decode_archive.py` and `team_ratings.py`. For a draft model, new ladder downloads (`cambc matches list/download`) are enough.

## 8. Training box (original laptop) reference

- Repo: `C:\projects\cambridge battlecode\work\neural-full-stack`.
- Python (CUDA torch 2.11): `C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe`.
- Hardware: 20 CPU threads, RTX 5070 Ti laptop GPU (12 GB).
- Optional remote control: `ops/runner.sh` on branch `ops`, with its clone at `work/ops-runner`. The user must start it there (`nohup bash ops/runner.sh > runner.log 2>&1 &`, or add `--status-only`). It then runs scripts you push to `ops/jobs/pending/` and pushes their logs; see `ops/jobs/README.md`. It is not running now.

## 9. Suggested next steps (in order)

1. Read the match-group results and the ladder since v52 (§6). Confirm the stampede, big_world and islands fixes on the ladder.
2. Fix boss_battle (finding 5), then concentrated_wealth, elkring, swirl and yellow_brick_road. Use the §5 method, one fix per version, and gate each one.
3. Fuel: profile the hot paths with the `PROF`/`PROF_CHECK` instrumentation in `bot.cpp` and make them cheaper without changing behaviour. Because of finding 2, measure every change.
4. Neural, only with A/B evidence: a draft win-probability model (map plus both drafts → winner) from ladder downloads. Our win rate ranges from 39% to 58% depending on our picks (`ladder_report.py`).
5. Release loop: gate → submit → track → match groups → repeat.

## 10. Codex session update (2026-10-25)

Setup completed in this existing checkout using the vendored checksum-verified 3.0.5 CLI and Python 3.12.14. Existing login works; no credentials entered. Config paths were adjusted locally. Rows smoke: 2/2 +168 vs heuristic-v1; stampede setup sweep reproduces the archived 5/6 +536 vs v51 (not a universal 6/6). Initial and refreshed ranked/unranked snapshots are under data/ladder/v52_*.

Read artifacts/claude_ops/V53_PLAN.md, V53_LOSS_REPORT.md and V53_DRAFT_REPORT.json. Refreshed results are ranked 8/20 and unranked 27/55. All 40 losses plus seven top-team wins have now been downloaded, decoded and audited, 47/47 successful. Local logging/profile reproductions cover the five weak development maps. The failed stampede candidates each had a release holdout check; see the plan for results and explicit disclosure of repeated exposure.

Fuel profiling confirms costly world updates and scoring. Removing duplicate mask clears and reusing observation buffers failed their applicable gates; patches are preserved, source restored. Hoisting open-call scans was initially held back under an extra target-sweep requirement I imposed on general optimizations; after reading v52's release precedent, it was evaluated correctly as a general optimization with no map-specific behavioral claim. It passes development 87/168 (51.8%), -2.1, and its once-per-candidate aggregate holdout 39/72 (54.2%), +5.3; zero faults. Individual holdout map tradeoffs remain and are disclosed in bots/v53/CHANGES.md. No-action micro fallback, two fixed boss drafts, a learned counter-pick model and earlier concentrated banking were rejected. The draft model fits 243,904 games on this machine's existing archive and improves held-out prediction, but loses in games; do not enable it based on predictive accuracy.

Live v53 contains only the open-call invariant hoist in score_groups. A2_GATE_JOB stays off and A2_SOLE_FROM remains 500. Source SHA256: 2929c1e5cdf9520fea777f0f15ed596a45f7e33378133f3bc27cfe2c2fc1b35b. Gate assertions and file hashes are in artifacts/claude_ops/V53_RELEASE.json. It was submitted successfully as platform version 53 at 13:08:26 UTC; see results/v53-submit.txt.

The rejected stampede R1100 experiment is still useful for v54: target 6/6 +343.2, minimum +54, deaths 10 vs 20, and at R900 one seed earned 4644 gold versus v52's 2352. However global timing changed another sole-gem map and all scoped implementations had negative release holdout margins. Do not copy it into a release without a new independently motivated candidate and full gate.

The user explicitly approved pushing these plans, CLI snapshots, analysis reports and source changes to Infosuii/neural-networkk-battlecode, branch claude/compare-fix-replay-decoder; raw replays and credentials remain excluded.

## 11. V54 analysis handoff (2026-10-25)

The user changed the current session to **analysis and detailed improvement planning only**. Do not build, train, submit or schedule v54 under that analysis request. The user subsequently asked for the findings to be pushed and a reusable Claude Code implementation prompt; supplying that prompt does not execute it. The earlier exploratory bots/v54 directory has been removed, and no build/submission automation was created. A future explicit implementation request or the user invoking the prepared build prompt changes that scope.

Read artifacts/claude_ops/V54_PLAN.md, V54_MATCH_REVIEW.md, V54_WINNER_PLAYBOOKS.md and V54_EVIDENCE.json. Snapshot cutoff is games created through 13:30:12 UTC: ranked 5/10; unranked 31/65, including 0/10 in targeted groups against meow and Hidden Altar Keepers. All 75 v53 games, 40 v52 losses, 10 v52 winning controls and 11 diverse top-team wins have been decoded and audited (136/136). Raw replays remain local-only under artifacts/local-only/v53-review. The analysis tools and game-level derived measurements are committed; a fresh clone can regenerate the text match review without raw replays.

The main strategic recommendation is joint economic openings/reward ownership plus coordinated objective conversion, with mission-aware tactics and bounded computation. In v53 losses, median R250/R500 equipment ratios are 0.71/0.67; targeted opponents produce 17.5 versus 3.5 deaths and 3 versus 31 banks. Important counterexample: on boss_battle against Hidden Altar Keepers we led equipment at R500 but lost 0–1690 banked gems. The new ranked boss win was 0–0 on a gold tiebreak, not a solved altar problem. Candidate replenishment/clock control and transport logistics are rule-supported hypotheses, not validated improvements.

The original gate remains mandatory. The plan's >=60% development wins and >=+100 mean gems versus v53 are additional research aspirations, not measured gains or a replacement gate. The existing 12 holdout maps have prior exposure; do not claim they are pristine. The learned draft predictor improved prediction but won only 8/30 in deployment; do not enable it without joint plan/controller evidence. Corrected SDK camp labels in V53_LOSS_REPORT; its numerical measurements are unchanged.

For future implementation, use artifacts/claude_ops/V54_CLAUDE_PROMPT.md as the task prompt, keep bots/v53 frozen, and preserve the analysis/implementation distinction in the audit trail.

## 12. V54 implementation session (Claude Code, 2026-10-25)

The user asked for v54 to be implemented and evaluated from the v54 findings (the §11 analysis-only restriction
applied to the preceding session). `bots/v54` was built from frozen `bots/v53` (file hashes re-verified). Nothing was
submitted; no credentials were entered. Read `bots/v54/CHANGES.md` first, then
`artifacts/claude_ops/V54_BUILD_LOG.md` (actor-level loss explanation, every experiment, rejected variants) and
`V54_RELEASE.json` (hashes, gate, research numbers). The actor-level ledger is `V54_ACTOR_LEDGER.md`.

Findings to keep (do not relearn):

1. The opening economy is lost through time use and yield, before deaths: in v53 losses we attack camps 20% of alive
   rounds vs 25%, wait beside dead camps 3x as much, and earn 144 vs 267 capture gold per champion by R250. Shared
   captures are 0 for us; redundant occupancy is not the problem.
2. **v53 bug:** a multi-champion job's staging clock started at the walk, so jobs beyond ~7 tiles lapsed before helpers
   arrived, and the group was banned for 60 rounds. v54 M1 fixes this and adds on-site claim codes (64 + group on maps
   with ≤ 48 groups; fight orders keep 112-118) so hidden teammates count as present.
3. Treasure-first emblem plus Bruiser stacks helps only together (+148 with M1; either alone ≈ M1 alone).
4. An occupied spawn tile delays the whole group's respawn (engine-checked). v54 M3 holds a sole-gem camp while
   ahead by one cycle; it engaged in 5/12 stampede games, all wins.
5. Winners reuse fixed 3-tile teleport shortcuts; v54 M4 carries a crystal and hops when it saves ≥ 8 turns.
6. bench2 is fast on 20 threads (168 games in about 4 minutes). Inert changes move single maps by ±100 gems and up to
   ±4 wins in 12 through trajectory divergence: use 6-12 seeds (`bench2.sh ... 1 2 ... 12`) and
   `tools/bench_maps.py` for per-map tables across runs; `tools/replay/ledger_bench.py <prefix>` gives the economy.
7. Open weakness: PvP death spirals on brawl maps (hooks holdout 1/6; dev eight, quadrants, gold-rush). Next target.

Gate status for v54 vs v53 (§4): (a) declared targets concentrated-wealth, fragment, stampede, swirl, big-world all
6/6 on both sides, seeds 1-3; (b) 0.649, +149.0; (c) holdout aggregate 41/72, +30.8, its single post-freeze pass. The
holdout maps had prior exposure. Release recommendation: submit v54 after the user's go-ahead (the standing approval
covers submitting a version that passes the gate), then track ranked/unranked games and queue groups against meow
and Hidden Altar Keepers.

## 13. Brawl-map PvP survival research (Claude Code, 2026-10-25, after §12)

User direction: do not submit v54 yet; work on PvP survival on brawl maps. Full write-up:
`artifacts/claude_ops/V55_BRAWL_FINDINGS.md`. v54 is unchanged and still the recommended candidate; no v55 candidate
was kept. The 95 new ladder losses (180 games after the 13:30 UTC snapshot, all v53) are local-only under
`artifacts/local-only/v53-after`; the listing is `data/ladder/v53_after_snapshot_20261025.json`.

* Ladder PvP gap = damage, not positioning: equal contact time, cohesion and focus fire; once hurt, identical
  behaviour and outcomes; but we get hurt 54% more often and deal 42 vs 57 enemy hp per contact round.
* v54's local brawl weakness traces to carrying a teleport crystal (hooks 10/24 vs 20/24 without, with no hop by
  anyone); the mechanism is unknown. Gating the purchase, readiness rules and three old survival levers were tested
  and rejected or neutral (paired tables in the findings).
* `tools/bot_match.py` no longer imports torch per shard (it exhausted the paging file and dropped games).
* hooks (a holdout map) was used for this research at the user's request; treat it as exposed.

**Submission (2026-10-25 16:24:00 UTC):** at the user's instruction v54 was submitted as platform version 54 (`results/v54-submit.txt`). v53's whole ladder life (13:08:26-16:24:00): 325 games, 161-164; ranked 36/90, unranked 125/235 (`data/ladder/v53_full_life_20261025.json`). Games created after 16:24:00 are v54.

## 14. v53 ladder-life analysis and v55 brief (Claude Code, 2026-10-25, after the v54 submission)

All 325 v53 ladder games (161-164) were decoded and analysed: `artifacts/claude_ops/V53_LIFE_ANALYSIS.md` (narrative)
and `V53_LIFE_DATA.md/.json` (tables, per-game rows), produced by `tools/replay/run_life_tools.sh` and
`life_report.py`. Main findings: the equipment gap is 2× already at R100; winners wait at dead camps 2.7× less, take
2.4× the big-camp gems, open with Treasure, draft Vesper in 93% of games, place 4-5× as many wards, and win the damage
exchange because of gear. The prompt for the next agent (GPT) to build v55 is `artifacts/claude_ops/V55_GPT_PROMPT.md`.
Rank at 16:25 UTC: 115 (1788.8). v54's first 30 ladder games: 14/30 (`data/ladder/v54_first_20261025.json`).

## 15. v55 release candidate and contract audit (2026-10-25)

The user explicitly authorized submitting a definite improvement over v54. No further permission is pending.
Frozen candidate R10 is in `bots/v55`; release state, source hashes and checks are in
`artifacts/claude_ops/V55_RELEASE.json`. Source hash using the bench3 convention:
`91be1f2103d7466806bcabfba188826da6dafd7650d3d0eb25bd49c4cbc94a83`.
The independent official build exactly matches the benchmark seed1 wasm:
`3978e8d7053cd2f1cd2e8f3b91180aacc6a075abbb58c359cde722855d28d11a`.
v53/v54 file hashes still match their frozen release records. Local machine config and unrelated files are preserved.

Changes: complete learned camp commitments on capture (`V55_COMMIT_EVENT`), use Heart's damaging camp dash
deliberately (`V55_HEART_CAMP`), and remove enemy picks from the learned selector's availability mask
(`V55_DRAFT_LEGAL`). Enemy picks remain model inputs. Draft legality alone was neutral in all672games.
Do not claim it explained the entire ladder deficit. Damage-model/cache and spell-kill retarget experiments are off.

Development versus v54: **414/672 (61.6%),+106.0 gems, map-clustered95%[+44.5,+174.9]**. The retained completion
foundation is726/1344,+19.8,[+3.5,+37.1] over24seeds, now explicitly paired with an inert control. Adding Heart to
that foundation gives+79.2,[+4.2,+160.6]. The reverse completion-on-Heart ablation is inconclusive: report it honestly.
Final R500 ledger: capture gold363.2versus321.8per actor, equipment1911.6versus1670.0, dead-camp waits127.2versus135.3.
Heart capture gold319.4versus235.0; successful dash casts45.24versus35.21, camp-adjacent landings8.56versus1.23per actor.
Camp adjacency is a post-cast marker, not direct damage attribution; timeline kind23 is not a complete cast counter.

Gate: once-only frozen12-map holdout150/288,+21.3; versus v53:469/672,+240.1. v48 portfolio:113/168,+232.0,
against v54's107/168,+154.6. v53/v48 paired incremental intervals include zero; these are compatibility checks.
All runs exited0 and have exact coverage and0native faults on BOTH teams. Fuel: dev965/962, holdout83/81,
v53test1050/924, v48test273/290. General economy/controller change; no map-specific all-seed win target declared.
Gold-rush regressed107.9gems in development; brawl aggregate81/120,+98.7 has an interval including zero.
All40maps are reused; hooks had extensive prior development exposure. No holdout tuning occurred. Top25 remains
a live ladder target, not an established result of same-lineage testing.

Only `bench3.sh` and `bench_compare.py` for new work. Old bench2/bench28/bench_paired tools were retired in
`f9cb4bc`; historical logs unchanged. Restart research: `V55_RESTART.md`, `V55_CONTRACT_AUDIT.md` and the
hash-checked restart patches. Reconstruct with `python tools/reproduce_v55.py r10-heart-completion <new repo-local dir>`.
Raw replays/downloads/builds remain local-only. Read the release manifest for submission status before submitting
again; it is updated after the authorized upload succeeds.

