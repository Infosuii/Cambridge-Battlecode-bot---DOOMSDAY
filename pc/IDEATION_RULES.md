# Ideation rules for the 5060 and 5070 (approved by Rishik, 2 Nov 2026)

Both helpers now invent and build x1 features in parallel with the PC, under these rules.

## Branches and code
1. Push only to your own branch: `build/z-plan-5060` or `build/z-plan-5070`. Never push to `main`, `build/z-plan`,
   `lab/box`, `ops`, `experiment/*`, `research/*` or Tamim's branches.
2. Every idea goes behind a new switch, off by default, named `X1_G60_*` (5060) or `X1_G70_*` (5070).
3. With every switch off, the build hash must stay 1746f2bb7fa3 (check with `tools/x1_flag_hashes.py`).
4. The PC stays the only writer of `bots/x1` on `build/z-plan`; it ports winning ideas after reviewing the code.
   Base your work on the latest `build/z-plan`.
5. v81hl parts and Tamim's features may be reused; never edit Tamim's code.
6. No ladder games, CLI logins, uploads or submissions.

## Before writing code
7. Each idea gets an ID (I-60-01, I-70-01, ...) and a card in `<machine>/ideas/<ID>.md`: the problem, with game or
   replay ids as evidence; the mechanism; expected fuel cost; the test plan.
8. Areas (no duplicate work):
   - PC: plan selector (CBR/IM), team camp planner (TOPTW), merging everything.
   - 5070: fights: kill-securing coordinator, range-ring kiting, survival / death reduction.
   - 5060: economy and banking, sparring stand-ins (S1/S2/S3), map-specific weaknesses.
9. Mining our own losses and replays for ideas is encouraged, inside your area.

## Fuel
10. Use as much of each turn's fuel as is safe, with zero fuel-outs: check the remaining budget before every
    expensive step; prefer anytime methods (deepen while `tc.allow()`).
11. An idea that gains wins but adds fuel-outs gets 2-3 attempts to cut its fuel; still adding fuel-outs ->
    rethink or drop.
12. No randomness without a fixed seed; replays stay exact.

## Testing
13. Gate with `x1_gate.sh` vs x2 and x2-s2 on ladder + styled + maze (59 maps). Baseline = current best line,
    BP = `--set X1_BUSHPRE=15 --set X1_BUSHPRE_LAZY=60`, not plain x1. Say the baseline in every report.
14. Pass: total wins >= baseline; no map kind more than 2 points worse; no new faults; no new fuel-outs on ladder
    or styled. Maze fuel-outs are reported only (pc/msgs/0009).
15. A pass must also hold vs v86h and v81hl (ladder + styled) before it is proposed for merging.
16. 38-game quick screens are bug / fuel checks only; nothing is ranked on them.
17. Retry before rejecting (research/x1/RETRY_QUEUE.md, R0-R3).

## Reporting and priority
18. Results in `results/*.md` + results.json and provenance only. Report every fuel-out, fault and loss.
19. Update STATUS.md; poll comms every 10 minutes.
20. At most 3 hours per idea before reporting where it stands.
21. Gate jobs from the PC (J*/K*) come first; ideation fills the remaining machine time.

## Real-ladder tests (Rishik, 2 Nov)
22. Rishik runs real-ladder games against the top teams for helper bots too. When your line has passed rule 15
    (vs v86h and v81hl), build its zip, commit it under `<machine>/ladder/<ID>.zip` on comms with a note
    (switches, gate results, which opponents and how many games you want). The PC checks it and sends the request
    to Rishik; do not contact him directly. Ladder results come back through pc/msgs.
