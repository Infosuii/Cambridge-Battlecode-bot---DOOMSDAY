# Feasibility-gated objective selection — 2026-10-29

Production change (first since `069dfb0`). Default Wasm SHA256:
`c4de5a1c21d673de7fe8549d9ac0522c09603f1ec24d7b4ee590cbc08b83bb1b`
(built from the source frozen in `dz-crew-idle-06` / `dz-crew-v65-06`).

## Diagnosis that motivated it

From the existing 140-game pools (`dz-low-fuel-regression-*`):

- Against **idle**, DZ banked 23 / 106 / 279 by R100 / R250 / R500 and died
  14.75 times per game, every death camp-caused (2,065 in 140 games). Each camp
  death destroys the bag and costs 60+ rounds.
- The planner score was `distance + 0.03 × strength`: an elk added 1.8 tiles of
  penalty, although the validated duel shows a lone Vendetta needs 35 hits and
  dies after 17. Champions walked into fights they could not win.
- 19% of captures had 2+ allies present and split the reward (crowding).
- Against v65, DZ died 10.65× per game to champions and 7.66× to camps.

## What changed

- `clear_risk.h` (SDK-free, host-tested against the native duel numbers):
  per-member attack work, Smith-order kill sequence, every live member assumed
  to hit each camp phase; `clear_survivable` needs HP > 1.25 × loss + 10% max.
  `crew_share` prices one crew member's share as two members' worth.
- Observation always reads Jungle/Durability (incoming) and Monster (outgoing).
- Planner: reward rate = (gems + 0.1 gold) / claims / (travel + clear + capture),
  solo-survivable groups only, pruned by an upper bound before pricing.
- Crews: only the lowest living slot (leader) starts a crew job; a follower that
  cannot solo the leader's damaging target joins it. The executor never wakes a
  sleeping damaging group unless the allies within 4 tiles make it survivable.
  An awake losing clear is abandoned. Crew contracts allow 40 idle rounds.
- Exponential avoid back-off (15..240 rounds) for failed contracts; reset when
  a group is seen respawning.
- Starvation fallback: 150 rounds without team income → that champion uses the
  old nearest-group score with no gates for 300 rounds.
- Clear risk memoized per group (HP version counter, damage, factor). Idle
  champions re-plan every 4 rounds.

These are heuristics, not the calibrated ObjModel; V-M1 stays open.

## Results (140 games each: 70 maps × both sides; deterministic, not seeds)

| Run | Opp | Banked | Opp banked | Deaths | R100 / R250 / R500 banked | Fuel p99 | Faults / outs |
|---|---|---:|---:|---:|---|---:|---|
| dz-low-fuel-regression-idle-01 (base) | idle | 903.5 | 0 | 14.75 | 23 / 106 / 279 | 53,220 | 0 / 0 |
| dz-feasible-idle-01 | idle | 819.5 | 0 | 1.45 | 37 / 124 / 282 | 73,044 | 0 / 0 |
| dz-crew-idle-01 | idle | 823.6 | 0 | 0.12 | 38 / 127 / 290 | 95,143 | 0 / 0 |
| dz-crew-idle-02 | idle | 827.1 | 0 | 0.05 | 39 / 129 / 292 | 89,823 | 0 / 0 |
| dz-crew-idle-03 | idle | 842.6 | 0 | 0.04 | 39 / 132 / 295 | 89,057 | 0 / 0 |
| dz-crew-idle-04 | idle | 860.9 | 0 | 0.06 | 40 / 134 / 298 | 73,841 | 0 / 0 |
| dz-crew-idle-05 | idle | 850.6 | 0 | 0.26 | 40 / 133 / 298 | 86,115 | 0 / 0 |
| **dz-crew-idle-06** | idle | **918.4** | 0 | 3.80 | 41 / 135 / 306 | 55,581 | 0 / 0 |
| dz-low-fuel-regression-v65-release-01 (base) | v65 | 186.0 | 1033.7 | 18.31 | 13 / 44 / 102 | 52,358 | 0 / 0 |
| **dz-crew-v65-06** | v65 | **200.3** | 1020.1 | 17.38 | 20 / 65 / 116 | 55,742 | 0 / 0 |

Paired against base, `-06`: idle +14.8 banked (60 cells better, 72 worse),
R500 +27.5; v65 +14.3 banked (72 better, 54 worse), first contested win (1/140).
Worst idle cells: 01concentrated-wealth, 00ribs, 01the-farm (−300..−430).
Worst v65 cells: 01yellow-brick-road A, 01islands B, 01big-world A.

## Retained failures and lessons

- `-feasible-01`: the gate alone idles on elk/golem-only maps (zero banked).
  Same failure as the earlier camp-safety experiment: survival without an
  alternative productive job loses banking.
- `-crew-01..03`: crew pricing used the evaluator's own strength and assumed
  concentrated damage, so weak hitters refused to join; crews spread across
  members. Fuel p99 reached 95k: recomputing risk for every group, every turn
  cost 50-68k planner fuel and made `tc.allow` cut candidate loops short,
  which itself caused idling (`dz-fuel-trace-01` vs `-02`).
- `-04/-05`: the crew pass only ran when no solo option existed; soft claims
  split crews over several groups. Leader-only crew decisions fixed 02gift-wrapping
  but 01islands / 02the-pond still collapsed until the starvation fallback.
- Trace diagnostics `dz-crew-trace-gift-*`, `dz-trace-islands-*`,
  `dz-fuel-trace-*` are behavior diagnostics, not strength evidence.
  `dz-trace-islands-02` froze a temporary per-round trace window (since removed).
  Attempts `dz-crew-trace-gift-02/03/04` failed to build (trace printf escape),
  have SEED_LEDGER rows and no capsule.

## Open problems

- 01islands still farms little in the new mode before the fallback; it likely
  needs teleport-aware routing (map feature, not yet investigated).
- Contested deaths are mostly to champions: engagement/retreat logic is next.
- The 1.25 margin, 2/crew share, 150/300 fallback timings and 0.1 gold weight
  are untuned guesses. Tune only on the development pool, never the holdout.
