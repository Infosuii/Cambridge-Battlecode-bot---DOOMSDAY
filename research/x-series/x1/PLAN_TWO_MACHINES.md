# x1 plan on two machines (from 2 Nov 2026 08:00)

Goal unchanged: a competition-winning bot clearly above v88 (the benchmark: v86h + x1's fuel fix + camp watch).
Approach unchanged: hardcode a few team strategies; algorithms discover, choose and tune them; every feature goes
through the retry protocol (research/x1/RETRY_QUEUE.md) before it can be rejected.

## Who does what

| Machine | Strength | Role |
|---|---|---|
| **PC** (Rishik, 8 threads) | where the code and history live | **Develop**: sole writer of `bots/x1` and the plan docs. Writes every switch, builds it, checks it fires (R0), quick screen on 38 + 38 cells, then posts a gate job. Fits the small models (plan selector, race model) from the 5060's data. |
| **5060 PC** (faster CPU, 2x RAM, RTX 5060) | game volume (games are CPU-bound Wasm; the GPU is not needed for games) | **Run at volume**: full gates (R1), retry variants (R2), the branch farm (phase 3), the joint search (phase 7, R3), the league. Sole writer of its own code branch and results. |

Games are deterministic, so a result from either machine is exact and comparable (checked at 5060 setup by
reproducing x1 vs x2 on the ladder: 68/140, game for game).

## Development cycle (each feature)

1. **PC** writes the change behind a switch on `build/z-plan`, builds it, checks the binary changes and the
   behaviour fires (R0), and runs a quick screen (19 ladder + 19 styled maps vs x2, ~10 min). The quick screen only
   catches bugs, faults and fuel-outs; it never rejects on score.
2. **PC** pushes, then posts a job on `comms/x1` (`pc/jobs/Jnnn.md`: commit, bot, switches, expected hash, run type).
3. **5060** pulls that exact commit, checks the hash, runs `tools/x1_gate.sh` (all map kinds, x2 and x2-s2), posts
   `g5060/results/Jnnn.md` with the verdict by the rule below plus the run `results.json` files.
4. **PC** applies the verdict: kept switches turn on in `bots/x1` (PC only); others go to the retry queue with
   their next retry step. Kept and retry-pending switches all enter the joint search (R3).

Gate rule (R1): total wins ≥ base on all cells combined, no map kind more than 2 points worse, no new fuel-outs or
faults. Both machines read the same numbers, so the verdict is mechanical.

## Schedule

| When | PC (develop) | 5060 (run) |
|---|---|---|
| 2 Nov 08-10 | Plan hook in x1: `X1_PLAN_ID` / `X1_PLAN_ROUND` read through volatile (as v76p did), checked that branches equal the base before the switch round | **B0** setup, hashes, reproduce x1 vs x2 ladder 68/140; take over sweep 1d (the PC stops its copy) |
| 2 Nov 10-14 | Plan 1: answer to early contact (QS2isLaw / 0xDEADBEEF profile) | **B1** sweep 1d remainder vs x2; retry round 1 (queue #1, #2 variants: R1 + R2) |
| 2 Nov 14-22 | Plans 2-4: fast farm and bank; endgame denial with the power-play trigger (#14); safe bank when ahead. Port v86h's four structural pieces into x1 as switches (#7) | **B2** branch farm starts on plan 1 as soon as its job lands; adds plans 2-4 as they land (rounds 150 / 250 / 350, all lost and close games vs x2 and x2-s2, all map kinds) |
| 3 Nov | Plan selector from the farm's labels (map features + signals by R150; stance rule #15 as an input); race / finish-time model; fights code: cohesion, isolated-enemy targets, dead-end and choke maps (draft-turn precompute) | **B3** farm finishes; gates for every PC candidate; retry round 2 (#4 mastery from x1-vs-v88 games, #12-13 HoR inside plan 1, #16 hunter pair, #3 under plan 1, #10 Lanchester plan gate) |
| 4 Nov | Integrate gate passes into x1; set up the search space: all kept + retry-pending switches with their knobs, plan knobs | **B4** joint structure + knob search (R3) with held-out maps of all three styles, validated on seed builds, read in 5-generation windows |
| 5 Nov | Final x1 build, ablation report, zip for the ladder; analyse new ladder games | **B5** ladder layer and per-map tables refit on top of the search centre (seed-validated); league with sparring stand-ins (early-contact aura, a potential-field bot); final ablation (every switch off one at a time) |
| 5 Nov night | **Finish**: final zip to Rishik for upload | final gate numbers posted |

This is about a day earlier than the one-machine plan (6 Nov), with nothing dropped: the full gate runs on every
candidate, every rejection gets its retries, and the joint search covers every switch.

## Findings protocol (Rishik, 2 Nov)

Any findings the 5060 pushes (g5060/results, g5060/findings) are the PC's to act on: the PC decides what happens,
updates this plan and RETRY_QUEUE.md, and answers in pc/STATUS.md. The 5060 keeps running its queue meanwhile.

## Inputs added on 2 Nov

- research/x1/TOP_TEAMS_2026-11-02.md: 35 games vs ranks 1-5 + QS2isLaw + 0xDEADBEEF, 3 wins. Slow economy (half
  their gold by R500) and feeding collapses (9/35). -> X1_ANTIFEED (J006); gold and deaths now in every report.
- research/x1-audit-2026-11-02 (branch, ishanp765): 35 replays, 20 reproduced byte for byte from x1. Retreat/farm
  oscillation, collection throughput (68% of the loss deficit), team-bag conversion, four model defects. -> six
  switches (J007) and the throughput knobs in the joint search.
- Sparring: v88 never farms us, so a stand-in that makes early contact and out-farms us is needed earlier (5060
  proposal after J003).

## Phase 4 design: case-based plan selection over influence maps (2 Nov)

research/x1/CBR_IM_ARCHITECTURE.md (Weber & Mateas AIIDE-09 conceptual neighbourhoods; Sugandh, Ontañón & Ram
AAAI-08 alive conditions and on-line adaptation): cases = J005 branch outcomes keyed by influence-map topology and
game state; retrieval picks the team plan per checkpoint; alive conditions revert it. **Deferred until the current
gates (J009, J010, J006, J008, K002) report**: those decide which plans and switches the selector chooses between.
Then: PC builds X1_IM / X1_CBR; 5060 J011 (harvest map descriptors) and J012 (case library + leave-one-map-out test).

## Rules that keep the two machines apart

- Code: PC pushes only `build/z-plan`; 5060 pushes only `build/z-plan-5060` (its harness and helper code). Neither
  pushes `main`, `lab/box`, `ops`, any `experiment/*` branch or Tamim's branches, and neither merges the other's
  branch; the PC cherry-picks 5060 tools when needed.
- Comms: orphan branch `comms/x1`, folder `../x1-comms` (via `tools/x1_comms.sh`). PC writes only `pc/`, 5060
  only `g5060/`. Nothing in `comms/x1` is ever merged into a code branch, and no code is committed there.
- Big files: `evidence.zip` replays stay on the machine that played them; comms carry `results.json` and summaries.
- Each machine polls `comms/x1` every 10 minutes while it has open jobs.
