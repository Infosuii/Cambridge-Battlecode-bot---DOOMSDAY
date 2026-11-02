# Feature sweep on x3 (= v92): every dropped feature, refit or abort (Rishik, 2 Nov 17:00 UTC)

Base: bots/x3 (v92 patched onto x1; default build byte-identical to v92, 5704d7ba41ac). Every feature dropped since the
first research prompt is retried on this base, optimised when it fails, and aborted only after the refinement steps.

## Protocol

- **Screen S**: x3 + variant vs v92, gate set `pool` (the 86-map competition pool, both sides, 172 games).
  Deterministic; noise floor about +-8 (g5060 findings/0006). x3 plain vs v92 = 86/172.
- **S >= 92 (+6)**: promote to **Full F**: vs v92, v86h, x1bru on pool + styled + maze; pass = total >= base + 6 with a
  paired sign test z >= 1.3, no kind more than 2 points worse, ladder+pool fuel-outs not up more than 10%.
- **S 81-91**: refine, up to 3 more variants: the parameter around the best value; + `X1_WALKTAIL=3` when fuel-outs
  rose; + the best partner feature; a mechanism change (PC) when the switch is structurally wrong for v92.
- **S <= 80 after refinement**: abort, with the reason written here.
- Survivors are stacked greedily (best first, each kept only if the stack gains), then re-tuned together.
- Note: x3 has A2_HYB 3 (v81 knobs, no runtime structural switches on recognised ladder maps); compile-time
  switches still apply everywhere.

## Features (owner: 60 = g5060 J019, PC = new or changed code)

| # | Feature | Earlier best | Variants to screen | Owner | Status |
|---|---|---|---|---|---|
| 1 | A2_BURST2 | +13, fuel +20 | 1; 1 + WALKTAIL 3 | 60 | |
| 2 | A2_TS_VIS | +11, fuel +84; +16 maze | 1; 1 + WT3; 1 + BUSHPRE 15/60 + WT3 | 60 | |
| 3 | V58_LOCKS | +8, fuel | 1; 1 + WT3 | 60 | |
| 4 | A2_DISENGAGE | +7, fuel | 1; 1 + WT3 | 60 | |
| 5 | X1_PRUNEFIX | +11, styled fail | 1; 1 + WT3 | 60 | |
| 6 | X1_ECON stage | +11 | STAGE_MULT 0.5 / 0.7 / 0.35 | 60 | |
| 7 | X1_ECON wait | +8 / +9 | WAIT_MULT 1.5 / 2.0 / 1.25 | 60 | |
| 8 | X1_ECON need | +6 | NEED_MULT 1.3 / 1.15 / 1.5 | 60 | |
| 9 | A2_BELIEF | +5, +13 on BP | 1; 1 + WT3 | 60 | |
| 10 | A2_HIDEREC | +7 | 1; 1 + WT3 | 60 | |
| 11 | X1_SOAK64 | +10 | 1 | 60 | |
| 12 | APEX_ESCORT | +8 | 1 | 60 | |
| 13 | A2_BURST_HOLD | +3 | 1 | 60 | |
| 14 | X1_SECURE | +4, +2 on P4 | MULT 3 (0 on v92: done), 1.5, 6 | 60 | 86/172 at 3 |
| 15 | X1_BUSHPRE | +18 on x1 | 15/60 (79: done), 25/70, 10/50 | 60 | 79/172 at 15/60 |
| 16 | X1_SIEGEFUEL | +2 | 45, 55 | 60 | |
| 17 | X1_ANTIFEED | +27 (af3w250, pre-fuel-fix) | 3/250, 5/400, 4/150 (each + WT3) | 60 | |
| 18 | X1_FLEEDROP | 22 vs 17 screen | 15, 25, 40 | 60 | |
| 19 | X1_FLEEHOLD | -18 | 4 | 60 | |
| 20 | X1_TEAMWIN / X1_HEARTFIX / X1_BAGRISK | -1 / 0 / quick +3 | 1 each; BAGRISK 40 / 80 | 60 | |
| 21 | X1_HUNT_SOLO | 0 games changed on x1 | 3, 5 | 60 | |
| 22 | X1_ALONE (x1's alone alert) | -25 on x1 | 1 | 60 | |
| 23 | V58_VISION / A2_THREAT / APEX_STALE_BAG | -13 / -2 / -11 | 1 each | 60 | |
| 24 | A2_RESETFIX / A2_FIELDFIRST / A2_MAP_PROFILE | -4 / -13 / -6 | 1 each | 60 | |
| 25 | A2_POLICY / A2_ASSESS | -27 / -35 (fuel) | 1 + WT3 | 60 | |
| 26 | Items: V58_ITEM_PLAN=0 (Treasure + Bruiser), A3_ITEMS 1 / 2 | -6 / -14 on x1 | each | 60 | |
| 27 | Plans 1-8 per map on the 16 new maps | plan 7 20/32 vs v92 | per-map table X1_MAPPLAN | PC | search running |
| 28 | Plans 4 / 7 as whole-game lines | p4r150 +39 pooled on x1 | p4 R100 / R150, p7 R0 / R250, each + WT3 | 60 | |
| 29 | X1_EARLYFLEE / X1_LEASH | deaths up on x3 | refit as fight-model inputs (PC) | PC | |
| 30 | Conversion fix (bank the winning bag) | BANK_RATIO 3.0: 0.83 -> 0.88 | I-60-04 rebased on x3 | 60 | |
| 31 | Kill-securing coordinator (full) | never built | PC builds on v92's Lanchester verdict | PC | |
| 32 | Bruiser items + v92 fight model | not tried | V58_ITEM_PLAN=0 with Lanchester weights re-read from stats | PC | |
| 33 | Team camp planner (TOPTW) | never built | PC, after 31-32 | PC | |
| 34 | Plan selector (CBR / IM) | parked | revisit once the per-map tables show which plans win where | PC | |
| 35 | X1_CORNERED (fight back when a losing chase has lasted N turns, chaser within 2) | new; 03one-gem N=2: deaths 76 / 35 vs 72 / 21 | N = 2 / 3 / 5 on pool vs v92; + X1_KD fight ES best | 60 | |
| 36 | X1_FIRSTFIELD (turn-1 field guard) | new; 03contours all bodies ran out on turn 1 | 1 on pool vs v92 | 60 | |
