# Model ABI: Agent 2 student in the jd-g5070-1104 candidate (FEAT-003)

This is the runtime and data contract between Agent 2's network code (agent2-neural `56b60b96`, `rl_workspace/agent2/lab`) and the candidate `bots/jd-g5070-1104`.

The default build compiles none of it. With every `JD_*` switch at 0, the release WASM hashes to v92 (`5704d7ba…`). The port is applied by `py tools/jd_g5070-1104/mk_nn.py`, which refuses lab sources whose git blobs differ from 56b60b96.

## Versions and identity

| item | value |
|---|---|
| feature layout | **2** (500 int16). Layout 3 (828) is not supported. |
| model check | `jd_nn_event.cpp` `kModelOk` checks the header against the code: `kc_off == 248`, `kc_n == 10`, `kc_w == 22`, `ka_w == 12`, `ke_n == 8`, `kl_off + kl_n*kl_w == 500`, and `A2_NN_LAYOUT == 2`. On a mismatch the network is disabled and v92 decides (fallback reason `model`). `tests/nn_infer_test.cpp` static-asserts the same layout. |
| weights | `bots/jd-g5070-1104/src/jd_nn_weights.h`, written by Agent 2's `nn_export.py` (unchanged), sha256 `36ad83e1…` for `student_i2.pt` (sha256 `ba275a7d…`). See `MODEL_MANIFEST.json`. |
| export precision | `nn_export.py` prints floats with `%.7e` (8 significant digits). float32 needs 9 to round-trip, so the header holds a network that is about 1 ulp off per value. On 32 in-game decisions the logits differ from the raw checkpoint by up to 3.8e-3 abs (1.8e-3 rel), and by 1.1e-5 from the rounded network. Argmax agrees on all 32. `nn_golden.py` checks both. |

## Features (`nnrec.cpp` `nn_feats_t<10, 12>`, the recorder's code)

Every value is `q(v) = clamp(v, -32000, 32000)` cast to int16. Absent entity rows are all zeros: the buffer is cleared before every capture, which fixes Agent 2's stale-buffer bug.

| block | offset | rows x width | content (index: field) |
|---|---:|---:|---|
| g global | 0 | 1 x 16 | 0 round, 1 ally score, 2 enemy score, 3 winning gems, 4 team size, 5 slot, 6/7 map w/h, 8 #groups, 9 #allies, 10 alive enemies, 11 #sightings, 12 official map, 13 target_group (**dropped**), 14 fight (enemy within 6), 15 nearest enemy distance |
| s self | 16 | 1 x 44 | 0 type (one-hot of 13), 1-7 hp, max hp, strength x10, focus x10, range, gems, gold; 8-17 two spells (present, kind, range x10, cooldown, ready); 18/19 x/y; 20 spawn-field distance; 21 altar-field distance (-1 not ready); 22 bush; 23 hot zone; 24 recalling; 25 submitting; 26 prev hp; 27 can attack; 28 on ally spawn; 29 heading_home (**dropped**); 30 melee; 31 own id (**dropped**); 32-43 history: rounds on target, target changes in 50, hp 5/20 ago, dx/dy over 10, gems 20 ago, since bank, since contact, since respawn, min(round, 32), has target |
| a allies | 60 | 5 x 12 | nearest first. 0 present, 1 type, 2/3 dx/dy, 4-8 hp, max hp, strength, focus, range, 9 distance, 10 handle (**dropped**), 11 spawn distance |
| e enemies | 120 | 8 x 16 | visible (flag 1, nearest first), then sightings at most 30 rounds old not matching a visible enemy (flag 2). 0 flag, 1 type, 2/3 dx/dy, 4-11 hp, max hp, strength, focus, range, gems, tributing, recalling, 12 distance, 13 sighting age, 14 handle (**dropped**), 15 spawn distance |
| c camp groups | 248 | 10 x 22 | known walking distance first, then Chebyshev. 0 present, **1 group index** (dropped from the input; it maps the pointer slot to a group), 2/3 centre dx/dy, 4 Chebyshev, 5 gems, 6 gold, 7 state (0 alive, 1 reward, 2 respawning), 8 respawn in, 9 hp left, 10 max hp, 11 strength, 12 harmless, 13 since enemy seen, 14 other allies' claims, 15 allies near, 16 walking distance (-1 unknown), 17 enemy-side margin, 18 altar distance, 19 spawn distance, 20 allies closer, 21 is our current target |
| l altars | 468 | 4 x 8 | nearest first. 0 present, 1/2 dx/dy, 3 distance, 4 enemies within 4, 5 allies within 4, 6 spawn distance, 7 x*128+y (**dropped**) |

**Missing masks.** Row field 0 is the presence flag. Encoders run only on present rows. The pointer logits of absent camp slots are `-1e9`. Pooling is masked mean plus max (0 when empty).

**Normalisation (`nn_model.Prep`, exported mu/sd).** For every kept field: `(sign(x)*log1p(|x|) - mu) / sd`, with sd clamped at 1e-3 when fitted. Type fields are one-hot: self/ally/enemy type has 13 classes, clamped to [0, 12].

**History reset rules.** History is per champion VM (`Hist`, nnrec.cpp): 32-round rings of hp, gems, x and y. A round gap over 3 counts as a respawn. A bank is detected when the bag empties without a gap, and a target change from a `target_group` change. Static per-group constants (`gst`: centre, camp count, spawn and altar distance) are cached once and rebuilt only when bridges turn on.

**Field building.** With `A2_NN_FAST`, `nn_feats` builds the remaining group distance fields only while more than 110k fuel is left, so in practice only on the 200k first turn. Unbuilt groups read walking distance -1.

## Actions

| head | use | legal mask / executor |
|---|---|---|
| target pointer (10 camp slots + 1 "far") | **camp target** = the slot's group index. "far" = **KEEP_BASELINE** (v92 picks; fallback `far`). | Only present slots can win. The group must still exist, must not have gone to respawning since capture, and must not be unreachable (`group_distance >= kUnreach`). Executed by v92's own `farm()` (claims, staging, fights). |
| behaviour (8) | **BANK** gate only (`A2_NN & 2`, `A2_NN_FAST` form). 1 = force v92's tribute trip when gems > 0. Any other class suppresses v92's ordinary tribute call while the decision is held. No decision held: v92 banks as usual. | v92's `tribute_if_needed` executes. The win-now bank (`tribute-win`) is not gated. |
| option (5) | not used (`A2_NN_MACRO 0`). HOME / REGROUP / HUNT are not wired. | |
| micro heads | not evaluated (`kHBeh \| kHTarget \| kHOption` only) | |

## Runtime contract (`JD_NN_EVENT`, `jd_nn_event.cpp`)

- **When it infers.** An event arms the pipeline. Events: first turn, respawn, leaving contact, the held target finished or became unreachable, another ally newly claims it, the bag crosses 0/20/40/80 gems, or the decision is `JD_NN_PERIOD` = 16 rounds old. A held decision is dropped after `JD_NN_MAXDUR` = 64 rounds. Forced events (first, respawn, contact exit, finished, unreachable, max duration) restart a pipeline that is already running. The other events wait for it. The network never runs in contact; v92's fight code decides there.
- **Commitment.** The published target is held until an event. On periodic, bag or claim replans it is replaced only if the new slot's logit is more than `JD_NN_HYST` = 0.5 above the held target's slot.
- **Compute and admission.** The pipeline is step 0 (features), then six `nn::pipe_stage` steps. It runs at the end of the turn (`main.cpp` after `play_turn`). Each step is admitted by `rb::admit_optional(rb::kNN, est + 5k)` in the tail phase. `JD_GOV` bit 8 provides the reservation API without changing any stage. `est` is the worst case seen so far (+1/8) and is not learned from first runs or from steps that started with more than 100k. An overrun raises `est` to the step's true cost (left plus the part taken from the next turn), capped at 80k. At most one decision is published per turn. While a network target is held, `farm()` skips v92's own group scoring, so the full network and v92's scoring never run for the same choice.
- **Fallback (v92 decides).** Reasons: no decision yet (`nodec`), "far" slot (`far`), held target finished (`finished`) or unreachable (`unreach`), features older than `JD_NN_STALE` = 8 rounds at publish (`stale`), no camp group in the features (`ood`), held past the max duration (`maxdur`), respawned (`respawn`), model check failed (`model`). A refused step does not drop a valid held decision.
- **Controls.** `JD_NN_ZERO=1` runs the same computation at the same cadence and ignores the outputs: the data-only control. Agent 2's every-turn deployment is `JD_NN=3, A2_NN_FAST=1` without `JD_NN_EVENT`.
- **Diagnostics.** These are never on in a release build. `JD_NN_LOG` prints a `JDN D` line per decision (fuel, max step, steps, turns, event, target, bank class) and a `JDN C` counter line every 100 rounds. `JD_NN_REC` writes NR feature rows in `nn_record.py`'s format; they are queued and written on their own admission at about 28k fuel each. `JD_NN_DUMP=N` prints golden lines.

## Fixtures and tools

- `py tools/jd_g5070-1104/host_tests.py` runs `tests/nn_infer_test.cpp`: 400 inputs including all-zero, int16 extremes and random full-range rows with random presence flags. It checks finite logits, absent slots masked at -1e9, a deterministic forward, pipelined stages bit-identical to the one-shot forward, and slog symmetry and saturation.
- `<venv>\Scripts\python tools/jd_g5070-1104/nn_golden.py --dump <run>` needs a `JD_NN_DUMP=4, JD_NN_REC=1, JD_NN_LOG=1` run.
  - Feature transport: the features at publish equal the features at capture.
  - Argmax: WASM vs torch.
  - Host C++ vs torch on the dumped rows plus 64 saturated or random rows.
  - Pass: argmax 100%, rel err ≤ 1e-4 against the exported network, rel err ≤ 5e-3 against the raw checkpoint.
- `py tools/jd_g5070-1104/mk_nn.py --smoke` is the one-command path. It ports the lab code, checks the default hash (5704d7ba) and builds `JD_NN_EVENT`.
- `py tools/jd_g5070-1104/nn_bench.py <runs>` reports decisions, fuel per decision, fallback rates, thrashing and hold durations from `JDN` lines.
- Training driver: `tools/jd_g5070-1104/rl_dagger.py`. It does DAgger with the teacher as the expert, at the deployed cadence and official fuel. Lineage is written into `MODEL_MANIFEST.json` under `rl_runs`.
