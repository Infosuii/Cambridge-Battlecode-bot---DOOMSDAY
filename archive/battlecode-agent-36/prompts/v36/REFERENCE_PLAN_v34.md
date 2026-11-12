# v34 improvement plan (2026-10-19)

Built from the "Battlecode bot implementation brief", checked against this workspace's code and measurements. Evidence:
`FINDINGS_2026-10-18.md`. Folder guide: `HANDOFF.md`. The claim checks are in the appendix.

## Priority order

| # | Item | Why it is here | Expected gain | Effort |
|---|---|---|---|---|
| 1 | Pin down the baseline and the live version | Every comparison and ladder read depends on it; v34 appears live | Enables everything else | Hours |
| 2 | Measure and fix fuel failures | 2.5 lost champion-turns per game (61% of games); item 3 needs fuel headroom | Small directly, large as an enabler | 1–2 days |
| 3 | Combat-search coverage and the snapshot | The search gives no verdict in 17–28% of our fight turns and ~40% of close fights vs top teams; deaths decide the ladder | The most promising lever | 2–4 days |
| 4 | Two small verified fixes: flee-hit, pruning bound | Confirmed bugs with clean fixes | +1 point or so each | Hours each |
| 5 | Draft lineup model from the replay database | The draft is the only change that clearly moved the ladder (+25 Elo) | Possibly +10–30 Elo on some maps | 2–3 days |
| 6 | Ladder A/B of the best candidate | Local tests can't resolve gains under ~25 Elo | Truth | 4–8 hours of ladder time (team's decision) |
| 7 | Simulator validation | Item 3's search is only as good as its simulator; never checked against the engine | Enabler | 1–2 days |
| 8 | Farming-race maps (rows, lanes, corners) | Our worst ladder maps; games there have 0–3 deaths, decided by farming | Map-specific, a few points | 2–3 days |
| 9 | Narrow ML for farming decisions | Only after 1–7; predictive models so far didn't turn into wins | Unknown | Days |

Not to redo (tested, neutral or negative): see the last section.

## How every item is tested (common protocol)

Run all four steps for each change, comparing a candidate built with the change against the same build with it off.
1. **Build and mirror check.** With the switch off, the new build must play v34's games (unseen maps exactly; official
   maps can differ in a few fuel-dependent games).
2. **Quick screen (the user's protocol).** Head-to-head vs v34 on 200 unseen maps (`maps_rdev`, both sides) in 50-map
   chunks, stopping early if clearly worse or similar. Then once on each official map (34 games).
3. **Calibrated pool.**
   - `tools/spar_build.py` + `tools/spar_pool.py` against farm, calm, v34 (pool name `v34c`; it plays v34's official-map games), sparexp, aggro, v30base and spartop, seeds
     1–4.
   - Scored with `tools/spar_compare.py` (paired change, deaths overall and vs sparexp).
   - Then **fresh seeds 5–8**: best-of-several picks shrank 2–4 points on fresh seeds every time.
4. **Unseen-map pool** (`tools/poolbench.py ... --mapdirs maps_real:1`): the finals use unseen maps.

Noise to expect:
- 34 official games: ±9 points.
- 400 unseen games: ±2.5 points.
- Pool at 8 seeds × 7 opponents: ±1.2–2 points.
- Ladder version steps: ±20–40 Elo (opponent-clustered SEs).

Head-to-head wins can mislead (spar_top beat v34 55.9% one-on-one but its settings lost 60 Elo across the pool).

---

## 1. Pin down the baseline and the live version

**Why.**
- The downloaded `bot_v34 (1).zip` is exactly `bots/v34` (18/18 files identical by SHA-256).
- v34's code appears **live** (platform "v36"). In 3 of our newest stampede games (19 Oct, ~11:45 UTC) we captured the
  big camp at r143/159/438 and won. The previous live bot (v32b) never took it before r300 on the ladder.

**Steps.**
1. Get the platform submission time of "v36", and of any later submission.
2. Fix the version windows in `tools/spar_calib.py` (`VERSIONS`). The current "v32b: 18:13 → now" window mixes v32b and
   v34 games.
3. Re-run `python -I tools/spar_calib.py ladder` (all and ranked) to get the first real ladder read of v34. The
   calibrated pool predicted v34 at +26 ± 12 local Elo over v32b.
4. The baseline for all work is **v34** (`bots/v34`, identical to the zip).
5. Record the source hash, artifact hash and switch set of every evaluated bot (the brief's requirement).
   `bots/<name>/src/common.h` lines above `#pragma once` hold the switch set.
6. Find the teammate's `bots/v35` (fuel governor) and `PLAN.md`. They are not in this workspace.

**Done when** the baseline is fixed, the windows are corrected and the v34 ladder result is known.

## 2. Measure and fix fuel failures

**Why.**

| Source | Exhausted champion-turns per game | Games with at least one |
|---|---|---|
| v34, local official maps (1,904 games) | 2.51 | 61% |
| v32b, local | 2.19 | 56% |
| Ladder (older bots, 623 games) | 1.80 | 47% |

- v34 adds 0.24 per game on **round 1**, which v32b never had: route depth 2 runs on the first turn.
- A turn that runs out of fuel does nothing (a champion standing still in a fight can die).
- Item 3 needs headroom.

**History.**
- Raising every cap at once (fight search 80k, cheaper cost estimate, 40 groups scored, 6 fields) gave 66 exhausted
  turns vs 8 in 12 games and won 3/12. Rejected.
- Fight-search budget 45k → 70k with the original cost estimate: +1.7 pool points, no extra overruns. That became v33.

**Steps.**
1. **Measure where turns run out.**
   - The replay bundles carry per-turn fuel (`tools/fuelstat.py`). The stats JSON has `fuelExhausted` events with round
     and champion (count entries, not records: every champion has a record, usually empty).
   - Build a debug variant that logs the last phase entered each turn (`PROF_CHECK` points already exist in
     `handle_enemies`).
   - Classify: fight search, route search, distance fields, camp scoring, first turn.
2. **Fix the first-turn case.** On round 1 skip route depth 2, or cap it by fuel. It is new in v34 and cheap.
3. **Governor.**
   - Each optional stage (fight search, route search, extra fields, camp scoring past N groups) checks a reserve that
     covers "pick a legal action and end the turn".
   - The check happens before the stage starts.
   - The fallback must be coherent (the existing fallbacks: no verdict → formula; no route → single target).
4. Keep four separate counters: exhausted turns, suspended turns, skipped stages (by stage) and runtime faults. The brief
   is right that a broad threshold can silently disable planning; report skip rates per stage.

**Test.**
- Exhausted turns per game on the 34 official games plus 200 unseen maps.
- Skip rates.
- Then the common protocol: the governor must not cost strength.

**Done when** exhausted turns are ≈0 on the regression suite, skip rates are reported, and strength is unchanged or
better.

## 3. Combat-search coverage and the snapshot

**Why.** This is the biggest plausible lever.
- Against the top 12 we die 14.5 times a game to their 5.1, and the team with fewer deaths wins 86% of games.
- The fight-or-run search (`tactical_decide`, `bots/v34/src/tsearch.cpp`) costs 2,200 × units × (rounds + 1) per
  playout. Two playouts (fight, run) must fit 70,000.
- 5 units fit (66,000 at 2 rounds); **6 or more return no verdict** (79,200).
- From the per-turn action logs, snapshots with 6+ units are **17–21% of our fight turns**, 24–28% with an enemy within
  4. In top-team games they are **29% and 42%**. Against strong teams the search is blind in about 4 of 10 close fights.

**Snapshot problems** (`ts_snapshot`, `tsearch.cpp:120`):
- It takes us, then up to 3 allies within 7, then enemies within 8 until 8 units, **in list order, not by distance**
  (the comment says "nearest first"; the loop doesn't sort).
- **Camps are left out** (`APEX_TS_CAMPS 0`).
- The verdict **overrides** the formula's danger flags in `handle_enemies` (outnumbered, burst-aware). So a "fight"
  verdict can override camp danger the search never saw.

**Steps** (each a separate switch, tested alone):
1. **Relevant-unit selection** (first, cheapest).
   - Sort allies and enemies by distance and threat (enemy burst on us, our damage on them).
   - Keep at most 5 units total, so the search always runs.
   - Always keep Cassi and Issac together (linked death; `note_ci` already tracks the pair).
   - Log what was dropped.
2. **Measure the real playout cost** per unit count and horizon: time `ts::rollout` with the fuel counter in a lab
   build. The 2,200 is an old estimate. If real costs are lower, 6–7 units fit at 2 rounds.
3. **Adaptive horizon and model count**: 1 enemy model and a 2-round horizon for big fights; the full search for small
   ones.
4. **Camps.**
   - Variant A: `APEX_TS_CAMPS 1` (camps within 7 in the simulation).
   - Variant B: a fight verdict cannot override the danger flag when an awake camp is within reach.
5. **Logging.** A no-verdict reason for every call: budget, safety reserve, no enemies in range, unclear (inside the
   margin).

**Test.**
- Coverage table by snapshot size (before/after).
- Fuel counters (item 2).
- The common protocol, with **deaths vs sparexp** as the key secondary metric. sparexp is the only pool bot that kills
  v34 at the top bot's rate (16.7 a game; the top bot 13–18).

**Risks.** The search could be wrong in big fights; that's why item 7 exists. More search means more fuel; do item 2
first.

## 4. Two small verified fixes

### 4a. Flee-hit (`NOVA_FLEE_HIT`, built in `bots/v36fight`)

**Why.**
- A fleeing melee champion hits only its *chosen* target (best kill-time per value, often a wounded enemy a few tiles
  away), never the adjacent enemy hitting it.
- Top-team melee hit back 70–74% of turns when outnumbered; ours 38–63% (517 top-team replays vs our local games).

**Change.** In `handle_enemies`, before `escape_or_stand`: if fleeing, melee, and able to attack, hit the weakest
adjacent enemy first. Melee can attack and then move.

**Measured.** +0.9 ± 1.2 pool points over 8 seeds (+0.5 on seeds 1–4, +1.3 on fresh seeds), 0.36 fewer deaths a game,
1.8 fewer against sparexp.

**Next.** Port to v34 and run the quick screen and the unseen pool.

### 4b. Pruning bound (`bots/v34/src/bot.cpp:3324`, `best_case` before `prune_bound`)

**Why.**
- `best_case = (gems + gold weight × gold) × stickiness / (walk + wait + capture time + 4)`.
- Positive terms applied later and missing from it: `NOVA_BIGJOB_MULT` ×6 (a group holding ≥60% of the map's gems,
  from round 60) and the early harmless-camp boost ×1.333 (`APEX_BOOT_BONUS` while items < 15). A group can be pruned
  that would have won after the bonus.

**Change.** Multiply `best_case` by the largest multiplier that can apply to that group. Keep the explicit
16-group cap (`APEX_DET_SCORE_N`) separate.

**Test.**
- Pruned-vs-exhaustive diagnostic: same choice when caps are lifted.
- Official maps (stampede especially) and the farm bench (`tools/opening_bench.py`, rounds to 1000).

**Expected.** Small: the stampede rush already works (1080–0 vs v33).

## 5. Draft lineup model from the replay database

**Why.**
- v30 (top-team lineups per official map) is the only change that clearly moved the ladder (+25 Elo, 1814 → 1839).
- Every behaviour change since has been within noise.
- An earlier counter-pick model failed, but on small data.
- Now there is the daily replay database: ~30,000 replays a day, matched to teams through `cambc matches list`.

**Steps.**
1. Download several days of replay-database summaries; drafts and results are in the match lists.
2. Per map: lineup win rates for teams in our rating band and above, Elo-adjusted (`tools/draft_meta.py`,
   `tools/draft_fit.py`), with team fixed effects so strong teams don't inflate their lineups.
3. Candidates where a lineup clearly beats ours on a map. Hints from the earlier data: corners/lanes Tavi lineups,
   though a local Tavi test on lanes lost; that is exactly the kind of conflict to resolve with more data.
4. Implement as per-map lineup rows in `draft.cpp`, behind a switch (an unused row once changed 1 in 34 mirror games,
   so guard new rows).
5. Test per map on official maps (seeded, `tools/pb_paired.py`). Then ladder.

## 6. Ladder A/B of the best candidate

**Why.** Local testing predicts per-map ladder shape (r ≈ 0.65) but can't resolve version gains under ~25 Elo.

**Steps** (the team decides on submissions):
1. Submit the candidate.
2. After 4–8 hours, refresh with `tools/platform_list.py` and `tools/refresh_ratings.py`.
3. Run `tools/ladder_ab.py` / `tools/spar_calib.py ladder` with the new window.
4. Read ranked and all games separately, with opponent-clustered SEs. Unranked games come in 5-game groups vs one team.

## 7. Simulator validation

**Why.** Item 3 makes more decisions depend on `ts::rollout`, which has never been checked against the engine.

**Steps.**
1. Lab scenarios in `bots/lab`: 1v1, 2v2 and 3v3 on open ground; a stun; Cassi/Issac linked death; a camp attacking;
   a dash escape.
2. Record the engine's next-round state and compare it with the simulator's one-step prediction.
3. Fix the biggest gaps first, then measure longer horizons.
4. `APEX_TS_CALIB` exists (calibrated aggression and flee thresholds from 2,590 real fight rounds); check it is still
   right for the current engine.

## 8. Farming-race maps (rows, lanes, corners)

**Why.**
- Our worst ladder maps (ranked, v32 window): lanes −36, rows −36, corners −27 points vs expectation.
- Games there have 0–3 deaths, so they are farming races.
- Rows: we take as many wolf packs by r300 as the top teams (12.3 each), but our first capture is r40–42 vs r29.
- Lanes: every camp sits in the shared middle, 32 tiles from either spawn; top teams take 25 camps by r300, we 19.

**Steps.**
1. Per-map farm-bench runs (`tools/opening_bench.py`, `tools/farmbench.py`) plus replay comparisons. The top-team
   capture sequences on these maps are in `replays_db/` and `platform/sum`.
2. Map-specific changes behind official-map checks (`Bot::is_official_map()`).
   - Rows: opening order (the melee-tank opening variant of `v35op` got the first capture to r26).
   - Lanes: shopping trips (a recall plus a 32-tile walk back costs ~37 rounds).
3. Test per map (seeded) and on the pool.

## 9. Narrow ML for farming decisions

**Why last.** Three models predicted well and changed nothing:
- death risk (AUC 0.945);
- location risk (AUC 0.82);
- the top-team fight network (47.9% vs a 30.8% base rate; +0.6 to +1.4 ± 2.2).

Our per-turn fight choices already match the top teams' in the same situations; the gap is the situations.

**Steps** (if pursued): the brief's predictors for completion time, damage/recovery cost and interruption risk, used as a
bounded correction to the hand score.

Lessons to apply:
- **Gate model calls by relevance.** Running the location model for every scored camp every turn starved turns of fuel
  (18–22% vs v34 even at weight 0.001) until it ran only near enemies.
- Split data by match.
- Judge by full-match results only.
- Keep `local_model.h` / `APEX_TS_LOCALNET` off until it is verified.

---

## Not to redo (tested, neutral or negative)

| Idea | Result |
|---|---|
| Fight switches: aggression, focus, outnumbered retreat, strength gate, hunting | 38–55% head to head, pool within noise or worse |
| Cohesion as a camp penalty | −4 points (race maps −11 to −16), though −19% deaths |
| Flee toward teammates (`NOVA_FIGHT2 4`) | −66 Elo |
| Teammates answer distress calls (`APEX_DISTRESS`) | −15 to −49 Elo, more deaths |
| Death-risk flee trigger (`NOVA_DANGER`) | Neutral or harmful |
| Location-risk camp choice (`NOVA_POS_RISK`) | 46% vs v34 |
| Team camp assignment (`v36tp`); pair sectors from draft memory (`v37team`) | −1.6 points; 44–50% |
| Opening schedule (`v35op`) | Neutral on official and `maps_rdev`, +4–6 on short generated suites |
| Two shared sightings / sightings off (`v37mem`) | Even (51.3% on 200 unseen, 19/34 official) |
| Draft-memory distance table (`NOVA_DTABLE`) | Even |
| Counter-picking | Noise once per-size champion values are fitted |

## Appendix: claim checks

| Brief's claim | Result |
|---|---|
| Reviewed source = `bot_v34/src` | Yes: the zip = `bots/v34`, 18/18 files identical |
| v34 is the baseline | Yes |
| v34 contains the pruning issue | Yes (`bot.cpp:3324`); missing terms are the ×6 big-group and ×1.333 boot multipliers |
| Six-unit comparison 79,200 > 70,000 | Yes, exactly; 5 units fit |
| Fuel-exhaustion events occur | Yes: 2.5/game local v34, 1.8/game ladder |
| v35 governor result (94 → 0) | Not verifiable here: no `bots/v35` in this workspace |
| v36 = v34 source | Consistent with the ladder: stampede big-camp captures at r143–159 today |
