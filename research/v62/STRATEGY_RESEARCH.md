# Strategy research: what could give DOOMSDAY its big break (2026-10-26)

Claude Code. Sources: public Cambridge Battlecode 2026 repositories and READMEs, MIT Battlecode postmortems,
RTS/MOBA AI research, and our own ladder data (`research/v59/`). Every proposal is tied to a gap we measured.
External claims are attributed; most public CAMBC repos come from teams ranked below us, so their ideas are
treated as hypotheses, not proof.

## 0. Summary: ten strategies, ranked by expected impact

| # | Strategy | Gap it attacks (measured against the top 12) | Evidence | Effort |
|---|---|---|---|---|
| 1 | **Burst-ready engagements**: hold spells for fights and engage only with spells up | They cast on our champions 2x as often at the same total cast rate; we take 36.6 hp per contact round to their 17.1 | Our replays; MIT postmortems; our own `APEX_SPELL_HOLD` note (Oct 15) | Low: candidates v62d/v62f exist |
| 2 | **Team focus target in shared memory** | They kill us 11.9 times per game, we kill 4.0 | Lanchester square law; dps/hp kill-order proofs; Siege (CAMBC) byte-7 focus target | Medium |
| 3 | **Turn-order tempo micro**: step into range only on rounds where we act first, kite after hitting | Half the damage per contact round | Rules: the starting team swaps every round; MIT 2023 "Don't @ Me" kiting | Medium |
| 4 | **Careful mode / death-spiral breaker** | We die 14.2 times per game, they die 5.0; 23% of our deaths come within 60 rounds of respawning | Siege (CAMBC) careful mode and respawn wait; our spawn-death data | Low-medium |
| 5 | **Move as a pack** (follow-first, step-up) | Outnumbered 18-21% of contact time vs their 11-13%; whole-team pushes by Supaswag | MIT 2023 "follow first"; OpenAI Five team fights; Lanchester | Medium |
| 6 | **Carry economy**: one designated capturer/banker per region, escorted banking | Their Vesper earns 2,700 gold; ours 870; their carries buy 40+ Bruiser shards | Claudus study; Siege's Marcella banker and escorts | Medium |
| 7 | **Combat forward model** for engage/retreat (Portfolio Greedy Search) | Our engage verdicts are heuristic thresholds | SparCraft/PGS (Churchill & Buro 2013) | High |
| 8 | **Mine top-vs-top replays** for decision thresholds | Our tuning only ever saw our own lineage | `cambc matches list --team <any team>` works for other teams | Low |
| 9 | **Evolutionary candidate loop judged by ladder duels** | One candidate per hour by hand | dawkaw0dy/battlecode-agent-evo; the "winning" plugin; FunSearch in chamyao | Medium |
| 10 | **Adaptive "fortress" defence** around spawn | 6.5 of 13.8 deaths per loss within 15 tiles of our spawn | Spawn heals to full every round (100/100 samples) | Done in v60; extend |

If only three things are done: **#1, #2 and #3 together**, as one fight package. Each alone is small; together
they reproduce how the top teams win fights: arrive together with spells ready, hit first, focus one target.

## 1. What we are trying to fix (from our own data)

From `research/v59/V59_LADDER_TESTS.md`. v60 against the top 12 (ranks 1-12, 120 games): 15 wins, mean gem
margin -465.

| Per game | Us | Top 12 |
|---|---:|---:|
| deaths | 14.2 | 5.0 |
| kills | 4.0 | 11.9 |
| gold earned | 4,156 | 7,108 |
| gold at R100 / R500 | 295 / 1,704 | 353 / 2,520 |
| hp lost per round in contact | 36.6 | 17.1 |
| PvP spell casts (Marcella / Heart / Ryth) | 12.5 / 10.2 / 12.3 | 23.7 / 20.2 / 22.7 |
| damage per PvP action (Vesper / Marcella) | 98 / 108 | 203 / 185 |

The action mix in contact is otherwise the same: attack rate, moves, total casts per round. So the gap is *what*
our actions hit and *when*: spells already spent on camps, damage spread over several targets, and fights taken
outnumbered or at the wrong moment. The economy gap (gold) follows from deaths: every death is 60 rounds of no
farming, 100 gold to the killer and the carried bag.

## 2. What other CAMBC 2026 teams do (public repositories)

Treat these as idea sources. None of these repositories is from a team ranked above us, as far as we can tell.

**Siege (MathCosine/cmbc)**, the most complete public write-up:
- **Team focus target**: the team agrees one enemy through shared memory (byte 7). Damage spells and stuns
  fire at that target, or at the weakest enemy in spell range, *before* moving.
- **Ranged patience**: ranged champions let enemies step into range, for up to 6 turns, rather than stepping
  into theirs.
- **Calls for help and joining**: a champion in a fight sets a status flag. A healthy teammate within 14 tiles
  walks over, and champions join a teammate's fight when an enemy within 7 is hitting one of us. Carriers with 30+
  gems neither answer nor join.
- **Careful mode**: after 3 team deaths in 150 rounds the team banks at 10 gems, avoids camps near the enemy
  spawn and counts even fights as losses, until deaths stop. After 2 deaths in 120 rounds, a respawned champion
  waits up to 40 rounds for a teammate.
- **Banking**: bank at 40 (10 in careful mode). A 30+ bag on its last 10 tiles gets an escort, and the banker
  waits up to 8 rounds for it. Marcella acts as banker (she earns 2 gold per gem tributed) and teammates leave gem
  rewards to her within 8 tiles. Never start a channel the enemy could kill you during.
- **Altar zone**: camps within 6 of a middle or enemy-side altar score 40% more; camps nearer the middle up to 30% more.
- Their own caveat: some local gains did not carry to the ladder (version 20 went 3-17 on the ladder).

**Others**:
- **chamyao/battlecodecamb** notes Sprint 1 was won by Intercontinental Fish (runner-up Nyx). Measured single
  changes against weaker opponents: strength shards +0.22, abilities on camps +0.20, recall at 20% health +0.11,
  and delaying tribute for a bigger bag hurt. Against strong opponents, our data says spells must be kept for
  fights; both can hold, at different times and against different opponents.
- **bird-business**: a test "ganker" bot that hunts carriers beat their main bot; their own conclusion was to
  "move and fight as a pack, focus fire, stuns". Their unranked games against top-75 teams: 0 kills, 94 deaths in
  4 games.
- **userVatsal (goldrush)**: "stay on spawn until healed" fixed a loss pattern against a top UK team.
- **Evolutionary tooling**: dawkaw0dy/battlecode-agent-evo runs an evolutionary search over bots written by
  Claude Code cloud agents, evaluated on GitHub Actions. The `winning` plugin in mishafyi/claudus-maximus deploys
  3 agents per round on competing strategies and keeps the verified winner. The name matches the rank-4 team, but
  that is unconfirmed.

## 3. What MIT Battlecode winners report

- **Micro is a weighted score over candidate moves**, built from game constants taken at face value (SPAARK 2025):
  "just taking all the game constants at face value is enough to be competitive with top teams". They score each
  candidate tile (direction to goal, danger, ally crowding, one-shot risk) and **consider both orders, attack then
  move and move then attack**. Many frameworks only consider one.
- **Target value** (Don't @ Me 2023): unit type value + damage dealt + half the enemy's missing health + 100 on
  kill, always preferring targets already in action range.
- **Kiting and tempo** (Don't @ Me 2023): attack first, then step back, possibly out of the enemy's vision, for a
  free hit. This works best when your unit moves first in the round. **Step up**: if an ally is already in range
  of the enemy, step in rather than kite away.
- **Follow first** (Don't @ Me 2023): top teams' units "would stick together ... to take grouped trades against
  isolated" units. Their fix: each unit follows the first nearby ally that moved this turn.
- **Fallback**: hurt units return to a healing zone and stay until full unless an enemy appears.
- **Testing**: many top teams run large parallel A/B scrimmage systems (No Thoughts 2023). Scrimmage analysis
  matters more than raw win rate against old bots, and overnight runs are productive (SPAARK). Do not ship
  last-minute changes without the test script.

## 4. What game-AI theory says

- **Lanchester square law**: under aimed fire, fighting strength grows with the square of the number of units, so
  two against one is four times stronger, not twice. Being outnumbered in 18-21% of contact time (theirs 11-13%) is
  much costlier than it looks. Grouping and refusing uneven fights is the cheapest large gain.
- **Kill order**: in sequential fire the optimal order sorts targets by damage output divided by time to kill
  (attack/hp), recomputed as health changes (AAAI small-scale RTS combat; Smith's rule). "Lowest health" is a close
  cheap approximation. Everyone hitting the same target also removes enemy damage fastest.
- **Combat search**: Portfolio Greedy Search (Churchill & Buro 2013, SparCraft) searches over a small portfolio of
  scripted behaviours per unit (attack-closest, kite, focus-weakest, retreat) with playouts, beating alpha-beta and
  UCT for up to 50 v 50 at 40 ms. Its strength depends on how faithful the forward model is. Our `tsearch` module
  and the `A2_TSX` switch are the place for this.
- **OpenAI Five**: humans spread out to farm and kept net worth even, but lost because "when the inevitable big
  confrontation between the two teams happened, OpenAI Five always came out on top". That matches our data: the
  farming gap is 10-24%; the fight gap is 3x in kills.

## 5. Proposals in detail (with where they go in our code)

### P1. Burst-ready engagements
- Turn on stun hold first: `APEX_SPELL_HOLD 2` plus `NOVA_STUN_FOCUS 1.0` (candidate `bots/v62f`, -23 locally,
  not yet ladder-tested). Then full hold (`APEX_SPELL_HOLD 3`, `bots/v62d`, -75 locally).
- New rule: a healthy champion without a sure kill waits outside enemy reach until at least one damage spell or
  stun is ready, then engages. The cooldowns are already tracked (`spell_ready`, `cooldown[]`) and can be read for
  visible enemies (`sdk_champion_cooldown`).
- Expected local cost: slower camp clears. Expected ladder effect: more PvP casts and kills. Ladder-duel it
  against the top 12, not in self-play.

### P2. Team focus target
- Shared memory is fully used: six 8-bit claim slots plus a 16-bit sighting. The claim codes 112-118 ("engage enemy
  k", `write_order`) already exist for the team fight commander, so a focus target can be published as a fight order
  in the engaging champion's slot.
- Rule: the first champion that engages writes its target. Every ally within 8 adds a large worth bonus to that
  target in the `handle_enemies` key (`worth` in `bot.cpp` around line 3240), ahead of its own pick. Choose the
  target by attack/hp, highest first.
- Overkill guard: if the target dies to hits already landed this round, fall back to the next attack/hp target.

### P3. Turn-order tempo micro
- The starting team swaps every round, and within a round teams alternate turns. A champion can work out whether
  it acts before the enemy's next turn. Rule for ranged champions: step into range only when we then act again
  before the enemy can respond; otherwise wait at range+1 and let them step in (Siege's "ranged patience"). After a
  basic attack, a melee champion with a dash or reset steps back out of range when the enemy acts next.
- Consider both orders (attack-then-move and move-then-attack) for every champion each turn, as SPAARK did. Our
  ranged champions cannot do both, but melee can, and `V58_ACT` bits 4 and 8 already cover part of this.

### P4. Careful mode and death-spiral breaker
- Team death counter in shared memory: the claim slot code 254 already marks a dead champion, so recent deaths can
  be counted from claim changes. After 3 deaths in 150 rounds: bank at 10, skip camps nearer the enemy spawn, treat
  even fights as losses (`APEX_OUTNUMBERED` margin to 1 temporarily), until 60 quiet rounds.
- Respawn wait: after 2 team deaths in 120 rounds, a respawned champion stays on spawn (`home_guard` from v60) up
  to 40 rounds until a teammate is within 6.

### P5. Move as a pack
- Follow-first: when no camp job needs this champion within 3 rounds, step toward the nearest ally that moved this
  turn. Step-up: when an ally is already in range of an enemy, step in instead of kiting.
- `A2_TEAM 2` + `APEX_COHESION 0.3` (v62c) was neutral to slightly negative (15/120 vs 15/120, margin -29 ± 44):
  cohesion through camp choice alone is not enough. Movement-level following is the next step.

### P6. Carry economy
- One designated capturer per region: the champion with the best gold multiplier (Vesper 1.33, Treasure +0.2)
  stands on captures; others move on. `UB_GOLD_FUNNEL` does this for Vesper only.
- Marcella as banker (2 gold per tributed gem) with escorted final approach (Siege). Bank at 40 normally, 10 in
  careful mode.
- Fix our Vesper first: drafting her first lost -90 locally, and our Vesper earns less than our Vendetta despite
  +33% gold. Profile her turns with a logging build (`docs/handoff.md` section 5).

### P7. Combat forward model
- A fight evaluator over a small portfolio of team behaviours (all-in on focus target, hold at range+1, retreat to
  spawn), scored by a 3-5 round deterministic playout using real stats, spell cooldowns and the turn order. Run it
  once per round by one champion (fuel), and publish the verdict as a fight order. `tsearch.cpp` exists;
  `A2_TSX` is off.

### P8. Mine top-vs-top replays
- `cambc matches list --team "Intercontinental Fish" --kind ranked --json` lists any team's matches, and
  `matches download` fetches their replays. Pull top-4 vs top-12 games and run `tools/replay/fight_review.mjs` and
  `hero_actions.py` on both sides. Measure engagement conditions: local numbers, hp, spells-ready share at first
  hit, who acts first. These become our thresholds, rather than copying their visible choices.

### P9. Evolutionary loop judged by the ladder
- Use `tools/replay/duel_pipeline.sh` overnight: a queue of candidates, each played on the same top-12 plan
  (`research/v59/duel_top1.json`; baseline arms v60, v61 and v62c are already played), at 24 groups per arm and up
  to 2 arms per hour. Generate candidates as switch combinations and small code edits (FunSearch / the `winning`
  pattern), keep the best by paired gem margin, and re-test the winner on a fresh plan (`duel_top2.json`) before
  shipping.

### P10. Fortress defence
- v60's home guard holds the spawn while enemies are visible. Extend it: when 2+ enemies are within 10 of our
  spawn, every champion within 25 converges to the spawn edge and fights from spawn tiles (full heal each round).
  An enemy that commits there loses the fight.

## 6. Suggested order of work

1. Ladder-duel v62f, then v62d, against `duel_top1.json`; keep the better one if its paired margin is positive.
2. Build P1 (engage only with spells ready) and P2 (team focus target) on top; duel.
3. Build P3 (tempo micro) and P4 (careful mode); duel.
4. In parallel, run P8 (top-vs-top replay mining) to set the thresholds for 2-3.
5. Run P9 overnight with the remaining switch inventory (`research/v59/V59_LOSS_ANALYSIS.md` section 1).

## Sources

- [MathCosine/cmbc (Siege)](https://github.com/MathCosine/cmbc)
- [itz-lakshya/battlecode](https://github.com/itz-lakshya/battlecode)
- [mustbethewayforward/bird-business-battlecode-camb26](https://github.com/mustbethewayforward/bird-business-battlecode-camb26)
- [userVatsal/Cambridge-battlecode](https://github.com/userVatsal/Cambridge-battlecode)
- [chamyao/battlecodecamb (docs/STRATEGY.md)](https://github.com/chamyao/battlecodecamb)
- [dpark2380/cambridge-battlecode](https://github.com/dpark2380/cambridge-battlecode)
- [Ahmed-Abdul-Rahim/definetly-not-battlecode](https://github.com/Ahmed-Abdul-Rahim/definetly-not-battlecode)
- [dawkaw0dy/battlecode-agent-evo](https://github.com/dawkaw0dy/battlecode-agent-evo)
- [mishafyi/claudus-maximus](https://github.com/mishafyi/claudus-maximus)
- [privateducksheep/pdsheep-tracker](https://github.com/privateducksheep/pdsheep-tracker)
- [Battlecode 2025 Postmortem, SPAARK](https://battlecode.org/assets/files/postmortem-2025-spaark.pdf)
- [Battlecode 2023 Postmortem, Don't @ Me](https://battlecode.org/assets/files/postmortem-2023-dont-at-me.pdf)
- [Battlecode 2023 Postmortem, No Thoughts](https://battlecode.org:443/assets/files/postmortem-2023-no-thoughts.pdf)
- [Churchill & Buro, Portfolio Greedy Search and Simulation for Large-Scale Combat in StarCraft (2013)](https://www.cs.mun.ca/~dchurchill/publications/pdf/combat13.pdf)
- [An Analysis of Model-Based Heuristic Search Techniques for StarCraft Combat Scenarios](https://ojs.aaai.org/index.php/AIIDE/article/view/12962)
- [Combat Models for RTS Games (arXiv 1605.05305)](https://arxiv.org/pdf/1605.05305)
- [Small-scale RTS combat target ordering (AIIDE)](https://ojs.aaai.org/index.php/AIIDE/article/download/12410/12269/15938)
- [Lanchester models (NPS)](https://faculty.nps.edu/mpatkins/docs/lanchester.pdf)
- [Which unit do you shoot first?](https://stuvel.eu/post/2007-04-11-which-unit-do-you-shoot-first/)
- [OpenAI Five (alignment newsletter commentary)](https://www.lesswrong.com/posts/WCpv3KH7hvRqLTKqw/alignment-newsletter-19)
- [OpenAI Five, Wikipedia](https://en.wikipedia.org/wiki/OpenAI_Five)
