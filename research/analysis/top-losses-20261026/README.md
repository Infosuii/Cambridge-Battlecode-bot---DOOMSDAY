# DOOMSDAY: complete recent top-team failure audit

## Scope and evidence

This review covers **every finished loss to a current top-25 team in the fixed 24-hour window of match creation, 25 October 2026 20:24:26 to 26 October 2026 20:24:26 London time (UTC)**. The definition includes development teams. Opponent ranks come from the saved ladder snapshot, not historical rankings at match time.

We paginated all ranked, unranked and tournament listings through the beginning of the window: **2,795 encounters inspected; 585 completed top-25 games; 502 losses and 83 winning controls**. Ten losses used engine1.0.3; the current engine2.0.0 analysis therefore contains **492 losses and 83 wins**. Native summaries for all 585 games passed identity, checksum, result and event-total checks, with complete detailed capture and **zero runtime faults on either team**.

The exhaustive match ledger is [FAILURE_LEDGER.md](FAILURE_LEDGER.md), with a filterable [FAILURES.csv](FAILURES.csv) and complete derived measurements in [failure-ledger.json](failure-ledger.json). [REPLAY_REVIEW.md](REPLAY_REVIEW.md) covers the full replay audit; [decode-status.json](decode-status.json), [validation.json](validation.json) and [replay-crosscheck.json](replay-crosscheck.json) record coverage and verification.

This is an exhaustive audit of the recorded loss corpus, not proof that every possible bug in the bot has been found. Flags overlap and describe observations at explicit thresholds. Code findings, observed outcome patterns, and untested interventions are distinguished below.

## The largest gap is productive survival

Across the **105 known-v62c losses**, the winners produce almost twice the gold and player damage while losing fewer than a third as many champions:

| Per loss | DOOMSDAY v62c | Opponent |
|---|---:|---:|
| Earned gold | 3,657 | 7,173 |
| Champion deaths | 13.47 | 3.69 |
| Champion kills | 2.90 | 11.65 |
| Champion damage dealt | 16,143 | 33,288 |
| Collected gems | 614 | 1,146 |
| Banked gems | 394 | 1,028 |
| Gems lost to enemy champions | 132 | 30 |

These are same-match comparisons. Team body counts vary, notably with Cassi & Issac, so per-team deaths alone should not be treated as a normalized individual skill measure. The replay report adds dead-time and contact measurements.

The gap starts early. At R100 in those losses, gold is **291 vs 370**, gems collected **43 vs 60**, and deaths **0.81 vs 0.29**. At R500, gold is **1,628 vs 2,665** and deaths **4.85 vs 1.87** in the 102 games that reach that checkpoint. Later checkpoints have survivor selection; their denominators are published.

Death prevention is necessary but insufficient. In the 49 v62c losses where **neither side had died by R100**, our gold was **328 vs 360**, but gems were **43 vs 67**. Ten current-engine losses finished with **zero deaths on our side**. There is an independent resource-routing and objective-conversion problem.

## Findings and what the winners do better

### 1. Early routes and reward yield lag before the snowball

**Observed:** 355/492 current-engine losses meet the early-economy-deficit flag; 447/492 trail in final collected gems by at least 150. Collection includes dropped-gem recycling, so the latter is not a pure neutral-farming measure. Our first camp clear is not generally later: in the pooled losses it averages R25 vs R31. Simply initiating a camp sooner does not fix yield, reward ownership or the route after that camp.

**Better opponent behavior:** winners turn early activity into more resources and a larger equipment advantage by R500. Productive farming, safer movement and PvP rewards reinforce one another.

**Next test:** evaluate an opening and follow-on route as a team plan, with explicit reward owner and shop timing. Track collected gems, gold, deaths and equipment by R100/R200/R500. Count successful reward capture separately from the last hit that cleared a camp: the native `campClear` owner is not proof of who later captured its reward.

### 2. The fixed item opening still delays useful combat stacks

**Observed:** in the 105 v62c losses, **none of our 502 champion appearances bought a Bruiser shard by R300**. Opponents had 114/495 champion appearances do so. Among heroes that eventually bought Bruiser, the median first purchase was **R775.5 for us vs R423.5 for them**; that median is conditional on buying it, not the whole roster. In 232/492 current-engine losses the opponent bought at least five early Bruiser shards while we bought none.

**Source:** `V59_ITEMS=2` replaces the old Greed tail but still places five or six five-shard passive milestones ahead of Bruiser for most heroes. The first-300-round item lists show the effect directly. This is a delayed-stats finding, not a claim that Bruiser is always the best item on every map.

**Better opponent behavior:** efficient combat scaling arrives while early encounters are deciding the resource race. Opponents also use different mixes of Treasure, Jungle, Durability, Health and damage items; copying only their late-game inventory misses the opening.

**Next test:** a role-specific shorter opening, coordinated farming and survival package. Do not assume an item-order change alone is sufficient or proven. Existing v62a is a relevant unvalidated ladder candidate rather than a newly discovered idea.

### 3. The carry exists in the draft but not in our economy

**Observed:** same-hero comparisons in v62c losses:

| Hero | Our appearances | Opponent appearances | Gold ours / theirs | Player damage ours / theirs |
|---|---:|---:|---:|---:|
| Vesper Vale | 55 | 80 | 869 / 2,539 | 3,149 / 10,360 |
| Marcella | 89 | 89 | 677 / 2,246 | 4,023 / 9,963 |
| Heart of Ruin | 62 | 91 | 556 / 1,147 | 2,570 / 6,697 |
| Vendetta | 103 | 80 | 796 / 1,409 | 3,665 / 5,913 |

These are observational same-hero aggregates over different appearances, not a controlled hero A/B. The ledger flags 275 current-engine losses with a severe Vesper/Marcella income gap.

**Source:** `UB_GOLD_FUNNEL=1` is a local handoff: another hero yields only when Vesper is already on the reward region or nearby with a matching claim. The repeated team economy director and routing packages are off. This does not schedule a remote carry to arrive before the reward is available, and it does not establish an equivalent fallback carry when Vesper is absent.

**Better opponent behavior:** Vesper and Marcella become high-income, high-damage carries. Draft prevalence alone cannot explain or repair our poor performance on the same heroes.

**Next test:** schedule clears, capture ownership, carry arrival and shopping together, with a fallback carry. Measure the carry's early gold and damage contribution without sacrificing total team income.

### 4. Retreat and reinforcement rules leave unsafe encounters open

**Observed:** 281/492 current-engine losses have at least eight deaths and twice as many deaths as the opponent. The full replay ledger identifies isolation, repeated deaths after respawn and pressure near home for each match.

**Source-confirmed rule gap:** `APEX_OUTNUMBERED=2`, `V59_ALONE=0` and `NOVA_EARLY_SAFE_UNTIL=0` mean the explicit numbers guard triggers at `foes >= friends + 2`. A lone champion is **not forced to leave two enemies** by this guard. Other danger logic can still make it retreat; this is not a claim that the entire controller always stays.

**Source-confirmed limitation:** `A2_TEAM=2` joins a visible ally fight but does not enable the hold/disengage bit. The join helper checks health, bag size, distance and local counts; it has no explicit equipment-power or arrival-time check before walking toward an ally. Recent hidden-enemy belief is disabled. These are plausible mechanisms for late reinforcement and repeat feeding; assigning an individual death to one of them requires the relevant observed state.

**Better opponent behavior:** winners survive combat with much lower death rates while preserving economic output. Merely moving our heroes closer together has not reproduced that.

**Next test:** protect solo 2v1s and coordinate a safe retreat/regroup point, including after respawn. A reinforcement should join a fight it can help win on arrival, rather than arrive after the ally has died. Retain economic targets in the test so passive avoidance is not mistaken for progress.

### 5. Spells need a direct readiness audit, not a cast-count story

The inherited replay tool approximates hostile casts from target proximity. That can miss area effects or attack resets and does not prove that a spell was ready or legal. Therefore the earlier assertion that winners "arrive with spells ready" is not accepted from cast counts alone.

This review adds **actual own-perspective champion-turn cooldown checks** at entry into visible contact, and tracks whether a cooling ability was last observed being cast at a camp. Across all 492 current-engine losses, **20.2% of our offensive contact entries have no offensive ability ready, versus 28.4% for the winners**. Camp-cast cooldowns are present at **4.1% of our entries vs 7.3% of theirs**. In known v62c losses the corresponding figures are **23.2% vs 28.1%**, and **4.3% vs 8.1%**. These metrics do **not** support a blanket spell-readiness explanation for our disadvantage. Different kits and encounter selection still matter; this is not a causal test of conserving a particular spell. [REPLAY_REVIEW.md](REPLAY_REVIEW.md) publishes the complete results and definitions.

**Source:** the v62c snapshot has `APEX_SPELL_HOLD=0` and `APEX_SAVE_DASH=0`; farming can spend stuns/damage/movement abilities. These settings alone are not proof of waste. Existing v62d/v62e/v62f target conservation but need ladder evidence. Prioritize damage application, target choice, equipment and safe engagement over assuming that merely holding more cooldowns solves combat.

### 6. Camp risk is a separate failure, not all PvP feeding

**Observed:** 42/492 losses have at least two camp deaths that account for at least a quarter of our deaths. These are individually identified, including games with no player-caused deaths. Blindly increasing team aggression or farming speed could make these worse.

**Next test:** check the actual camp, health, support and reset conditions before the failed clear, then tune staging/soaking/abort behavior. Do not add costly risk evaluation inside every candidate loop without measuring its budget impact.

### 7. We collect enough resources but fail the map's winning objective

**Observed:** 27/492 losses collected at least 300 gems and banked zero; 20 ended with enough held-plus-banked gems to reach 1,000, and 12 had roughly competitive collection but substantially worse conversion. These categories overlap.

**Concrete gated-bank failure:** v62c vs Sponge on `01boss_battle`, match **2dbe21e8-fc0c-4787-9313-7c2ad7ad704b**. We collected **1,356**, banked **0**, lost **256** gems to players and **233** to camps, and still held **867** at the finish. Sponge cleared blocking group16 at **R864**, then banked at **R879, R883, R984 and R1032**, finishing with **1,039**. Our team never recorded a group16 clear. At R500 our gold was 3,945 vs 4,578: this is not just an empty economy.

**Source:** the explicit gate-job package remains off following earlier rejected rushing attempts. "Bank earlier" does not open a blocked altar.

**Next test:** a gear- and team-readiness-gated objective plan that clears access and brings the carriers through the same opening. Validate group clear, bank completion, deaths and carried gems, not only total collection.

### 8. Single-objective maps still fail against strong opponents

**Observed:** `00stampede` is **0/8** in this current-engine top-team corpus; four losses collected no gems while the enemy collected at least 160. The sole-camp heuristic winning older self-play was not evidence that this objective was solved against top teams. `00dunes` is 0/23, `02famine` 0/17, `00elkring` 0/14, and `02arena` 0/13. Full map tables include the opponent/version selection behind each result.

**Next test:** examine the economy before the large objective, clear/capture ownership, interruption, and repeated banking cycles. A camp-clear last hit and a successful capture are separate events. Avoid a universal earlier-rush change based only on these losses.

### 9. Bag protection and finishing the race have their own cases

**Observed:** 164/492 losses have at least 100 PvP gem losses and twice the opponent's PvP bag loss; 34 lose despite banking at least 800. The Fish crater collapse is a clear feeding example: match **abc9f6f6-1278-40f4-b171-791b2d042de0**, **27 vs 2 deaths**, **134 vs 1,056 collected**, **0 vs 1,009 banked**; all 134 of our collected gems were lost to enemy champions. By R500 we had already died 15 times.

**Next test:** threat-aware carrier routes and fight selection, and explicit end-race banking/interception decisions. The final inventory alone does not prove a safe winning bank was available earlier.

### 10. Runtime faults are ruled out; fuel and inactivity need context

All 585 summaries have **zero bot faults**. In current-engine losses, our side has 245 fuel-exhaustion events across 67 games; the winners have 2,584 across 131. Frequency alone does **not** support the blanket claim that fuel exhaustion caused this top-team gap. Budget effects remain possible and require action-level profiling.

The full replay ledger identifies **85 stationary intervals across 30 current-engine losses**, lasting at least 80 rounds outside spawn without observed movement, attacks or casts. At the inspected turn, **82/85 permit movement, have legal neighboring tiles and have no active channel**. **75/85 produce no earned gold, collected gems or banked gems during the interval**. These still require interpretation: an intentional capture, camp wait or denial is not automatically a stuck-path bug. Historical moat fixes are not reintroduced as current bugs without evidence. Every detected own-team interval, including five historical-engine cases, is inspected at an actual champion turn; [stationary-cases.json](stationary-cases.json) records movement legality, nearby enemies, channel state, live camps and resource changes. One sampled state does not prove the state of every intervening turn.

Two concrete symptoms survive the initial check:

- **Vault, known v61**, match `b64343a2-8550-4c92-adac-3072228f7fcc`: Vendetta stands at (19,15) from R227 through R2000; Marcella stands at (19,14) from R232 through the end. At R500, Vendetta is at full health, has no buffs or channel, both abilities ready, and **six legal neighboring movement tiles**. The game ends **343–347**, a four-gem tiebreak loss. Legal movement rules out a blanket inability to move at that sample; it does not identify the controller's intended target or prove a profitable route existed.
- **The pond, known v62c**, match `bf70f1fe-05ff-40b5-bdf6-074b18b54dfb`: Vendetta remains at (16,15), holding 21 gems, from R1074 through the final partial round. At R1300 it is at full health, unchanneled, with both abilities ready and **five legal neighboring tiles**. This game ends **473–1009**, with **24–0 deaths**; inactivity is an additional failure symptom, not an alternative explanation for all of that loss.

These cases warrant a progress watchdog and target/state-specific diagnosis, including finite/blocked objectives and waiting on shared jobs. A naive timer that breaks every camp hold can destroy valid capture/denial behavior.

## What the existing version tests actually establish

The saved duel plan links arm versions to group IDs, avoiding guessed activation times:

| Arm | Platform | Wins / 120 | Mean gem margin | Deaths per game |
|---|---:|---:|---:|---:|
| v60 | 59 | 15 | −465.0 | 14.19 |
| v61 | 60 | 21 | −462.3 | 13.80 |
| v62c | 63 | 15 | −494.0 | 12.51 |

The maps, sides and planned opponent slots match across arms. Opponent submissions may change, and outcomes can vary with initiative/seed. The v62c-v61 margin difference is **−31.7**, with an opponent-cluster bootstrap 95% interval **[−89.2, +28.2]**. This does not establish a reliable regression or improvement. It establishes that **lower deaths alone did not demonstrate better top-team results**.

The fixed-window ranked subset is **17/30**, while deliberate challenge games are **66/545** on the current engine. These must not be pooled and described as our normal ranked win rate. Claudus is heavily oversampled (170 encounters). Fifteen current-top-25 opponents were encountered; we do not claim to have played all 25 teams.

## Recommended order for the next implementation session

1. **Economic opening + real carry ownership + earlier useful stats**, evaluated as a coherent package against these top teams. Preserve neutral-farming output while reducing early deaths.
2. **Safe regroup and fight admission**, including lone 2v1s, post-respawn behavior and reinforcement arrival. Judge both deaths and win/gem outcome.
3. **Restore productive action in terminal stationary states**, with a progress watchdog that checks actual progress, current objectives and movement legality before abandoning a task.
4. **Explicit gate/capture/bank plans** for boss_battle, stampede and other flagged objective maps, with map-specific success checks.
5. **Combat damage application and target selection**, informed by the direct readiness audit. Spell-conservation candidates remain hypotheses rather than a proven fix.
6. Review every **camp-death, late-race and fuel** case in the ledger before calling any of those solved.

No bot was built, trained, activated, submitted, or queued for matches by this audit. The work is analysis and reproducible evidence. A source preprocessing pass captured effective configuration; it did not compile a bot binary. No new feature is described as proven stronger.

## Reproduction and files

Use the Python runtime and CLI configured for your checkout; the scripts derive the repository root from their own location. Existing Battlecode login is required for collection. Collection never queues matches or changes submissions. Both engine visualiser bundles must already be installed for offline replay decoding; their hashes are verified.

```text
python research/top-losses-20261026/collect.py
python research/top-losses-20261026/collect.py downloads
python research/top-losses-20261026/verify.py
python research/top-losses-20261026/analyze.py
python research/top-losses-20261026/decode_all.py
python research/top-losses-20261026/replay_report.py
python research/top-losses-20261026/failure_audit.py
python research/top-losses-20261026/stationary_audit.py
python research/top-losses-20261026/additional_checks.py
```

- `finished-top25.json`, `losses.json`, `ladder.json`, `duel-plan-snapshot.json`: the match universe and cohort evidence.
- `manifest.json`: native-summary/replay locations and checksums. Raw replays and native summary files remain under ignored `artifacts/local-only/`.
- `metrics.json`, `aggregates.json`, `DATA_REPORT.md`: complete native-summary measurements, all cohorts and maps.
- `all-loss-fights.json`, `replay-aggregates.json`, `REPLAY_REVIEW.md`: full replay-derived evidence and limitations.
- `failure-ledger.json`, `FAILURE_LEDGER.md`, `FAILURES.csv`, `failure-counts.json`: one entry per loss and explicit review flags.
- `SOURCE_EVIDENCE.md`, `effective-macros.txt`, `source-evidence.json`: exact local source excerpts and effective configuration.
- `stationary-cases.json`, `additional-evidence.json`: every stationary-state inspection and the detailed item-timing/deathless counterexamples.
- `paired-uncertainty.json`: reproducible uncertainty calculation parameters for the known duel comparison.
- `validation.json`, `decode-status.json`, `replay-crosscheck.json`: completeness and crosschecks.

The fixed historical cutoff is intentional. Running collection again does not turn this review into a monitor or change its time window. This audit does not assign unknown matches to a version based solely on creation time, does not merge engines, and does not publish credentials or raw replay archives.
