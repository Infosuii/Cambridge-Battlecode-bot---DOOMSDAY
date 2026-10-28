# Handoff: fixing the three fight/gear gaps (bots/v80), 2026-10-28

## New structural mission and audit errata

**Paused at the user's request for a fresh-laptop handoff.** Start at repository `CONTINUE_HERE.md` and
`research/v81/HANDOFF.md`. New V81-85 experiments and the MG18208504 geometry correction are recorded there.
No benchmark is running and no platform operation was made. Do not restart research until the user resumes.

The user has authorized sustained local architectural research, not only the historical V80 fixes. Current research is
in `research/v81/RESEARCH.md`; preserve all frozen V76/V80 evidence. V76 remains the established comparator, V80 is not
a proven upgrade. No submission, activation or live change is authorized. Official read-only status confirms repo v74
is live platform **68**; platform 69 is repo v75 and inactive.

The old movement comparison was wrong: `micro.py` counted only action sets exactly `{4}` and excluded moves with
recall/cancel/ward. Correct movement without basic/cast in the 90 losses is **46.6% ours vs 42.9% top**, not 44.7% vs
20.9%. Type-specific strict-movement conclusions also fail. `micro.py` is now corrected; historical output is preserved.
Casting and exact native early income gaps survive. Raw HP and loss selection do not establish equal combat power.

`ladder_duel.py run` ACTIVATES each arm. The suggestion below to use paired ladder arms without live selection was
incorrect. Do not execute that workflow without explicit approval for submission AND temporary activation.

Repo root: `C:\projects\cambridge battlecode\work\neural-full-stack`. Python: `../neural-gameplay/.venv/Scripts/python.exe`
(called `$P` below). Bash (Git Bash) for the commands. Goal: a bot that wins CAMBC Battlecode 2026; the user wants real
results, not marginal tuning.

## Continuation status (read before the historical plan below)

The six pending screen runs completed. `v80_fix_paired.txt` and `v80_fix_replay_measures.txt` have the comparisons and
the original ladder metrics; `v80_fix_pooled.txt` adds identical-schedule pooled metrics/early equal-power fight deaths.
SHARE reduces splits but adds deaths (v65 +2.3/game) and is rejected. RECALL alone has no demonstrated plain-build gain
across four opponents (-24/+8/-27/+4 gems vs v65/v61/v58/proxy). It is the recall-only research **control**, run names
`V80-{opp}`. `TEAMFIGHT.md` has the full continuation results.

New switches and measured results:
- `V80_CAST_FLEE`: forced healthy melee nuke before fleeing; validated on all four and rejected (-1/-98/-69/+38 vs RECALL).
- `V80_TREASURE`: same-stat Treasure instead of Prospector opening; four-opponent deltas +23/+4/+16/+44, whole-game gold
  +449/+426/+396/+404. Exact native income at R300 changes only +6/-1/+7/+3: **does not fix the early gold gap**.
- `V80_SHARE=2`: strict contact-only sharing, floor half threat. v65 -20, proxy -28; no pooled split improvement. Rejected.
- `V80_RESET_FLEE`: attack reset before retreat without consuming movement; keeps a ready dash, avoids resetting a corpse.
  The ladder audit found a hit with an unused ready reset/no dash in 5.1% of our early losing contact turns vs 0.5% top.
  `V80RESET-v65` / `V80RESET-proxy`: +53/-31 gems versus recall-only, deaths -0.5/-0.4, contact casts +1.2/+0.7 points.

### Final saved research candidate (not a proven upgrade)

`bots/v80` now defaults to **RECALL=1, TREASURE=1, RESET_FLEE=1; SHARE=0, CAST_FLEE=0, V79_TF=0**.
This is the combined candidate tested as `V80PKG-{opp}` / `artifacts/tmp/v67/q-80package` (not the earlier `V80-*` control).
No bot was submitted or activated. There is **no demonstrated competition-strength breakthrough**.

140 paired games each, versus v76 (Q-*-v78 seed-24 intersection): v65 -12 [-119,+109], v61 -3 [-92,+84],
v58 +52 [-38,+138], proxy -5 [-94,+90]. Combined wins 397/560 versus 396/560. All intervals include zero.
Whole-game gold +419/+427/+764/+411, but R300 income versus recall-only -30/+2/+1/-6. Do not claim these three gaps
are fixed. Pooled splits/contact/early-even deaths/farming are in `v80_package_replay_pooled.txt`; exact native windows
in `v80_package_native_windows.txt`. Gold per camp-hit remains ~3.8 and early fight results are mixed.

Clean official builds of both v76 and v80 succeeded. v76 is byte-identical to the Q-v65-v78 comparator; v80 is byte-identical
to the tested V80PKG Wasm. v80 SHA256 `8d11f97cfa7269736330acf119e3c61b08123530220455a5f558aa51e0903c73`.
Source review bundle: `artifacts/tmp/v67/v80-review/source.zip`, per-file hashes and switches in `manifest.json` there.
`bots/v80/CHANGES.md` is the concise candidate review. No tests remain running.

### Next step / approval boundary

The useful unresolved question is whether the **movement-preserving resets**, not forced standing, help against actual
top teams. The original handoff proposes paired v76/v80 ladder arms on the same `research/v59/duel_top1.json` groups.
User approval is still required **before either submission**; do not infer approval from this handoff. No live selection
is authorized. Once approved and actual platform IDs are known, use the existing ladder_duel/collect_duel workflow below
and recompute the ladder metrics. Without that approval, continue research locally rather than submit.

For further economy work, target opening capture value and conversion (65 vs 78 base gold/capture, 86% vs 90% conversion),
not another late passive swap. Audit same-map/group size and AoE/attack-reset clear efficiency; first-camp type cohorts can
be mixed. Avoid repeating the already-failed carry/director, loose sharing or forced movement-exclusive cast ideas.

All 120 existing ladder games now have `audit500.json`: actual turn-start observations/cooldowns, actions, camp metadata
and reward-state transitions. Run `audit_report.py INDEX FOLDER`, `capture_bonus.py INDEX FOLDER`; outputs
`v80_ladder_audit.txt`, `v80_capture_bonus.txt`. Main discoveries: unused ready spells, not farm cooldown, dominate the
casting deficit; larger-value captures, lost conversions and payout bonuses all contribute to gold/hit. See TEAMFIGHT.

To run original ladder scripts on local replays:
`$P research/v75/teamfight_scripts/local_index.py RUN`, decode with c_timeline_batch.py as usual, then
`$P research/v75/teamfight_scripts/split.py research/v75/RUN_index.json .` (and micro/state_policy/farm_eff).
`compare_runs.py RUN ...` pools all 140 games and reuses c_engage's fight clustering for early-even fights.
The original scripts expect **two positional arguments**. New helpers with their own CLI: local_index (one run),
compare_runs (run list), audit_batch (index/folder/workers), audit_report (index/folder/result), capture_bonus (index/folder),
native_windows (candidate/base). Do not blindly glob and execute every `.py` with the old two-argument convention.

Git Bash is at `C:\Program Files\Git\bin\bash.exe`; it requires expanded process permissions in this Codex environment.
No platform submission or live selection was made. Many preexisting untracked bots/tools and tracked user changes exist;
do not reset or clean them.

## Historical user rules and original handoff

- Don't overtest: about 140-280 paired games per opponent per check. Never tens of thousands of games.
- Analyse ladder replays (the live version's duel losses are valid data), not just win counts.
- Submitting a version (`tools/vendor/cambc.exe submit bots/vNN --note ...`) and activating/re-pinning the live version
  need the user's explicit OK each time. The user handles the live version. Live is v74 (platform 68) unless they changed
  it.
- Plain, measured reporting; say when something didn't work.

## The three problems the user wants fixed (from the 120 v74 duels vs the top 12)

Full analysis: `research/v75/TEAMFIGHT.md`. Ladder scripts: `research/v75/teamfight_scripts/*.py INDEX FOLDER`
(e.g. `$P research/v75/teamfight_scripts/split.py research/v75/duel_v74.json artifacts/local-only/duel-v74`).

1. **Team splits mid-fight.** Two of ours side by side in contact: one hits while the other leaves in 21.8% of rounds
   (top teams 13.7%); all of ours leave in 9.1% (2.8%).
   **Root cause found:** in `handle_enemies` (bots/v80/src/bot.cpp, threat loop near the top), `threat_on_me` adds the
   full damage of every enemy within max(range+2, 5) as if all of them hit us alone. The time-to-die check then fires.
   Logged runs (A2_MICLOG + dsrc tags, `tools/v67/c_fleesrc.py MIC80-proxy MIC80-v65`) show it set **96%** of flees
   beside a teammate at 50%+ health, and 71% of all contact flees (burst 15%, search 8%, low health 7%).
   **Fix built: `V80_SHARE`** (default 0). Each enemy's damage is shared among our champions about as close to it, the
   weaker taking more: P(us) = (1/hp) / sum(1/hp).

2. **Early fights lost at equal gear.** Before round 300 both sides hit equally hard with equal health, yet even fights
   cost us 0.76 deaths to their 0.36. In contact they hit/cast more and step away less.
   - V80_SHARE also addresses this, since the time-to-die formula drives most flees.
   - **Bug found and fixed: `V80_RECALL`** (default 0). Five of the top 12 (Mite, NEETCoders, Trzy Kwaterki, willow best
     girl, print dont int) start a recall at the end of every turn and cancel it next turn. Our code treats a recalling
     enemy as harmless: tsearch.cpp:173/341 (search says it won't fight back), tsearch.cpp:1119 (caster micro treats it
     as stunned), bot.cpp nearest_enemy_melee/kite_step (ignored), plan_escape (assumed still), target worth +0.5.
     The fix is in `World::observe_champions` (world.cpp). A recall counts only once its channel time
     (`sdk_champion_channel_time`) has gone down between two consecutive rounds; otherwise the recalling bit is cleared.
     The proxy opponent imitates this trick per team, so local proxy runs can show the effect.
   - Not done yet: they cast in 20% of contact rounds to our 15% (same champion: Marcella 19% vs 12%, Ren 23% vs 14%,
     Issac 16% vs 9%). Look at `cast_on_enemy` conditions and whether spells are spent on camps right before contact.

3. **Gear gap from round 300** (their Vesper 1,700 health vs our 1,000; items 10.5 vs 7.6 late). Decoded with
   `tools/v67/c_items.mjs` / `c_items_batch.py` (items.json per duel game, already exported for duel-v74) and
   `tools/v67/c_gear.py`:
   - Stats per gold are about equal across item families (emblem = 5 stats + passive; greed/bruiser +40% stats), so it
     is **gold**, not item choice.
   - In losses their team earns 38% more by R300 (1,318 vs 956) and 68% more by R500 (2,587 vs 1,540). Their top earner
     (Vesper/Marcella) takes 41-47% of team gold; ours about 30%. `APEX_SHARE_GOLD 1` gives rewards to our poorest
     champion. A carry loop was already tried (v68c): carry gold up, team gold down 600-870, -176 to -223 locally.
   - Source split (gold_sources.py, R500 in losses): farming 2,265 vs 1,523, kill gold 512 vs 209 (about 100 per kill).
     Our farming is about 1,500 by R500 in both wins and losses; theirs varies.
   - Farming decomposition (farm_eff.py, first 500 rounds): dead 12.8% vs 6.7%, camp-hit share 20% vs 22%, gold per
     camp-hit round 3.57 vs 4.64 (+30%). Crowding is not it (camp_crowd.py: 1.19 vs 1.36 champions per camp).
   - Next: find why their gold per camp-hit round is 30% higher: camp value choice, capture conversion, Treasure (+10%)
     vs our Prospector opening (prospector passive 0.25, meaning undocumented in engine-2 SDK), passive/assist gold. The
     fight fixes cut deaths, which also cuts the kill gold we feed them and adds alive farming time.

## What exists

- `bots/v76`: best validated per-map build (+27 to +44 vs v74 locally), never ladder-tested.
- `bots/v79`: v76 + team-fight layer `V79_TF` (default 9). Locally -24 to -107 vs v76 on all four opponents; not a
  candidate (`research/v75/v79_paired.txt`, `bots/v79/CHANGES.md`).
- `bots/v80`: copy of v79 with `V79_TF 0` (plays v76 game for game; checked on 10 games), plus:
  - `V80_RECALL` and `V80_SHARE` switches (both default 0) in common.h.
  - A2_MICLOG debug: MT lines now end `... gems ntype dsrc x y`. dsrc bits: 1 ttd, 2 low hp, 4 burst, 16 search run,
    32 search fight, 64 formula winning, 128 knob-41 engage.
  - No CHANGES.md yet.
- Variants (logged builds) in `artifacts/tmp/v67/q-80share`, `q-80recall`, `q-80both`.

## Running when this was written

Background screen started at hand-off. Output: `research/v75/v80_fix_screen.txt` (6 lines when done; about 30-40 min).
Runs:
- `MIC80-proxy-{share,recall,both}`: seed 24, proxy per team.
- `MIC80-v65-{share,recall,both}`: seed 24, vs v65.

Baselines with the same logging: `MIC80-proxy`, `MIC80-v65` (v80 all off, A2_MICLOG 1). Evaluate with:

```bash
for o in proxy v65; do for v in share recall both; do $P tools/v67/c_paired.py MIC80-$o-$v MIC80-$o | sed -n 3,8p; done; done
$P tools/v67/c_fleesrc.py MIC80-proxy-both MIC80-v65-both   # flee sources should shift away from "ttd formula"
$P tools/v67/c_miclog.py MIC80-proxy-both                   # contact turns: act share up, walk-without-acting down
```

If any run is missing (the machine was shut down), rerun it, e.g. `$P tools/v67/c_batch.py --seeds 24 --workers 8
--opponent proxy --per-team --plan research/v70/pool_plan_teams.json RUN=artifacts/tmp/v67/q-80both`, or for v65
`--opponent v65` without `--per-team --plan ...`. Run names must be new (the tool refuses an existing run folder;
delete a half-finished one under `artifacts/evaluations/v67/` first).

## Next steps

1. Read the screen. Watch for 00vault; it swings ±1,500 on a round of timing in its opening 4v4.
2. If share/recall/both are not worse, set the defaults in `bots/v80/src/common.h` and run the plain (non-logged)
   build against all four opponents on seed 24. Baselines `Q-<opp>-v78` cover seeds 24/25, and c_paired intersects:
   ```bash
   for o in v65 v61 v58; do $P tools/v67/c_batch.py --seeds 24 --workers 5 --opponent $o V80-$o=bots/v80; done
   $P tools/v67/c_batch.py --seeds 24 --workers 5 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json V80-proxy=bots/v80
   for o in v65 v61 v58 proxy; do $P tools/v67/c_paired.py V80-$o Q-$o-v78; done
   ```
3. Local league is our own lineage; fight changes have so far kept their local sign on the ladder (v75 lone guard:
   neutral locally, -91 ladder). The real test is a ladder duel arm on `research/v59/duel_top1.json` (24 groups, quota
   50/hour; `tools/replay/ladder_duel.py run --plan ... --version N --arm NAME`; collect with
   `research/v75/collect_duel.py ARM`; timelines with `tools/v67/c_timeline_batch.py`). Propose v76 and v80 as paired
   arms. **Ask the user before submitting or activating anything.** After an arm, recompute the three gap measures
   (split.py, state_policy.py, gear) on its replays.
4. Remaining work on gap 2: casting rate in contact. Remaining work on gap 3: gold per camp-hit round (see above).
5. Write `bots/v80/CHANGES.md` and update `research/v75/TEAMFIGHT.md` with the results.

## Memory notes

Claude's memory at `C:\Users\omdha\.claude\projects\C--projects-cambridge-battlecode\memory\`. Most relevant:
- `battlecode-v79-teamfight.md`
- `feedback-use-ladder-data.md`
- `battlecode-v75-loss-forensics.md`
- `battlecode-local-testing-fidelity.md`
