# Champion meta: roles before rankings

The most defensible core is Vesper Vale, Marcella, Heart of Ruin and Vendetta. In 60 selected match sides their pick counts are 51,51,50 and 47. This establishes widespread elite use, not four independently estimated power advantages. The sample includes different team sizes, 17 teams, one match per map, unknown opponent submission changes and a developer team. See DRAFT_EVIDENCE.md for every denominator and composition.

## Evidence tiers

| Practical tier | Champions | Role, evidence and uncertainty |
|---|---|---|
| S: strongly established role candidates | Vesper, Marcella, Heart, Vendetta | Broad prevalence and several distinct winning controllers; medium confidence that the role is useful, low confidence in universal best-pick ordering. |
| A: flexible or specialised complements | Ryth 29, Willow 11, Tavi 9, Cassi & Issac 6, Varg 5 | Ryth offers health-scaled melee/control; Willow supplies healing; Tavi spends in the field; duo adds a body with linked-death risk; Varg supplies splash/attack reset. Conditional strength, not inferior in every context. |
| B: narrow or underidentified | Prism 3, Stellar 2, Ren 2 | Prism is central to the boss_battle access sequence; Stellar appears on both a win and a loss; Ren appears in Ad Astra's two wins. Too little independent coverage for intrinsic ranking. |

All 12 draft choices were investigated through current handbook specifications, SDK definitions and available replay appearances. The 13 physical champion definitions and 84 item definitions are indexed in MECHANICS.json. Cassi and Issac are separate bodies. No unsupported experience/level system is assumed: equipment adds champion-specific growth increments.

## Why the common core works as a candidate system

Vesper's33% gold passive makes capture credit valuable, but gold must become productive stats. Jungle-first Vesper works for Mite, Treasure-first appears elsewhere, and Prospector-first requires cluster income. Her ranged movement restriction makes attack-reset sequencing and route proximity important. She is not automatically the best recipient when moving her to collect a reward costs more than the bonus.

Marcella is both stun-immune and earns 2 gold per submitted gem. That creates a conversion-to-equipment feedback distinct from Vesper's capture economy. On eight, print dont int's Marcella banks 830 and earns 6774; on elkring, Supaswag's Marcella banks 797 and earns 6422. Those are strong observed scoring roles. However, her 808 collected/zero submitted on the losing boss_battle side shows that this passive produces nothing without altar access. Infer a scoring role only when the route can be completed.

Vendetta combines high base Strength, melee movement plus attacks, an attack reset and a dash. Her cooldown reset applies to camp monster kills as well as champion kills. Therefore small finishing targets can have value beyond their nominal reward. That interaction is a mechanics-backed reason to search target sequences; this study does not claim every observed reset was optimally planned.

Heart's missing-health damage, shield and area dash support sustained farming/control, with survivability needed to use the passive. Do not equate a low HP fraction with weakness without shield, nearby threats and expected damage. Mite's Jungle openings and several other teams' health/focus paths show different ways to support this role.

## Complements and counterconditions

Ryth converts bonus health into Strength and supplies area control/reset; Sponge's Ryth–Vendetta–Marcella defeats the popular trio on arena and fragment. Willow is a possible durability/tempo complement, but must keep an actual high-value ally alive to repay reduced independent farming. Tavi avoids many shopping trips; health bought away from spawn does not restore current HP. Cassi & Issac adds turns and simultaneous jobs, but either body dying kills both and both bags are lost. Physical deaths should not be counted as independent pick failures.

Varg supplies splash farming and mixed-stat resilience. On boss_battle he banks 544 while Prism banks zero. Prism gains 1.5 Focus per carried gem; a989-gem bag adds 1483.5 Focus before other bonuses. Banking it removes that power. Stellar supplies front-loaded single-target/area damage, while Ren retaliates and can threaten attackers even on his death. Both need context-specific tests; their low pick rates are not evidence of impossibility.

## Conditional composition candidates

For ordinary repeated farming, start testing Vesper/Heart/Vendetta with Marcella or Ryth according to slots and delivery geometry. This is a prior, not a hard-coded optimum. For constrained three-pick maps, directly compare it with Ryth/Vendetta/Marcella: mirrored drafts and alternative trios both occur, and controller quality dominates several outcomes.

For gate-controlled altars, assess a scalable damage specialist plus durable delivery bodies and, if useful, healing. Newer team's Vesper/Vendetta/Prism/Willow/Varg at boss_battle is one successful complete system. It should not be transferred as a universal five-pick lineup. For fragmented routes, mobility and remote shopping can matter more than another raw-damage body. For low-gold gem combat, immediate survivability and reliable capture/delivery can beat a long economy build.

Draft optimisation should enumerate legal own-unique sets, allow enemy mirror picks, and score the jobs that become possible. With 12 choices, there are 220 triples, 495 four-sets and 792 five-sets. Evaluate camp damage, survivability, cluster/monster composition, carrier routes, gate feasibility and revealed opposing picks; account for future uncertainty instead of reading an opponent's future draft. Use draft fuel for static geometry and cache the chosen plan in 1024 bytes. Fuel and rollout details are in META_TO_ALGORITHM.md.
