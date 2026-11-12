# Continue v67 here

## Current status: this supersedes the historical checkpoint below

The frozen portfolio `b40-four-seed-policy` actually achieved **220/240 strict gem-margin wins** on the exact
seed 1/2 schedule, +508.6 mean margin, zero faults. **It is overfitted:** untouched seeds 7/8 and reserved 3/4
both scored **137/240**. Older-opponent guards: 139/240 vs v61, 159/240 vs v58, 141/240 vs v66b, all zero faults.
Fuel exhaustion is higher than opponents. Do not describe this as a generally dominant or flawless bot.

Read [README.md](README.md), [FINAL_REPORT.json](FINAL_REPORT.json), [FINAL_BENCHMARK_OUTPUT.md](FINAL_BENCHMARK_OUTPUT.md)
and [CONTINUATION.md](CONTINUATION.md). The `FINAL_*` files document this frozen candidate, not completion of
the user's broader strength goal. Seeds 3/4 are now consumed and must never guide subsequent tuning.

The live `bots/v67/src` stays frozen and matches all seven validation runs. Further experiments use separate
prototype directories. At this update, `p48-package-complete-lifecycle` is testing combat-package-v3; it restores
the established priorities/death/job/field lifecycle while using the new contact controller. Results pending.
The prior combined-controller prototype p42 scored 17/240; do not promote it. The user explicitly asked us to
keep working autonomously and fix confirmed defects immediately. There is no impossibility evidence.

## What the user wants

Read the original `GPT_PROMPT.md` in this directory. Latest strength goal: **v67 wins at least 220/240 against
unmodified v65**, or provide clear evidence that it cannot. The original historical checkpoint was far below
the target; the newer fitted threshold result and its validation limits are recorded above. Continue autonomously.
This handoff originally existed because the user said usage is low and asked
for files so another agent on the same device can continue. Do not interpret the checkpoint as completion.

Earlier mimic objectives were superseded by this v67 request. Do not modify `bots/mimic` or `bots/v65`.

The user's latest strategic advice is central: v65 lacks shared teammate positions, its layered controller
overrides individual fixes, grouping must work together with focus/burst/survival/economy, and tests need to
measure the mechanism and external opponents rather than only our lineage. The attempted rewrite has not
delivered those benefits yet. Do not portray a protocol or a few switches as a solved strategy.

## Environment and boundaries

- Workspace: `C:\projects\cambridge battlecode\work\neural-full-stack`.
- PowerShell. Python: `..\neural-gameplay\.venv\Scripts\python.exe` (torch/CUDA). Node is on PATH.
- Official CLI: `tools/vendor/cambc.exe`, engine 2.0.0. Branch `claude/compare-fix-replay-decoder`.
- No AGENTS.md was found. Do not spawn subagents without explicit authorization/applicable instructions.
- Never log in or enter credentials; never submit/queue ladder games without asking.
- Leave modified `config/paths.json`, all `bots/v66x_*`, `bots/v66y_*`, other bots' compile_commands.json,
  `.cambc`, data/ladder/v57_games_20261026.json and unrelated artifacts alone.
- `GPT_PROMPT.md` was user/other-agent authored; do not commit it as our authored work.
- Official builds need access to the user's compiler cache. Tool runs used `require_escalated` with task-specific
  explanations; automatic review approved. No approval rejection has occurred.
- Original copied C++ source uses CRLF. Preserve it with read_bytes/decode/write_bytes when editing. New files LF.
- Native g++: `C:\msys64\ucrt64\bin\g++.exe`.

## Start with these files

1. `GPT_PROMPT.md`: exact acceptance criterion and required prior research.
2. `RESULTS.md`: all completed scores, not just the best one.
3. `BENCHMARK_OUTPUTS.txt`: full saved output; local raw outputs also remain under artifacts/evaluations/v67.
4. `MAPS.md`, `MAPS.json`, `OPENINGS.json`: map study and selected winning replay openings.
5. `bots/v67/src/v67_team.cpp`, `team_memory.h`, `v67_opening.cpp`, `map_plans.h`.

Required prior research was read: research/v62/BIG_STRATEGIES.md, research/top-losses-20261026/README.md and
FAILURE_LEDGER.md, research/v58/V58_CLAUDUS_FINDINGS.md, research/proxy/README.md, research/mimic reports, local
GameRules.md and SDK. Runtime balance comes from SDK metadata, not old fixed tables in the prose rules.

## How to run the fixed benchmark

From the workspace above:

```powershell
& '..\neural-gameplay\.venv\Scripts\python.exe' tools/v67/run.py --run NEW_NAME --note 'What changed'
```

Optional repeated `--set NAME=VALUE` rewrites all definitions of that macro in v67 common.h before running.
Every run must have a fresh name. The wrapper executes:

```text
python tools/proxy/local_duel.py --plan research/v59/duel_top1.json --bot bots/v67 --name v67 --proxy bots/v65 --seeds 1 2 --workers 16 --replays --out artifacts/evaluations/v67/NEW_NAME
```

The extra `--replays` only retains analysis inputs. Do not alter the plan, side assignments or seeds. Keep exactly
one literal `#define NOVA_SEED 1` in common.h. The builder rewrites it per seed.

run.py saves the actual output, games.json, audit.json with source hashes, and both teams' faults, fuel, deaths,
kills, gold and gems. It appends RESULTS.md/jsonl and verifies every v65 source file against V65_SOURCE_SHA256.json.
Every completed run has 240 games and 0 faults on both teams so far. Fuel can still suspend actions without faults.

**Seeds 3/4 remain untouched.** Freeze the final candidate before `--holdout --seeds 3 4`. Do not tune on them.
Before claiming success, run majority-win checks with `--opponent v61`, `v58`, `v66b`, plus fuel/fault audits.
None of these final guard runs has happened yet.

## Results and exact source recovery

All completed experiments are in RESULTS.md. Before the final camp-state trial, best was b06-life15:
137/240, +108.0 margin, fuel 335/295, gold 6343/game, deaths 14.02, kills 12.95. Baseline b00 was 136/240,
+81.9, fuel 947/358. b00 literally used the same wasm on both sides: its advantage is the fixed schedule's
side/initiative baseline, not an improvement. Duplicate map/side/seed jobs yielded identical outcomes.

The strongest result is not the current source configuration. Exact historical source copies are retained under:
`artifacts/evaluations/v67/<run>/build/src-bot-s1/src` and `src-bot-s2/src`; the seed-1 copy has NOVA_SEED 1.
The build directories also contain the tested .wasm and build logs. Recover the best from b06-life15 if needed.
Do not claim a modified current source has b06's score without rerunning it.

Failed b04-fish-meta and b13-team-local-economy builds are retained; corrected runs b04b and b13b completed.

Failed families:
- Early stat build 110/240; team commander 131; economy director 108; Fish draft+items 81.
- New visible-power combat: 25 wins, deaths fell but gold fell to 3920/game. Over-retreat starved the economy.
- Opening invasion 44; old item path 113; melee micro 95; removing tactical verdict search 121.
- Independent controller: b11 0 wins, b12 3, b13b 6. Do not enable it expecting improved strength.
- Winning-map examples: full draft/items/routes 77; draft only 81; draft+items 76; draft+routes 80.

An offline per-map oracle over the first 11 runs found 212/240. This is only an upper bound from selecting separate
results after the fact, saved in artifacts/tmp/v67/portfolio-preview.json. It is NOT an implemented candidate and
not a score to claim. A real map-specific policy would need implementation, full rerun and untouched holdout.

## Current code structure

v67 started as a byte-identical copy of the 33 v65 source files. The copy inherited read-only attributes; only
v67's attributes were cleared. v65 and mimic git diffs have remained zero. New source is experimental:

- v67_build.inc: early Jungle/damage/Bruiser build, controlled by V67_BUILD, normally 0.
- v67_meta.* / v67_tables.h: copied top-team map drafts and item milestones. V67_META=-1 disables it; 3 is Fish.
- v67_fight.cpp: bounded visible-power combat; V67_FIGHT=0 disables it. Rejected as a full replacement.
- team_memory.h / v67_team.cpp: new shared memory and own play_turn priority. V67_TEAMPLAY=0 disables it;
  1 uses the team farm chooser, 2 uses legacy farm() with conservatively inferred on-site work.
- Legacy write_claim/unmark_onsite/write_order/share_sighting become no-ops when TEAMPLAY is enabled. decode_claims
  also becomes idle; v67_team_sync then supplies inferred nearby claims. Avoid interpreting position bits as claims.
- v67_opening.cpp / map_plans.h: intact winning-team examples for all 70 maps. V67_OPENING bit1 enables the map
  draft, bit2 the example's item milestones, bit4 its coordinated first-150-round camp route. 7 enables all.
  The draft selects a compiled plan via map hash and stores its index at draft memory bytes 980–981 (magic 0x67).
  Opening routes mirror by spawn, progress on observed camp capture/cooldown, and time out after 45 rounds per job.
  They are not timed action replays. Existing pathing and action legality execute them.
- V67_CAMP_STATE=1 enables legal out-of-vision group state/cooldown queries in World::observe_groups. The final
  b18-public-camp-state experiment isolates this on baseline gameplay. Check its output/result for final score.

At checkpoint the active configuration is b18: TEAMPLAY=0, OPENING=0, META=-1, BUILD=0, FIGHT=0, CAMP_STATE=1,
TRACE=0, other macros at original v65 defaults. The exact final score is in RESULTS.md and CHECKPOINT.json.

The large legacy controller remains in bot.cpp; new-team mode returns before entering it. Old helper reuse is
intentional (pathfinding, shop, cast/attack/reset, camp execution), but full rewrite is nowhere near competitive.

## Concrete next investigations (not proven fixes)

1. **Check a likely startup/fuel gating defect before judging the architecture.** The new turn calls
   `if (bc::fuel_remaining() > 60000) build_fields();` at the end. Legacy farm() immediately declares low_fuel while
   field_calls==0, so a sufficiently expensive initialisation/sync may prevent both initial fields and any first job.
   The original pipeline always calls build_fields(), whose own quotas/reserves limit work. Test unconditional
   build_fields() in the new turn, instrument field_calls/remaining fuel and income. This hypothesis is untested.
   b13b had 2087 fuel suspensions vs v65's 84; field and on-site inference cost need measurement, not guesswork.
2. The current one-rally farm chooser sends too many heroes to small jobs and clears slowly. Do not let grouping
   erase the baseline economy. Earlier trace showed partly cleared groups still consuming turns after R100.
   Proven fight_camps(g,1) improved 0→3 wins but did not solve income. Separate route choice, actual action rate,
   visibility/approach, capture ownership and ready-to-respawn occupancy in the diagnostic ledger.
3. **Current protocol has no battle location.** Six 9-bit positions (5x5 cells), 3 focus bits, 7-bit farm rally use
   all 64 bits. A focus enemy ID does not tell unseen allies where the fight is. Proposed next format (not built):
   six 8-bit positions (7x7 cells), 3 focus bits, 10-bit rally payload and 3-bit round timestamp. With focus>=0,
   payload could encode a 4x4-cell battle point (25x25); otherwise it can hold a farm group. Expire contact at age3
   so allies don't march to stale fights. Native protocol tests must change with the encoding.
4. Match fight readiness with actual arrival time and unknown ally gear/health. Current approximate hp×DPS test
   over-retreats, counts unseen allies conservatively but poorly, and gives up farming for enemies at distance7.
   Consider the existing bounded tactical simulation and a coherent engage/focus/burst/leave decision.
5. Map drafts/items alone do not reproduce the winning team's strategy. Use MAPS evidence to preserve coherent
   clear crew, carry ownership, reset timing and contact zones. Winning examples currently regress to ~80 wins.
6. After a real improvement, inspect per-map failures and opening economy, then final frozen guards. Do not fall
   back to declaring impossibility just because these attempted changes were poor.

## Diagnostics and data

One trace without modifying sources (fresh artifacts path):

```powershell
& '..\neural-gameplay\.venv\Scripts\python.exe' tools/v67/trace.py --map 00quadrants --define V67_TEAMPLAY=2 --define V67_CAMP_STATE=0 --out artifacts/evaluations/v67/trace-NEW
```

trace.py builds temporary copies with V67_TRACE=1 and optional defines. a.txt has T67 modes every25 rounds,
including position, health, unspent gold, bag, rally/job, group state/remaining HP and exact visible ally count.
For baseline TEAMPLAY=0 the T67 printer is not used; old MICLOG/MODESTATS compile-time diagnostics also exist.

Existing trace: artifacts/evaluations/v67/trace-b11-quadrants (573 vs1025, faults0, gold1710, collected714, R610).
Opening economic ledgers: artifacts/evaluations/v67/b11-economy and b00-economy. R250 candidate capture gold fell
652→378; still time rose .157→.218, clearing .184→.131. tools/mimic/economy.py is reusable read-only; its report
labels the proxy v65 as "mimic", so compare the explicit v67@250 row, not that label.

Protocol test (already passed exhaustively over 100x100 cells, six slots, focus/rally, death resets):

```powershell
& 'C:\msys64\ucrt64\bin\g++.exe' -std=c++20 -O2 -Wall -Wextra -Werror tools/v67/team_test.cpp -o artifacts/tmp/v67/team-test.exe
& 'artifacts/tmp/v67/team-test.exe'
```

Map evidence:
- tools/v67/openings.mjs uses pinned official engine-2 replay decoding and map group API. It extracts actual basic
  attack routes, nearby crew, capture incomes, first contact/fight and empty camp tile occupation through R150.
- tools/v67/study.py --workers 8 extracts/caches 1177 replays, joins native summaries/meta crawl and writes MAPS.
  Cached under artifacts/local-only/v67/map-study. Map underscores are normalized to hyphens, covering all70.
  Cached crew entries of zero from the first extractor version are filtered in the report. Actual attack crew
  intervals are15 rounds, not an exact same-turn count. Items/banking use full-game native summary events.
  First fight is a basic attack; spells can precede it. Empty-tile occupancy does not prove deliberate denial.
  Altar-lock usage is explicitly unmeasured. Small draft win rates are not causal matchup estimates.
- tools/v67/compile_plans.py chooses intact winning replay sides with supported drafts; within a chosen lineup,
  it selects the example with most opening capture gold+2*gems, not local benchmark score. It emits map_plans.h.
- study.py and compile_plans.py can rerun. hook_opening.py and hook_camps.py are one-use historical edit scripts;
  rerunning them on already-hooked sources fails its assertions. screen.py currently reruns b15..b18 and needs new
  fresh names before reuse; it resets common.h to baseline between candidates. Do not rerun blindly.

Existing local data is on this device: artifacts/local-only/proxy/replays/index.json (1177), meta/20261027,
9.7M mimic training examples, engine visualiser assets in user's AppData. No network needed for the next steps.

## Mimic checkpoint context

Committed/pushed prior checkpoint 579f3905c9421b4adf2f468d0db55a36941d0bfd contains independent mimic v9 and tooling.
It fixed stale recall cancellation permissions, dead-camp navigation roots, reward ownership, respawn timing and
parity. v9 still lost0/240 to v65 (margin -912.6), but gold rose1017→2122 and R250 capture gold235→408. Native/WASI
parity: 39,288 observations/shared words and37,867 full decisions, 1,484 fields, zero mismatches. No ladder submit.
The unfinished later mimic prototype was preserved in artifacts/tmp/v67/mimic-experimental, then tracked mimic
was restored. Do not resume by modifying it; use v67.

## Checkpoint discipline

This source checkpoint is research, not the strongest tested release. Keep every honest failure result. Preserve
holdout seeds. Once strength actually passes, complete the required guards, update README and commit/push only
our files. The user explicitly asked to be able to hand this work to another agent on the same device.
