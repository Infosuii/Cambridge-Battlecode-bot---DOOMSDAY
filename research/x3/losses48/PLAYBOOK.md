# Strategy playbook: map categories x strategies learned from the teams that beat us (3 Nov 2026)

## 1. How the system works (works on unseen maps)

1. **Map features from the bot's own world model** at game start (`bots/x3/src/x1_atlas.h`): size, team size,
   group count, gems, blocked share, jackpot / top-3 share, harmless / strong-camp share, own / contested / enemy-side
   gem shares, gems within 15 / 30 steps, unreachable share, nearest and mean group distance, altars, camp health per
   gem. Offline values come from the bot's own print (`X1_ATLAS`, `tools/mapatlas/collect.py`): 86/86 maps match the
   bot's fingerprints exactly.
2. **Category** by a depth-3 tree on those features (`tools/mapatlas/categorise.py --source bot`, generated C++
   `x1_categories.h`; runtime check: 28/28 games classified as offline). Categories (`research/x3/atlas/CATEGORIES.md`):

| Category | Maps | Rule | Plainly |
|---|---|---|---|
| C1 | 18 | small; mean group distance <= ~22 steps; fighting camps | small, close, contested farm |
| C2 | 4 | small; close; > 62% of gems in harmless camps | small peaceful race |
| C3 | 24 | small; spread; < 17% harmless | small, spread, dangerous camps |
| C4 | 13 | small; spread; some harmless | small, spread, mixed |
| C5 | 21 | large; dangerous camps; most gems beyond 30 steps | large, expand far |
| C6 | 3 | large; dangerous; gems near home | large, rich home |
| C7 | 3 | large; mostly harmless | large peaceful |

3. **Strategy profile per category** (`x1_portfolio.h`, `X1_PORTFOLIO`): profiles and the category -> profile table
   are data; test builds force one profile everywhere (`X1_PORTFOLIO_FORCE`, bots `pf1`..`pf7`).

## 2. What the teams that beat us did (last 48 h, rated >= 2000)

898 distinct losses (459 ranked, 439 unranked) to 40 teams on all 86 maps (`tools/ladder/losses_recent.py`,
`summary_profile.py`, `archetypes.py`; first 294 analysed so far, all 898 pending). Consistent across categories:

| | winners | us, same games |
|---|---|---|
| wards placed per game | 80-170 | 40-90 (about half, every category) |
| first deposit (round) | 90-230 | 70-600 (later in 5 of 7 categories) |
| deposits per game | 15-38 | 6-38 (1.4-2.5x fewer in most) |
| Bruiser shards by round 300 | 3-12 | 0 |
| Treasure opening | 10-40% of games | 0% |
| teleport crystals | 1-4 | 1-10 (we buy more) |
| first kill (round) | earlier in 5 of 7 categories | |

Archetypes (k-means on 24 strategy features; overlapping tendencies, silhouette ~0.08):
- **Raid and bank** (31%): 23% of their gem pickups on our half (us 10%), 22% / 19% of mid / late clears on our
  half (us 10% / 6%), 39 deposits a game (us 22).
- **Treasure opening** (22%): 88% open with a Treasure emblem (+10% gold); we open Jungle 86%.
- **Hoarder** (5%): first deposit ~round 1100, 188-gem deposits.
- **Bruiser + altar locks**: Bruiser first, 7.6 locks a game.
- **Balanced, slightly more on our side** (the rest).

## 3. Strategy profiles (first set)

| Profile | Name | Rules |
|---|---|---|
| 0 | v92 | unchanged |
| 1 | Vision | spend every ward charge on scouting wards: furthest unwatched tile towards the enemy, near our target group, bushes preferred (`ward_vision`) |
| 2 | Raid and bank | vision; from round 300 enemy-half camps at 0.7 value; raider on; bank at 0.75x bag |
| 3 | Stat fighter | vision; Treasure + Bruiser item plan; engage only with a numbers edge; focus fire |
| 4 | Early bank | vision; bank at 0.6x bag until round 400 |
| 5 | Top-team economy | vision; Treasure / Jungle / Bruiser / Power opening; bank at 0.8x bag |
| 6 | Fortress | vision; own half only; aggression 0.8; bank at 0.7x bag; antifeed |
| 7 | Push | vision; invade from the start; aggression 1.2; hunt +2; Bruiser; numbers; focus |

## 4. Test plan

- Local: crash / fault / fuel check of pf1..pf7 (14 maps x 2 sides vs v92).
- Ladder duel plan `research/x3/duel/duel_20261103b.json`: the 12 teams rated >= 2000 that beat us most in 48 h
  (0xDEADBEEF, QS2isLaw, an iq too high, we were fed fish, Shawarma, Nameless, bbas, 剑桥夜爬者, Beehive, will
  think later, smurphy, EggsAfter11AM), 2 groups each, 64 maps. Arms: v92, pf1..pf7, v92 again (drift check).
- Per category: each profile's paired result vs v92 on that category's maps; the category table takes the best
  profile where it clearly beats v92, else v92. Then one portfolio arm (category table) on a fresh plan.

## 5. Local check of the profiles (14 maps x 2 sides vs v92; v92 vs itself = 14 / 28)

| profile | wins / 28 | faults | fuel-outs | deaths / game |
|---|---|---|---|---|
| 1 vision | 11 | 0 | 34 | 13.5 |
| 2 raid and bank | 8 | 0 | 38 | 15.7 |
| 3 stat fighter | 10 | 0 | 28 | 14.0 |
| 4 early bank | 9 | 0 | 34 | 13.5 |
| 5 top-team economy | 10 | 0 | 34 | 16.1 |
| 6 fortress | 9 | 0 | 26 | 12.9 |
| 7 push | 8 | 0 | 29 | 17.4 |

No faults; fuel normal. Every profile is below even against v92 in self-play (v92 is tuned against its own play),
which self-play cannot tell apart from ladder value; the ladder duel (plan b) decides.
