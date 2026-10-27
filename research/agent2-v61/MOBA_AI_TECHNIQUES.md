# Stack stats, move in packs, measure honestly

The techniques most likely to lift CAMBC a lot are not deeper search or neural networks. They are the boring, proven parts of MOBA and competition-bot practice. The first is a scripted power-curve build: OpenAI Five reached superhuman play with fixed item orders. The second is pack movement with retreat toward allies: Battlecode's XSquare-style micro and Lanchester-gated engagement. The third is explicit objective timing and altar control: Tencent HMS's macro layer was worth 75–25 head-to-head. All three need an evaluation setup that can see the ladder's real opponents. The project's own data shows where the losses come from. In 11 platform losses we bought **0 stat shards in 8 games against their 56–402**, died **184 times against 49**, often alone while fleeing, and never placed an altar lock. A small income edge (+0.25 gold per turn) turns a 50% matchup into about 18%. Making the C++ faster would matter little: turns already leave 40–75k of the 100k fuel unused, and more search budget, up to 10x, was neutral or harmful. The plan therefore has to serve two audiences that pull in opposite directions. Against v61 and bot 5, which share our economy-first build and spacing, the measurable gains come from exploiter-style knob tuning, farming speed and the draft. On the ladder, the gains come from stats, grouping and locks, and those changes have tested neutral-to-negative against our own bot family. Every change should therefore pass two gates: no regression against the reference bots, and a real gain against stat-stacking, grouped opponents. Expected total: roughly +3–8 points against the reference bots and a substantially larger, but still unmeasured, gain on the ladder.

## The ladder gap is power and spacing, not decision depth

The causal chain behind the platform losses is now well documented. Our economy-first build buys no stat growth. Fights are even until about round 200–300, after which the opponent out-damages us **2–17x**. By round 200 their Vesper had 130 strength and 2,100 HP against our 45 and 1,000. By the end, their Vesper carried 19–26 Bruiser emblems and 580–760 strength ([MATCH_ANALYSIS_E63 §1](../agent2/MATCH_ANALYSIS_E63.md); [EXPERIMENTS E65](../agent2/EXPERIMENTS.md)). Our deaths ranged from 5 to 41 per game (median 10) against their 0–9 (median 2). Up to 22 of 41 deaths in one game came with no ally within 4 tiles. Mean distance to the nearest living ally was **5.0–11.5 tiles for us versus 3.2–7.9 for them** ([MATCH_ANALYSIS_E63 §2](../agent2/MATCH_ANALYSIS_E63.md)).

The death pattern is specific. Flee mode is the last mode before 75% of deaths. The flight starts at a median 30% health, with one enemy near and no ally, 24 tiles from home, and death follows a median 5 turns later ([EXPERIMENTS E65](../agent2/EXPERIMENTS.md)). Top teams recall at 63–67% health against our 47% ([FINDINGS_2026-10-18 §4](../FINDINGS_2026-10-18.md)). Carriers carried up to 270 gems into death per game, and on road-of-riches every carrier died before banking. The opponent held locks on our altars for 37–90% of rounds; we held locks for 0 rounds in all 11 games ([MATCH_ANALYSIS_E63 §3–4](../agent2/MATCH_ANALYSIS_E63.md)). Across 87 ladder games, the team with fewer deaths won 86% and the team with more gems by round 200 won 83% ([FINDINGS_2026-10-18 §4](../FINDINGS_2026-10-18.md)).

The per-turn fight decision is not where these games are lost. Where the engine prefers a side at all (12% of states), the simulator verdict agrees with it 95.5% of the time, at a regret of about 0.01 value per state. Replacing the fight search with rules alone (APEX_TS_DECIDE=0) moved the score by 48.7% ± 4.1 against the combo, "nothing measurable" ([EXPERIMENTS E24, E39](../agent2/EXPERIMENTS.md)). Top teams' per-turn fight choices match ours: a network predicts both at 47.9% accuracy, and the remaining gap is positioning ([replay-learning memory](file:///C:/Users/Iniya/.claude/projects/C--Users-Iniya-Videos-Default-Project-2/memory/cambc-replay-learning.md)). This matches the MOBA literature. Tencent HMS matched or beat humans on macro but made about 15% fewer kills, and OpenAI Five's losses came from opponents who refused fair fights and split-pushed, not from lost micro duels ([HMS](https://arxiv.org/abs/1812.07887); [ONE Esports](https://www.oneesports.gg/dota2/openais-bots-trounced-humans-7215-to-42-in-dota-2/)).

### Why the lab cannot see the problem, and why that splits the plan

v61 and bot 5 play almost identically to our bot, so they share its weaknesses. Against our own family, the Prospector-first economy build beat v57 67/100 in the real engine, while every power-curve build (V59_ITEMS 1/3/4/5) tested neutral or negative ([EXPERIMENTS E52, E64, E67](../agent2/EXPERIMENTS.md)). Escape retreat combined with squad farming cut deaths 27% (382 to 279) but won no more lab games. A cohesion penalty cut deaths 19% and lost 4 points, 11–16 of them on race maps ([EXPERIMENTS E66](../agent2/EXPERIMENTS.md); [IMPROVEMENT_PLAN_v34](../IMPROVEMENT_PLAN_v34.md)). The team's own verdict is that the bot "is at a local optimum for its design" and that the bench "cannot show gains against platform-style opponents" ([EXPERIMENTS E67–E68](../agent2/EXPERIMENTS.md)).

This is the overfitting that PSRO's joint-policy-correlation metric was built to expose: independent learners overfit to their training partners ([Lanctot et al. 2017](https://arxiv.org/abs/1711.00832)). It also matches the clearest datum in the competition literature. RAISocketAI beat benchmark bots 91% after self-play but beat the previous champion only 20% of the time, until it was fine-tuned against that champion, which took it to about 90% ([Goodfriend 2024](https://arxiv.org/pdf/2402.08112v1)).

The consequence is that **beating v61 and bot 5 and doing well on the ladder are different optimisation problems**. Some changes help one and hurt the other, and the plan below keeps them apart.

## Eight transferable techniques, ranked by expected impact

The table ranks techniques by expected impact on the user's combined goal. Expected gains are my judgement from the cited effect sizes, not measured CAMBC numbers. "Refs" means v61 and bot 5.

| Rank | Technique (source system) | Key outside evidence | Expected vs refs | Expected on ladder | Cost |
|---|---|---|---|---|---|
| 1 | Ladder-like opponent pool with honest statistics: archetype bots, exploiters, CRN, SPRT, held-out maps (AlphaStar league, PSRO, fishtest) | Self-play champion beat the prior winner only 20% until fine-tuned against it | Enabler; stops phantom gains | Enabler; the only way to see ladder gains locally | Medium |
| 2 | Scripted power-curve build: 2–3 economy emblems, then Bruiser/Power stat stacks (OpenAI Five scripted items; Battlecode "copy the top teams") | Superhuman Dota with fixed build orders; macro copied from higher-ranked teams | −3 to 0 pts (risk) | Largest: +5 to +15 pts | Low |
| 3 | Pack movement plus XSquare-style per-tile scorer with retreat toward allies and Lanchester-gated engagement (Battlecode) | Micro "30–50%" vs macro "5%"; copying XSquare took a team from about 1850 to above 2000 rating | −2 to +2 pts | +3 to +8 pts | Medium |
| 4 | Altar lock war and small-bag banking with escorts (OpenAI Five's undefended-objective losses; HMS objective timing) | Arena losses came from undefended Ancient and split-push | about 0 | +2 to +5 pts, concentrated on altar maps | Low–medium |
| 5 | Exploiter knob tuning aimed at v61/bot 5: ≤20 knobs, SPSA/CMA-ES with re-evaluation and racing (AlphaStar exploiters, UH-CMA-ES, Texel) | Exploiters "expose the main agent's flaws" | +2 to +6 pts | 0 (risk of harm) | Medium |
| 6 | Phase-conditioned destination table plus analytic "imitated communication" (HMS, JueWu-SL, OpenAI Five replicas) | No-macro lost 75–25; ally-intent features 62.5–37.5 | +0 to +3 pts | +1 to +4 pts | Medium–high |
| 7 | Draft: precomputed lineup-value table plus exact minimax on the 10M-fuel draft turn (OpenAI Five drafter, JueWu MCTS) | MCTS drafter 0.68 vs greedy, in predicted win rate | +0 to +3 pts | +0 to +4 pts, if refit to the ladder meta | Low–medium |
| 8 | Counterfactual-rollout value labels distilled into a small tree or int8 MLP (VIPER, finite-horizon MC, NNUE) | 3- to 769-node trees matched DNN teachers | +0 to +2 pts | +0 to +3 pts; mainly diagnostic | High |

Not worth doing: end-to-end deep RL or league training of a neural policy, which needs 3–6 orders of magnitude more compute; MCTS over neural draft nets, since exact search fits; and deeper fight search on the current simulator.

### Fix the yardstick before moving anything (rank 1)

The team's ES runs gained 5 to 29 points in training and about 0 on fresh seeds. The winner's curse explains most of that. The expected maximum of 100 noisy candidates is about 2.5 standard errors. At n=200 games (SE ≈ 3.5 points), picking the best of 100 shows **about +8.8 points from noise alone**. An ES run that keeps the best-ever candidate over thousands of evaluations inflates further. This is the "optimizer's curse" ([Smith & Winkler 2006](https://scholars.duke.edu/publication/798952)).

The remedies are cheap at 0.3 s per game:
- Common random numbers: every candidate plays the same (map, seed, opponent) tuples with mirrored sides, and the tuples are resampled each generation.
- Racing: a ~100-game screen, then promote the top 10–20% to 1,000+ games.
- A final SPRT on maps and seeds never used in tuning. Fishtest uses [0, +3]-style gainer bounds and [−3, +1]-style non-regression bounds and caps retries at four or five ([CPW SPRT](https://www.chessprogramming.org/Sequential_Probability_Ratio_Test); [Fishtest FAQ](https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-FAQ.html)).

A fixed-sample head-to-head test needs about **4,900 games to detect +2 points, 780 for +5 and 200 for +10**. That is about 25 single-core minutes for the +2 case. Comparing two bots separately against a pool needs twice as many.

The harder part is the opponents. The team's earlier stand-ins failed. spar_top copied top teams' opening, gold and spacing but correlated with the ladder at only r = +0.10 / −0.15. op1 copied their build and draft but lost to our bot 41.4%. A sandbox gold handicap made opponents richer without making them play like the ladder ([sparring-pool memory](file:///C:/Users/Iniya/.claude/projects/C--Users-Iniya-Videos-Default-Project-2/memory/cambc-sparring-pool.md); [EXPERIMENTS E65, E67](../agent2/EXPERIMENTS.md)).

The AlphaStar lesson is that useful sparring partners are not copies of the field but **exploiters**: agents whose only job is to find the main agent's holes ([DeepMind](https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/)). For CAMBC that means hand-scripted archetypes that behave unlike us on purpose:
- a "pack hunter" that moves as a trio and attacks any of our champions with no ally within 6 tiles;
- a "stat stacker" that buys 2 economy emblems and then only Bruiser/Power;
- a "lock warden" that keeps a lock in stock and locks our altar whenever a carrier approaches.

Each archetype is valid only if it reproduces the platform signature against our current bot: deaths several times ours, many of them alone, a power gap by round 200, and long enemy lock times. That validation can use per-game mechanism metrics, which reach significance in tens of games rather than thousands.

### Buy stats like the winners do (rank 2)

The literature is unusually unanimous here. OpenAI Five scripted ability builds, item purchase order, consumables and the courier, and "achieved superhuman performance before" un-scripting any of them. Its learned buyback started worse than the scripted version ([OpenAI Five paper](https://arxiv.org/abs/1912.06680)). Battlecode winners improved macro by "scrimmaging against good teams, and copying what they do" ([GST 2026](https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf)), and a switch to fully aggressive micro alone gained one team 130 rating points ([Cout for Clout 2024](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf)).

The ladder winners' build is known. They take 2–3 economy emblems, then main-stat Bruiser/Power stacks with health every 2–3 purchases, and casters focus a single stat ([MATCH_ANALYSIS_E63](../agent2/MATCH_ANALYSIS_E63.md)). Every emblem type is worth roughly the same 16–28 banked gems, and converting gold into emblems is what counts ([FINDINGS_2026-10-18 §11](../FINDINGS_2026-10-18.md)).

This is the single largest ladder lever, because stats feed every other link in the chain: faster camp kills, won fights, fewer deaths and safer banking. Against the reference bots it is a risk, since power-curve builds tested neutral or negative there ([EXPERIMENTS E64, E67](../agent2/EXPERIMENTS.md)). Two ways to manage that risk:
- Accept it only under a non-regression SPRT against the reference bots.
- Make the switch point adaptive. Stay economy-first while the visible enemy stat totals stay low, and switch to stats once they rise. Whether enemy stats are observable in-game on cambc 4.0.0 is not documented in the notes and must be checked.

### Never be the lone champion (rank 3)

Battlecode's highest-leverage, cheapest technique is the XSquare micro: score all candidate move tiles on a handful of features (enemies that can hit the tile, distance to allies, HP of allies and enemies) and compare them with a fixed priority order. "Nearly every other top team has benefited from copying" it ([The Kragle 2025](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf)).

Its retreat rules address our exact failure:
- Move toward allies rather than just away from enemies.
- "Move backwards if the ally behind you has more health than you."
- A health threshold scaled by level (`450 + (lvl−3)·150`) triggers retreat.
- Chase only with a 2+ unit advantage. Two teams cited Lanchester's square law, and a 47-vs-50 test lost 90% ([Cout for Clout 2024](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf); [Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)).
- After each fight, regroup on the healthiest ally nearest the objective, with the low-HP unit behind ([Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)).
- A shared "nearest battlefront" location gave "massive improvements" ([The Kragle 2025](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf)).

The project's own history adds a constraint. A death-risk model that predicts deaths well (ladder AUC .945) was neutral or harmful as a flee trigger, and leaving fights early costs about as much as dying ([death-model memory](file:///C:/Users/Iniya/.claude/projects/C--Users-Iniya-Videos-Default-Project-2/memory/cambc-death-model.md); [EXPERIMENTS E38](../agent2/EXPERIMENTS.md)). So the fix is not "flee sooner". It has three parts:
- Do not be alone in the first place. Add a cohesion term while farming in contested space, not a camp penalty that wrecks race maps.
- Retreat *toward allies* through the same tile scorer, never on a straight path home.
- Gate engagement on local power, summed stats and HP, rather than on health alone. Fight decisions currently use health rather than a power comparison ([MATCH_ANALYSIS_E63](../agent2/MATCH_ANALYSIS_E63.md)).

OpenAI Five's quartic HP value, x + 1 − (1−x)⁴/2, gives a ready-made smooth risk curve to use inside that score instead of a hard threshold ([OpenAI Five paper](https://arxiv.org/abs/1912.06680)).

### Contest altars, not just camps (rank 4)

Gems count only once tributed. A stun, a death or a lock breaks the channel, and a lock costs 10 gold and needs 5 hits ([GameRules](../v3/GameRules.md)). The opponents exploited this all game while our pre-lock and deny code never fired, and the existing A2_LOCKAWARE switch almost never triggers in the lab (48.0 vs 49.1), because our own bots never lock ([EXPERIMENTS E61](../agent2/EXPERIMENTS.md)). This is OpenAI Five's blind spot in CAMBC form: the bots "never try to deny towers" and failed to "protect its Ancient" against opponents who avoided fair fights ([Vice](https://vice.com/en/article/we-will-win-openais-dota-2-team-is-crushing-humans-online-but-players-are-not-giving-up); [ONE Esports](https://www.oneesports.gg/dota2/openais-bots-trounced-humans-7215-to-42-in-dota-2/)).

The behaviour to add:
- Keep a lock in stock.
- Lock the altar an enemy is channelling at.
- Clear locks on our altar as a group.
- Read enemy locks before walking a carrier in.
- Bank small bags early. Top teams make their first bank around round 56 against our 99 ([FINDINGS_2026-10-18 §4](../FINDINGS_2026-10-18.md)).

Against the reference bots this does almost nothing, because they do not lock either. It can only be measured against the lock-warden archetype and on the platform.

### Beat the mirror with exploiters and income (ranks 5–7)

Against bots that share our design, history says gains come from knobs and economy, not new behaviour. v61 itself came from a black-box knob search: the middle-camp weight moved from 0 to 0.63, and v61 beat t58 57% over 200 real-engine games ([EXPERIMENTS E54](../agent2/EXPERIMENTS.md)). The Prospector build beat v57 67/100 ([EXPERIMENTS E52](../agent2/EXPERIMENTS.md)).

Because the target here is a fixed opponent, overfitting *to that opponent* is the goal, as for an AlphaStar exploiter. Overfitting to maps and seeds is still the enemy. Run SPSA or UH-CMA-ES on 10–20 knobs with fitness equal to win rate against v61 and bot 5 only. Use CRN, re-evaluate the top candidates to measure rank stability ([UH-CMA-ES summary](https://arxiv.org/html/2409.16757v3)), and accept only after a held-out SPRT. Where knobs feed a value-like score, Texel-style regression on logged states fits them without new noisy games per candidate ([CPW Texel](https://www.chessprogramming.org/Texel%27s_Tuning_Method)).

Income edges are worth chasing against mirrors because the mirror amplifies them: +0.25 gold per turn moved a 50% matchup to about 18% ([EXPERIMENTS E65](../agent2/EXPERIMENTS.md)). The ceiling is far away. v34 harvested 21% of the maps' gem regrowth, spent 48–49% of turns travelling, and re-took wolf packs every 70–85 rounds against top teams' 52–58 ([FINDINGS_2026-10-18](../FINDINGS_2026-10-18.md)). A farm-speed knob search came back as noise ([EXPERIMENTS E68](../agent2/EXPERIMENTS.md)), though. The remaining lever is structural, not a knob: respawn-timed pre-positioning, HMS's "be at Baron when it spawns" effect, which was worth 65–35 ([HMS](https://arxiv.org/abs/1812.07887)), and melee-tanks-for-ranged pairing. Top teams' ranged champions take 0.16 camp damage per damage dealt against our 0.33 ([FINDINGS_2026-10-18 §11](../FINDINGS_2026-10-18.md)).

The HMS/JueWu-SL destination idea fits this budget in a simple form: label each logged state with the region of that champion's next scoring event, and fit a phase-conditioned lookup table. The JueWu-SL ablation without macro intent fell to 31% against the full model ([JueWu-SL](https://arxiv.org/abs/2011.12582)). The project's own evidence tempers the expected gain. Local macro choices tested flat (+0.1 ± 0.3 gems per decision), and those ablations were measured on top of a learned micro layer with no other macro ([EXPERIMENTS E27, E44](../agent2/EXPERIMENTS.md)).

HMS's "imitated communication" transfers fully as an analytic trick. Each champion runs the same deterministic assignment function for every visible ally, so the joint plan emerges without messages, and the 8 shared bytes are kept for facts allies cannot recompute ([HMS](https://arxiv.org/abs/1812.07887); [OpenAI Five paper](https://arxiv.org/abs/1912.06680)). It degrades wherever allies' vision differs, and a duplicate-suppression rule already lost 1.6 points in the pool ([team-assignment memory](file:///C:/Users/Iniya/.claude/projects/C--Users-Iniya-Videos-Default-Project-2/memory/cambc-team-assignment.md)). Use it to pair champions, not to spread them out.

For the draft, OpenAI Five precomputed win probabilities for all 4.9M lineups and ran minimax ([OpenAI Five paper](https://arxiv.org/abs/1912.06680)). JueWu's MCTS drafter scored 0.68 against greedy highest-win-rate picking, but that figure is the predictor's own estimate ([JueWu](https://arxiv.org/abs/2011.12692)). Our draft net is already worth about +8 points in the lab, and counters are noise once per-size values are fitted ([EXPERIMENTS E48](../agent2/EXPERIMENTS.md); [draft-fit memory](file:///C:/Users/Iniya/.claude/projects/C--Users-Iniya-Videos-Default-Project-2/memory/cambc-draft-fit.md)). Exact minimax over an additive per-size table fits easily in 10M fuel, so the remaining question is which meta to fit. Ladder opponents always take Vesper and Heart, while V60_VESPER_FIRST tested 53.0 / 48.2 / 16.4-vs-20.0 in the lab ([EXPERIMENTS E64–E65](../agent2/EXPERIMENTS.md)).

## Faster C++ buys fuel nobody is short of

The code can be made noticeably more efficient. Each SDK bitboard temporary is a host call plus an aligned heap allocation, and p64 declares 63 local bitboards in bot.cpp and 30 in world.cpp. Distance fields cost 3k–33k fuel each and are rebuilt per champion, because only 4 bytes per group cross the draft-memory boundary. Fight-simulator playouts scale at about 0.7–1k × units². Around 62 try blocks guard SDK calls that throw outside the map. The build links with `--no-wasm-opt` and sets no explicit -O level ([common.h, world.h, tsearch.cpp, CMakeLists](../v4/bots/p64/src/common.h); [cambc.h](../v4/sdk/cpp/cambc.h)). In order of fuel saved, the fixes are:
- a cheaper playout, using per-turn threat tables and early termination;
- a compressed group-to-group and group-to-altar distance table in the 1,024 draft bytes;
- reusable scratch bitboards held in World;
- throw-free bounds checks in loops;
- a newer Binaryen to re-enable wasm-opt.

It would not matter much, for four measured reasons:
- Later turns use 23–59k of 100k on average, and only 3 turns in about 43,000 reached 99k ([MATCH_ANALYSIS_E63 §6](../agent2/MATCH_ANALYSIS_E63.md)).
- Cutting fuel-exhaustion events by 80–98% was strength-neutral (−0.9 ± 1.1 points). Raising the fight budget from 70k to 85k was neutral. Search at 10x fuel won 32/100 because "more search exploits the simulator's errors" ([EXPERIMENTS E8, E28, E64](../agent2/EXPERIMENTS.md)).
- A lab whose fuel is effectively unlimited reproduced the real engine's aggregate win rate (57/100 vs 56/100) ([EXPERIMENTS E56](../agent2/EXPERIMENTS.md)).
- The simulator already reproduces 95.2% of recorded turns exactly. Its limit is behaviour modelling, with 0.42 move-ranking agreement against a 0.90 ceiling ([EXPERIMENTS E33, E35](../agent2/EXPERIMENTS.md)).

This matches the Ants 2011 lesson: the author of a minimax combat module "spent too much time writing the combat code for the benefit" ([LessWrong](https://www.greaterwrong.com/posts/ELCsD7MYaqnkarPBi/ai-challenge-ants-post-mortem)).

Expect **0–2 points** from optimisation alone.

Efficiency becomes worth doing only as an enabler. The fight search gives verdicts in 0–3% of 6+ unit scenes, because a 6-unit comparison needs 79,200 fuel against the 70,000 cap ([FINDINGS.md §4](../agent2/FINDINGS.md); [IMPROVEMENT_PLAN_v34](../IMPROVEMENT_PLAN_v34.md)). Those are exactly the grouped team fights the ladder punishes us in. Widening the snapshot from 3 to 4 units did cut deaths by 0.73 per game ([EXPERIMENTS E12–E13](../agent2/EXPERIMENTS.md)). A cheaper playout that admits 5–8 units, or room for a learned power or value evaluator near enemies every turn, is therefore a reasonable second-wave project, tested against the pack-hunter archetype.

One hazard: fuel-dependent cut-offs once moved strength by ±20–40 Elo, about ±3–6 points, which is why APEX_DET exists. Any optimisation must replay identical games at setting 0 before its strength is measured ([common.h ~L1993](../v4/bots/p64/src/common.h)).

## Near-perfect play is a power-curve pack that banks small and locks often

Assembled from the rules and the winners' observed behaviour, near-perfect CAMBC play has six parts:

**Draft.** Draft for income and team-fight power on the map. The ladder winners always take Vesper's +33% gold and Heart.

**Opening.** Use the 10M-fuel draft turn to plan walking-distance routes. Make first captures by about round 25, against our 41 ([FINDINGS_2026-10-18](../FINDINGS_2026-10-18.md)), with a melee champion tanking each camp for a ranged partner. Buy only one or two economy emblems.

**Mid game.** Turn gold into main-stat stacks so the team is at least as strong as the enemy at every contact from round 200. Move in pairs or trios within about 4–6 tiles; top teams keep about 35% more teammates within 4 tiles in fights. Wards cover approach routes ([replay-learning memory](file:///C:/Users/Iniya/.claude/projects/C--Users-Iniya-Videos-Default-Project-2/memory/cambc-replay-learning.md)). Be at each camp when it respawns.

**Fights.** Engage only with local superiority in numbers *and* power. Focus the shortest time-to-kill target; JueWu-SL found raw replay data biased attacks toward tanky targets ([JueWu-SL](https://arxiv.org/abs/2011.12582)). Stun channelers. Leave while the walk home is still survivable, and always leave toward allies.

**Banking.** Bank small bags often at the nearest safe altar, and escort carriers on contested routes. Death costs about 91 team gems with an empty bag and 177 carrying 40+ ([EXPERIMENTS E26](../agent2/EXPERIMENTS.md)). Lock the altar the enemy is channelling at, and clear locks on ours as a group.

**Endgame.** Project both teams' finish. When ahead, play safe and deny. When behind, contest altars and carriers. Near round 2,000, farm lifetime gold for the tiebreak ([GameRules](../v3/GameRules.md)).

Our bot already does the farming machinery, the draft and per-turn micro well. It does not buy stats, does not farm or retreat as a group, does not fight the lock war, and drafts away from the ladder meta.

The structural obstacle is the architecture. Every champion runs its own program with 8 shared bytes, all of them currently used by claims, and no shared vision. Coordination therefore has to come from identical deterministic rules over shared observations, which is how OpenAI Five coordinated at test time ([OpenAI Five paper](https://arxiv.org/abs/1912.06680)). It can also come from reassigning 2–3 bytes to a rally point plus a time-to-live, the Battlecode battlefront pattern ([Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)).

None of the near-perfect package has been shown to win as a whole. Each element was either observed in opponents' replays or tested only against our own family, where it was neutral.

## An ordered plan with two gates per change

Every candidate passes two gates. **Gate R** is a non-regression SPRT against v61 and bot 5: bounds [−3, +1] points, α = β = 0.05, mirrored sides, CRN, on maps and seeds not used in development. **Gate L** is a gainer SPRT [0, +5] against the validated archetype pool, followed by platform match groups. Score platform groups first on mechanism metrics, then on wins, because ladder version steps of ±12–23 Elo are too noisy to rank by result alone ([sparring-pool memory](file:///C:/Users/Iniya/.claude/projects/C--Users-Iniya-Videos-Default-Project-2/memory/cambc-sparring-pool.md)). Mechanism metrics move with huge effect sizes and need few games: deaths per game (us 184 vs them 49 over 11 games), deaths with no ally within 4–6 tiles, stat shards at round 200, our and their lock-rounds, and gems carried into death.

Changes aimed only at the reference bots (step 6) skip Gate L but must not worsen the mechanism metrics.

| Step | Action | Helps | Expected gain | How to measure |
|---|---|---|---|---|
| 1 | Evaluation harness: CRN tuples resampled per generation, held-out map/seed set, SPRT runner, mechanism-metric extractor from event logs | Both (enabler) | Ends phantom +5–29 gains | Re-run the last accepted change: its gain should shrink to the held-out value |
| 2 | Build and validate three archetypes (pack hunter, stat stacker, lock warden), plus an ES exploiter tuned only to beat v61 | Ladder (enabler) | Makes ladder gains visible locally | Each must reproduce platform signatures against v61 over about 50 games: deaths ≥2x ours, ≥40% alone, power gap by round 200 |
| 3 | Power-curve build: 2–3 economy emblems, then Bruiser/Power stacks, optionally switched on visible enemy stats; submit the packaged p64/p63sq candidates to the platform in parallel | Ladder | +5 to +15 pts ladder; −3 to 0 refs | Gate R, then Gate L; stat shards at round 200 ≥ opponent's |
| 4 | Ally-aware tile scorer: retreat toward allies, power-gated engagement, quartic HP term, cohesion in contested space, 2–3 shared bytes for a rally point | Ladder | +3 to +8 pts ladder; −2 to +2 refs | Gate R, Gate L; alone-deaths and flee-deaths should fall ≥30% against the pack hunter |
| 5 | Lock war: lock in stock, lock enemy channels, read and clear locks, small-bag banking with escort | Ladder | +2 to +5 pts on altar maps | Gate L on contest/anvil/road-of-riches; enemy lock-rounds on our altars and gems carried into death |
| 6 | Exploiter tuning against v61/bot 5: SPSA on ≤20 knobs including the respawn-timing and pairing terms; Texel regression where knobs feed a score | Refs | +2 to +6 pts refs | Racing, then held-out SPRT [0, +3] against refs; mechanism metrics must not worsen |
| 7 | Draft: per-size additive lineup table fitted on both lab and ladder-meta games; exact minimax on the draft turn | Both | +0 to +3 refs, +0 to +4 ladder | Gate R; then platform groups, since the lab table cannot see the ladder meta |
| 8 | Second wave: cheaper playout admitting 5–8 units; counterfactual CRN rollouts (fight vs retreat) to train a power/value model, distilled to a depth-6–10 tree or 16–32-unit int8 MLP | Ladder mainly | +0 to +3 pts | Parity replay at setting 0 first; Gate L against the pack hunter |

The ordering follows two rules: build the yardstick first, then go after the largest ladder levers that tests can resolve in a few hundred games. Steps 3–5 can be packaged as separate switches and run in parallel once steps 1–2 exist. Step 6 is the only step that targets the reference bots directly. It is the most dependable route to the "beat v61 and bot 5" goal, because it is the same method that produced v61.

Use the counterfactual-rollout design in step 8 even if its model never ships. Branch "fight" and "retreat" from the same state on paired seeds. That separates "this decision does not matter" from "the labels were confounded". The earlier learner trained on 4,200 observational situations could not tell those two apart, and at a 0.05 effect size it needed about 1,600 samples per arm even without features (derived from n ≈ 2·(2.8·0.5/Δ)²). Finite-horizon Monte Carlo targets are adequate for this ([Amiranashvili et al. 2018](https://arxiv.org/abs/1806.01175)).

Several things remain unknown and could change the ranking:
- the exact emblem passives on 4.0.0;
- whether enemy stats are visible in-game;
- whether a scripted archetype can reproduce the platform opponents' low death rate, when two earlier attempts could not;
- whether "bot 5" differs from v61 in any way the exploiter could use; the research notes do not describe it separately.

## Conclusion

The research changes the question from "how do we make the bot smarter?" to "how do we make our test opponents behave like the ladder?" Every MOBA and competition system that beat strong opponents measured itself against opponents unlike itself: prior champions, exploiters, scrimmages against higher-ranked teams. CAMBC's tuning loop has measured against mirrors. That is why a build that loses every platform fight looked best locally, and why death fixes that cut deaths by a quarter showed no wins.

Making the C++ faster, searching deeper or training networks attacks a bottleneck the project has already shown is not binding. Copying the ladder's power curve, keeping champions within reach of each other and contesting altars attack bottlenecks it has shown are binding. Expect the reference bots and the ladder to disagree about these changes. Treat that disagreement as information, not noise, and gate each change on both.
