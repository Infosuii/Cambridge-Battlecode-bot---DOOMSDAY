# NN_BENCH: Agent 2's student at official fuel (FEAT-003)

This benchmarks the lightly trained student `student_i2.pt` (sha256 `ba275a7d…`, header `36ad83e1…`; see `MODEL_MANIFEST.json`) inside the candidate at **official fuel**: no `--fuel-quantum`, so 10M draft, 200k first champion turn and 100k ordinary turns.

**Status labels:** runtime/export path **working**; numbers **measured**; model **lightly-trained**; heads **experimental, kept OFF**.

**Cells.**
- **conf** = the 16 largest dev maps x v92/x3inv/p65pack x both sides = 96 cells.
- **dev** = 90 dev maps x v92 x both sides = 180 cells.

Every arm is paired cell by cell with v92 on the same map, opponent and side. d_score is in points (100 x score) with a map-clustered bootstrap 95% CI (2000 resamples, seed 1104). All runs: 0 missing, 0 failed, **0 bot faults**.

Run data: `jd-eval/runs/<run>`, compact copies in `research/jd-g5070-1104/runs/<run>.json`, network statistics in `nn_bench.json` (from `tools/jd_g5070-1104/nn_bench.py`).

## Arms

| arm | build (`jdrun.py freeze jd-g5070-1104 --defines`) |
|---|---|
| nn-every | `JD_NN=3, A2_NN_FAST=1, JD_NN_LOG=1`: Agent 2's every-turn deployment. Features and the full forward run on every out-of-contact turn. |
| nn-event | `JD_NN=3, A2_NN_FAST=1, JD_NN_EVENT=1, JD_NN_LOG=1`: the event runtime (MODEL_ABI.md). |
| nn-zero | nn-event + `JD_NN_ZERO=1`: same computation and cadence, outputs ignored (data-only control). |
| target-only | nn-event with `JD_NN=1` (no bank gate). Cadence revision 1. |
| residual | nn-event + `JD_NN_RESID=1`: KEEP_BASELINE dominant; the network target must beat v92's choice by 1 logit. Cadence revision 2. |
| `…q` | same arm without `JD_NN_LOG`: the release-like fuel-out count. |

**Runtime versions.**
- **v1:** Agent 2's overrun rule fixed (capped).
- **v2:** an overrun raises the estimate to the true cost.
- **v3 (final):** the step-0 estimate is sized by map area (64k above 60x60) and learned from the first run.

## Results

| run | arm (runtime) | wins / v92 wins | d_score (95% CI) | fuel-outs (v92) | decisions per champion | net fuel per decision p50 / p95 / max | max step p50 / p95 | suspended NN steps |
|---|---|---|---|---|---:|---|---|---:|
| conf-nn-every-01 | every | **0** / 56 | **-58.3 (-67.7, -49.0)** | 189,175 (147) | 403 | 84.9k / 88.0k / 117k (one turn) | = | 182,653 (97% of decisions) |
| scr-nn-every-01 | every | 3 / 90 | **-48.3 (-50.0, -46.1)** | 282,969 (123) | 355 | 86.1k / 89.4k / 133k | = | 270,927 |
| conf-nn-event-01 | event v1 | 53 / 56 | -3.1 (-17.7, +12.5) | 536 (147) | 45.2 | 105k / 125k / 167k | 28.3k / 37.7k | 353 |
| conf-nn-zero-01 | zero v1 | 68 / 56 | +12.5 (+3.1, +20.8) | 578 (147) | 38.3 | 104k / 125k / 170k | 27.4k / 37.1k | 354 |
| scr-nn-event-01 | event v1 | 73 / 90 | **-9.4 (-16.7, -2.2)** | 497 (123) | 58.0 | 107k / 127k / 154k | 25.7k / 35.3k | 249 |
| scr-nn-zero-01 | zero v1 | 88 / 90 | -1.1 (-8.3, +6.1) | 544 (123) | 52.2 | 106k / 127k / 153k | | 248 |
| conf-nnevent2-01 | event v2 | 54 / 56 | -2.1 (-13.5, +6.3) | 574 (147) | 32.1 | 104k / 125k / 167k | 26.9k / 37.3k | 357 |
| conf-nnzero2-01 | zero v2 | 62 / 56 | +6.3 (-2.1, +14.6) | 592 (147) | 25.8 | 103k / 125k | | 359 |
| conf-nnevt1-01 | target-only v2 | 52 / 56 | -4.2 (-16.7, +6.3) | 591 (147) | 31.3 | 104k / 125k | | 356 |
| conf-nnresid-01 | residual v2 | 58 / 56 | +2.1 (-9.4, +13.5) | 592 (147) | 26.1 | 103k / 125k | | 359 |
| conf-nnevent3-01 | event v3 | 57 / 56 | +1.0 (-14.6, +15.6) | 270 (147) | 21.7 | 103k / 127k / 181k | 26.7k / 37.0k | **16** |
| conf-nnzero3-01 | zero v3 | 61 / 56 | +5.2 (-6.3, +16.7) | 218 (147) | 16.8 | 103k / 129k / 181k | 26.5k / 38.1k | 16 |
| conf-nnresid3-01 | residual v3 | 51 / 56 | -5.2 (-17.7, +6.3) | 252 (147) | 16.2 | 103k / 130k | | 18 |
| scr-nnevent3-01 | event v3 | 70 / 90 | **-11.1 (-17.8, -4.4)** | 409 (123) | 46.3 | 107k / 128k / 181k | 24.9k / 34.6k | 74 |
| scr-nnzero3-01 | zero v3 | 91 / 90 | +0.6 (-6.7, +7.2) | 379 (123) | 37.9 | 107k / 128k | 24.5k / 34.3k | 76 |
| scr-nnresid3-01 | residual v3 | 55 / 90 | **-19.4 (-26.1, -12.8)** | 397 (123) | 37.7 | 107k / 128k | | 75 |

**Release-like builds (runtime v3, no `JD_NN_LOG`).** The logging lines cost fuel too: a JDN line costs roughly 20 fuel per byte of stdout.

| run | arm | wins / v92 wins | d_score (95% CI) | fuel-outs (v92) | fuel-out games (v92) |
|---|---|---|---|---:|---:|
| conf-nnevent3q-01 | event | 57 / 56 | +1.0 (-11.5, +12.5) | 197 (147) | 36 (39) |
| scr-nnevent3q-01 | event | 76 / 90 | **-7.8 (-13.9, -1.7)** | 255 (123) | 40 (25) |
| conf-nnzero3q-01 | zero | 59 / 56 | +3.1 (-9.4, +15.6) | 166 (147) | 37 (39) |
| scr-nnzero3q-01 | zero | 91 / 90 | +0.6 (-6.1, +7.8) | 222 (123) | 38 (25) |

**Event runtime v3 behaviour.** Shares are of out-of-contact turns, conf / dev.
- **Applied rate:** a network target was held on 19.8% / 45.5% of turns.
- **v92 fallback by reason:**
  - respawned, waiting for the first decision: 38.9% / 20.7%
  - held target finished, next decision pending: 16.5% / 21.3%
  - no decision yet: 15.4% / 5.3%
  - "far" slot chosen: 6.4% / 5.5%
  - stale (features more than 8 rounds old at publish): 2.6% / 0.9%
  - max duration: 0.5% / 0.7%
  - out of distribution / model: 0.
- **Target thrashing:** 5.58 / 5.52 switches per 100 turns, against 5.88 / 5.70 for the zero arm (v92's own switching).
- **Held-decision durations:** mean 17.2 / 21.5 rounds.
- **Decision latency:** p50 1 turn, p95 3-4, max 8.
- **Pipeline counters (dev):** 2,944 aborted (contact or forced events), 87 stale, 283k refused step admissions. A refusal waits for the next turn.

## Findings

1. **Every-turn inference cannot run at official fuel.** Features plus the forward cost 85-89k on one turn, on top of v92's own work, so 97% of decisions suspend the champion. Result: 0/96 and 3/180 wins. The 109k-per-decision figure from Agent 2 is confirmed (event arm p50 103-107k, p95 125-130k).
2. **The event runtime fits official fuel.**
   - **Pipeline:** the decision is spread over 1-4 turns of end-of-turn spare fuel, each step admitted by `rb::admit_optional(kNN)`.
   - **Volume:** 17-58 decisions per champion per game, with 0 faults.
   - **Suspensions:** 16 suspended network steps on conf and 74 on dev after the v3 estimate fix (353 and 249 in v1).
   - **Two bugs found and fixed in Agent 2's pipeline logic:**
     - The overrun rule `est = left + reserve` locked the pipeline after the 200k first turn (nn-golden-01: one decision per champion per game).
     - The 34k features estimate is wrong on maps above 60x60, where features cost 55-60k.
3. **The student's decisions are worse than v92's at the deployed cadence.**
   - **nn-event vs v92:** -9.4 and -11.1 on dev, with CIs excluding 0.
   - **nn-event vs nn-zero:** -15.6 / -4.2 on conf and -8.3 / -11.7 on dev.
   - **Revisions tried:** two cadence revisions (target-only, then a KEEP-dominant residual) gave no credible gain. The residual arm was worse on dev (-19.4). It keeps v92's target, so the bank gate holding "do not bank" between decisions is the likely cost. FEAT-003 stops revising here, as planned.
   - **Release status:** heads stay **OFF** (Rejected for release).
4. **The data-only control is not neutral.**
   - **Measured:** nn-zero won +12.5 (+3.1, +20.8) on conf in v1, and +6.3 and +5.2 in v2/v3 (CIs crossing 0). It is neutral on dev (-1.1, +0.6).
   - **Mechanism candidate:** with `A2_NN_FAST`, `nn_feats` builds every remaining group distance field on the 200k first turn whenever more than 110k is left. That is a pure side effect of the network code. Claude independently connects it to FEAT-002's large-map losses from deferring work.
   - **Status:** discovered on conf/dev, so it must be judged only on **selection** (and the large-map stratum), then holdout. **Conditionally useful (unverified mechanism)**, to be isolated as its own switch in FEAT-004/005.
5. **Fuel-outs (suspended champion turns) do not track wins here**, as in FEAT-002. The zero arm has 1.5-3x v92's fuel-outs and is neutral to positive.
6. **Export fidelity.** `nn_export.py`'s `%.7e` loses float32 round-trip precision: up to 3.8e-3 logit error against the checkpoint, 1.1e-5 against the rounded network, argmax unchanged on all sampled decisions (`nn_golden.py`). The SIMD path is compiled: the event build has 284 `f32x4.add` and 206 `f32x4.mul` opcode patterns against 30/28 in v92, and the WASM is 822 KB against 449 KB.
7. **Recording cost.** Printing one 500-feature row costs about 28k fuel (95k with std::string + printf), so `JD_NN_REC` queues rows and writes them on their own admission. Training data is recorded at the deployed cadence without slowing it.
