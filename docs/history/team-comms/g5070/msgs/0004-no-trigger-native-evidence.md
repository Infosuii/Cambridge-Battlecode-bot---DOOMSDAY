# Follow-up: zero-death outcome flips, unchanged draft

K005 K2/W150 vs BP has five observed outcome flips where both versions recorded zero team deaths. Native summaries confirm the draft roster/order is identical. Examples: 00rows side A vs x2 and x2-s2 both change win to loss, with zero fuel exhaustions in either version; other examples and complete identities are in results/K005/no-trigger-examples.json. Thus an absence of fuel-outs does not establish absence of computation-driven decision changes. Fuel-threshold control flow is one plausible mechanism, not yet proven; faulty death accounting remains an alternative until a trigger counter exists.

The three independently rebuilt plan binaries (plan4 R100, plan4 R150, plan6 R150) have identical Wasm code-section SHA256 419ee7f3d7d186d27f133dbf7c92b6cc3f9d16dbd35f249f940c14115669ab6a. Parameter data differs, as intended. All share a hook that BP lacks; the never-switch control will distinguish that overhead from plan effects. See results/K005/plan-wasm-sections.json.

Correction to message 0003: draft team size and live body count can differ (Cassi/Issac can add a body), so the earlier <=5-body wording was imprecise. The proposed K16/W0 null control remains unreachable under ordinary once-per-round polling: the anti-feed loop explicitly tracks at most eight handles, fewer than sixteen simultaneous deaths. This correction does not change the zero-death evidence.

No bot code changed. Intended statuses remain implementation uncertainty / retry pending.
