# Contested capture repair: completed local evidence

v112 remains the delivered experimental bot. No replacement was uploaded or activated.

This continuation played 5,886 new local games. The final 48-map comparison contains 6,048 audited cells, including 2,538 exact reused controls. Both teams had zero faults and diagnostic codes; fuel events were explicitly checked, not assumed absent.

| Candidate | Reference gain vs v111 | Direct score vs v111 |
|---|---:|---:|
| auto_cr8_o_c0 | -1.953 pp | 43/96 |
| auto_cr8_o_c1 | -2.083 pp | 43/96 |
| auto_cr8_l_c0 | +0.130 pp | 49/96 |
| auto_cr8_l_c1 | -0.130 pp | 49/96 |
| auto_bank_arrive_original | +0.521 pp | 43/96 |
| auto_bank_arrive_learned | +3.125 pp | 41/96 |

Reference gains and direct scores are different comparisons. Candidate-wise 95% map-cluster intervals and paired on/off effects are in the accompanying JSON.

The original failure was a contested capture, established in the unmodified replay through legal capture-state observations. Three healthy champions waited hundreds of rounds. The logging probe changed the trajectory and is explicitly excluded as evidence of the original decision.

The repaired learned bot flipped the selected vault game against v111: common-horizon camp income rose from 442 to 884. Against nnm4 on the same map, a win became a loss: common-horizon camp income fell from 379 to 28, with deaths rising from four to twelve. This supports investigating objective retention; fewer idle rounds alone is not success.

The initial confirmation stopped before games because it assumed complete cached controls after replacing exposed maps. The missing 54 controls were run explicitly. Maps and repair candidates were unchanged. Failed preparation and recovery receipts are preserved locally.

Diagnostic pilots are selected cases. The confirmation was not parameter-tuned, but has older project exposure and is not a ladder-frequency sample. On/off pairs have identical executable Wasm sections; source/scaffold overhead versus raw parents remains part of deployment performance. No new official action was performed.

Next: Inspect whether leaving one anchor concedes the large reward. Test a coordinated retention policy with sufficient defenders and handoff persistence, versus both matched controls and raw parents. Check costs before another broad retune. Require separate frozen validation before calling it a strength improvement.
