# Plan for large gains, v3 (3 Nov 2026)

Status: v92 is still the best bot. Paused at the user's request after E113.

## 1. Why the 3 Nov attempts did not show gains

The 3 Nov attempts were E101–E113: imitation, the economy core, the schedule optimiser, the contested-game model, item builds, the self-play draft, endgame, intel, wards, and the top-team structure plus ES. All were judged against v92, its family (v81, x1, v61, b5) or x3ctr, and all came out level or behind. Three facts explain this better than "v92 is optimal".

1. **The yardstick does not contain the opponents that decide ladder games.**
   - Ladder winners farm twice as much early, then fight 4–6 against 1–4 at jackpot groups (E75).
   - Our family spreads out and contests little, so any concentration or contest plan loses locally (E75 pack and jackpot copies, E109, E113's top-team structure).
   - Local self-play has never predicted the ladder (r 0.00–0.26 for proxies; about 0.65 at best for the weighted pool).
   - The one big ladder step on record was v30, which used top-team lineups: rank 47 → 28 in 4 hours. Local benches had undervalued it.
2. **The engine is deterministic per pairing.** Against a fixed bot, a counter can memorise trajectories: x3ctr went 139/140 against v92 and was −3 on held-out opponents. Ladder opponents are also fixed bots for days at a time. That is an opportunity (section 2, B), not only a trap.
3. **Compute in a turn is not the bottleneck.**
   - Fuel against no fuel is flat, the fuel-waste test was flat, and the depth-2 planner did worse than greedy.
   - What we lack is knowledge: which positions are safe and which fights win, not more search per turn.
   - That knowledge has to be learned offline, where compute is unlimited, and then baked into the bot.

## 2. The plan, in order of expected gain per hour

### A. Unblock and re-measure (user, about 15 min; then me, about 1 hour) — needed before everything else

- **User:**
  - `cambc login`;
  - `cambc maps pull`. x3ctr has rows for 14 "03-" maps that are not on disk, so the ladder pool may have changed. v92's per-map table (ladfit) and v70 lineups would then be blind on those maps.
- **Me:**
  - fetch our last 3 days of ranked games and the top-15 teams' games (`tools/platform_fetch.py`, rate-limited);
  - run `tools/ladder_ab.py` to get our current rating and per-map results;
  - check which current ladder maps lack table rows.
- **Expected gain:** possibly large if the pool has changed, because the per-map rows are fitted to the old maps (their value on new maps is not measured). Otherwise this is only the baseline for B–D.

### B. Opponent-aware play: identify the opponent in the draft, then counter it (largest ceiling)

- **Existence proof:** x3ctr beats a fixed bot 99% once that bot's play is known. Ladder bots are fixed too.
- **Identify:** the draft exposes the enemy's picks (`bc::draft::current_draft(team::enemy)`, used in draft.cpp). Top teams' lineups per map are very consistent (draft_meta). A per-map lookup of lineup → team fingerprint, built from platform match lists, names the opponent by the end of the draft.
- **Counter:** for each top team (about 10) and each official map, use their replays to extract their opening:
  - first targets;
  - arrival rounds at each group;
  - where their whole-team fights happen;
  - their bank timings.

  Choose a counter per (team, map, side) from a small menu: contest their first jackpot with 5, take the groups they skip, ambush their first bank, or avoid and out-farm. Store it as a table like x3ctr's, keyed by fingerprint instead of v92.
- **Measure without a login:** a "ghost" sparring bot replays a top team's recorded actions from the action logs (the replay DB has them) until our play changes what it would see, then falls back to v92. The engine is deterministic, so the ghost is exact for the opening (roughly the first 60–150 rounds), which is the window where E75's deciding fights happen. Score each counter on the ghost's maps; confirm on the ladder.
- **Guard against memorising (E101):** choose counters on half of each team's replays, test on the other half, and then on the ladder.
- **Expected gain:** this targets the games that cost rating, against the top 10. Even half of x3ctr's margin on 30% of games is about +10 points of win rate overall.
- **Cost:** 2–3 days. This is the first build.
- **Note:** this uses past games to model opponents, not to copy them. Top human teams scout opponents the same way; it is analysis of public replays, not platform exploitation.

### C. Positioning and survival learned offline in the engine lab (largest general gain)

- **Problem:** the gap with top teams is positioning (replay learning). We die about 3× as often for the same kills. The death model predicts deaths well (AUC 0.945), but its fixed flee rule did not help, so the problem is the response, not the prediction.
- **Method:**
  - sample about 50k fight states from our own real games (lab `replay_lab.js` trajectories);
  - for each state and each candidate move of each champion, roll out 5–15 rounds in the engine lab (`engine.wasm`, unlimited compute offline), with both sides on v92's policy;
  - label each move's value: lives × 25 + health × 12 + gold, ours minus theirs, which is the lab's existing score;
  - fit a small move-value network with the 16–32 features the bot already computes;
  - bake it into the bot as a positioning term in `tactical_decide`, whose weights are hard-coded today.
- **Self-play with this net is safe from the yardstick problem:** each label comes from a real engine rollout from a real ladder-type state, not from game wins against our family.
- **Gate:** deaths per game −20% without fewer kills, on held-out maps and against x3ctr, v92 and the weighted pool; then the ladder.
- **Expected gain:** by E73's rates (1 kill ≈ +17 points), 1–2 fewer deaths a game is worth +10–20 points.
- **Cost:** 3–4 days. Run it after B, or in parallel when RAM allows (it is a Node job, not a cambc batch).

### D. Ladder A/B on candidates already built (cheap, user decision)

- **Candidates:**
  - p2f05 (imitation layer: 54% against v92 on ladder maps);
  - v93 with intel only (51% overall, 54% on ladder maps);
  - the best E113 tts candidate (top-team structure; judged only by opponents that punish it).
- **Why:** all three are structurally different from v92 in the direction E75 says matters, and local benches would hide a ladder gain (as with v30).
- **How:** one 4-hour window each, about 120 ranked games and ±4.5 points (`tools/ladder_ab.py`). I prepare the zips and the comparison; you submit.
- **Expected gain:** unknown, 0 to +60 rating. It is the only true measurement we have.

### E. Rule edges by reverse engineering (allowed; medium)

- Diff `rules_2_0_0.json` against the 1.0.3 rules the top teams tuned on.
- Probe value-per-tick of each mechanic that v92 under-uses:
  - altar locks and prelock timing;
  - camp respawn timing (arrive as a group respawns);
  - tribute bag sizes against risk;
  - emblem stacking;
  - vision and ward lines.
- Earlier probes found the Prospector emblem gives +9% to capture gems; v59 (v57 + Prospector build + knobs) then won 67% against v57. More such misvalued mechanics may exist.
- This stays within the game's rules: no platform or engine exploits, and `cambc.exe` is never modified.
- **Cost:** 1 day of probes, then targeted builds.

### F. Cheap fixes on the way

- Fix p2a's BC feature-3 mismatch (trained as capture phase, computed as "damaged") and re-run p2f05, the D candidate.
- Restore `e96_state.json` from `e96_es.hist` gen 1.

## 3. Stop doing

- Knob ES or variant searches judged against v92 or its family. These were E92–E96 and E113: no movement, and a risk of memorising.
- Gating on head-to-head against v92 or x3ctr alone (pairings are deterministic; E101 showed memorisation).
- Designing from simulators fitted to our own bot (E108 schedule, E109 contest, E111 self-play draft): their lessons didn't transfer.
- Spending more fuel per turn (option 3).

## 4. Gates for any package

- Better than v92 on held-out maps (mazetest 0–99 + real200b 50–99) and on the current ladder pool.
- At least 200 games against x3ctr, v92 and the weighted pool (farm .30, calm .20, v34c .15, sparexp .15, aggro .10, v30base .05, spartop .05).
- No loss of more than 3 points on any group.
- The final word is a ladder A/B, which is the user's decision.

## 5. What I need from you

1. `cambc login`, then `cambc maps pull`, from the Terminal panel. This unblocks A, B's fingerprints and D.
2. Your choice: start B (opponent-aware counters) first, or C (offline positioning) first. B has the higher ceiling against top teams; C gives the broader gain.
