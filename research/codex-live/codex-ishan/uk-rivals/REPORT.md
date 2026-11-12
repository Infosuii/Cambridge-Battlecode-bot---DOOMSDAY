# Direct UK rival replay analysis

The official ladder read identified QS2isLaw, 0xDEADBEEF and bentheboss above DOOMSDAY. The [frozen sample](SAMPLE.json) contains 30 completed direct games, each using engine 2.0.0. The 48-hour ranked captures had 21 losses and four wins against 0xDEADBEEF and 23 losses and 17 wins against bentheboss. For each of those two teams the review takes six recent losses and four wins, with at most two per result from a group and exact draft/map/side deduplication. It uses all ten archived v92 Plan C games against QS2isLaw because no direct ranked QS2isLaw game was in the captured census. These are cases and controls, without a causal estimate or a current live head-to-head test. The ranked rows do not identify exact submissions.

| Rival | DOOMSDAY cases | Rival ahead in inferred camp gold through R300, losses / wins | Median camp-gold gap, losses / wins | Rival ahead in total earned gold at R300, losses / wins |
|---|---:|---:|---:|---:|
| QS2isLaw | 7 losses, 3 wins | 4/7, 1/3 | +271, −21 | 6/7, 1/3 |
| 0xDEADBEEF | 6 losses, 4 wins | 4/6, 1/4 | +56.5, −121.5 | 4/6, 1/4 |
| bentheboss | 6 losses, 4 wins | 5/6, 1/4 | +377, −36 | 4/6, 3/4 |

Positive gaps favor the rival. Camp gold is inferred from completed captures and health snapshots with the existing attribution limits. In these samples, opponent camp gold separated losses from wins more consistently than total gold or grouping. QS2isLaw banked more by R150 in six of seven losses, against one of three wins. bentheboss had more early deaths in all six DOOMSDAY losses. Thus the opening deficit against bentheboss persisted even in games where it lost more champions early. Each rival drafted Vesper in every sampled match, including every DOOMSDAY win. That recurring draft difference gives no within-rival contrast to establish that taking Vesper ourselves would fix the losses.

## Own-view turning points

| Rival and replay | Observation |
|---|---|
| QS2isLaw, 7c64f1a2-96c7-4807-a2e2-2722e17c436c, Treasure Box R50 | Rival gold lead held from R50 and reached 1,589 at R300. Our Vendetta saw four enemies and zero camps at the R50 input and recorded no move or basic attack. Rival Vendetta saw two enemies and also had zero visible camps at that input. This turn shows contact and an inactive unit, rather than a camp choice visible to the actor. |
| 0xDEADBEEF, 7e5f5fb3-d2df-429e-a4d8-4d9b98157a88, Geodes R150 | Rival led by 174 earned gold, growing to 523 at R300. Our Vendetta carried 56 gems, saw zero enemies and zero camps, and moved. Opponent Vendetta carried 11, saw two camps and no enemies, and attacked. This is a direct economy-versus-conversion contrast. Earlier banking is a plausible explanation for the move, with the private decision unavailable. |
| bentheboss, 01a1a765-6f00-7b0e-93ae-033f5989ca45, Ambush Field R50 | Rival gold lead held from R50, reached 273 at R150 and 1,146 at R300. Our Vendetta held 22 gems and saw zero camps. Rival Vendetta held 18 and saw 11 camps. Neither saw an enemy or recorded a move or basic attack on the sampled input. Visibility and earlier route divergence are measurable here. The exact prior choice is unresolved. |

The six [own-view traces](turns) show the engine observations and recorded actions for the same champion on both sides. They do not reconstruct either bot's historical private memory. The local hypothesis is that routes should choose more camp rewards realizable inside the opening window. Compare exact release binaries in dev and respect the original safety gate. The rival identities and maps are used only to analyze replays. The policy receives neither. [Per-game profiles](PROFILE.json), [EXP-030 protocol](../EXP-030-RELEASE-PLAN.md).
