# v113 integration and champion stall repair

`sw08` fixes the confirmed camp-target loop and spawn-healing loop. It reduced quiet trailing stall rate by 49.5% from mx500 and by 17.4% from v114 in the sealed replay sample. It did not clear the full strength gate, so it was packaged for review and kept off the official ladder. v114 remained active at the last status check.

Latest user explicitly authorized uploading the strongest satisfactory bot to the ladder on 2026-11-08. That supersedes the root Battlecode AGENTS.md prohibition for this delivery. Do not turn on the old continuous controller; its STOP stays intact.

The reattached v206.zip is exactly the supplied archive already named v113.zip: SHA-256 93332ea2a4d972852bbfdf3341493897245381042984d6e845fe8fa4e1d407e5. No new source was present. Four starting versions and original binaries remain frozen.

The campaign started from DOOMSDAY v113. The next read confirmed that a teammate had activated **v114**, whose supplied source was frozen separately as `b114`. Recheck the active version immediately before delivery and preserve concurrent teammate selection. CLI and pinned local engine identities are in `starting-identities.json`.

## Correctness and interactions

- Full builds of original v113, controlled masks, release candidates, and RL collector passed. Same executable sections verified across n00/n01/n02/n04/n08/n15; only mechanism data differ.
- Three release panels: 320 initial + 448 mechanism + 320 healthy-spawn diagnostic games, zero own/opponent faults. An additional 112 debug mechanism games had zero faults and recorded 34 camp-spawn releases plus 559 forced spawn escapes. These are activation evidence, not victory causality.
- The optional RL logger was broken by upstream staged inference. Fixed publication of frozen observations and logits, coherent slot mapping, NRZ identities, NRQ actual behavior distribution. Strict parser refuses lost/malformed/unmatched rows. Initial 16,362 decisions matched logged native probabilities to <0.000012, with no discarded rows. Training checks every later batch before updating.
- Exact supplied neural weights were recovered from header (57 tensors; all 75 re-exported arrays bit-identical). Old v111 checkpoint differs and is not silently reused.
- Full merge p15 preserves channel retries/locks/fuel changes, bank recall intent, shortcut routing, terminal bank exceptions, camp-spawn release, crystal cache correction, plus healthy spawn escape. Four-bit source details in merge.py.
- p15 loses six wins to camp-release-only n04 on the 64-cell diagnostic, despite more clears. Conserved gem ledgers show lower acquisition and more deaths, not proof that one mechanism caused them. Larger 432-cell development reverses that comparison: p15 283/432, n04 275/432, v113 265/432, v112 277/432, bterm 281/432, v111 264/432. All zero faults. Avoid rejecting changes from the small diagnostic alone.
- Focused **q15** repair removes compulsory early escape movement. Instead, the existing hot-spawn health guard releases the heal wait and lets normal combat/farming choose the action. All other fixes stay on. q15 79/128 vs p15 71/128 on matched 16-map/four-style diagnostic; zero faults. Full development and training follow.

## Training and selection

`train_campaign.py` initial campaign corrected-v113 completed six iterations, 576 rollout games and 1,344,237 decisions. Native probability checks passed; all evaluated new weights were weaker than initial on development: s000 283, s002 264, s004 273, s006 262 of432. Original weights remain selected. Classification: Retry required, not Rejected. A frozen copy of the initial trainer is training/train_v1_frozen.py.

Second campaign corrected-q15 uses repaired behavior, half learning rate, and all nine styles balanced within each 96-game batch (48 maps, both sides), correcting the first campaign's style blocks. Four iterations. No final-map use. Native-anchored PPO, team terminal-win Monte Carlo credit, bounded previous-round lead potential; privileged critic only, legal observations for actor. Source, data, optimizer, RNG and checkpoints retained.

`retune_q15.py` waits for that campaign; retunes eight behavior axes with identical executable code, +/- coordinate checks, then coordinate-informed joint/shrunken/double-direction attempts, then full development selection. Fixes remain enabled. The superseded p15 retune waiter was terminated before any t000 sources or experiments existed.

`qualify_campaign.py` waits for the frozen winner. Sealed final: 24 published +24 fresh generated maps, nine styles, controls v111/v112/v113/bterm, plus direct vs112/113. Protocol and gates are frozen before games. It packages exact source/Wasm but does not upload. Inspect results and delivery implications before separately submitting. Failed qualification requires focused investigation and a new fresh confirmation set, not choosing winners from the final results.

## Disk and retention

User cleanup reclaimed ~242 GiB inside C:\projects\cambridge battlecode; original replay files, all source/checkpoints, evidence and unfinished campaigns preserved. Audit is ../cleanup-20261108/REPORT.md. Do not refill historical raw caches.

New runner keeps complete native reports compressed losslessly, complete zipped replays, a 150 GiB free-space floor and 25 GiB local campaign cap. Never resume the stopped old controller. No old sources/checkouts were modified by this campaign.

## Completed training, v114 review, and first holdout

The second training campaign completed four 96-game iterations. Original q15 scored 292/432; the fourth full update scored 286/432; the half update (`mx500`) scored 297/432. It keeps the verified runtime repairs. None of the tested retuning arms beat the half update over the full development set.

v114 adds an early shop cap and additive map profiles. They were verified to activate and tested separately, together and at reduced strength on the corrected runtime. No feature arm beat mx500. Preserve their results for conditional future study; the supplied v114 build itself scored 260/432 and exhausted fuel 5,375 times against mx500's 1,648 on the same schedule.

The frozen mx500 holdout ran 5,472 games without faults or diagnostic codes. It was +2.66 percentage points over v111 against shared opponents, -4.05 points vs v113, and -0.58 points vs v114. Direct scores were 50/96 vs v111, 48/96 vs v113 and 46/96 vs v114. Fuel exhaustions per 1,000 scheduled champion rounds: 0.792 vs 0.812 for v113 and 3.236 for v114. This candidate failed the strength gate; the exact package is for reproduction.

## Champion stalling

- A 12-game recent ranked sample had 472 long movable idle rounds, only two overlapping fuel exhaustion. The public replay records do not identify the exact submitted source. The detector excludes capture stands, channels and observed actions, but still flags useful respawn waits. Three long windows were checked using engine substeps.
- On 64 matched local games per build, b114 had 5,416 quiet trailing stall rounds across 333,858 alive pairs, mx500 had 4,705 across 334,836. Reports and scripts preserve the definitions and normalized denominators.
- A rejected banking or shopping trip in the respawn branch could return before the normal camp fallback. `sw01` fixes that and requires a reachable altar; 296/432 versus 297/432, with a small reduction in general long idle time. It does not explain the largest confirmed loops.
- On Islands, pathing marked a target to avoid after repeatedly making no progress. Neural selection still reselected it. Reproduced 369- and 240-round episodes with positive avoidance timers and fuel still available. `sw02` enforces the cooldown after neural overrides, retaining the rule-based choice. It scored 300/432 with zero faults; quiet trailing stall rate fell from 1.405% to 0.869%.
- On Homonoliths, Cassi waited to heal for 341 rounds. Native camp damage and healing counters rose by the same 540 per round over a sustained stretch. The existing 85%-health guard never released her during that stretch. `sw03` tried a short safe escape after a detected plateau, but the exact trace did not show the escape action firing. `sw08/sw09` test attacking the damaging camp from the protection of spawn when no safe step is available.
- Each counterattack arm logged 139 successful actions on Homonoliths across the traced matches. Cassi's 341-round stall did not recur in the same fixture. Both arms scored 299/432 and 1,628 fuel exhaustions versus 297/432 and 1,648 for mx500. `sw08` was frozen with the target guard and counterattack, without the unverified forced escape. In 64 matched development games, quiet trailing stalls fell by 37% per alive round, and all long idle flags fell by 34%. The published diagnostic direct scores were 20/32 against v114 and 17/32 against v113.

`stall_qualify.py` selects once using development games and then evaluates on 28 previously unused map hashes. Upload is conditional on independent strength, runtime and stall gates. `deliver_cycle.py` reconciles uploads using one unique note and checks the active version before changing it.

## Independent result

Across 2,128 games, neither side registered bot faults or diagnostic codes. Against shared references, sw08 scored 349/504, mx500 348/504, v113 329/504 and v114 312/504. Gains vs v113 (+3.97 points) and v114 (+7.34 points) had map-cluster intervals of [-2.58, 10.72] and [-0.60, 15.67] points, respectively. Direct scores were 25/56 against v113 and 35/56 against v114. Fuel exhaustion was 0.531 per 1,000 scheduled champion rounds, versus 0.514 for v113 and 2.084 for v114. The quiet trailing stall rate on sealed b111 replays was 1.62%, versus 3.20% for mx500 and 1.96% for v114.

**Classification:** the two fixes are accepted as local stall repairs; the full candidate needs another strength pass before release. Against b111 on fresh generated maps, sw08 lost nine more cells than mx500. In the 17 cells that flipped to losses, sw08 banked 130 fewer gems and died 2.47 more times per game on average, with unchanged fuel exhaustion. These outcome-conditioned figures are leads for focused combat and routing inspection, not causal attribution. Keep the fixes available, investigate the first productive action after a target is refused, and use a fresh holdout for any follow-up selection.

The replay audit runs locally. It extracts actions by champion and round, checks parity with the official summary, groups long idle windows, and ranks cases for focused inspection. Use the stored reference and candidate rates as baselines when reviewing new ladder games. Keep useful waits and suspected faults in separate categories; use the substep trace or a same-map local control to confirm a cause.

The published source ZIPs include the actual weights and are suitable for rebuilding with Cambridge Battlecode CLI 5.0.0. The experiment tools retain their pinned local project and asset paths; running the full comparison elsewhere also requires the exact opponent Wasm and map files identified in the panel manifests. Raw replays remain on the laptop.
