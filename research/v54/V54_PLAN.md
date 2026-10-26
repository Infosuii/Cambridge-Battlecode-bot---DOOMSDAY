# V54 strategic review and improvement plan

**Status: analysis only. No v54 implementation, build, training run or submission is authorized by the current request.** The two earlier exploratory v54 changes were rejected; their experimental source directory has been removed. v53 remains live.

## 1. Recommendation

Build the next competitive advantage around **team-level economic and objective planning**, supported by reliable tactical execution. The present bot has substantial local intelligence, but it often allocates its champions, rewards and attention in ways that compound the opponent's advantage.

The central question should be: **which coordinated sequence of actions gives our team the best chance of securing a winning score before the opponent?** A locally attractive camp, safe-looking fight or powerful champion is useful only as part of that sequence.

Our differentiating strategy should combine:

1. Planned openings that reach useful item breakpoints quickly.
2. Deliberate ownership of camp rewards, matched to champion economics and roles.
3. Coordinated objective campaigns, including banking and protection.
4. Legal control of resource replenishment and altar access.
5. A small portfolio of strategies selected from the map, draft and observed opponent behavior.
6. An execution layer whose decisions survive small changes in computation cost.

The ambition is to remove exploitable weaknesses across all dimensions. That does not mean maximizing every activity simultaneously. More fighting, more grouping, more banking trips and more concentrated gold can each be harmful in the wrong situation. We need better decisions about these tradeoffs, measured by wins and secured score.

## 2. Evidence base and limits

### Latest platform results

The latest saved v53 snapshot includes games created through **2026-10-25 13:30:12 UTC**, retrieved around 13:34 UTC:

| Cohort | Record | Interpretation |
|---|---:|---|
| Ranked | 5/10 | Too small, and opponents/maps differ, to establish a version effect |
| All unranked | 31/65 | Mixed opponent strength and deliberately selected maps |
| Targeted groups against meow and Hidden Altar Keepers | 0/10 | Strong evidence that the specific weak-map strategy gap persists |
| Other unranked games | 31/55 | The bot remains competitive against parts of the field |

The standings snapshot places DOOMSDAY **78th, rating 1848.9**; 25th is **2026.6**, and first is **2380.1**. These are descriptive gaps, not a forecast of how many changes will close them. The movement in rank is not attributed to v53.

The new ranked boss_battle victory is particularly revealing: **0–0 banked gems after 2,000 rounds, won on lifetime gold**. It is a useful fallback win, but the altar-conversion problem remains.

### Replay coverage

**136 replays decoded successfully, 136/136:**

- All 75 v53 games in the latest saved snapshot, including wins.
- The 40 v52 losses from the earlier snapshot.
- Ten selected v52 winning controls on different maps.
- Eleven reference wins from Intercontinental Fish, Claudus Maximus and Mite.

Game-level measurements are in `V54_EVIDENCE.json`; map/opponent/draft tables and seven concrete trajectories are in `V54_MATCH_REVIEW.md`. `V54_WINNER_PLAYBOOKS.md` adds paired first-target/bank details and named R500 inventories for those cases and eleven top-team wins. The analysis is reproducible with `tools/replay/strategic_metrics.py`, `report_v54.py`, `winner_playbooks.py` and the pinned replay decoder. Raw replays remain local-only.

Equipment value below means original shard-purchase gold represented by current equipment: five purchased shards per emblem. It does not confuse an emblem with one shard or count its bonus stats as extra expenditure. It excludes consumables and is not a complete lifetime-spending measure if items have been sold. Equipment ratios omit games where the opponent has zero equipment; their sample counts are recorded in the evidence JSON. For v53 losses/wins respectively, R100 ratios use 36/28 games, R250 uses 39/35, and R500 uses 39/35. Deaths and time dead are sampled from successive round snapshots. Attack counts exclude spells and are not measures of damage efficiency. First-bank medians omit games with no bank.

These comparisons reveal associations and failure patterns. They do not prove that changing one variable will cause a win. Games against the same team and games from the same group are correlated. The selected v52 winning controls are not a random sample. Submission attribution is based on timestamps; the CLI match list does not expose our source hash. The two explicitly queued post-v53 groups are the clearest version association.

### What separates v53 wins and losses

| Metric, us/opponent unless stated | 39 v53 losses | 36 v53 wins |
|---|---:|---:|
| Median per-game equipment ratio, R100 | 0.60 | 1.00 |
| Median per-game equipment ratio, R250 | 0.71 | 1.45 |
| Median per-game equipment ratio, R500 | 0.67 | 1.30 |
| Median champion deaths | 12 / 4 | 3 / 11 |
| Median champion-rounds dead | 657 / 241 | 155 / 639 |
| Median completed bank channels | 16 / 30 | 31 / 13.5 |
| Median of each game's bank amounts | 22 / 29 | 27 / 28 |
| Median first bank, conditional on banking | R151 / R113 | R74 / R115 |

Against the two targeted opponents specifically:

| Metric | Us | Opponent |
|---|---:|---:|
| Median equipment value R100 | 135 | 285 |
| Median equipment value R250 | 660 | 1260 |
| Median equipment value R500 | 1755 | 3285 |
| Median champion deaths | 17.5 | 3.5 |
| Median champion-rounds dead | 1040.5 | 211 |
| Median completed banks | 3 | 31 |
| Conditional first-bank median | R78 | R79 |
| Median bank amount | 22 | 25.5 |

The last two rows matter: on these maps, simply lowering the bank threshold is not an adequate diagnosis. The teams can start banking at similar times and with similar bags, then diverge dramatically in continued production, survival and conversion. Winners also have more equipment **and**, in this cohort, more unspent gold. The problem is not explained by an unwillingness to visit the shop alone.

### Different losses require different explanations

The cohort average must not become another universal heuristic. The latest games separate at least three failure families:

- **An opening economy deficit before deaths:** fragment is 0/5. In the loss to Crimson Pathfinders, neither team had died by R250, yet equipment was 210 versus 720; by R500 it was 570 versus 2280. On concentrated_wealth against meow, our R250 equipment was 570 versus 1230 with zero deaths on our team. These are strong cases for reconstructing routes, capture ownership and purchase timing before blaming late fighting.
- **Contact and economic collapse reinforcing each other:** elkring is 0/4 and swirl 1/5. The worst swirl loss had 30 deaths versus 3, 1775 versus 181 champion-rounds dead, and equipment 480 versus 5400 at R500. Here an economic opening that ignores early enemy pressure will fail; mission-aware safety and useful retreat choices belong in the same prototype.
- **Capital that fails to become score:** boss_battle is 1/3, and its only win banked nothing. In the loss to Hidden Altar Keepers, we led equipment 3960 versus 3480 at R500, but banked 0 versus 1690. This is a direct warning that improving farming alone will not solve gated objectives.

stampede is 0/4, including a ranked 320–320 loss on gold. The old sole-gem trigger removed one inactivity bug; it did not establish a robust objective strategy against strong teams. The complete map table is in the match review. The small sample and selected groups do not justify a stable league-wide ranking of maps or drafts.

## 3. What is going wrong

### A. We enter the economy–survival feedback loop on the wrong side

Poor opening allocation or premature contact produces fewer useful purchases. That makes clearing and fighting less efficient, increases recalls/deaths, gives up further camp cycles and creates an even larger equipment deficit. Death then removes a champion for about 60 owner turn ends, in addition to losing its bag and potentially rewarding the enemy.

The equipment gap is already visible early. In the older v52 loss cohort, median deaths at R100 were zero on both sides while our median per-game equipment ratio was only 0.61. That makes opening routing and allocation a serious candidate cause, rather than treating every equipment deficit as a consequence of later deaths. In the newest targeted v53 cohort, early deaths also contribute, so both directions of the feedback loop must be measured.

**Implication:** optimize the opening as a coordinated capital-building process, then distinguish avoidable deaths from deliberate, profitable objective sacrifices.

### B. Strategic intent loses to local reactions

`Bot::play_turn` calls enemy handling before winning-bag tribute, home travel, normal tribute and farming. Much of the combat decision concerns short-horizon damage, danger or a fight verdict. This can repeatedly divert a champion whose most valuable contribution is a capture, an item purchase, an objective rendezvous or a protected bank.

The existing controller already has banking rules, route search, cohesion, claims and some tactical simulations. The missing abstraction is not another local behavior. It is a durable **team intent** with an explicit value, completion condition, risk allowance and abort condition.

**Implication:** tactical behavior should execute or protect a strategic mission, and override it for a justified emergency. Seeing an enemy should not itself define the team's objective.

### C. Resource ownership is managed too much as local fairness

`poorer_ally_takes` and `group_capture_covered` often prefer the poorer nearby champion. That can keep teammates useful, but it does not directly optimize the next team power spike or the special return different champions get from the same reward.

The controller's item-equivalent estimate is based on stats rather than a paid-inventory ledger. It compensates for Ryth's health-derived strength, but Prism's bag-derived focus is also present in the stats. This is not automatically a bug—effective power can be the desired quantity—but it makes the meaning of “poorer” ambiguous. Capital, current combat power and future marginal return are different quantities.

Top-hero equipment concentration alone does not explain our results: the distributions do not justify a blanket “feed one hero” policy. We need **role- and reward-specific allocation**, including minimum equipment needed to keep supporting champions alive.

### D. Large objectives are not managed as complete operations

boss_battle is an access-and-conversion problem. Killing the monoliths, taking their reward, reaching the altar, surviving the channel and controlling the banking window are separate tasks that must line up.

The reference wins use materially different schedules and carriers:

| Winner | First bank | First amount | First banker |
|---|---:|---:|---|
| Intercontinental Fish | R684 | 581 | Marcella |
| Claudus Maximus | R646 | 427 | Vesper |
| Mite | R420 | 148 | Heart of Ruin |

These are successful examples, not universal timings. First basic attacks on monoliths may precede these banks by a long time; casts may precede the first basic attack. We should not replace R500 with another universal date.

Mite's reference win also contains 32 sampled champion deaths. This shows why “fewest deaths” is not the final objective either: a costly operation can still win if it secures the score. Our problem is spending lives without an adequate conversion plan.

### E. Combat/world models have correctness and calibration gaps

One concrete discrepancy deserves investigation before trusting more search: the rules say damage wakes the **whole camp group**. `World::hot_zone` accounts for healthy members of an awakened group, but `World::awake_camps_near` and the fast caster-micro camp list filter for individually damaged camps. An undamaged member of an awakened group can therefore be absent from that danger list. The source discrepancy is real; its contribution to particular deaths still needs a controlled test.

Other approximations needing calibration, rather than immediate replacement, include uniform ally contribution estimates, Varg's fixed multi-target damage multiplier, bounded camp lists, partial linked-pair state and short tactical horizons. The right question is where these approximations change the action selected, not whether a more complex simulation sounds superior.

### F. Fuel is an architectural constraint and a source of policy instability

v53 reduced development fuel-exhausted turns from 274 for its opponent to 235 over 168 games: about **0.23 fewer per game**. That cannot by itself explain losses with hundreds of additional champion-rounds dead. This does not measure all damage from skipped optional work, and early pauses can have disproportionate consequences, but it argues against treating fuel reduction as the main strategic thesis.

The deeper problem is sensitivity: small computation changes alter admission/fallback decisions and then the entire trajectory. `APEX_DET` is already enabled, but fuel safety thresholds and optional stages remain coupled. `farm` can reuse an old target or give up when field preparation or tactical work consumed its allowance. The first gameplay turn can fail to farm after initialization.

**Implication:** guarantee a cheap coherent decision, place optional work under explicit quotas, and make fuel checks safety guards rather than an accidental strategy selector. Retain the handoff's once-per-call/turn discipline and avoid adding business logic to camp/group hot loops.

### G. Our evaluation is good at finding regressions, weak at proving superiority to the field

v48, v50, v51, v52, v53 and heuristic-v1 are closely related. Beating the previous version can exploit its own habits. The delayed stampede objective won 6/6 against v52 but only 2/6 in its first test against v53. A better held-out draft predictor won only 8/30 in gameplay. These are warnings about opponent specificity and controller compatibility.

The 12 release maps have also been exposed repeatedly across rejected candidates and earlier experiments. We should still run the required release gate, but cannot present them as a pristine unseen test set.

## 4. The proposed strategic advantage

### Priority 1 — Joint economic openings and explicit reward ownership

Plan the opening for the team, not as six independent nearest-best-camp decisions. The output is a collection of compatible jobs: clear, capture, shop, relocate, protect and bank. Each job identifies a crew, reward owner, timing window and next useful purchase.

The planner should estimate **time to a power spike and subsequent income**, not use one constant exchange rate between gold and gems. It must include terrain-aware travel, actual champion kits, item breakpoints, the five-round capture phase, respawn cycles and healing/shop trips. Penalize unnecessary overlapping capture occupancy: extra allies do not speed capture.

Use static full-map information during draft to prepare route candidates and role assignments. Finish choices that depend on the completed draft within the later draft budget. Store compact itineraries and intentions in draft memory; do not attempt to store full distance fields in 1024 bytes.

This should produce coordinated parallel farming, with temporary grouping only where the group clears enough faster or safer to repay the lost farming elsewhere. A support should leave a finished capture for the next task once another ally can keep the region occupied; the region must never become empty during the handoff.

**Expected reach:** broad, especially concentrated_wealth, elkring and early snowball maps. **Main risk:** over-planning against a static opponent or over-concentrating resources. **Evidence required:** earlier useful purchases, greater reward per available champion-turn, and retained effectiveness under harassment—not merely a prettier route.

### The economics make role specialization plausible

For a single capturer, before Treasure and ignoring rounding, compare the extra gold created by champion passives:

| Camp | Base gold / gems | Vesper extra on capture, 33% | Marcella extra after banking, 2/gem |
|---|---:|---:|---:|
| Gold cluster | 20 / 0 | 6.6 | 0 |
| Wolf | 40 / 4 | 13.2 | 8 |
| Elk | 90 / 15 | 29.7 | 30 |
| Golem | 160 / 36 | 52.8 | 72 |
| Monolith | 300 / 200 | 99 | 400 |

These are marginal passive returns, not complete champion rankings. Travel, clear speed, safety, rounding and equipment growth can dominate. Gold and gems are not freely transferable between teammates, so reward ownership must be planned at capture time.

A Treasure emblem adds 20 percentage points, including on Vesper. Recovering its 150-gold purchase cost through the passive alone requires about **750 additional base gold**, not 150/0.53. Its stats and the opportunity cost of delaying another item must also be included.

A promising role family is a gold-efficient farmer on gold-rich routes, a safe gem converter on gem-rich routes, and the best area-damage clearer where camp geometry rewards it. This is a coupled role/route/item hypothesis. The failed experiment that merely forced Vesper first—3/6, −56.8 against v53—shows why changing the opening pick alone is insufficient.

### What the winners' inventories and opening targets add

The detailed playbooks distinguish a strategy from a lineup:

- On stampede, both meow and v53 start by attacking gold clusters. Our first targets are not simply the wrong resource type. At R500, however, meow has Treasure emblems on all five actors, several Bruiser purchases and more equipment overall; we have no Treasure emblems and much less equipment. Its first 160-gem bank is R777. Compare capture ownership, purchase payback, clear speed and objective readiness, rather than imposing “gold first” on a bot already doing it.
- In the Intercontinental Fish boss reference, R500 Marcella has 4900 maximum HP and 22 Bruiser strength emblems, while Cassi has no items. This is purposeful-looking specialization in the observed outcome, not balanced equipment. We cannot infer its internal policy, and the aggregate data does not support feeding one hero everywhere. The testable idea is to fund a specific objective role enough to change the operation's outcome.
- The fragment winner has a heavily developed Vesper and first banks 26 gems at R56; our first bank is 8 at R174, with only 570 total equipment value at R500. Its Vesper's R500 inventory includes Monster, Durability, Treasure and Jungle emblems plus Bruiser damage/health. Our corresponding actors are still largely at Jungle-only builds. This combines income, survivability and conversion rather than optimizing one stat.

Test item packages against the next task. A Bruiser purchase trades some primary-stat specialization for other useful stats; Treasure needs enough future income to repay its cost; mitigation matters only against the damage actually taken. Compare time-to-clear, damage/recall cost and future productive turns at equal gold, then test the route/role/item mechanism in games. Copying the final inventory without reproducing its funding sequence is not a viable implementation plan.

### Priority 2 — Objective campaigns with carrier protection

Replace a fixed-round boss rush with an operation:

**Build capital → assess readiness → rendezvous → focus the gate → capture/handoff → protect banking → hold or release access → return to economy.**

Readiness depends on the actual nearby crew, health, items, cooldowns, gate health, known enemy pressure and gems that can be converted. Do not gather indefinitely: every rendezvous has a deadline and a comparison against the value of continued farming.

Two equal monoliths have about 40,000 combined health and 400 combined base damage per round while both attack. With total effective damage D, a simple uninterrupted focus-fire model takes about 24,000 damage at D=500, before shields, stuns, mitigation, range and tank rotation. Splitting damage evenly makes this worse. This explains why an early nominal “whole team” is not necessarily a viable crew. The admission test must use real mechanics and actual crew contribution.

Banking must be part of the same operation. Damage does not cancel tribute; stuns, death and locks do. The protection policy should distinguish these threats. Marcella's stun immunity is a role advantage, but the other reference wins show it is not mandatory.

**Expected reach:** very high on boss_battle and other dominant objectives. **Main risk:** helping the enemy open the same access or dying after the kill but before conversion. **Evidence required:** useful banked score after an attempt, crew time cost, bag losses, and the opponent's simultaneous conversion—not just gate damage.

### Priority 3 — Control replenishment and the clock

This is the most interesting rule-supported strategic departure from the current controller.

The rules say **any occupied spawn tile delays the entire camp group's respawn**. After clearing and capturing a valuable group, a zero-bag holder could keep it unavailable. On a sole-gem map, a team that has banked a lead may prefer to prevent another gem cycle and defend that lead until round 2000, rather than keep racing toward 1000 on equal terms.

For gated altars, holding a dead monolith spawn could maintain an open banking window. This turns access into something the team can control and schedule, instead of repeatedly rediscovering it through farming.

These are **hypotheses supported by the written mechanic, not validated winning tactics**. Important counters and costs:

- A holder gives up farming and can be killed or displaced.
- An open gate can let the enemy bank too.
- A score lead is not safe if the enemy already carries enough gems.
- Holding a resource also sacrifices our own future harvest.
- The holder should not retain a valuable bag, and replacing it must not leave the region empty at a critical respawn phase.

The decision should compare the value of the denied enemy cycle and preserved lead against our lost harvest and holding cost. Test it as an objective-control strategy, including opponents explicitly trying to dislodge the holder. Do not claim novelty relative to all top teams without further replay evidence.

### Priority 4 — Treat mobility as logistics, not just draft eligibility

Build a topology graph with walking, dash, teleport and recall edges. A teleport crystal costs 10 gold, has a three-turn channel and reaches three tiles across intervening terrain; landing must still be legal. Recall provides a return route and healing. This can make a productive expedition possible for a champion that lacks a dash.

The consequence could be larger than another island-specific reachability patch: draft the best farming or objective composition, then buy the logistics needed to reach the map's value. But one crystal is not an unlimited travel network. Champions can carry one, consumables generally require spawn/dead shopping, and Tavi's remote shopping does not exempt consumables. Plan outward trip, work, return, replenishment and enemy interruption together.

**Expected reach:** high on big_world, islands and disconnected maps. **Main risk:** spending eight or more turns on transport for a low-value camp, or losing a linked-pair member on an exposed island. **Evidence required:** completed profitable sorties, not merely successful crossings.

### Priority 5 — Make combat selective, exact where it matters, and mission-aware

Every engagement should have a strategic reason: securing a camp, protecting a carrier, killing a valuable bag, denying a bank, breaking a blockade, defending a lead, or accepting a favorable resource trade.

A fight's value includes stolen gems, gold, enemy income denied during respawn, our own lost farm, our risk of losing bags and whether the fight changes who can finish first. A wounded enemy with no bag can be a bad chase even if we would eventually win. Conversely, a dangerous contest can be correct if avoiding it loses the game.

Correct the model's decisive blind spots before expanding search: whole-group aggro, camp sleep/reset behavior, linked deaths, shielding/mitigation, attack resets, movement exclusions, channel completion order and legal vision. Use detailed simulation in the small number of states where it changes the choice; use a conservative bounded fallback elsewhere.

An optional specialist strategy is to retain a protected Prism bag as temporary focus capital for a decisive objective, while other carriers bank. This must account for the score delayed and the amplified loss if Prism dies. It is lower priority than fixing the basic economy and should not become a general “hold gems” rule.

### Priority 6 — Deny the opponent's plan without giving up our own

Use cheap altar locks, timed stuns, camp contests and opportunistic harassment where their denied income or conversion exceeds our opportunity cost. The current bot already implements local tribute denial; the new advantage would be scheduling and positioning for denial as a team task.

Do not send a unit on a long low-value raid simply because harassment is fashionable. A good raid forces the opponent to spend more champion-time or lose more secure value than we spend. Contested-camp attacks should account for the camp's own damage and who it is targeting. Personal wards should observe valuable routes and objectives; their vision is not automatically shared with allies.

## 5. A capability standard for every part of the bot

| Dimension | What being better should mean | Proof to demand |
|---|---|---|
| Draft | Select a composition that can execute the chosen map plan and answer plausible counters | Full-draft/plan tests, not raw pick win rates |
| Economy | Reach profitable item breakpoints earlier without exposing the team | R100/250/500 capital, reward rates, survival under pressure |
| Reward allocation | Give a capture to the champion with the best team return | Marginal income/score gain; supporting-role equipment floors |
| Items | Buy for the next job and the actual damage/mitigation breakpoint | Measured clear time, damage taken and purchase payback |
| Pathing | Complete the cheapest useful legal route, including logistics | Time per successful job; unreachable-target and reroute rates |
| Farming | Harvest more useful resources per champion-turn | Gold/gem reward throughput, not basic-attack counts |
| Capture | Avoid redundant occupancy and execute safe handoffs | Crew idle time and rewards lost to empty/contested regions |
| Combat | Win consequential exchanges and avoid worthless ones | Bag swing, objective control and opportunity cost |
| Survival | Preserve productive time and valuable carried capital | Time dead, avoidable deaths, lost bags; allow profitable sacrifices |
| Banking | Convert enough gems safely before the opponent can finish | Secure score, channel success and predicted finishing time |
| Vision | Spend limited observation and communication on relevant uncertainty | Action changes justified by new information; no fog leakage |
| Coordination | Make complementary commitments and arrive together when needed | Missed rendezvous, double-booking, abandoned jobs and plan completion |
| Adaptation | Select a robust response to the opponent's observable style | Performance across race, brawl, raid, denial and control opponents |
| Compute | Always produce a coherent timely action and spend optional work usefully | Tail fuel cost, suspensions, quota/fallback counts and decision stability |

## 6. Proposed architecture, if implementation is later authorized

### A. A compact team plan above the existing executor

Keep useful navigation and action primitives. Introduce a common mission representation: target, role, crew, arrival window, reward owner, readiness condition, completion condition and abort condition. The current controller becomes an executor with emergency safeguards, not a set of unrelated priorities competing to own the turn.

Use three timescales:

- **Draft:** static topology, plan family, compatible compositions, opening jobs and item milestones.
- **Periodic/event-driven macro update:** choose the next campaign when a camp, death, bank, item milestone or relevant sighting changes its value. Avoid a complete rescore every turn.
- **Each turn:** local legality, urgent safety, mission execution and bounded tactical improvement.

The old disabled draft planner is not ready to enable. It uses fixed damage, coarse health-based crew sizes and geometric travel; excludes large jobs; and derives the number of actors from draft picks, which needs special handling for Cassi/Issac. It does not model the economy/health/banking loop required here. Reuse its communication idea only after replacing its assumptions.

### B. Design coordination inside the actual memory limits

There are 1024 draft bytes and only 64 live shared bits. There is no omniscient team commander: champions have separate vision, including separate ward vision.

A possible live protocol replaces some individual claims with a team objective command plus compact actor status. For example, 16 bits for target/phase/generation and six 8-bit status slots totals 64 bits. A status could encode health band, bag band, readiness, local contact and a short epoch. This is a design candidate, not a finalized wire format. It requires freshness/wrap handling, actor/death semantics and a fallback for maps whose group IDs do not fit. Giving up detailed claims is a real tradeoff; draft-assigned farming territories would need to replace that coordination function.

Draft memory can store a few hundred bytes of itineraries and role data, leaving room for validation and fallback data. Full distance fields do not fit. Respect the API's snapshot behavior when writing draft memory; do not assume assignment updates the current instance's readable snapshot.

### C. A shared value model, not a single magic score

Use a phase-dependent model of expected secured gem difference, time to finish, future income, carried-gem exposure and champion-time cost. Maintain separate estimates for what is observed, inferred and uncertain.

Gold's value is nonlinear: the next 30 gold can complete a decisive item, while a large late surplus may be nearly irrelevant unless a tiebreak is likely. Carried gems have both score potential and risk; Prism adds a temporary combat use. An action's value should include its downstream effect on the plan rather than treating these as unrelated bonuses.

This model should first be calibrated offline against actual trajectories. A more sophisticated but inaccurate planner is worse than a simple reliable one.

### D. A bounded runtime

Create a cheap coherent fallback decision before optional search, reserve enough fuel to execute it, and admit optional work by fixed stage quotas with conservative cost bounds. Do not spend the last budget deciding whether a turn should have been spent farming.

Initial budget targets could be observation/state <=25k, mission selection <=5k, urgent legality/safety <=10k, optional tactical work <=30k and execution/tail/reserve <=20k. These are design targets requiring measurement, not claims that the current code fits them. Large-map preparation must be amortized without sacrificing all opening actions.

All new strategic logic remains behind once-per-call/turn or event checks, outside per-group/per-camp hot loops. Precompute marginal values and shortlists rather than inserting more scoring terms into those loops.

## 7. Draft and learning: what should change in the research approach

The 243,904-game draft model improves test log loss from 0.6004 to 0.5925 and accuracy from 62.8% to 64.4%, but its greedy deployment wins only 8/30, with mean gem margin -147.1. Its holdout separates unordered team pairs; it does not establish generalization to unseen team policies or a later metagame. Its 31 geometric map signatures also merge some of the 40 maps. Final-draft prediction does not validate choosing from an incomplete draft.

Use replay models to propose hypotheses and rank a small number of complete plans. Evaluate a pick by plausible completed allied compositions, enemy continuations, mobility coverage and the jobs our controller can actually execute. Both teams may choose the same champion; there are no opposing-team bans to invent.

Do not restart the abandoned policy-v2 cloning effort or simply train the small camp network longer. If learning is later used, prefer a narrow, observable macro decision or calibrated outcome/value estimate, trained with team-level reward and actual execution feedback. Validate inputs under the champion's legal perspective. Omniscient replay analysis must not leak hidden state into deployed decisions.

## 8. Evaluation must test whether we are becoming harder to exploit

Keep the required bench2 gate against the current live version. For a substantial strategic redesign, passing the old 47%/−30 noise floor should be a compatibility check, not the definition of success.

Proposed additional research targets, to agree before future implementation:

1. A material development advantage, provisionally >=60% wins and >=+100 mean gems against v53, while satisfying all original target-map requirements.
2. On the strong targeted cohort, move paired R250/R500 equipment ratios toward at least 0.9 without merely avoiding all contested value.
3. Reduce unproductive time and bag losses; preserve the ability to accept profitable objective sacrifices.
4. Show useful score conversion on boss_battle, rather than counting 0–0 gold tiebreaks as solving it.
5. Retain performance across a diverse opponent portfolio and unfamiliar legal map layouts.
6. Meet explicit compute tail-cost and fallback reliability targets at official fuel.

The numerical research targets are aspirations for a major step, not predicted effects or replacements for the handoff gate.

Build a future evaluation portfolio with genuinely different race, brawl, bag-hunting, altar-denial, split-mobility and resource-control behaviors. Earlier versions of our bot are useful regression opponents but are not a diverse league. Replays do not provide opponents' source, and the CLI's unranked groups use the currently submitted bot; an unsubmitted candidate cannot be claimed to have beaten top teams directly on that basis.

Separate exploration from selection. Freeze the final candidate before the release holdout; log rejected variants and repeated exposure. Add genuinely new evaluation conditions rather than pretending the reused 12 maps are unseen. Treat NOVA_SEED 1–3 as policy perturbations, not 168 independent random observations. Analyze uncertainty at map/opponent/group level, and record side, draft, date and opponent strength.

Use ablations for coherent mechanisms: economic allocation with and without role ownership; campaign planning with and without readiness; holding a camp with and without a score lead. Components with necessary interactions should be tested together and then ablated, rather than dismissed solely because one isolated scalar failed.

## 9. Ordered research and development roadmap

**Current authorization stops at this analysis and plan. Everything below implementation research is proposed future work.**

| Phase | Deliverable | Question answered | Exit criterion |
|---|---|---|---|
| 0. Evidence and contracts | This review, game-level metrics, source/rule cross-checks, frozen v53 | Where is value actually lost? | Reproducible evidence and explicit uncertainty; completed for current snapshot |
| 1. Economic audit | Per-actor opening timelines, reward ownership, purchase milestones, lost-time ledger | Is the opening plan economically dominated, and why? | Explain the largest gear gaps with specific missed jobs/deaths, not just correlations |
| 2. Calibrated planning model | A small offline model of clearing, travel, captures, items, healing and channels | Can we predict useful sorties and objective readiness? | Prediction error bounded on withheld trajectories; no bot deployment yet |
| 3. First coherent strategic prototype | Joint opening jobs, reward owner and item milestone as one mechanism | Can coordinated capital formation beat independent greed? | Strong development and diverse-opponent evidence; original gate remains mandatory |
| 4. Objective-control prototype | Readiness, rendezvous, gate conversion, carrier protection, hold/release policy | Can we turn resource advantage into reliable wins? | Secured score and positive opportunity cost under explicit counterplay |
| 5. Logistics and selective tactics | Transport graph, exact critical mechanics, mission-aware fight choices | Can we cover the map and defend the plan? | Profitable sorties, fewer decisive model errors, bounded compute |
| 6. Plan selection and robustness | Small strategy portfolio and observable-style adaptation | Can opponents force us into a bad matchup? | No collapse against exploiters, stable results beyond our lineage |
| 7. Release assessment | Frozen candidate, required gate, honest holdout, post-release monitoring plan | Is this a substantial competitive improvement? | Evidence meets agreed goals; only then consider submission |

If phases 1–2 show that the opening economy is already near its realistic ceiling, reprioritize objective conversion or tactical correctness. Do not continue a favorite architecture after its causal explanation fails.

## 10. What we should deliberately avoid

- Another round-number, carry-threshold or opening-pick change presented as a strategic redesign.
- Optimizing basic-attack count, low deaths or gold concentration as ends in themselves.
- Copying a top lineup without its routes, reward allocation, item choices and objective behavior.
- Treating a predictive model's accuracy as proof that its decisions improve this controller.
- A full rewrite of every proven action primitive before a small strategic prototype demonstrates value.
- Large generic neural training without a validated environment, reward, observation contract and diverse opponents.
- More search whose model omits the mechanics causing our losses.
- Repeated holdout tuning or a tiny local gain marketed as evidence of top-25 strength.

## 11. Lessons from related games

These sources inform the design hypotheses; they do not establish that a tactic will work in CAMBC.

- **OpenAI Five:** coordinated long-horizon objective decisions can matter even when a local mechanical skill is imperfect; team-level incentives help align agents. The transferable idea is shared strategic value, not copying its enormous training system. [OpenAI Five](https://openai.com/index/openai-five/).
- **AlphaStar:** a portfolio of previous opponents and dedicated exploiters helps expose strategy cycles and blind spots. The practical analogue is a diverse evaluation league rather than exclusively testing against our previous version. [AlphaStar league](https://deepmind.google/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/).
- **Battlecode 2025, confused:** resource conversion and a clear economic philosophy produced a large improvement, while idle time and expansion were treated as strategic problems. Our analogue is converting gold, champion-time and altar access into secure score. [Postmortem](https://battlecode.org/assets/files/postmortem-2025-confused.pdf).
- **Battlecode 2025, Om Nom:** useful unit lives and avoiding computation overruns were important, but these served the game's resource priorities. Our runtime should reliably execute the chosen economy/objective plan. [Postmortem](https://battlecode.org/assets/files/postmortem-2025-om-nom.pdf).

## 12. Audit trail

Primary local references: the user-supplied `game rules/GameRules.md` and `BotAPICpp.md`; `docs/handoff.md`; v53 `bot.cpp`, `world.cpp`, `tsearch.cpp`, `draft.cpp`, `strategy.h` and `runtime_budget.h`; the saved platform snapshots and pinned replay decoder.

Key data files: `data/ladder/v53_since_live_analysis_20261025.json`, `v54_analysis_ladder_20261025.json`, `v54_control_wins_20261025.json`, `v54_diverse_top_wins_20261025.json`; `research/v54/V54_EVIDENCE.json`; and the earlier `V53_LOSS_REPORT.md`, `V53_PLAN.md`, `V53_DRAFT_REPORT.json` and release measurements.

Camp-type labels in the earlier loss report were corrected against the SDK enum: wolf, elk, gem cluster, gold cluster, monolith, golem. The numeric replay measurements were unchanged. The top boss reference's first-basic-attack wording was also corrected: its two monolith tiles were first targeted at R284 and R518, not one objective start at R518.

v53 submission was observed in the CLI log at **2026-10-25 13:08:26 UTC**, platform version 53. The experimental `bots/v54` source directory was removed. Earlier rejected benchmark artifacts remain under `artifacts/evaluations` for audit; they are not a release candidate. No future build/submission automation has been created. Further implementation requires a new user instruction; `V54_CLAUDE_PROMPT.md` is supplied for the user to invoke later.
