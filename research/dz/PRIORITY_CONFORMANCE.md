# CT-6 priority scheduling conformance — 2026-10-29

Probe: `tests/dz/priority_probe` (C&I, Vendetta, Marcella, Ryth, Vesper, so every
roster contains a linked pair). Both teams run the probe; the scripted opponent
adds +1000 to every priority it sets, which separates per-team ordering from a
single global sort. Priorities change at R3 (100+slot), R6 (slot 0 = 500, others
200+slot) and R9 (all -7). Each body prints its SDK view through R12.

`tools/dz_priority_audit.mjs` replays the official native replay with the pinned
engine 2.0.0 reader, extracts the phase-14 champion-turn order and gates it
against both stdout transcripts. `tools/dz.py conformance --fixture priority
--fixture-opponent` freezes the reader and `replay/engine.mjs` into the run.

## Retained harness failure

The first (never-run) draft of the reader required `snapshot.awaitingInput` at
phase 14. Inspection of an existing native replay (`dz-objective-tribute-98-0-03`)
showed `awaitingInput` is **false** at every phase-14 champion turn, so it would
have recorded no turns. The reader now keys turns by `(round, turn)`, as the
lifecycle reader does. Fixed before any priority game ran.

## Runs (all pass; none relabelled)

| Run | Maps | Rounds | Bodies/team | Native faults / fuel-outs (both teams) |
|---|---|---:|---|---|
| dz-ct6-priority-01 | 00collision, 01big-world × A/B | 20 (truncated) | 4, 6 | unmeasured (truncated) |
| dz-ct6-priority-four-01 | four-pick × A/B | 20 (truncated) | 5 | unmeasured (truncated) |
| dz-ct6-priority-full-01 | 00collision, 01big-world × A/B | full game | 4, 6 | 0 / 0 measured |

Every game: 0 SDK assertion failures for both teams, 0 native order mismatches.

## Established (engine 2.0.0, these 3/4/5-pick rosters)

- `set_priority` during round R leaves `prev_priority()` (the value in force)
  unchanged and is visible immediately in `priority()`. The new order applies
  from R+1 and persists until changed.
- Within a team: higher current priority acts first; equal priority acts in
  ascending champion handle. Linked bodies are scheduled independently.
- Teams strictly alternate turns. Team A starts odd rounds, team B even rounds
  (round 1 = team A), independent of either team's priority values.
- An opponent's larger priorities do not move its bodies ahead of ours: ordering
  is per team, then interleaved.

## Production consequence

The default order already equals ascending handle, which is what the current
`100 - slot` setting reproduces (slots are sorted handles). No production change
is needed. Any future reordering (for example, letting a capturer or banker act
first) takes effect only from the next round. Mixed dead/respawning bodies and
mid-round priority changes by a body that already acted are not tested.
