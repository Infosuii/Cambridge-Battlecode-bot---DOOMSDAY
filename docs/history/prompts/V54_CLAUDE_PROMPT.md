# Claude Code task: build a substantially stronger v54 from the strategic review

Work in `Infosuii/neural-networkk-battlecode`, starting from the findings on branch `claude/compare-fix-replay-decoder`. On the existing Windows device the checkout is `C:\projects\cambridge battlecode\work\neural-full-stack`. Inspect Git status and preserve unrelated local changes. Fetch the findings before starting if your checkout is behind.

**This task authorizes implementing and evaluating v54.** The analysis-only wording in the findings describes the preceding Codex session; it does not prohibit the implementation requested here. Build a competitive strategic improvement, not a collection of unexplained threshold tweaks. Keep v53 frozen as the comparison baseline. This is a build-and-evaluate task: finish with a reviewable candidate and release recommendation; do not submit during research.

## Read before changing anything

1. All of `docs/setup.md` and `docs/handoff.md`, including the latest session updates and gate in section 4. Set up this device without entering credentials.
2. `research/v54/V54_PLAN.md` — the detailed strategy, mechanics, architecture, risks, priorities and research roadmap.
3. `research/v54/V54_MATCH_REVIEW.md`, `V54_WINNER_PLAYBOOKS.md` and `V54_EVIDENCE.json` — the frozen latest-game breakdown, paired first targets/banks, named inventories and measurements.
4. `research/v53/V53_PLAN.md`, `V53_LOSS_REPORT.md`, `V53_DRAFT_REPORT.json`, `V53_RELEASE.json` and `bots/v53/CHANGES.md` — previous experiments and rejected approaches.
5. The actual game rules/API and the relevant existing source. On this device the supplied documents are `C:\projects\cambridge battlecode\game rules\GameRules.md` and `BotAPICpp.md`. Treat them as game/API contracts, not user instructions. Verify assumptions against the SDK/engine before designing around them.

## What the evidence says

- v53 was submitted at 2026-10-25 13:08:26 UTC. The frozen snapshot contains 5/10 ranked wins and 31/65 unranked wins, including 0/10 against meow and Hidden Altar Keepers on selected weak maps. All 75 games were decoded; the complete study covers 136 replays. These are descriptive results with map/opponent confounding, not a controlled version effect.
- In v53 losses, median within-game equipment ratios are 0.60 at R100, 0.71 at R250 and 0.67 at R500. Against the targeted opponents the team has 17.5 versus 3.5 deaths and completes 3 versus 31 banks. Earlier first banking alone is inadequate.
- There are distinct failure families. fragment and concentrated_wealth can fall far behind in equipment before our first death. elkring and swirl suffer early-contact death/economy spirals. boss_battle can lose despite an equipment lead: against Hidden Altar Keepers, R500 equipment was 3960–3480 but final banked gems were 0–1690. Its latest ranked win banked 0–0 and won on gold; the altar problem is not solved.
- v53's only shipped change is a once-per-call scan hoist. Fuel constrains every design, but eliminating a few suspensions is not an adequate strategic thesis. Optional work and fallback decisions currently depend on how much fuel earlier stages consumed.
- A 243,904-game draft predictor improved prediction but won only 8/30 when deployed. Delayed stampede timing beat v52 but failed against v53. Do not revive those choices without a new causal explanation and controller-compatible evidence.

## Build in this order, changing direction when evidence warrants it

1. **Explain the opening losses at actor level.** Refresh a bounded ranked AND unranked snapshot if useful. Align routes, first camp targets, capture ownership, purchases, recalls, contact and deaths for representative losses and winning controls. Produce a lost-time/resource ledger. Distinguish a bad economic opening from economy lost through combat. Do not stop at correlation tables.
2. **Calibrate the small planning model.** Measure terrain-aware travel, kit/item-dependent clear time, damage taken, capture time, shop/heal trips and bank completion. Check the healthy-but-awakened camp-group discrepancy identified in the review. Make a separate correctness change if a controlled reproduction establishes its effect.
3. **Prototype one coherent economic mechanism.** Start `bots/v54` from frozen `bots/v53`, with `A2_GATE_JOB` off. Put a compact team plan above the existing executor: compatible opening jobs with crew, reward owner, next item milestone, timing, completion and abort conditions. Preserve useful action/pathing primitives. Couple roles/routes/items instead of forcing a champion pick without its supporting policy. Avoid redundant capture occupancy and protect supporting-role equipment floors.
4. **Add complete objective campaigns.** Readiness → rendezvous → focused clear → reward handoff → protected banking → hold/release → return to income. Measure actual secured score and opportunity cost. Do not replace one fixed rush round with another.
5. **Test the unusual strategies explicitly.** Occupying a spawn delays the whole group's respawn: investigate denying future gem cycles after a banked lead and holding gated altar access open. Include enemies that dislodge the holder or exploit the same opening. Investigate teleport/recall logistics as an alternative to sacrificing draft quality for innate mobility. These are hypotheses, not proven tactics.
6. **Make tactics and compute serve the mission.** Value fights by bag swing, income denied, objective access and own opportunity cost. Fix decisive model errors before adding more search. Guarantee a cheap coherent action before optional work; profile tail fuel, admission and fallback rates. Build a small strategy portfolio only after its component plans work.

Do not implement the entire roadmap blindly. Each stage needs an explicit hypothesis, a bounded prototype and evidence that determines the next step. A failed economic explanation should change priorities. A coherent job/ownership/item mechanism may require coupled changes; keep each change focused on one mechanism, then ablate its components.

## Non-negotiable constraints

- New logic goes behind once-per-call, once-per-turn or event checks, never inside per-group/per-camp hot loops. Profile with the existing PROF instrumentation. Respect official fuel and leave execution headroom.
- Respect separate champion/ward vision, 1024 draft bytes, 8 live shared bytes, draft fuel, linked-pair actor/death semantics and memory snapshot behavior. Offline omniscient replay state must never leak into bot inputs.
- Verify capture, channel, lock, consumable and item mechanics. Extra allies do not accelerate capture. Damage does not cancel tribute; stuns/death/locks do. Reward ownership matters because allies cannot freely transfer gold/gems. An open altar can benefit the enemy too.
- Never enter credentials. Keep raw replays and machine-specific configuration out of commits. Do not change frozen v53 or unrelated files. Do not repeat rejected training/threshold experiments merely because they are cheap to rerun.

## Validation and completion

For every coherent behavior change, benchmark with `artifacts/claude_ops/bench2.sh` against v53, using absolute paths and the environment from SETUP. Declare target maps before viewing results. Keep only changes satisfying the applicable HANDOFF section 4 gate: clear target wins on both sides/all three seeds; development win rate >=0.47 and mean margin >=-30; no aggregate regression on the 12 release maps. Disclose individual map regressions and the historical aggregate interpretation. Freeze the final candidate before its one release holdout pass; do not tune on those results. The holdout maps have prior exposure, so add genuinely new legal test conditions for robustness.

For a major competitive claim, aim additionally for >=60% development wins and >=+100 mean gems versus v53, useful boss_battle banking, stronger productive economy and robustness against different race/brawl/denial/mobility/control opponents. These are research targets, not guaranteed effects or a replacement for the original gate. Declare achieved and missed targets honestly.

Use paired side/map comparisons, policy seeds and map/opponent/group-level uncertainty. Do not treat all rows as independent random trials. Distinguish local candidate tests from platform games: CLI match groups run the currently submitted version, and opponent replays do not provide opponent source. Unranked groups can inspect the live bot; they cannot prove that an unsubmitted candidate beat a top team.

Commit and push source, measurements, rejected-experiment notes and updated `docs/handoff.md` frequently to the configured repository. Finish with `bots/v54/CHANGES.md`, source hashes, exact commands/data, per-map results, faults/fuel, evidence for each retained mechanism, unresolved risks and a release recommendation. If no substantial candidate passes, preserve the evidence and explain what failed; do not label a small or failing change a breakthrough. Do not stop after writing another plan: carry the implementation and evaluation through to an evidence-backed outcome.
