# DOOMSDAY: supplied baseline versus current-version evidence

The supplied `bot (9).zip` has 33/33 files byte-identical to the previously reconciled frozen `bots/live-69` source. Its archive hash is 0433755c1cbc5f120247c132a6c875912f14c3ac5f36abaa7edbfe20845b325c. It is therefore an exact supplied-v69 comparison, not a filename guess. USER_BOT_IDENTITY.json records every file hash.

At the live metadata check on 29 October, platform 71 was active, note“V81”, source filename `v81_home_ladder_hybrid.zip`, submitted 04:40 UTC. The pre-existing Downloads archive matches that filename and 285565-byte size, but a fresh browser re-download timed out. Its source-to-submission identity is conditional, with no independently recovered server archive hash. CURRENT_SOURCE.json states this explicitly. No code from either archive was executed or changed. The frozen ladder snapshot places DOOMSDAY 47th, rating 2013.05; this is not attributed to a particular version.

## What should be retained

This is not a primitive controller missing all the visible meta components. The supplied and current-reference sources already contain per-body item plans, camp claims, legal mirrored drafting, recovery/banking logic, crystal routing, endgame logic, contact evaluation and fuel-aware routing. Much of the proposed strategic vocabulary already exists in code. Prior experiments also show that copying an elite draft or forcing a gold funnel can lose within this lineage.

The relevant gap is whether these components agree on a feasible job, timing and recipient, and whether the action completes before the scoring race ends. A broad rewrite is not established by these 30 matches. Neither is a superficial item-table edit.

## Source-specific findings

The supplied-v69 `bot.cpp` around 7005 cancels a safe recall when `win_now()` is true. Its tribute routine around 4538 can still reject banking due to `w.no_bank` or `tribute_off_until`. Prior exact reproduction and a bounded warm diagnostic established a real timer conflict, with narrow prevalence; see research/deep-2026-10-28/REPORT.md and followup-v70-2026-10-29/REPORT.md. This study verifies that the supplied archive is that source, but does not rerun or broaden those experiments.

The conditional-v71 archive's channel branch around 6991 no longer contains that safe-winning-bag cancellation branch. It retains a danger-based channel guard, hidden-recall protection and teleport preservation. Therefore the old defect is a supplied-baseline concern, not a proven unresolved current-v71 defect. Do not blindly port the old fix or disable the current guard.

The conditional-v71 `common.h` explicitly sets `A3_FOCUS=0`, `A3_NUMBERS=0`, `A3_ITEMS=0` and `A3_ONE_OWNER=0` before fallback defaults. Read active definitions, not comments describing alternative branches. Existing contact scoring still does work, so these switches do not establish an absence of targeting or coordination. They identify isolated candidates for measurement.

Its active V58 item-plan branch aroundbot.cpp 99 uses champion-class templates, including Prospector openings and later survival/capture milestones. Marcella opens Jungle strength, then Prospector focus and defensive/offensive complements. The new elite sample instead shows successful Jungle-first, Treasure-first and Prospector-first policies. The next question is whether the current next job warrants that passive, particularly since Prospector only bonuses cluster rewards. This is not evidence that every Prospector opener is wrong.

`HOME_SIDE=1` with territory 0.3/aggression 0.8 and `LADDER_TABLES=1`/`LADDER_HOME=1` are active in the conditional reference. Draft tables identify named-pool signatures by width/height/pick count/group count around draft.cpp 765. That can preserve useful known-map knowledge while failing to generalise to new maps with the same coarse signature. Static geometry and mandatory access properties are safer transferable features, but the win effect of replacing the table has not been tested.

There is already a short job-sequence planner (`plan_search`, bot.cpp 5999), but its default `APEX_PLAN` is 0 and runtime overrides would need separate verification. Its channel estimate uses `ceil(bag/10)` and sequential “camp then bank” legs. The new 109→309 and 49→249 gate traces motivate modelling capture/tribute overlap and item-adjusted channel timing, rather than merely increasing search depth. This is a concrete model feature to investigate, not a claim that enabling the dormant planner would improve matches.

## Behavioural comparison limits

No fresh v71 DOOMSDAY games were selected into the primary 30-match elite sample. Historical v69/v70 results remain separate evidence, including duplicate-trajectory and reserved-set restrictions. Current source comments about older wins, branch experiments or rank gains are untrusted performance claims unless backed by their original measurements. The new 30-match sample establishes elite behaviours and legal mechanisms; it cannot quantify a v71 win-rate improvement or isolate the marginal cause of DOOMSDAY's present rank.
