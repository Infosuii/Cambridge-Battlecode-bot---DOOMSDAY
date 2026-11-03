# Gem collection and banking: what loses us games, what the literature says, what to build (2 Nov 2026)

Data: every ladder summary we have (`data/ladder/x1c1`, `data/ladder/v92`; 143 distinct games, 81 losses), audited
with `research/x3/banking/bank_audit.py` (output `audit.txt`, per game `audit.json`). Engine fact that drives
everything below: **a champion's carried gems go to its killer** (`bots/x3/src/common.h:2032`). A death with a bag is
a double swing: we lose the bag and the enemy gets it.

## 1. Where our gems go

| per 100 gems collected | banked | handed to the killer | still carried when the game ends |
|---|---|---|---|
| us, in our losses | **69.6** | **17.6** | **12.9** |
| opponents, in those same games | 91.9 | 4.3 | 3.8 |
| us, in our wins | 92.1 | 4.0 | 3.9 |

Per lost game (median): we collect 752 and bank 530, hand 65 to killers and strand 32; they collect 1,071 and bank
1,012. Two gaps, about equal in size:
- **Conversion** (what happens to a bag once picked up). Upper bound from the gem totals: **22 of 81 losses flip if
  our carriers never die with a bag**, 27 of 81 if we also strand nothing at the end.
- **Collection rate**: we collect about 30% less in losses. That's the camp / route / team-allocation side.

The opponents deposit about twice as often (27 vs 15 deposits a game, similar size ~25-29 gems) and spend fewer
champion-rounds walking around with 30+ gems.

### The zero-deposit games
- **00the_line vs SquidProxyLove (x1c1, twice: 0 banked of 491 and 334 collected).** A 33x33 map with a jackpot
  group in the middle. Each time one of ours picked up the jackpot it died in the middle before reaching our
  altar (13 deaths); their Marcella collected at our death tiles and banked at (3,16). Our collection fed their score.
- **03homonoliths vs 0xDEADBEEF (v92): collected 0.** We never captured a group at all (they hold the camps).
- adgato_gemcombat4 vs Claudus (210 banked of 1,107; 535 handed to the killer, 362 stranded), 03ultrastarvation
  (117 of 452; 335 to killers), 03showdown (97 of 363) follow the same pattern.

## 2. What the bot does now (bots/x3)

- `Bot::tribute_if_needed` (bot.cpp:4835): bank when the bag reaches `kTributeCarry`, when the altar is close, on a
  bank-rhythm rule (`dist * kBankRatio <= gems`), at the end of the race (only within 20 steps), or when threatened
  within 6 tiles with 20+ gems and the altar within 8.
- Carrier routing: with 15+ gems, enemy sightings within 10-15 rounds are drawn as **hard blocked squares** of
  radius 4 (`World::threat_zone`); if that leaves no path, the carrier takes the plain shortest path, straight
  through the enemies. Altar choice = nearest reachable ring tile; no risk term, no lock awareness.
- Camp choice: `route_search` (bot.cpp:6305) ranks routes of up to 3 groups by gems per champion-turn with teammate
  claims. The rate ignores the trip back to an altar and the risk of carrying the bag through that trip.

## 3. What the literature says (and how it maps)

- **Central-place foraging and the marginal value theorem** (Charnov 1976; Orians and Pearson): a forager that must
  bring loads back to a nest should take bigger loads the farther the patch is, and leave a patch when its intake
  rate drops below the habitat average including travel. **With predation risk**, loads shrink below the
  rate-maximising size (Barrette and Giraldeau 2008, chipmunks), and costs rise with distance and load (Olsson, Brown
  and Helf 2008). -> Our carry threshold should fall with route danger and rise with altar distance; camp choice
  should count the trip home.
- **Risk-sensitive foraging, the energy budget rule** (Stephens 1981; Kacelnik and Bateson 1996): be risk-averse when
  ahead of what you need and risk-prone when behind. -> When we lead the race, bank small and often; when we trail
  late, a big risky bag can be right.
- **Risk-aware path planning**: threat cost maps with severity and radius integrated along the path (bi-criteria
  planning, arXiv 1511.01166); Limited-Damage A* (shortest path under a damage budget, built for game AI); learning-
  accelerated risk-aware A* (arXiv 2409.11634). Plain Dijkstra works when the risk cost is additive per tile.
  -> Replace the hard threat mask with a cost field: cost per step = 1 + lambda * bag * risk(tile).
- **Halite (I-IV) bots**: returning ships pay turns plus a path cost; dropoff placement by nearby resource and how
  fast it can be delivered; Halite IV bots weight enemy threat by cargo ("halite in a hold is stealable, in the bank it
  can never be lost"). -> Same economy as ours: a loaded carrier is a target; bank at the cheapest safe altar.
- **Multi-agent pickup and delivery** (Ma, Li, Kumar, Koenig, AAMAS 2017: Token Passing / with task swaps) and
  **consensus-based bundle allocation with time windows** (CBBA; Ponda et al., Godoy and Gini): greedy online task
  assignment with swaps when another agent is better placed. -> Camp ownership (one owner per capture, Agent 2's
  11.6 vs 19.6 gems per capture) and respawn timing as time windows.
- **Battlecode postmortems** (2023 Gone Fishin', no thoughts head empty; 2025 SPAARK, confused): weighted pathing
  that prefers friendly space and avoids enemy space; carriers clogging the base area.

## 4. Features to build, ranked by evidence x size

| # | Feature (switch) | Mechanism | Targets |
|---|---|---|---|
| B1 | **Risk-cost carrier routing** (`X1_SAFEROUTE`) | Dijkstra (bucket queue, integer costs) from the altar rings over a cost field: step cost 1 + lambda * min(bag, 120)/30 * risk; risk(tile) from every recent sighting: enemy can reach the tile no later than we do (their distance field vs ours, staleness-decayed), plus a bonus for tiles near allies. Pick the altar by total cost, skip enemy-locked altars. Never falls back to walking through enemies: if every route is too dangerous, wait near allies. | 17.6% handed to killers |
| B2 | **Bag-at-risk banking** (`X1_BAGRISK2`) | Bank when bag * hazard * trip_time > expected gems from staying (MVT with a hazard term); hazard from enemies seen near the route, our health, enemy numbers; x2 for the killer-takes-it swing. Carry threshold falls when the map centre is contested (00the_line). | 17.6% + small bags |
| B3 | **Race-aware endgame** (`X1_RACEBANK`) | Project both teams' finishing round (banked + visible carried, deposit rate); once theirs is within our trip time + margin, every bag of 5+ goes to the cheapest altar at any distance; when we lead, bank everything smaller. | 12.9% stranded |
| B4 | **Carrier shadowing** (`X1_ESCORT`) | When a carrier with 40+ gems has an enemy within 8, the nearest healthy ally within 6 moves between them (or the carrier routes past it). | lone carrier deaths |
| B5 | **Hunt loaded enemy carriers** (`X1_BAGHUNT`) | Target priority by enemy carried gems (we take them on a kill). | double swing in our favour |
| B6 | **Trip-aware camp choice** (`X1_TRIPRATE`) | `route_search` rate = gems / (capture + travel + trip home), the trip home costed with B1's field. | 30% collection gap |
| B7 | **One owner per capture** (`A3_ONE_OWNER`, tracker row 37) | Already in the code, off; screening in J019. | collection gap |

B1-B3 are one carrier module and go first; they need fuel care (one Dijkstra per carrier per turn, cached for 3
turns, only when the bag is 15+ and an enemy was seen; cap at 25k fuel and fall back to the current BFS).

## 5. Results (3 Nov 2026): B1-B3 built and gated, none adopted

Gate: pool maps vs v92 / v86h / x1bru, both sides, 516 games; base x3mf (X1_MAPFIT=1) 96 / 115 / 130 = 341.
Noise floor: the do-nothing build `X1_NOOP=1` (one volatile store per call, so only fuel and code layout change)
scored 99 / 113 / 126 = 338, so a pure layout shift costs about 3 games. Anything at -10 or worse is a real loss.

| line | total | vs base |
|---|---|---|
| RACEBANK (B3) | 340 | -1 (noise) |
| SAFEROUTE 1 (B1, reach mask, cached per round) | 314 | -27 |
| SAFEROUTE 1 + BAGRISK2 (B1 + B2) | 307 | -34 |
| SAFEROUTE 1 + RACEBANK | 312 | -29 |
| SAFEROUTE with bag 40 / bag 25, 3 layers | 318 / 321 | -23 / -20 |
| SAFEROUTE 2 (old mask first, layers only as fallback) | 320 | -21 |
| SAFEROUTE 2 + hold when no safe route | 302 | -39 |
| SAFEROUTE 2, lazy reach search | 312 | -29 |

**SAFEROUTE is aborted.** Two causes, both measured: (1) fuel. Each reach search is a host BFS plus a ring rebuild;
it raised fuel-outs (171 -> 479 in the first version) and, even under a 35k fuel guard, it takes fuel the fight
search uses at the end of the turn, so fights get worse. (2) detours. A safer route is longer, and the carrier farms
less; the hold rule (wait instead of walking through) was the worst line. The 17.6% of gems handed to killers is
real, but avoiding sightings does not recover it: most of those deaths come from fights the carrier was already in.
Next banking work is B4 (shadowing) and B5 (hunt loaded carriers), which act in the fight, and the opening contest
(00the_line is an early-fight snowball, not a banking failure).
