# Follow-up to sw08

`sfhs002` is the frozen candidate. Across 2,192 qualification games, it gained -4.58 points against shared references compared with v113. The 95% map-cluster interval was [-9.79, +0.83] points. Its direct score against v113 was 45.00% on new maps and 58.33% on published maps.

Failed release gates: current_reference_gain, positive_cluster_confidence, direct_v113_above_half, stall_guard_pass. Ladder release state: no upload.

Replay traces identified a broad late veto in sw08. It applied short ally capture preferences as if they were navigation failures, which could redirect a nearby champion to a distant target. The code screens compared ranked fallback, rechecking a handoff, preserving the short preference separately from hard path cooldown, and allowing nearby continuation. The route fallback was parked after no recorded activation in 12 targeted games. The spawn-healing counterattack remains in the tested variants.

Two native training runs collected 1,386,675 decisions in 576 games. The rollout sampler masks blocked targets using the same eligibility rules as deployment. Weight selection used separate development games, native exports and tests against the incumbent. The protocol freezes fresh map hashes and the candidate before final evaluation. Source ZIP, exact WASM and the selected checkpoint are under release. Raw replays are local.

The second screen tested the stall and targeting repairs on the v113 strategy, both with the incumbent weights and with the latest trained weights. It used a separate set of map hashes. All three variants fell short of the development floor.

The final screen tested only confirmed route failures and the spawn-healing loop, with original v113 weights and no broader strategy changes. `rv11` failed the stall-rate requirement on the published failure maps.
