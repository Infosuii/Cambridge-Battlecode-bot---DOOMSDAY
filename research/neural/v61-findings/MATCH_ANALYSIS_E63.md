# Platform match analysis (E63, 27 Oct): 3 match groups, 11 distinct games, 0 wins

Source: `match-group-02acbb16`, `-a6d76dcb`, `-a9948bc0` (15 replays, 4 duplicated across groups). We are team A
(the `team-a.fuel` log is ours; our bot opens Prospector / Jungle / Durability / Monster / Capture / Collectors =
V59_ITEMS 2 = the m62 / b5 family). Opponent names need `cambc login` (not done). Tools: `tools/viz/extract.js`,
`agent2/lab/match_report.py` (timeline + fuel), `agent2/lab/match_deep.js` (items, deaths), lock probes (scratch).

## Results

| game | map | size | rounds | banked us - them | our deaths / theirs | our picks (first = Vendetta every game) | their core |
|---|---|---|---|---|---|---|---|
| g01 | anvil | 3v3 | 1067 | 84 - 992 | 17 / 2 | Vendetta Marcella Ryth | Vesper Heart Marcella |
| g02 | starfish | 5v5 | 983 | 32 - 977 | 29 / 8 | Vendetta Ren Varg Marcella Vesper | Vesper Vendetta Heart C&I Willow |
| g03 | contest | 5v5 | 848 | **0** - 800 | 30 / 6 | Vendetta Vesper Marcella Ryth Prism | Vesper Vendetta Heart C&I Marcella |
| g04 | harvest | 6v6 | 951 | 571 - 969 | 5 / 2 | Vendetta Ren Marcella C&I Vesper | Vesper Vendetta Heart Varg C&I |
| g05 | collision | 3v3 | 1222 | 838 - 999 | 9 / 7 | Vendetta Varg Vesper | Vesper Heart Marcella |
| g06 | vault | 4v4 | 367 | 343 - 927 | 10 / 7 | Vendetta Marcella Ryth Varg | Vesper Vendetta Heart C&I |
| g07 | gemcombat3 | 4v4 | 514 | 280 - 980 | 9 / 2 | Vendetta Marcella Heart Ren | Vesper Vendetta Heart C&I |
| g08 | breadcrumbs | 3v3 | 1211 | 802 - 997 | 8 / 2 | Vendetta Marcella Heart | Vesper Heart Vendetta |
| g09 | road-of-riches | 5v5 | 517 | **0** - 990 | 5 / 0 | Vendetta Varg Marcella Heart Ryth | Vesper Vendetta Heart Varg C&I |
| g10 | reverse-spiral | 4v4 | 1468 | 146 - 993 | 41 / 4 | Vendetta Marcella C&I | Vesper Heart Marcella |
| g11 | treasure-box | 6v6 | 925 | 806 - 950 | 21 / 9 | Vendetta Varg Ren Heart C&I | Vesper Vendetta Heart C&I Marcella |

Close games: collision (838), treasure-box (806), breadcrumbs (802, we led 659-596 at round 800 and 754-724 at 1000).

## Why we lost, in order of size

### 1. We never buy combat stats (the biggest single cause)
Shards bought by the end (emblem = 5 shards), economy/utility families vs stat families (Bruiser / Power / Greed):

| game | us economy | us stats | them economy | them stats |
|---|---|---|---|---|
| g01 | 37 | **0** | 40 | 146 |
| g02 | 48 | **0** | 48 | 266 |
| g03 | 87 | **0** | 73 | 221 |
| g04 | 115 | 5 | 62 | 124 |
| g05 | 90 | 59 | 40 | 252 |
| g06 | 16 | 0 | 22 | 9 |
| g07 | 9 | 0 | 25 | 1 |
| g08 | 39 | **0** | 38 | 56 |
| g09 | 20 | **0** | 49 | 57 |
| g10 | 68 | **0** | 40 | 402 |
| g11 | 127 | 54 | 64 | 272 |

- Our opening is six economy emblems (30 shards per champion) before any stat. With our income, most champions
  never finish it: g02's Vesper ends a 983-round game with str 75 / hp 1000 (base) owning Jungle + Prospector only.
- Their build: Treasure (or Monster) + Jungle (+ Durability) = 2-3 emblems, then main-stat **Bruiser** (or **Power**)
  emblems: their Vesper ends with 19-26 Bruiser strength emblems (str 580-760), their Marcella 47 (str 1139, g10).
  Their Heart stacks Bruiser health (hp 7500) or Power focus (foc 420-470).
- Power gap opens by round 200 and compounds: g02 their Vesper r200 130 str / 2100 hp vs ours 45 / 1000.
- This also explains the lab: our reference opponents (v61, b5) buy the same economy-first build, so economy-first
  looked best in closed-loop tuning (E52). Against a stat-stacking team it loses every fight.

### 2. We die far more, mostly alone or outnumbered, in our own half and the middle
- Deaths 5-41 per game (median 10) vs theirs 0-9 (median 2). g10: 41 vs 4; g03: 30 vs 6; g02: 29 vs 8.
- Of our deaths: "alone" (no ally within 4) 4/5 in g09, 22/41 g10, 21/30 g03, 15/29 g02; outnumbered by 2+ 22/30 in g03.
- Many deaths with low health a round earlier (60-350 of 1000-1500): we stay in fights we cannot win.
- Spread: mean distance to the nearest living ally us 5.0-11.5 vs them 3.2-7.9 (g04 11.5 vs 5.8, g07 10.9 vs 5.9,
  g03 8.6 vs 4.1). They move as a pack and pick off our single champions.
- Where: our deaths are in our own third or the middle (g03: 26 of 30; g10: 33 of 41): they farm and fight on our
  side of the map.

### 3. Gems lost on death and no banking
- Gems lost carried into death: g10 270, g09 212, g05 207, g11 123, g07 98, g08 80. g09 (road-of-riches): we carried
  33 / 61 / 83 / 177 gems at rounds 100-400 and banked **0** all game: every carrier died before reaching an altar.
- g03 (contest): we banked 0 and never carried a gem: we could not farm at all.

### 4. Altar locks: they lock, we never do
- Enemy locks on our altars (seen by us): contest 764 of 849 rounds (on average 1.76 of the 2 altars locked), anvil 747
  of 1068 (its only altar), reverse-spiral 578 / 1469, breadcrumbs 448 / 1212, starfish 405 / 984.
- Our locks: **0 rounds in all 11 games** (our prelock / deny code never fires against them).
- Our carriers spent 10-68 champion-turns standing next to an enemy-locked altar with gems (the tribute turns into
  hits on the lock). The bot does not read enemy locks at all (E61 audit; A2_LOCKAWARE written, untested here).

### 5. Draft
- We pick Vendetta first in all 11 games; they always have Vesper (+33% gold, their top scaler) and Heart, usually
  Marcella and/or Cassi & Issac. Our Vesper (when we draft her) never scales because of 1. b5's code has
  V60_VESPER_FIRST (off).

### 6. Fuel: not a cause
- Draft turn 1 uses 88-118k of 10M (1%); champion turn 1 80-181k of 200k (g09 5v5 on 51 groups: 181k, near the cap);
  later turns average 23-59k of 100k; turns at >= 99k: 3 in ~43,000. Overruns are not losing us games.
- So ~40-75k fuel per turn is unused: room for a deeper fight search / better retreat evaluation.

## What to change (each needs a test against a stat-stacking opponent, not only v61 / b5)

1. **Item plan: short opening, then stats.** At most 1-2 economy emblems (Jungle; Treasure or Prospector), then main-
   stat Bruiser stacks with health every 2-3 (V59_ITEMS 1 = the winners' order already exists in the code), casters
   focus. Buy stats first when behind in power. Expected to be the largest single fix.
2. **A realistic sparring opponent.** Make a v61 variant that copies this opponent's style (winner build, Vesper +
   Heart draft, group movement, altar locks) and add it to every lab test and knob search; our own family alone
   rewarded the wrong build.
3. **Stay together.** Raise cohesion (knobs k11 / k38), travel and farm in pairs or as a team early; no solo farming
   in the middle or the enemy half while enemies are unaccounted for.
4. **Retreat earlier when outnumbered or outclassed.** Use the power gap (enemy str / hp vs ours), not only health:
   leave fights at a higher health share, never fight 1-vs-2+; recall before the bag is lost.
5. **Bank smaller bags more often when enemies are near**; carriers walk with an escort; drop deep farming when a bag
   is large and the path is contested.
6. **Altar-lock war.** Read enemy locks (A2_LOCKAWARE), clear them as a group (5 hits) only when safe, and place our
   own locks on the altar they bank at (we place none today); keep a lock in stock (10 gold).
7. **Draft.** Test Vesper first (V60_VESPER_FIRST) and Heart, since their core beats ours every game.
8. **Use the spare fuel** (~50k a turn) for a deeper fight / escape search once 1-4 are fixed.
