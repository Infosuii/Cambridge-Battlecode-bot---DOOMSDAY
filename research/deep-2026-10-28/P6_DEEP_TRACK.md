# Exact reproduction, decision traces and bounded tests

**Measured:** all ten selected losses and two control wins were reproduced in full, byte-for-byte, by the unchanged frozen source against the exact enemy script. Both-scripted controls also reproduced all twelve games. Independent state hashing passed 24/24 comparisons and 25,184 draft/round samples. See REPRO_PLAN, REPRO_RESULTS and REPRO_STATE_VALIDATION. The local rebuild is `29f79745ef2a69b26741e3751ef6e9ee8855d93b9a4991d3dce42295e9d69057`; the server Wasm hash remains unavailable. Full-game behavioural fidelity on these twelve contexts is stronger evidence than a guessed compiler-flag list.

The input parser was first validated on five excluded calibration games by reapplying every accepted command through the official engine, reproducing every round hash and raw replay bytes. The selected twelve passed the same check. Map bytes are exact; native seeds are fixed by the map in this corpus. Fuel-exhaustion turns are reproduced, including VM continuation on the next turn. CLI run output is a ZIP bundle: compare its extracted `replay.repl26a`, not the ZIP bytes.

## Trust limits of logging

Numeric full probes were byte-identical for seven of twelve full games. C030 first diverged at R472 and C011 at R961, after their complete selected windows. C004, C082 and C026 diverged before their windows; none of those full-probe lines are evidence. Separate minimal end-of-turn traces reproduced all three full games exactly. Thus all twelve have valid selected-window telemetry, but only nine have detailed guard probes; the other three have sparse mode/effective-threshold observations. A separate bank-context tail trace on C004 also reproduced the complete game exactly.

Verbose C034 logging changed the first traced turn at R113 from a normal yield to a fuel exhaustion; a focused mid-channel C004 probe first diverged at R35. Both have zero trusted lines. Those failed attempts remain in TRACE_RESULTS.json and TRACE_RESULTS_CHANNEL.json. Numeric records include emission round; a delayed line from a fuel-paused frame is excluded at or after the first accepted-input divergence. State divergence is retained separately. Do not infer safety from an unchanged result or a log that merely looks plausible.

| Case | Physical actor | Trusted trace interval | Observed rule path and conclusion |
|---|---:|---|---|
| C004, guardians, loss | 1 | 1680–1732, sparse; bank-context tail exact | Home/recall while banking disabled, then tribute-win, trib-deny and flee. Exact cancellation conflict confirmed below. |
| C034, vault, loss | 6 | 113–163, detailed | Already banking; enemy cast at R122 is followed by a health drop and channel end without submission. Danger=true and winning=false thereafter; actor flees each actionable turn before death R140. Not evidence of a missing lone-retreat guard. |
| C070, treasure_box, loss | 6 | 370–420, detailed | Approach → fight-champ/fight → flee, with brief re-approach. Guards can admit fights and later reverse as state changes; repeated death does not identify a watchdog fix. |
| C082, corners, loss | 7 | 705–755, sparse | Victim7 approaches, briefly flees, re-approaches, fights and flees before dying. Card carrier6 is a different body. Mid-guard explanation remains unresolved. |
| C018, galaxy, loss | 2 | 330–385, detailed | Wait-respawn/approach followed by 23 tail records in flee. Losing state does not imply the bot chose to keep fighting. |
| C030, dunes, loss | 5 | 276–327, detailed | Tribute/flee/fight-champ plus gap-dash/flee-dash. At R277 guard reports danger=true, winning=false; no tested replacement rule. |
| C048, galaxy, loss | 4 | 460–515, detailed | Wait-respawn/approach/fight/capture/tribute/flee. Capturing then banking and escape are present; allocation/capture denial remains a contextual hypothesis. |
| C060, dunes, loss | 4 | 75–125, detailed | Fight-champ14 tail records, flee7. At R75–76 guard reports winning=true and danger=true, target TTK3.18/4.87. This admits combat under existing priority, not an inactive V75 switch. No causal replacement tested. |
| C011, the_pond, loss | 5 | 441–493, detailed | Tribute31/flee17/fight-champ2 tail records. Alternation is a trace observation, not itself a mistake; full trace diverges only much later. |
| C026, ambush, loss | 3 | 557–609, sparse | Stage/approach/teleport. Focus actor is not automatically the victim behind a team-level model drop. |
| C099, packs, win | 3 | 12–62, detailed | Approach/fight/flee/capture-stand/home/wait-respawn all occur in a win too. Control against simplistic mode labels. |
| Matched C034 control, vault, win | 0 | 130–180, detailed | Banks343 around R150, later fight-champ/flee. Same-map matched context is not the same state or a causal alternative. |

Intervals refer to requested trace ranges; dead/channel/early-return turns need not reach every probe. Tail mode counts are emitted records, not a complete duration denominator. Trace JSON files retain exact effective values and validation receipts.

## Effective switches and thresholds

Across these selected traces the realised carry threshold is65, shop threshold138, retreat HP≈0.11595 and danger HP≈0.180385. V75_LONE=2, V75_BAG=0, V75_RACE=0, V75_GATE=0, V58_ACT=12, V58_SURVIVE=0, tactical-search=0 and stand2=0. The standalone survive-contact function is compiled out; its absence from logs is not a runtime failure. Full probes record all48 realised A2 knobs at window start. Sparse probes record only the listed thresholds/switches, not an invented full vector.

Aggression differs by map: vault≈3.93454; guardians≈1.79236; corners/ambush≈1.76508; treasure_box≈1.41179. Read the runtime value after the per-turn reset and V71 override. A source default or old lab comment is insufficient evidence. Source landmarks are bot.cpp `play_turn`, the V71/A2 block, `handle_enemies`, `tribute_if_needed`, and tactics.cpp `act_enemy_before_walk`/`survive_contact`.

## M1: winning-bag recall cancels for a bank that is disabled

**Causal (tested), bounded decision only.** C004 actor1 carries736, own banked280, enemy178. R1668 begins recall. R1669–1682 each accepts cancel-channel followed by recall, without moving. In the exact bank-tail trace at R1680–1682, HP1296.4/5500 is above the danger threshold; `no_bank=0`, gated=1, `tribute_off_until=1683` and recalling=true.

At bot.cpp around7005, `play_turn` cancels a safe recall whenever banked+bag is winning. That condition ignores the disable timer. `tribute_if_needed` around4535 immediately refuses banking while `round < tribute_off_until`. The timer is set around4639 after twenty non-progress bank turns. Control flow cancels recall to pursue an action that this same bot currently forbids, and later starts recall again.

TAKEOVER_PLAN.json was committed before the trial. A diagnostic copy adds bank availability to **only this actor's** winning-bag recall cancellation from R1669. The original accepted inputs and round states remain exact before takeover. The original fails the assertion with four cancel+recall pairs at R1669–1672; the diagnostic passes with zero. Recall completes R1673 at spawn(19,0), HP5500, bag736. First enemy puppet rejection is R1701, beyond the predeclared ten-round cap R1678. TAKEOVER_RESULT.json retains the precise input/state first differences. No full-game outcome is interpreted.

This is one confirmed source inconsistency, not proof that all recall loops share its cause or that736 gems were recoverable by this fix. The examined proxy finds any qualifying recall loop in49/191 losses and46/169 wins. The previous-round winning-bag descriptor appears in1/191 losses and7/169 wins. The exact bank-timer mechanism has been traced in only one loss. Its observed breadth is small. The native repeat-death and large-bag-loss categories must not be relabelled M1.

Executable case: tests/loss_cases/M1-recall-disabled-bank.json and run_case.py. Both expected baseline failure and diagnostic pass were checked again after adding rejection of incomplete/too-short candidate replays. Frozen source files were not edited.

## Masking check

MASKING_PLAN.json fixes two warm-state probes. At C034 actor6 R123, restore the baked48 A2 values before per-turn application, removing only the V71 vault profile. The accepted inputs and every-round states before takeover are exact. No accepted action changes in the permitted ten-round interval R123–132; first difference is R214, which is not interpreted. C099 actor3 on packs, which has no V71 row, is a negative control: restoring the already-default vector preserves the entire replay byte-for-byte. Both builds are diagnostic copies. MASKING_RESULTS.json records them.

This checks sensitivity in two contexts, not unseen-map generalisation. It provides no support for an aggression-only fix of the vault escape. It does not test removing the whole A2 vector, whole-game default profiles or a new production policy.
