# Prompt: start v53 development

You are continuing development of DOOMSDAY's Cambridge Battlecode 2026 bot. Repo: https://github.com/Infosuii/neural-networkk-battlecode (branch `main`). Goal: climb from ladder rank 87 to the top 25, then as high as possible.

1. **Set up and read.** Set up this device with `ops/SETUP.md`. Read all of `ops/HANDOFF.md` before changing anything.
   - Hard rules from it:
     - the bot runs at its fuel limit, so new logic goes behind once-per-call or once-per-turn checks, never inside per-group or per-camp loops;
     - judge every change with `artifacts/claude_ops/bench2.sh` and the gate in HANDOFF §4;
     - never enter credentials.
   - Approvals: you may queue unranked match groups, run long training, and submit a version that passes the gate.

2. **Analyse what v52 loses** (v52 has been live since 2026-10-25 12:02 UTC):
   - Pull our ranked games since then with `cambc matches list --team me --kind ranked --json`, then run `tools/replay/ladder_report.py` and `tools/replay/track_submission.py --since 2026-10-25T12:05:00Z`.
   - Read the queued match groups in `data/ladder/match_groups_20261025.json`.
   - Download and decode the v52 losses (`cambc matches download`, `tools/replay/decode_replays.mjs`). Rank them by map, opponent and draft.
   - For each loss pattern, compare what the winner did: farming order, bank timing and size, fights, deaths, draft and items.
   - Reproduce the worst maps locally with the logging build (HANDOFF §5) and find root causes, as was done for the moat and stampede bugs.

3. **Plan.** Write `artifacts/claude_ops/V53_PLAN.md` with ranked improvements, each with expected ladder impact and how it will be measured. Draw on:
   - top teams' replays (`cambc ladder --json`, then download their recent wins), especially on our weak maps: boss_battle, concentrated_wealth, elkring, swirl, yellow_brick_road, monolith, fracture;
   - strategy from similar games (MOBA jungling and objective timing, RTS economy and harassment, earlier Battlecode years' winning post-mortems): when to farm, bank, fight or group up;
   - fuel: profile the hot paths (`PROF` macros) and make them cheaper. It is likely the biggest general gain;
   - draft: our ladder win rate ranges 39-58% by pick. Build a draft model from ladder data and counter-pick.

4. **Build and ship.** Work in `bots/v53` (v52 with `A2_GATE_JOB` off):
   - one fix per change, each benchmarked with bench2 against `bots/v52`;
   - keep only changes that pass the gate;
   - run the 12 holdout maps;
   - submit with `cambc submit bots/v53 --note "..."` and write `bots/v53/CHANGES.md` with the measurements;
   - commit and push often, update `ops/HANDOFF.md` as you go, then track the ladder and iterate to v54.
