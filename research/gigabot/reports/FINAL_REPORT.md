# GX final handoff

**Release decision: use the exact x3mf fallback.** None of the completed builds passed the primary gate, so none qualified for release. [gx-final source](../bots/gx-final/src) and the [CAMBC source bundle](ladder/gx-final.zip) reproduce the x3mf benchmark executable byte for byte. The [package note](ladder/gx-final.md) records both checksums and the archive verification. No ladder submission was made.

The [ledger](RESULTS.md) links 424 completed runs and their raw results (69,636 recorded games including controls, reproductions and conformance). The [pool audit](../research/gx/diagnostics/final-pool-audit.json) covers all 106 complete three-opponent matrices, including the x3mf reference. Promotion requires at least 351/516, paired z ≥ 1.5, no opponent more than three wins behind x3mf, zero faults, and at most 10% more fuel-outs. A qualifying pool build must then finish within three wins of x3mf in each generated set and opponent pairing.

| Build | v92 | v86h | x1bru | Pool wins | Paired gains / losses | z | Fuel-outs | Faults |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| x3mf / gx-final | 96 | 115 | 130 | 341/516 | 0 / 0 | 0.00 | 548 | 0 |
| Quieter supported camp (`packproof3`) | 103 | 119 | 128 | **350/516** | 16 / 7 | 1.88 | 536 | 0 |
| Nearby support tie-break (`packproof1`) | 102 | 116 | 128 | 346/516 | 17 / 12 | 0.93 | 545 | 0 |
| Bank channel priority (`bankpriority1`) | 98 | 116 | 130 | 344/516 | 6 / 3 | 1.00 | 548 | 0 |
| Frozen alternate-opponent fit (`shrinkcheck`) | 94 | 120 | 127 | 341/516 | 7 / 7 | 0.00 | 548 | 0 |
| Stronger field reserve (`fieldproof2`) | 94 | 116 | 127 | 337/516 | 17 / 21 | −0.65 | 434 | 0 |

The fallback's generated references are 50/100 and 42/100 on styled layouts, and 59/118 and 83/118 on maze layouts, against v92 and x1bru respectively. Its direct self-play reference is 86/172. Its three local sparring results were 142, 90 and 88 of 172. These are local tests of frozen opponents; no ladder result is inferred.

## What held up

- **Quieter supported work was the best lead.** `packproof3` was one win short of promotion. It gained seven wins over its same-executable control (10 gains, three losses), with identical total fuel-outs. The separate [single-action test](../research/gx/diagnostics/packonce-prefix.json) activated in nine pairs, matched every engine snapshot through the start of the selected round in all nine, and had two wins flip in favour of the action. The other 163 pairs had identical summaries. This establishes that the action can matter; its strength on generated layouts and independent opponents is untested.
- **Fuel improvements did not automatically improve play.** The original stronger reserve removed all 84 round-one fuel-outs. The matched field-reserve arm reached 434 total fuel-outs, down from 539 in its inactive control, and lost three wins relative to that control. The later draft estimate moved some exhaustions to later rounds and reached 649 in each active arm.
- **A build can change decisions before its new behaviour activates.** The [inert Wasm metadata control](../research/gx/runs/gx-identity-pool-v92/results.json) changed the module hash but reproduced all 172 replay hashes and fuel counts against v92. By contrast, the fuel-only executable controls scored 95, 90, 91 and 84 wins as the no-policy work changed. The original in-place bank build diverged before a potential winning bag in all 40 flipped games; the matched banking arms subsequently tied their control at 343 wins with no outcome flips.
- **The fit did not transfer.** The earlier side-A fit gained 29 there and lost 14 on side B. The later [frozen alternate-opponent table](../research/gx/diagnostics/shrink-frozen.json) improved its training set from 322 to 346, then tied x3mf at 341 on the untouched primary opponents. Neither table is part of the fallback.
- **Several promising signals did not yield a useful policy.** The open ward arm gained nine against v92 but lost 23 against v86h. The casualty forecast generalised to held-out contacts, but the two chase responses scored 332 and 336 against their 341-win control. Opening crew assignments lost to their control; the merchant arms all matched their 324-win control. The linked bank alarm added no wins over the alarm-only arm. Broad trip penalties, roster replacements and standing on contested captures also regressed.

## Next tests, in order

1. Confirm the quieter support result against the independent sparring opponents and direct x3mf, using its frozen bytes.
2. Run the same build on styled and maze layouts and preserve those sets as holdouts.
3. Measure whether the alternate camp is actually quieter at arrival and whether the helper remains close enough to engage.
4. Repeat the single-action prefix test against an independent opponent and across more actor slots, without using the observed winners to select cases.
5. Isolate first-turn field savings from later decision changes and check both fuel totals and action timing.
6. Use the finish-window replay evidence to choose earlier safe deposits; only seven baseline non-wins had enough live gems already at altar range in the last 25 rounds.
7. Verify the final-roster handoff using the submitted pick, then test crew assignments that abstain when the roster or job is uncertain.
8. Check whether first-emblem routes actually activate and advance a purchase before testing another release build.
9. Replay linked deaths with carried bags and measure whether the safe partner had enough time to bank after an alarm.
10. Consider a combined build only after a feature passes its standalone pool and holdout gates; retain the exact fallback until then.
