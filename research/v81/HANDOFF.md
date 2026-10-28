# PAUSED at the user's request, 2026-10-28

The user is low on usage and wants to continue on a fresh agent/laptop. Research is paused. No benchmark is running.
No bot was submitted, activated or selected live. Do not resume experiments until asked. Prepare/verify portability only.

Read `CONTINUE_HERE.md`, `research/v81/MISSION.md`, `RESEARCH.md`, then `research/v75/MG_18208504.md`.
The mission is sustained structural discovery, not threshold tuning. Target >=5pp robust gain, ~140-280 paired games
per opponent/check. Use ladder fight/economy measures, exact provenance, cheap mechanism tests before full screens.
No submission or activation without explicit approval. `ladder_duel.py run` activates its arms; never call it casually.

## Current truth

- Official read-only status: repo v74 is live **platform68**. Platform69 is repo v75, inactive.
- Established local comparator is v76. v80 (recall+treasure+reset) has not demonstrated improvement:397/560 vs396/560.
- Frozen v76 SHA256: `42071fa685aeabd7f074e86bbe73598db51ab9a0fae4d0bca62be2e2803d3cfb`.
- Frozen v80 SHA256: `8d11f97cfa7269736330acf119e3c61b08123530220455a5f558aa51e0903c73`.
- V81-85 are rejected or unproven experiments, **not releases**. Preserve v76/v80 source and review receipts.
- Old strict move-only metric was wrong. Correct no-basic/no-cast moves in90 ladder losses:46.6% ours/42.9% top,
  not44.7%/20.9%. micro.py fixed; historical outputs retained. Cast gap and native early-income gap remain.
- Public/mimic opponents all had unacceptable fuel exhaustion; do not claim strength against them.

## Completed new families

A, bots/v81: bounded complete action sequences. First implementation ran out of fuel. Corrected12-game check
4/12 vs7/12 control, paired -532 gems[-821,-243], deaths+3.8, gold-1513. Immediate damage objective failed.

B, bots/v82: event-based coalition economy scheduling. First12-game uncontested test exposes durable inaccessible
job on02arena. Added progress/watchdog release contract; still R200 gold-96, gems-76; R300 gold-110. Reject current
auction model, no broad competitive screen. V81/V82 disabled controls byte-identical to v76.

C, bots/v83: NumPy CART imitation of top-side retreat/hold/engage.50,912 actual legal snapshots, four whole-opponent
folds; confident intent accuracy69-79%, coverage34-47%. C++/NumPy inference checked on1,019 actual vectors. This is
classification, not counterfactual value. V83 disabled control identical to v76.140 paired games each, seed42:
v65 +3wins but -20gems[-139,+104]; proxy -8wins/-65gems[-167,+33]. Deaths and early-even fight deaths rise; R300
income falls. Reject stance imitation despite its classification accuracy. Full replay measures `intent_*`.

D, bots/v84: income-region denial. User pointed to fresh MG18208504 (0-5 vsSkibidiSloppers). Critical geometry
correction: yellow brick road's two600-gold groups are30-camp rows spanning BOTH spawns, not two exclusive home
camps. Gold group1 is already clear atR40 in the actual ladder game. A naive home-territory patch is not justified.
Tested two safe-endpoint guards against proxy, two sides:0/2 vs1/2, margin-886.5 vs+344.5; R300 own income-1890,
collected gems-36. Denial starves our own development. No broader screen. See `denial_*`.

E, bots/v85: concentrated gem objective with geometry detection, rendezvous and repeated clear/capture/reset cycle.
Tested10 games,5 maps/both sides vsv65:6/10 vs8/10, margin-231[-717,+307], gold-1790/game, fuel.4vs.1. Ribs
R300 collected gems+93 but final margin-205; concentrated-wealth+686, stampede-975, boss-battle-713, famine+54.
This is **not a finalist**. Family suggests harvest/conversion and gear prerequisites must be modeled together.
Latest source has only this first prototype. Do not broaden it without diagnosing readiness/banking interaction.
Geometry initialization also needs a hard per-loop fuel guard before any broader run. User paused before repairs.
Disabled v84/v85 control source folders exist (`q84disabled`, `q85disabled`) but their byte equality was NOT checked.

## Next highest-information work when resumed

1. Follow MG18208504 objective-conversion failures rather than reverting to the disproved2x movement-waste story.
   Inspect ribs' greater early gem harvest followed by lower final score: carrier banking, escorts, deaths and gear.
   Explicitly distinguish compact home groups from shared long strips; first-camp coordinates are not a centroid.
2. For any further concentrated-objective controller, use actual monster-clear feasibility and a team deposit/return
   phase. Current v85 sends workers toward difficult camps too early and lets the old bank/hunt hierarchy break cycles.
   This is a hypothesis requiring exact traces, not a request to tune the60% cutoff.
3. If continuing combat learning, learn value/counterfactual outcomes with calibrated legality/rollout models, not top
   action labels. Prior A2_ASSESS and tsearch work already exists; read history before duplicating it.
4. Representative local opponents remain unavailable. Current top replays cover12 teams but do not validate our
   candidate against them. No promising candidate currently warrants a submission/activation request.

## Reproduction and diagnostics

Git Bash from repository root. On this laptop Python was `../neural-gameplay/.venv/Scripts/python.exe`; on a fresh
laptop use the new virtual environment, never the old absolute path. CLI4.0.0, engine2.0.0, fuel100000.

```
P=.venv/Scripts/python.exe
"$P" research/v81/run_experiment.py NEW_RUN bots/v83 v65 --seed 42
"$P" research/v81/run_experiment.py NEW_PROXY bots/v83 proxy --seed 42 --per-team --plan research/v70/pool_plan_teams.json
"$P" research/v81/paired_strict.py CAND_RUN BASE_RUN
"$P" tools/v67/c_timeline_batch.py artifacts/evaluations/v67/RUN --workers 3 --glob "games/*/*.repl26a"
"$P" research/v75/teamfight_scripts/local_index.py RUN
"$P" research/v75/teamfight_scripts/compare_runs.py RUN BASE_RUN
"$P" research/v75/teamfight_scripts/native_windows.py CAND_RUN BASE_RUN
"$P" research/v81/diagnose_economy.py CAND_RUN BASE_RUN
```

The commands above are reproduction examples, not permission to resume while paused. Use fresh run names; strict
wrapper rejects incomplete games and records source/Wasm/SDK/CLI/engine hashes, both-team faults and fuel. Actual
opponent hashes and complete map/side/seed schedules must match. Invalid initial builds remain on disk for audit.

Evidence prefixes: SEQ81D, SCHED82D, INT83, HOME84D, OBJ85D; outputs in research/v81. Core v80 history in v75.
`HOME84D-trace2` is **invalid as behavior evidence**: debug code called group_distance before its field existed,
creating garbage distances and90.5 fuel-outs/game. Use unmodified HOME84D-baseidle/baseproxy instead. No strategic
claim relies on that trace. Do not rerun its preparation script unchanged. Other initializers may duplicate guards
or refuse existing directories; current frozen run sources and Git source are the authority.

## Portability scope

Code, research and tools are normal Git files. `continuation/checkpoint-2026-10-28/manifest.json` maps every archived
file to its SHA256. Split archive includes new full experiments, V76/V80 final comparison replay evidence, older V80
native summaries/build snapshots, actual v74/current/MG replays, parity vectors, release receipts and official Windows
runtime. Generic caches, compile_commands, credentials and the old CUDA training corpus are deliberately excluded.
They are not required for this research. Older V80 arm raw replays can be regenerated; reports, native summaries and
frozen source/Wasm are saved. Everything required for the immediate continuation is included.
