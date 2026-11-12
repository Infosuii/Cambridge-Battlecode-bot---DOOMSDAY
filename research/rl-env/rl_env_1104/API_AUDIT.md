# RL environment: engine/SDK API audit (E0 input)

Task `rl-env-adapter-1104`, branch `claude/rl-env-1104`, base `51d61696`. Sources read: `sdk/cpp/cambc.h` (SDK 4.0.0,
5,527 lines), `tools/vendor/cambc.exe` 4.0.0 (`--help` of `run`, `run-batch`, `summary`), one real game run on this PC
(v92 vs v92, `00corners`, `--release`), and Agent 2's recorder/trainer at `agent2-neural` `5616b3ae`
(`research/agent2-neural/code/nnrec.cpp`, `nn_rl4.py`, `nn_record.py`). Nothing below is inferred from docs alone unless
marked *unverified*.

## 1. Running games (the only simulator)

There is no Python simulator. Games run only through the official native engine via `cambc`:

| Command | Use for the collector |
|---|---|
| `cambc run BOT_A BOT_B --map M [--rounds N] [--fuel Q] [--release] [-o DIR] [--statistics F --json] [--log-limit B]` | one game |
| `cambc run-batch MANIFEST --jobs J [--rounds N] [--fuel-quantum Q] [--release] [--json] [--log-limit B] [--timeout S]` | many games; manifest rows `bot-a bot-b map replay.repl26a [--statistics path] [--json]` |
| `cambc run-batch --jsonl F` | "API v1 compiled-input JSONL manifest; stdout contains only machine events" (*format unverified*) |
| `cambc summary FILE -o out.json` | binary CAMSTAT summary → JSON |
| `cambc build BOT --release --output x.wasm` | release build; hash identifies the policy binary |

Measured here: a full 1,095-round v92 mirror game took **~1.1 s wall** on the i5-1135G7 (release, native engine).

Each game writes a replay bundle (`.repl26a`, a zip) containing `replay.repl26a`, `team-{a,b}.stdout`,
`team-{a,b}.debug` and `team-{a,b}.fuel` (binary per-turn fuel trace, magic `a62leuf`).

**Pitfalls the collector must handle:**
- `--log-limit` defaults to **1 MiB per team** for stdout/stderr/debug. Agent 2 raises it to 64 MiB. Recorder rows over the
  limit are silently cut, so the collector must detect truncation (row count vs expected, or a trailer row) and mark the
  episode `truncated_log`.
- `--statistics` is **only written for a finished game**. `--rounds N` below the game's natural end prints
  `truncated: round N+1` / "Unfinished … no result" and writes no summary. Reward/outcome then come only from the
  recorder rows and the episode is `truncated`, never `terminated`.
- `--release` skips `debug_block` and doesn't link the fuel-pause imports. A non-release build is a **different
  binary** with different fuel accounting (§5).

## 2. Match summary (rewards, outcome, lineage)

`--statistics F --json` (format `1.0`, `metricSemanticsVersion` 1) gives:

- `match`: `engineVersion` (2.0.0), `engineBuildHash`, `mapHash`, `width`, `height`, `seed`, `outcome` (`teamA`/`teamB`/…),
  `roundsCompleted`, `roundsStarted`, `finalRoundPartial`.
- `roster.draft[]` (pick order, team, champion) and `roster.champions[]` (`id`, `name`, `team`, `draftPick`).
- `champions[]`: final `metrics` (kills, deaths, assists, collected/submitted gems, gold earned/spent, damage
  done/taken by source, healing, shielding), items/consumables held and bought.
- `championTimelines[]`: per champion × metric, run-length `runs[{duration, value}]` over rounds (`sampleCount` =
  rounds+2). Metrics: assists, championDamageDone/Taken, collectedGems, deaths, earnedGold, gems, gold,
  healingDone/Received, kills, monsterDamageDone/Taken, saleRefunds, shieldingDone, spentGold, submittedGems.
- `teamTimelines[]`: `submittedGems` per team (run-length).
- `events[]` by kind: assist, botFault, buyConsumable, buyItem, campClear, death, fuelExhausted, gemCollection, gemLoss,
  gemSubmission, itemCombination, kill, resignation, sellItem, wardPlacement. Each entry has
  `timestamp{round, phase, substep, input, ordinal}`, `x`, `y`, `target`, `amount`, `value`.
- `diagnostics.botFaults{teamA,teamB}`, `diagnostics.codes[]`.

This is **training-only, privileged** data (full state of both teams). It may feed rewards and the centralised critic,
never actor inputs.

## 3. Observation API (what a body may legally see)

The bot runs one WASM instance **per champion** (plus one draft VM). From `cambc.h`:

- Self (authenticated `cached_self`/`self()`): position, health/strength/focus, gems, gold, items, consumables, ability
  cooldowns, ward charges and cooldown, `state()` flags, `remaining_channel_time()`.
- `champion_state` flags: `alive, recalling, submitting_gems, can_move, can_attack, completed_turn, recall_started,
  submit_gems_started, recall_cancelled, submit_gems_cancelled, can_cast, teleporting`.
- Others: `champions()` / `camps()` / `wards()` / `altar_locks()` / `teleports()` **only within vision**;
  `visible_tiles()`, `in_vision()`, `champion_at`/`camp_at`. Hidden and dead champions expose only immutable
  `identity`/design ("works for hidden and dead champions").
- Static map: `width/height`, `walls/bushes/holes`, `altars`, `spawn_region`, `symmetry` and reflections, `camp_groups`.
- Global: `round_number()`, `global_submitted_gems()` (public team score), `team_size()`, `current_draft()`.
- Memory: team **shared memory** (writable, capacity from settings) and **draft memory** (1,024 B, frozen after draft;
  `draft_memory` is a *startup snapshot*: assignment submits bytes but doesn't change the snapshot; shorter writes leave
  later host bytes; oversized writes truncate).
- Fuel: `fuel_remaining()`; first draft turn 100× base, each champion's first turn 2× base (SDK comment line 5409;
  builder probe measured ~9.985M and ~184k on entry).

**Consequence for the contract:** an actor observation is per body and per call. It must not contain other bodies'
private state unless it came through shared memory that turn, and must not use `events`, the summary, or the replay.

## 4. Action API and ordering

Per champion turn (methods on `champion`), each gated by `state()` flags and `buff_restrictions`
(`move, attack, cast, shop, consumable, ward`):

- **Movement:** `move(delta)`, `move_absolute(tile)`, `move_toward`-style pathing ("reachable tile on a shortest path
  … returns false when already there, unable to move, no route, or hidden obstruction"). `can_move` gates it.
  Returns `false` on a newly revealed hidden obstruction (the action is spent without effect, *unverified*).
- **Attack:** `attack_entity(champion|camp|altar_lock)` within range; `can_attack`.
- **Abilities:** `ability(i)` ×2 per champion, `cast_entity`, tile/AoE variants; `valid_targets`, `valid_tiles`,
  `cooldown`; `can_cast`.
- **Economy:** `buy(item, n)`, `sell(item, n)`, buy/use consumables; `can_buy`, `can_sell` (shop restriction, location).
- **Channels:** `recall()` / `cancel_recall()`; `submit_gems(altar)` / `cancel_submit_gems()` (range from
  settings; duration grows with gem count).
- **Wards:** `place_ward(tile)` within `ward_placement_tiles`; charges recharge.
- **Scheduling:** `set_priority(p)` takes effect next round; `end_turn()` / `skip_empty`; `resign()`.

Ordering: the flags are re-read live, so **masks must be recomputed after each executed primitive** (e.g. a cast may
consume the attack, a move may leave range). The exact exclusivity between move, attack and cast within one turn is
**not documented in the header** and must be measured (E0 test `test_action_phases`), not assumed.

## 5. Fuel and the collection-vs-release gap

- Turn fuel: 100k ordinary, ~200k first champion turn, ~10M first draft turn; no carry-over; running out suspends the
  champion (`fuelExhausted` event). Lost turns cost little in game outcomes (Agent 2 E125; builder JD_GOV), but timing
  and feature freshness matter.
- `debug_block{…}` runs with fuel **paused** in non-release builds and is **removed** in release builds.
- Agent 2's RL rollouts (`nn_rl4.py`) are **debug builds**: sampling (`nn_ens_sample`) and NRL/NRZ logging run inside
  `debug_block`. In release, `nn_ens_sample` returns v92's choice unchanged (its body is skipped), and the deployed
  decision is the deterministic blend rule instead.

So three things differ between collection and deployment and need explicit E0 checks:
1. **Code path:** sampled (debug) vs greedy blend (release). E0: a debug build with sampling forced greedy must match
   the release build's per-turn primitive actions exactly.
2. **Binary layout:** debug and release WASM differ, so per-instruction fuel may differ outside `debug_block` too. E0:
   per-turn fuel trace (`team-*.fuel`) equality on the non-debug part.
3. **Spare fuel:** if anything charged in release sits inside `debug_block` in collection, collection turns have more
   fuel left, which changes pipeline admission and feature ages. E0: per-stage admission log equality.

## 6. Agent 2 recorder row formats (layout source of truth)

From `nnrec.cpp` (`kNF = kG + kS + kA·kAF + kE·kEF + kC·kCF + kL·kLF`):

| Layout | g | s | a (5×) | e (8×) | c (10×) | l (4×) | NF |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2 | 16 | 44 | 12 | 16 | 22 | 8 | **500** |
| 4 (`A2_NN_XF`) | 22 | 44 | 12 | 16 | 27 | 8 | **556** |
| 3 (legacy) | 16 | 44 | 16 | 16 | 22 (×24) | 8 | 828 |

Features are `int16`, base64-encoded on one stdout line. Rows:
- `NRZ <zid> <b64 X>`: the slow-part summary features that a later decision used (stale block).
- `NRL <round> <slot> <a> <logp %.5f> <chg 0/1> <zid> <bs> <b64 X>`: one sampled target decision. `a` ∈ 0..10
  (10 = "far", outside the 10 nearest groups); `bs` = index of v92's own choice (bonus applied); `X` = this turn's fresh
  features. The champion's id is `X[s_off + 31]`.
- **Rows are subsampled:** every target change is logged, other decisions with probability 1/`A2_NN_RL_KEEP`.
  Unlogged decisions still happened. Any return/advantage computation must account for the gaps (elapsed rounds) and
  the **inclusion weight** (`KEEP` for unchanged rows, 1 for changes).
- Sampling seed is `my_id + 1` per champion, so rollouts are reproducible given the same binary/map/opponent.
- `NR …` / `NRC …` rows are the older imitation recorder (v92 decisions, no log-probability).

## 7. Lifecycle

- Death is **not** episode end: champions respawn after the settings' respawn duration. A WASM instance persists across
  death, so C++ statics survive (*verify per body*; the builder found a phantom-respawn defect in event handling).
  Recurrent state must reset on an explicit, logged lifecycle event (respawn), not on observation gaps.
- Game end: `match.outcome` + `roundsCompleted` from the summary (terminated). Round cap/`--rounds`/timeout/log cut:
  truncated (bootstrap from the critic).
- Draft is a separate VM; its globals don't reach champion VMs, only the 1,024 draft bytes do.
