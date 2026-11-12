# Strategic audit 2026-10-28: PAUSED checkpoint (user asked to pause, ~19:45 UTC)

Status: investigation partly done. No deliverable documents except this one. Nothing committed, pushed, submitted or
activated. Frozen bots/v76 and the deep-analysis holdout are untouched (only examined-set TIMELINE_DATA.json was read).

## Environment
- Checkout: `work/neural-full-stack`, branch `checkpoint/research-v85-2026-10-28` @ 8a62987 (pre-existing uncommitted
  `config/paths.json` + untracked build logs are the user's; leave them).
- Read-only worktree of `origin/analysis/deep-2026-10-28` (a68aa9f) at `work/deep-analysis-wt` (detached; remove with
  `git worktree remove ../deep-analysis-wt` when done). That branch forks from v67 (294500b) and lacks v76-v85.
- Live: deep-analysis verified platform 69 = repo v75 (`bots/live-69` == `bots/v75`, byte-identical). Not re-verified here.
- Python `../neural-gameplay/.venv/Scripts/python.exe`, cambc 4.0.0, engine 2.0.0, wasi-sdk-33, 20 cores.
- Env for runs: `PYTHONPATH=$PWD/python NFS_REPLAY_ENGINE=2.0.0 TMP=$PWD/artifacts/tmp TEMP=$PWD/artifacts/tmp`.
- Runs: `research/v81/run_experiment.py RUN BOT OPP --seed 71 --workers 10` (140 games in ~0.5-1 min!).
  Proxy: add `--per-team --plan research/v70/pool_plan_teams.json`. Seed 71 used throughout (3/4 reserved).

## Measured so far (all runs under artifacts/evaluations/v67/SA-*)
1. **Fuel is not binding for v76.** Engine fuel trace (`team-X.fuel` in each bundle; parser `scripts/fuel.py`):
   mean ~40k/turn of 100k, p50 ~41k, p90 ~67k, p99 ~82k, ~0.5 fuel-outs/game. Profile (SA-C-prof, instrumented,
   behaviour-altering: 26.7 fuel-outs/game): farm 45%, score_groups 32%, world update 27% (hot zones 17%),
   handle_enemies 7%, tactical decide 3%, campnet 1.3% (567 fuel/turn).
2. **Learned components in v76:** only A2_CAMPNET (321-weight MLP re-ranker) and A2_MLDRAFT (53x64 MLP, draft turn
   only, ~1% of draft budget) are active; A2_LAB=1 is a 48-knob tuning layer, not a net; all other nets compiled out.
   Campnet evaluates in 2.6% of turns, overrides the base pick in 24% of evaluations, then locks for <=40 rounds.
   Draft net decides the lineup on 40/70 pool maps (not in V70 table) and every unseen map (80/80 drafts changed).
3. **NN ablations vs v65 (140 paired):** no-campnet -91 gems [-225,+41], -2.9pp; no-draftnet -72 [-178,+35], -7.1pp
   (on its 40 maps -11.2pp [-26,+5]); both off 75 vs 88 wins. Uncontested both-off: -118 gold, -16 gems at R500.
   **NOT established** (user challenge): self-play only; proxy replication running (SA-P-*).
4. **Local contested evaluation is near-chaotic:** removing campnet flips the winner in 66/140 games; paired margin
   SD ~620-830 gems (SE ~70 per 140). Uncontested metrics (vs bots/idle81) have paired SD 20-180 -> ~10x sharper.
5. **Economy headroom (same-map, examined ladder set vs SA-IDLE-v76):** in 191 losses, opponents' contested capture
   gold 2145 / gems 414 at R500 = 96% / 93% of OUR uncontested level; we retain 66% / 62%. In wins we retain 68%/80%
   and opponents get 46%/47%. Self-play vs v65: we retain 84% gold / 69% gems, v65 gets 71%/61%. Their extra gold over
   our idle is kill gold (393 vs 161) + tribute bonus (132 vs 36). Caveats: different drafts, loss-conditioned.
6. **Channel time:** opponents in our losses spend 658 champion-rounds channelling by R500 vs our 93 (recall/tribute).
7. **Carry economy:** top teams concentrate gold (top earner 0.38-0.83; SkibidiSloppers Vesper 0.54-0.79, 11 items
   by R300). Opponents beating us draft Vesper 71%/Marcella 84% vs ours 34%/69%; first purchase R54 vs R71.
   Existing UB_GOLD_FUNNEL is nearly inactive (+2..+7 gold uncontested). Prototype `scripts/init_carry.py`
   (sa-carry, sa-role, sa-rolecarry; sa-carry0 = exact v76 control) raises Vesper share 0.20->0.26-0.32 but team gold
   flat/down, contested -32..+7 gems (n.s.). Scoring tweaks inside the greedy scheduler do not reproduce it. STOP here
   per user: no more economy-scoring variants.

## Running at pause (local only, no platform effect)
Batch `SA-P-{base,nocn,nodraft,tsearch,nomapknobs,nolab}` vs proxy and `SA-C-{tsearch,nomapknobs,nolab}` vs v65.
Analyse with `research/v81/paired_strict.py CAND BASE`. If a run dir is incomplete, delete only that SA-* dir, rerun.

### Batch finished after pause (raw summary lines; paired analysis NOT yet done)
```
SA-P-base 115/140 wins, margin 426.8, fuel-outs 0.49     SA-C-base (v65) 88/140, 194.6
SA-P-nocn 108, 368.6        SA-P-nodraft 113, 367.1
SA-P-tsearch 80, 60.9, fuel-outs 16.08                   SA-C-tsearch 58, -130.0, fuel-outs 16.04
SA-P-nomapknobs 107, 326.5                               SA-C-nomapknobs 72, 23.5
SA-P-nolab 99, 278.6                                     SA-C-nolab 63, -2.0 (opponent fuel-outs 8.34: check)
```
First read, unverified: tactical search as built runs out of fuel (16/game) and loses heavily; removing the knob
layers costs 8-25 wins/140 vs both opponents; draft-net removal vs proxy is only -2 wins (so draft value is not
replicated). Run paired_strict.py on each before using these.

## Remaining (user's broadened scope)
- Combat architecture audit: handle_enemies (bot.cpp 3162-4223) is a stack of ~10 verdict overrides (burst, outnumbered,
  side-hp, TFC, neural fight/run, tsearch decide, fight2 strength gate, assess model, team-fight numbers, lab force,
  stand/escape); trace which are compiled/active and who has final authority. Results of tsearch ablation pending.
- Coordination (8-byte claims protocol), banking conversion (63% vs 88%), repeated deaths (respawn behaviour).
- Strategy portfolio (8-12), three designs, routes A/B/C, all deliverable docs listed in the mission Part 12.
- Draft verdict must use matched ablations (proxy replication) before any keep/remove claim.

## Update 2026-10-28 (planning session): superseded by the algorithmic plan

The paired analysis of the post-pause batch is now complete. Results and their interpretation are in
`research/algorithmic-plan-2026-10-28/FINAL_DEEP_ANALYSIS.md` §3 (E4–E6). In brief:
- tsearch −366 / −325, significant
- map knobs −100 / −171, significant
- lab + map knobs −148 / −197, significant
- campnet −58 / −91, not significant
- draft net −116 / −112 on changed-draft games, not significant
- the SA-C-nolab opponent fuel-out anomaly is one 00vault game: the known v65 siege freeze

Correction to point 6 above: the opponents' high channel time is largely the perma-recall pattern, not banking.

New scripts: `scripts/lomo_draft.py` (leave-one-map-out draft generalisation, E6) and `scripts/early_divergence.py`
(E28). The first mission's deliverable list is superseded by the plan set in `research/algorithmic-plan-2026-10-28/`.
Start there with its `HANDOFF.md`.
