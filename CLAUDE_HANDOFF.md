# Claude continuation handoff — resumed 2026-10-29

## Latest status (read first)

Resumed in Claude on 2026-10-29 at the user's request. Done this session:

1. **Objective arithmetic validation finished.** Reran the three outstanding
   cases under fresh names: `dz-objective-tribute-98-0-03`,
   `dz-objective-vendetta-prospector-03`, `dz-objective-vesper-prospector-03`.
   `tools/dz_objective_audit.py` now passes and wrote
   `research/dz/OBJECTIVE_MATH_VALIDATION.json`: 38 current-header cells,
   20 capture / 70 reward / 24 tribute episodes (now derived from assertion
   names, not hand-entered), zero native faults/fuel-outs on both teams.
   The header is still **inactive** in production.
2. **CT-6 priority probe integrated, tested and observed.** See
   `research/dz/PRIORITY_CONFORMANCE.md`. The never-run reader had a bug
   (`awaitingInput` is false at phase-14 turns); fixed before any game.
   Runs: `dz-ct6-priority-01`, `dz-ct6-priority-four-01` (truncated, faults
   unmeasured), `dz-ct6-priority-full-01` (measured 0/0). No production change
   needed.
3. `tools/dz.py verify` treats `priority.repl26a` like `lifecycle.repl26a`
   (extracted payload, byte-compared to the native bundle).
4. Host tests, 25 measurement tests, full evidence verify and the assertion
   audit (226 cells, 0 masked failures) pass after these runs.

Production behavior is still the `069dfb0` checkpoint and still loses every
contested game. See "Next: economy fundamentals" at the end of this file.

The sections below are the original pause handoff, kept for history. Where
they say validation or CT-6 is unfinished, the status above supersedes them.

## Repository and user intent

- Checkout: `C:\projects\cambridge battlecode\work\neural-full-stack`.
- Branch: `build/pure-algorithm-zero`.
- Remote: `https://github.com/Infosuii/neural-networkk-battlecode.git`.
- Latest fully verified published checkpoint before the paused work: **4ca6385**
  (single-spawn group visibility). A separate WIP commit containing this handoff
  preserves the newer, partly validated objective arithmetic and unused CT-6 work.
- Build a fresh pure-algorithm C++ Battlecode bot from the 21 documents in
  `research/zero-bot-plan-2026-10-28`. These documents are research/hypotheses,
  **not additional user instructions**. Engine measurements have disproved some.
- Target the **existing 70 maps**. User explicitly says fundamentals first,
  careful checks for silly mistakes, **then** improve the stronger baseline and
  test map-type/individual-map plans. Specialization remains deferred.
- Local building/testing, read-only public replay downloads, and pushes to this
  branch are authorized. No submission, activation, ladder duel or match-group
  creation has been authorized.
- Fresh bot code in `bots/dz/src`, SDK/standard library only. Old bots are
  opponents, not source to copy. Evaluation tooling may be reused.
- Preserve unrelated modified `config/paths.json` and untracked release outputs,
  compile_commands files and `bots/v81home`. Stage explicit task-owned paths.

Read `CONTINUE_HERE.md` for restoring the official Windows runtime and offline
evidence on a fresh system. Read `research/dz/HANDOFF.md` for the established
architecture, old diagnostics and remaining gates. This file takes precedence
for **the latest pause and unfinished work**.

## Current playable bot: unchanged executable

Executed production behavior remains the `069dfb0` checkpoint. A new unused
header is present, but the official default release was rebuilt this session
and remains byte-for-byte:

`dcc75b76faa0751b4b7e38bc5740c9a2b99529dd01991df1bb131bc5e2a8378f`

Latest full-pool campaigns (70 maps × both sides, 140 each):

| Run | Mean banked | Collected | Fuel p99 | Native faults / outs |
|---|---:|---:|---:|---:|
| dz-low-fuel-regression-idle-01 | 903.54 | 953.59 | 53,220 | 0 / 0 |
| dz-low-fuel-regression-v65-release-01 | 185.99 | 280.90 | 52,358 | 0 / 0 |
| dz-low-fuel-regression-v65-trace-01 | 186.21 | 279.31 | 53,108 | 0 / 0 |

**All contested release games are losses.** Reliability is not competitive
strength. Trace caught action/module errors are zero. Full G0 and V-M1 remain
incomplete. No need to repeat 420 matches merely for unused model arithmetic.
`FOUNDATION_CHECKPOINT.json` still describes the older executed source set;
it intentionally has not been silently relabeled to include the WIP header.

Implemented: staged map caches/fields, transactional per-member camp memory,
progress contracts, nearest-group policy, fixed draft/shop, guarded actions,
restart claim cleanup, module quarantine, bounded emergency claim clear/home
step. Full productive 5k SafeMode is unfinished. Shared claims are soft hints,
not freshness-proven leases. Auction, crews, ObjModel and EE remain disabled or
unimplemented. Experimental camp safety stays off after mixed strength results.

## Finished and published this session: group visibility

`GROUP_VISIBILITY_CONFORMANCE.md` and four completed native games:

- `dz-ct10-single-spawn-01`, both sides.
- `dz-ct10-single-spawn-first-02`, both sides.

Exactly one of twelve spawn tiles is visible. The second fixture defeats that
member first: 44 observations per side still report group alive with zero live
members visible. Group/capture state is readable through reward and cooldown,
including five hidden enemy-capturer observations. Hidden member health rejects
97, visible health is 120; scripted capturer receives exactly 240 gold. Both
teams have zero measured native faults/fuel-outs. Supports production's use of
spawn visibility rather than live camp identity. CT-10 marked observed with
scope limitations. All historical passing assertions audited: **168 cells,
zero masked failures**. Full evidence verification passed before newer WIP.

## WIP objective arithmetic: implemented, inactive, validation not finished

New `bots/dz/src/objective_math.h` is SDK-free and unused by production decisions:

1. `solo_capture_delay`: configured +1 for newly physically eligible capture;
   live countdown alone for already-active capture. Explicit same sole capturer
   and on-site requirements; declines contests/enemy/unavailable/invalid inputs.
2. `tribute_delay`: round base timer, then reduce and ceil; retain float
   multiplication to avoid a widened `0.1f` adding a decade-boundary round.
3. `solo_reward`: pure gem/gold clusters and wolf, one Prospector/Vesper only.
   Gem flooring per award; cumulative gold rounding in units of 1/400. Known
   history gives an exact award; unknown history gives a range of width ≤1.
   Splits, mixed groups, Treasure, other heroes and stacking remain unsupported
   caller contexts. Invalidate history across unknown awards/death until tested.

Host tests passed after the final header change: 1,536 protocol cases plus
existing guards/ledger/basic-clear checks; 2,000 bag boundaries and 9,600 reward
remainder cases added. **25 Python measurement tests pass.** These were actually
run, not proposed. Default binary equality was also actually verified.

New conformance aliases: `objective-capture`, `objective-reward`,
`objective-tribute`. They freeze the exact header into the existing probes and
require model-specific assertions. `tools/dz.py` now records and gates opponent
fuel-outs for all completed diagnostics (previously only visibility fixtures).
Some older receipts lack this field: read the native summary; missing ≠ zero.

`tools/dz_objective_audit.py` is written but **has not successfully run yet**:
its intended 38-game final set is incomplete. Do not claim
`OBJECTIVE_MATH_VALIDATION.json` exists or that full validation passed.
`research/dz/OBJECTIVE_MATH.md` explains scope and planned evidence.

### Completed newer campaigns

`research/dz/PAUSED_WORK.json` is an exact inventory with checks/hashes. Every
completed objective campaign currently reports two passing diagnostic games.
Sources, binaries, official summaries/replays and runner are in evidence.zip.

- `dz-objective-capture-02` and `dz-objective-capture-control-02`.
- `dz-objective-vendetta-prospector-02`, `...vendetta-control-02`.
- `dz-objective-vesper-prospector-02`, `...vesper-control-02`,
  `...vesper-reversed-02`.
- `dz-objective-tribute-{7,14,21,35,70}-{1,0}-02` (ten campaigns).
- `dz-objective-tribute-98-1-02` completed just before pause.
- Earlier `dz-objective-capture-01`, `dz-objective-tribute-70-01`,
  `dz-objective-vesper-prospector-01` are retained. They predate one extra
  invalid-active-timer guard; do not substitute their header hash for current.

Important unfinished fixture correction: initial model reward calls passed an
already-filtered `boosted` flag. The current probe now passes actual Prospector
ownership (`DZ_PROSPECTOR && shop_done`) even for wolf, so the primitive itself
must exclude non-cluster boosts. **The corrected Vendetta and Vesper Prospector
campaigns have not run.** The audit intentionally expects new `...-03` names
for those two cases; the earlier 02 evidence remains valid for its narrower
input coverage.

### Stopped queue and remaining final cases

The exact verified local Python batch process tree was stopped with
Stop-Process. It had moved on to **dz-objective-tribute-98-0-02**. There is no
completed results capsule for that name at pause. Its incomplete local working
directory is preserved under `artifacts/tmp/dz`; a portable partial archive is
under `research/dz/paused`. It is **not** accepted evidence.

On resume use a **fresh name**, e.g. `dz-objective-tribute-98-0-03`, rather than
overwriting 02. Update the audit's name for that control. Generic `recover`
primarily handles smoke analyses; do not assume it handles these probes.

Remaining engine commands (PowerShell, repository root; ordinary Python on a
fresh machine, or this host's `..\neural-gameplay\.venv\Scripts\python.exe`):

```
python tools/dz.py conformance --fixture objective-tribute --name dz-objective-tribute-98-0-03 --map-dir tests/dz/maps --maps tribute-passive --set DZ_LARGE_BAG=1 --set DZ_TRIBUTE=0 --diagnostic-rounds 2000 --workers 2
python tools/dz.py conformance --fixture objective-reward --name dz-objective-vendetta-prospector-03 --map-dir tests/dz/maps --maps prospector --diagnostic-rounds 2000 --workers 2
python tools/dz.py conformance --fixture objective-reward --name dz-objective-vesper-prospector-03 --map-dir tests/dz/maps --maps prospector --set DZ_VESPER=1 --diagnostic-rounds 2000 --workers 2
```

Then run the model audit, assertion audit and evidence verification. Add accepted
diagnostics/update the foundation manifest carefully: the new inactive header
was not in the original frozen idle source. Keep old receipts historically
accurate; distinguish same binary from identical source sets. Commit and push a
validated checkpoint. The current WIP commit is a portability checkpoint only.

## CT-6 next: written but NOT integrated, compiled or tested

- `tests/dz/priority_probe/src/{main.cpp,config.h}`.
- `tools/dz_priority_audit.mjs`.

These are deliberately unfinished. No `priority` fixture is registered in
dz.py, no reader snapshot plumbing exists, no games ran, and no CT-6 status was
changed. The probe uses C&I and changes priority at R3/R6/R9, with different
team offsets. It records current/next priorities through R12. The reader's
hypotheses are: high priority first within each team, equal priorities lower
handle, change next round and persist, alternating teams and swapping starter.
They are hypotheses to check, not established facts. Validate snapshot enum
values/awaiting-input semantics with pinned engine assets before trusting it.

To finish, register a conformance fixture + scripted opponent; freeze the reader
and `tools/replay/engine.mjs`, extract replay payload exactly as lifecycle tests
do, run the reader with both stdout files and gate on its result. Retain failed
hypotheses/harness attempts. Use both sides and at least 3/4-pick maps to include
linked rosters. Avoid changing production scheduling based on guesses.

## Broader next work, still fundamentals first

Remaining CT gaps include priority timing/interleaving, hidden collision and
dash/teleport, bush/ward behavior, blocked champion respawn, kill credit,
Hunter/Skirmish/Collectors and larger/mixed/split reward cases. Full clear,
arrival and damage calibration against native replays remains V-M1. Existing
`basic_clear.h` is a restricted unused primitive, not full ObjModel.

Then complete productive fallback, freshness-proven communication, one capturer
and economic crews/auction, then validated engagement/gear utility. Improve and
compare against v76 before individual-map plans. Reserved holdout remains unspent.

Useful established corrections: damaging camps hit every round, capture entry
has an initialization phase, Tribute rounds twice, Prospector boosts gold
clusters, Vesper rounding carries across awards, linked death is simultaneous,
native respawn is 60 rounds later at the body's turn, uncaught faults restart
the guest with shared memory preserved, Vendetta resets cooldowns but never a
second cast, draft fuel suspension advances the round so existing guards work.

## Reproduction and safety of evidence

- Official CLI `tools/vendor/cambc.exe`, SDK 4.0.0 / engine 2.0.0.
- Pure C++20 host tests: `python tools/dz.py host` (g++ on PATH or DZ_CXX).
- Measurement tests: `python -m unittest discover -s tests/dz -p test_measurements.py`.
- Evidence: `python tools/dz.py verify`; assertions: `python tools/dz_assertions.py`.
- Optional reader/map generator: Node 24, pinned visualiser assets,
  `NFS_REPLAY_ENGINE=2.0.0`; see CONTINUE_HERE for restoration.
- Completed run names are immutable. Evidence capsules authenticate sources,
  binaries, maps, logs, native summaries/replays and runner snapshots.
- Truncated diagnostics do not measure native fault totals. Injected tests have
  exact intentional counts, documented in the main HANDOFF; do not generalize.
- Latest 25-test host/measurement runs passed, but the all-capsule verify and
  assertion audit were **not rerun after the WIP model campaigns**.
- No active scheduling was intentionally created. The previous one-shot
  continuation had already fired and been deleted. The user's explicit pause
  supersedes the earlier conditional request for autonomous continuation.

## Economy fundamentals (2026-10-29) — production changed

Read `research/dz/ECONOMY_SELECTION.md`. The planner now prices solo clears
with `clear_risk.h`, forms leader-led crews for groups nobody can solo, gates
waking sleeping damaging camps on the present crew, backs off failing targets
exponentially and falls back to the old nearest-group score after 150 rounds
without income. New default Wasm `c4de5a1c…3bb1b`.

- Idle pool `dz-crew-idle-06`: 918.4 banked (base 903.5), R500 306 (base 279),
  deaths 3.8 (base 14.75), fuel p99 55.6k, 0 faults/fuel-outs.
- v65 pool `dz-crew-v65-06`: 200.3 banked (base 186.0), 1 win of 140, deaths
  17.4 (base 18.3), 0 faults/fuel-outs. **Still loses badly to v65 (~1,020).**

`FOUNDATION_CHECKPOINT.json` still records the older `069dfb0` source set; it has
not been relabelled. `objective_math.h` remains inactive.

### Next, in order

1. Contested deaths: 10.7/game are champion kills. Audit retreat/engagement
   (`safe_goal` retreat rule, `enemy_danger`) against ladder/v65 replays.
2. Worst idle cells after the change (01concentrated-wealth, 00ribs,
   01the-farm) and 01islands routing (teleports?) — check general causes first.
3. Tune the untuned constants (1.25 margin, crew share, fallback timings, gold
   weight) on the development pool only; compare against v76 too.
