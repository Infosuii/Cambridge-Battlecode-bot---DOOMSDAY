# DOOMSDAY v118 root-cause cycle (2026-11-09)

Base: v117 = `arena/bots/hp01` (source `ea9a68340c2a`, Wasm `f9088c1d`, verified against `release/hp01/manifest.json`). hp01 = v113 + spawn-heal fix (rv11). sw08's route veto was not part of v117. Engine 3.0.0 / build `96ce858f`, CLI 5.0.0 (`4a94c150`).

Evidence labels: **[replay]** ladder replay observation, **[source]** source-confirmed rule, **[traced]** debug-trace of the live decision, **[controlled]** isolated by a controlled local test.

## 1. Homonoliths objective miss: fixed (H, Accepted for the target)

- [replay] Both 600-gem groups are three 20,000-HP monoliths (strength 200, range 5) adjacent to each spawn. 0xDEADBEEF attacked its home group from round 2 and cleared it by about round 323.
- [traced] In 6/6 local games, `score_groups` rejects groups 2 and 3 through round 1,000 with exactly one reason: `need > team_size` (`champions_needed` = 7, team = 4, `hp_left` 60,000). They are never scored, so the siege and big-job paths are never reached. Neural overrides occasionally select the group with `best_need = 1` (solo, idle).
- [source] The soak model (`group_soak`) ignores spawn healing. `bc::constants::spawn_healing` = **1.0** (full heal each round), and every spawn tile is inside monolith range.
- [controlled] With a 3-champion crew assigned and retained on spawn tiles (decisive test dx02), the existing draft took the home group at rounds 413–438 and won 6/6. A 4-champion crew captured at round 503 and won 5/6. So the miss is coordination, not draft or damage output.
- Census of the 128-map pool: only 03homonoliths has a gem group of ≥25% share reachable from spawn tiles (04plaza 16% and 02the-pond 10% are smaller). Other low-value farming losses (e.g. Islands) are a different mechanism.
- Fix H (`home_siege.py`): slots 0–2 stand on spawn tiles in range and attack the lowest-HP live camp until the group dies. Capture is left to the reward logic, and the champion yields if an enemy is within 8.
- Release-build incident check (18 games, 9 styles × 2 sides): v117 16/18, median first home capture r1,353 (0 by r600). H: 18/18, median r417 (18/18 by r600), zero fuel exhaustions.

## 2. Islands navigation stall: fixed (D + R, Accepted for the target)

- [traced] Stationary champions in mode `approach` for 125–500 rounds have a finite target field (3–10 steps), dash ready (cooldown 0) and no enemy near.
- [traced, terrain dump] `World::enable_bridges` marks each one-tile hole gap independently, so the walk field runs along diagonal chains of bridge tiles. The real dash landing then improves the field by only 1. `try_dash` requires an improvement of ≥2, `follow_field` has no walking step, and `bridge_hold` expires after 12 turns. The approach never reads as unreachable.
- [source] The A2_APPROACHFIX stall guard sets `avoid_until` after 25 turns, but the neural override at the end of target selection ignores `avoid_until`, so the same target is reselected (sw08's route veto was not in v117).
- Fix D: when no walking step exists at a bridge, accept a dash that improves the field by ≥1. Fix R: approach-stall and unreachable cooldowns also veto the neural override (sw08 `rv10` route repair).
- Release-build incident check (01islands, 18 games): v117 7/18, quiet trailing stall pairs 6,577 → D 14/18 (4,235), R 11/18 (3,351), DR 15/18 (3,970), HDR 14/18 (3,624). The worst remaining DR episode (686 rounds) is an enemy-adjacent standoff (enemy within 6 for all 686 rounds), not the quiet stall.
- Debug activation on 01islands (HDR, 18 games): 186 relaxed dashes and 157 route vetoes.

## 3. Swirl outnumbered contact: traced; gates Parked

- [replay] Varg advanced on 3–4 enemies with no ally within 6, was stunned, and died.
- [traced] Over 40 local games on 5 brawl maps, turns ending closer to ≥3 enemies with no healthy ally support break down as: `fight-champ` (handle_enemies committed) 528 episodes, 26% died within 15 rounds; fallbacks `approach` 4%, `join` 9%, `tribute` 6%. Combat itself chooses the approach; a declining branch does not fall through to an advance.
- [source] `winning` compares time-to-kill against time-to-die. Both numbers gates are compiled off (`A3_NUMBERS 0`, `APEX_OUTNUMBERED 0`).
- Paired development (880 games each): N (`A3_NUMBERS 1`) −127, deaths 10.3 → 7.2/game. O (`APEX_OUTNUMBERED 2`) −43. Focused repair L (lone champion vs ≥3 foes) −1/880 alone, and HDRL −34/2,704 versus HDR +20. Passivity costs more economy than it saves in deaths. **Classification: Parked.** The ladder cluster is opponent-specific (SkibidiSloppers 0–5 with an upgraded Vesper carry), and the local references don't reproduce it.

## 4. Banking: separated, no threshold change (Parked)

- [replay] Barbell: Marcella with 159 gems about 5 tiles from the altar, no enemy visible, walked 30 rounds away to farm, then recalled to shop (shopping/farming detour over banking).
- [replay] Twisty: 122 gems unbanked at round 2,000 while far from both altars (endgame timing; `hunt()` precedes `tribute_if_needed()` in the turn order).
- [replay] Braided River: Varg with 233 gems circled for 68 rounds while 3 enemies held the only altar pair (unsafe channel, not a route block).
- Local (v117, 372 dev losses): 26 end at the round cap, and 4 of those held a bag ≥ deficit. 53/372 end early while our bag would have covered the deficit (race banking, e.g. adgato-gemcombat5 792 held). Next: trace the carrier's banking decision in those race losses before changing `kTributeCarry` / endgame rules.

## 5. Retrain and retune (training: Retry required)

Recorder: v117's lineage lacked the verified NRZ/NRQ recorder repair (it lives in `merge.sources`). `rl_logger.py` applies it to rollout actors only. Native log-prob max error 1.2e-5 across ~260k rows/iteration.

Training: `train_v118.py` (train_campaign + incident maps forced into every 48-map batch), on-policy continuation of the v117 network on the HDR behavior, LR 5e-5, 6 iterations × 96 games, 9 styles. Plan in `training-plan.json`: 129 train maps, 19 selection maps, holdout excluded. Selection scores were it0 0.649, it2 0.605, it4 0.635, it6 0.617.

Four arms on 1,462 games over maps the training never saw (19 selection maps × 9 styles + 113 stability maps × 5 styles, both sides):

| Arm | Score | vs v117 |
|---|---:|---:|
| v117 | 875 | — |
| HDR frozen weights | 902 | +27 |
| HDR retuned (50% blend) | 859 | −16 |
| HDR fresh trained (it4) | 876 | +1 |

Resume: `TRAIN_PLAN=v118-rootcause/training-plan.json TRAIN_CAMPAIGN_NAME=v118-hdr TRAIN_SOURCE=v18HDR TRAIN_PREFIX=v18t TRAIN_ITERATIONS=<n> TRAIN_BALANCED=1 python v118-rootcause/train_v118.py` (resumes from `training/v118-hdr/state.json` and `resume_6.pt`).

## 6. Whole-bot measurement

Any code change diverges 65–90% of games (fuel-limited chaos), so an 880-game paired difference has a ±25-point 90% interval.

| Panel | Games | HDR − v117 |
|---|---:|---:|
| Dev round 2 (88 published × 9 styles + 113 generated × 5 styles) | 2,704 | +20 (90% CI −35..+78) |
| Unseen maps (four-arm run) | 1,462 | +27 |
| **Sealed holdout** (40 published × 9 styles) | 720 | **−4** (−0.56 pp, p10 −3.6 pp) |
| Fresh confirmation (129 unused generated × 9 styles, report-only) | 2,304 | **0** (p10/p90 ±1.9 pp) |

Faults are 0 in every panel. Fuel exhaustions run slightly lower than v117 everywhere except the holdout (2.59 vs 2.48/game).
Activation trace on the worst holdout maps (04terraces, 04waves, 02gift-wrapping): zero H, D and R activations, so those losses are divergence, not fix effects.

## 7. Release decision

Pre-registered gates (`release-protocol.json`): G1 targets ✅, G2 faults ✅, G3 fuel ✅, **G4 strength ❌**, G5 direct 42/80 ✅.
**v18HDR is packaged (`release/v18HDR`) with `approved_for_upload: false`.** The ladder was not touched. The CLI session was also logged out at check time (`cambc login` required), so the active ladder version could not be re-read. The last recorded active version was 117 (activated 2026-11-09T10:41Z). Teammate branch `claude/v115-fuel-merge-1109` reports v115 cancelled and the team pinned to v106 around 00:24Z, before v117. Recheck before any change.

Classifications: H Accepted (target), D+R Accepted (target), HDR whole-bot Conditionally useful (non-inferior within noise on 4 panels; the formal holdout gate failed), N/O/L Parked, retrain/blend Retry required, banking Parked pending a decision trace.
