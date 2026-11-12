# CAMBC from first principles: how the game works, what wins, how to build the best bot (3 Nov 2026)

Sources: the rules (`v3/GameRules.md`), engine 2.0.0 values read from the engine itself (`agent2/lab/rules_probe.js` →
`agent2/lab/rules_2_0_0.json`), our measurements (E-numbers in `agent2/EXPERIMENTS.md`), platform replays (E102),
and the MOBA AI research notes (`research_notes/MOBA AI techniques for CAMBC/`).

## 1. The game in one paragraph

Two teams of 3–5 champions on a 30×30 to 100×100 grid. Camps hold gems and gold. Kill every monster in a group,
stand on its region for 5 rounds uncontested, and the reward goes to the allies standing there (split evenly). Gems
count only when **tributed** at an altar; a tribute takes ceil(gems/10) turns, and a stun, a death or an altar lock
stops it, but damage doesn't. **First team to 1,000 tributed gems wins**; at round 2,000 the most tributed gems wins
(then lifetime gold, then kills). Gold buys stat shards (30 gold each; 5 make an emblem with a passive) on your own
spawn. A death costs 60 rounds out of the game, and the killer gets every gem you carry plus 100 gold. Each champion
sees 8 tiles, with walls and bushes blocking, and **vision is not shared**. Teams share 8 bytes of memory during
play, plus 1,024 bytes written in the draft. Compute: 100k fuel per turn, 10× on the first draft turn, 2× on the
first play turn.

## 2. The mathematics

### 2.1 The race

Winning means reaching 1,000 tributed gems first. Platform games between strong teams last about 1,200–1,700 rounds,
so a winning team banks about 0.6–0.8 gems per round as a team. On today's engine, top teams were ahead of us at
every point (70 match-group games): 29 vs 15 banked at round 100, 136 vs 92 at round 300, 369 vs 246 at round 600.
A team that farms 30% faster reaches 1,000 about 30% sooner, so **income rate is the game**. Fights matter through
what they do to income: deaths, stolen bags, and time.

### 2.2 Camp economics (engine 2.0.0 numbers)

| Camp | Health | Hits for | Range | Gems | Gold | Respawn |
|---|---|---|---|---|---|---|
| Gem cluster | 120 | 0 | – | 7 | 0 | 50 |
| Gold cluster | 120 | 0 | – | 0 | 20 | 50 |
| Wolf | 1,350 | 20 | 3 | 4 | 40 | 40 |
| Elk | 2,400 | 60 | 4 | 15 | 90 | 60 |
| Golem | 5,000 | 120 | 4 | 36 | 160 | 80 |
| Monolith | 20,000 | 200 | 5 | 200 | 300 | 150 |

Solo clear at base stats, counting the 5 capture rounds (damage per turn ≈ strength + 2 × focus / 8):

| Camp | Vendetta (str 70) | Vesper (45, ranged) | Marcella (45) | Damage taken / own health |
|---|---|---|---|---|
| Gem cluster | 7 turns, **1.0 gem/turn** | 7 turns | 7 turns | 0 |
| Wolf | 20 turns, 0.20 gem + 2.0 gold/turn | 25 | 28 | 0.3–0.5 |
| Elk | 31 turns, 0.48 gem + 2.9 gold/turn | 40 | 45 | **1.6–2.6: can't be soloed early** |
| Golem | 58 turns | 77 | 89 | 6–11: team objective |

A team of four (Vendetta, Marcella, Vesper, Heart of Ruin) takes a golem in 18 turns (1.6 gems per turn as a team)
and the monolith in 72 turns (2.6 gems per turn for 77 turns, taking 14,400 damage).

What this means:
- **Clusters are the best rate** (1 gem per turn) but small, and every cluster respawns only every 50 rounds, so
  they're contested and pay mostly in the opening.
- **Elk and bigger can't be farmed alone early without a heal trip.** Camps hit the *nearest* champion, so a tank
  (Heart of Ruin, Ryth, Marcella with 1,200 health; Jungle emblem −30% camp damage) beside a damage dealer turns
  "farm, recall, walk back" into continuous farming. This is the MOBA "leash / tank the jungle" idea, and it's why
  top teams have 0.91 teammates within 3 tiles at captures against our 0.41 (E95). Fixed pairs lose because they halve
  parallel farming (E99), so the helper must come for the big camps only.
- **Walking is the hidden cost.** Top teams walk 51 rounds between captures vs our 62, and clear in 14.7 vs 17.4
  rounds (E95). With respawn timers of 40–150 rounds, farming is a scheduling problem: the right camp is the one that
  will be up when you arrive, near your next one, and safe.

### 2.3 The snowball: gold → stats → farming speed → gold

A strength shard costs 30 gold and adds the champion's growth (Vendetta +6, Vesper +5, Marcella +4.5). Camps pay about
0.03–0.04 gold per point of damage. So strength grows in proportion to itself: it multiplies by e (≈2.7) every
120–180 turns spent attacking camps if all gold went into strength, or every 300–450 rounds with walking, capturing
and health purchases. Observed: top teams' Vesper goes from 45 to 194 strength by round 600 (≈1.5 e-folds). An early
lead compounds.

Measured (E73, 200 games each, control 53.5%):

| Given at round 100 | Win rate |
|---|---|
| +150 gold to each champion | **84.5%** (+31) |
| +300 gold to each champion | **97.5%** |
| +30 gems to each champion | 67.0% (+13.5) |
| 1 free kill | 71.0% (+17.5) |
| 2 free kills | 80.5% |
| +150 gold at round 400 | 76.8% (+23) |

**One early gold point is worth roughly 0.5–0.8 gems in win value; ~100 gold per champion early decides most games.**
Item builds that speed up farming are therefore huge: building Prospector first took a lab test from 40% to 61.5%
(E52), and v59's build plus knobs won 67/100 in the real engine. Economic multipliers are worth the most early:
Vesper +33% gold (+20% more with Treasure), Marcella +2 gold per gem she banks, Monster emblem +15% camp damage,
Capture emblem (capture timer 5 → 3), Hunter (+50 gold per kill).

### 2.4 Deaths

A death costs the dead champion 60 rounds (about 5% of the game, 20–25% of a champion's output over the next 300
rounds), hands the killer every carried gem plus 100 gold, and leaves the team outnumbered for 60 rounds. One kill
early ≈ +17 points (E73). Deaths run about 12 per team per game, almost all with an enemy within 4 and mostly after
round 300. Early deaths are mostly **flights that start too late**: 89 of 111 early deaths happened while fleeing, 72
of them outnumbered when the flight began, median at 32% health (E74). Fleeing is right; standing when caught is a
disaster (25.5% vs 53.5%, E73).

### 2.5 Combat

Champions deal their strength per basic attack (melee range 1 and can walk and attack; ranged range 3, walk *or*
attack) plus one spell per turn on 8-turn cooldowns, scaled by focus. With everyone hitting at once, fights follow
**Lanchester's square law**: a side's fighting power grows with the square of its numbers (strength × health per
unit), so 3 against 2 wins with few losses, while 2 against 2 is a coin flip that costs both sides. Stuns add a turn
of free damage and break tributes, recalls and teleports. Heart of Ruin hits up to +50% harder at low health; Vendetta
resets cooldowns on kills (snowballs fights); Marcella is stun-immune. Per-turn fight choices of top teams are close
to ours (October replay study: a network predicts theirs at 48% and ours just as well), so **micro is not the gap;
which fights you take and when you leave is.** Top teams operate 7.5 tiles apart against our 11.3 and die a third as
often.

### 2.6 Banking and denial

Carried gems are at risk; tributed gems are permanent. A bag of g gems takes ceil(g/10) turns to tribute, during
which a stun or an altar lock (10 gold, needs 5 basic attacks to clear) cancels it. Expected loss ≈ bag × chance of
dying before banking, so bag size should fall as danger rises. Taking a carrier down steals the whole bag: denial is
worth doing when cheap. In our tests it cost more farming than it gained (E40, E71).

### 2.7 Information and coordination

Vision 8, raycast, bushes block from outside, and **no shared vision**. Teammates know each other only through the 8
shared bytes (claims, intents) and the 1,024-byte draft plan. Coordination therefore has to come from each champion
predicting what its teammates will do with the same rules. Tencent's HMS feeds *predicted* ally intents as inputs:
worth 62.5–37.5 and lifted reasonable openings from 22% to 83%.

### 2.8 Compute

100k fuel per turn; running out suspends the turn. v92 runs at its limit, but wasting 10–20k fuel per turn changed
nothing measurable (E104), so it isn't fuel-starved at the margin. Fuel matters for *specific* hot paths: the x1
siege line-of-sight cache was decisive on ladder maps. Heavy logic belongs in the 10× draft turn (map analysis, an
opening plan in draft memory) and in per-map caches.

## 3. MOBA / RTS strategy mapped onto CAMBC

| Strategy idea | What it means here |
|---|---|
| **Jungle efficiency** | Clear speed (strength, Monster emblem), pathing between camps with respawn timers, sustain (Jungle emblem, a tank taking camp hits). This is most of the economy. |
| **Leashing / tanking** | Camps hit the nearest champion: a tank lets carriers farm elk and golems without retreating. Help comes for big camps, then splits again. |
| **Power spikes and tempo** | Each 150-gold emblem, and early items in general, are the spikes. A team ahead in items should press its advantage (invade, contest objectives); a team behind should farm safely and avoid even fights. |
| **Objectives** | Golem and monolith are the Baron/Roshan analogues: big shared rewards needing several champions; take them when you have numbers and vision, and contest theirs only with local superiority. |
| **Map control / counter-jungling** | Own your half early (contact on the enemy half cost us ~13 gems per champion); invade when ahead in numbers (alive and items). |
| **Roles** | Economic carries (Marcella: gold per gem banked; Vesper: +33% gold), tanks / initiators (Heart of Ruin, Ryth), skirmisher (Vendetta: highest strength, kill resets), utility (Tavi field shop, Willow heals, Cassi & Issac two bodies). Top teams route captures through the carries: Marcella 38% of captures and 41% of banking, Vesper 41% of team gold (ours about 20% each). |
| **Grouping vs split farming** | Split for parallel income; converge for big camps, objectives and fights. Fixed groups lose (E99); dynamic convergence wins (top teams: rich, near camps where allies already are). |
| **Fight selection** | Fight only with local superiority, focus the weakest or most valuable target, leave early. Fleeing late is how we die. |
| **Vision** | Bushes and no shared vision make ambushes and blind spots real; wards hold an area for 10-turn recharges. |
| **Race management** | Near the end, bank everything; when behind, deny (locks, carrier hunts) to stop their last tributes. |

## 4. What makes a good bot (ranked by measured value)

1. **Early economy (rounds 0–300):** the biggest lever (+150 gold per champion at round 100 = +31 points). It comes
   from clear speed (item build), camp scheduling (little walking, no waiting on respawns), tank-assisted big camps,
   and routing rewards to the champions with gold multipliers.
2. **No early deaths:** each early kill is worth about 17 points. Leave before the fight turns (local numbers ×
   strength × health), keep teammates within support range, and size bags to the danger.
3. **Item build:** builds have been worth +20 points on this engine (Prospector first, E52). Stats per gold and
   economic passives early, defensive passives later.
4. **Draft:** the learned draft net is worth about +8 (E49). Lineups have to suit *our* play: fixed top-team lineups
   lose 7–12 points in our bot (E49), so draft and play must change together.
5. **Fight selection, not micro:** our per-turn fight choices already match the top teams'.
6. **Banking discipline and objectives:** bank small bags often when danger is up; take golems and the monolith with
   numbers.

What does *not* help, measured: knob tuning (E92, E96: noise to +1.5), forcing other camp choices (−14, E97),
whole-team strategy switches (E98), fixed squads (E99), rushes (E73), standing to fight when caught (E73), pushing
camp choice toward elite choices every turn (E104: −4 to −14).

## 5. Where v92 stands

v92 does the per-turn machinery well: camp scoring, captures, micro, fleeing logic, the fuel-tuned search. Against
top teams it loses 11–34, and the data says why:

- **Economy:** they capture 41% more and bank 64% more by round 600, with 42% more gold.
- **Reward routing:** their Marcella and Vesper take two to three times our share of captures, banking and gold.
- **Camp choice:** they pick richer, nearer groups where allies already are, for almost every champion.
- **Draft:** Vesper in ~80% of their games, 9% of ours; their Marcella ends with +1,000 max health.
- **Items:** they open with Prospector strength; v92 opens melee champions with Prospector health.

Each of these has been copied piece by piece into v92 and lost or broken even (E93, E94, E99, E103, E104), because
v92's rules, knobs and per-map tables are tuned around its own lineups and habits. Moving one piece breaks the fit of
the others (E92: moving knobs undid the per-map table).

## 6. How to build the best bot possible

### 6.1 What the best bot looks like

An **economy-first pack bot** with five layers, each cheap at run time:

1. **Draft + build planner (draft turn, 10× fuel):** pick a lineup with economic carries and a tank, write a role
   per champion and an opening plan into draft memory (first ~150 rounds of camps per champion, by respawn timing).
2. **Economy scheduler:** each champion keeps a short route of camps (2–3 ahead) maximising (gold value + gems) per
   round including walking and respawn waits, with gold valued high early (0.72 gems per gold before round 250, per
   E73). Big camps are booked with a helper (tank) through the shared memory; rewards are routed to carriers.
3. **Danger and fight model:** the death predictor (NOVA_DANGER, AUC 0.945) plus local Lanchester power decides
   farm / fight / leave. Leave early, never stand when caught, and size bags to danger (bank at lower bag sizes when
   enemies are near).
4. **Micro:** v92's existing fight search and movement. Already at top-team level per turn.
5. **Coordination by prediction:** every champion runs the same rules over the same claims (8 bytes), so each can
   predict where teammates will be: convergence for big camps and fights without messaging.

### 6.2 How to get there: change the system together, not one piece at a time

Piece-by-piece copying fails because the pieces fit each other. The method that has worked here: build the whole
structure, then re-tune its knobs around it (v86h: structure plus knobs together gave +7 where each part alone was
neutral), then refit the per-map table in the real engine (v92: +4.8).

| Step | What | Gate |
|---|---|---|
| 1 | **Economy core:** route-based scheduler with respawn timing, tank-assisted big camps, reward routing to carriers (owner = Marcella for gems, Vesper for gold), Prospector-strength opening. One build, all on. | Allocation shares move toward the top teams' (Marcella 35%+ of captures, Vesper 35%+ of gold); gems banked by round 300 up 25%+ against v92 in the same games |
| 2 | **Draft to match:** Vesper + Marcella + Heart of Ruin + Vendetta (+ Ryth at 5), the lineup the new economy is built for; draft net retrained on real-engine games of the new bot. | Step 1 + 2 beats v92 on unseen maps |
| 3 | **Danger-sized bags and early leaving** (death model as the trigger, bank thresholds by danger). | Early deaths (rounds 0–200) down 30% |
| 4 | **Re-tune knobs around the new structure** (real-engine ES, 16–24 knobs, 200+ games a candidate, held-out maps). | +8 over v92 on held-out bots, ladder and unseen |
| 5 | **Refit the per-map ladder table** on the new play (`real_fit.py`, broad pool, never v92 / x3ctr). | Ladder held-out above v92's 60.9% |
| 6 | **Ladder A/B** (the user's decision): the only judge of draft / economy changes against top teams. | Rating up |

Evaluation throughout: the real engine with fuel metered; held-out bots *and* held-out maps; 1,000+ games per verdict;
never fit anything against the bots used to judge it (that is how x3ctr reached 99% against v92 and lost elsewhere).

**Status (E106, 3 Nov):** step 1 was built from the team's existing v58 economy director (V58_DIRECTOR / ROUTE /
CARRY_SHOP / DRAFT, already in v92's source, switched off). Under real fuel it loses to v92 (42.5% director + routing;
35.4% with carry shop and carry draft; 27.9% with the survival model). The step-1 gate also fails: the economy doesn't
move toward the top teams' (Marcella capture share 16.7% vs top teams' 38%, Vesper gold share 27% vs 41%; total team
gold down 8%). Rule-based routing doesn't reproduce their loop. Before more coding, the next step is to measure how
top teams' Marcella actually gets 38% of captures (alone on rich camps? shared with a tank that then leaves?) from
their replays, and build exactly that.

### 6.3 Why this can be much better and not +2

- The measured price of economy is enormous (+31 points for 150 gold per champion at round 100). Top teams are ahead
  of us by more than that by round 300 (44 gems banked plus the gold gap).
- Every earlier attempt changed one piece inside v92's tuned whole. Steps 1–4 change the whole and then re-tune it,
  which is the only pattern that produced large gains here (v59 +17 from build + knobs; v86h +7 from structure +
  knobs).
- The risk is real: the economy core may lose to our aggressive bots locally even if it would win on the ladder (v30
  won on the ladder and lost locally). That's why step 6 exists and why the gates in steps 1–3 measure the economy
  itself (allocation, banked gems, deaths), not just wins against v92.
