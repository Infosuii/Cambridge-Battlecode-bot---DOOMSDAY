# Diagnostic findings

The prescribed matrices and focused controls are complete and verified. Frozen K004–K006 bot source is commit `6efc360`, tree `1936131c445dcf87e1a1be3a8729ec3246bae16d`. Supplied K007 uses isolated commit `6ed38b9`; its off, BP and P150 binaries match the earlier binaries. Supplied WALKTAIL comparisons use a third isolated checkout at `2732245` and are reported separately. No production bot source was edited. All configuration changes use `--set`.

## 1. BUSHPRE can expose incomplete component identities

`World::pre_step` (`bots/x1/src/world.cpp`, approximately line 190) labels popped bush tiles before the active flood completes. `bush_cluster` (approximately line 246) immediately returns a popped tile's ID, while another tile in the same unfinished component can remain unknown when the lazy fuel floor stops work. `bush_ambush` and `hidden_here` compare IDs, so a known own ID and unknown same-component enemy ID can incorrectly imply cover.

`World::update` (approximately line 805) also discards visible wards whose component lookup is unknown. Later component completion does not itself repair `warded_clusters`; `World::warded` reads that cached vector. This creates a second coherence problem even if partial IDs are hidden.

Evidence: reachable source paths, [component inventory](K004/bush-component-diagnostic-maps.json), and [detailed report](../msgs/0005-bushpre-partial-label-invariant.md). Frequency in actual matches and contribution to specific losses have **not** been measured. BUSHPRE must therefore be treated as an information/behaviour change as well as a fuel optimization.

Smallest recommended correction: publish component IDs only after completion; retain unresolved observed ward positions and resolve them against complete current labels, or invalidate ward membership when components complete. Unknown component/ward information must not prove hidden status.

Targeted R0 after the main PC supplies a switchable repair: `01islands`, `02the-pack`, `02gift-wrapping`, both sides versus x2, BP+HIDEREC, with counters for partial-ID exposure, unresolved wards and hidden claims. Largest bush components are 358/113/152 tiles; BP recorded 5/29/1 fuel-outs over both x2 seeds. Proposed diagnostic/fix switches in message 0005 are **not implemented today**. First verify the repair-off BP SHA remains `ae786617849b65282edac38dbe374f9811110121bc485846b680cd99ebc67624`. Then use uninstrumented full gates for BP versus BP+repair and HIDEREC on the repaired baseline. Status: implementation uncertainty; repair and retest recommended.

## 2. HIDEREC can preserve a stale visibility snapshot

`Bot::play_turn` checks the hidden-recall exception before `w.update(round)`. `hidden_here` reads cached enemies and ward membership. A successful channel-preserving return skips that refresh, allowing the observation to remain older than one turn. A newly entering enemy or new ward can therefore be absent from the hidden predicate. This source path is independent of the partial-component issue.

Smallest correction: refresh enemy/ward evidence before granting the exception, or query current vision there and return conservative false for unresolved information. R0: begin recall while alone in a bush, then introduce an enemy into the same component or place a visible ward on the next turn; include an unfinished-component case. Record fresh/stale/unknown observations and exception triggers. Re-gate HIDEREC on the repaired BP baseline afterward. [Detailed source trace](../msgs/0006-hiderec-stale-world-before-guard.md). No repaired version or causal loss attribution is claimed. Status: implementation uncertainty / retry pending.

## 3. Changed games do not establish plan or anti-feed activation

Plan 4 R150 and plan 6 R150 differ from BP at R100 on 31/480 ladder/styled cells, before intended activation. Their Wasm code sections match plan 4 R100 (`419ee7f3d7d186d27f133dbf7c92b6cc3f9d16dbd35f249f940c14115669ab6a`); volatile parameters differ in data. They share a hook BP lacks. A plan-R5000 control retains that hook without intentional activation.

Anti-feed K3/W250 changes gameplay fields in 90/94 cells whose candidate total deaths are below three. K2/W150 has five outcome flips with zero deaths in both versions and identical native draft rosters; four also have zero fuel exhaustions. Per-turn history work interacting with budget-dependent decisions is plausible, but erroneous death accounting remains an alternative without trigger telemetry. No fuel exhaustion does not imply no computation-driven decision changes.

The focused K16/W0 anti-feed control retains history work with an unreachable same-round threshold under ordinary once-per-round polling: the loop tracks at most eight handles. It wins304/596 versus BP327 (-23), despite no intended activation. It is not identical compiled code to all tested thresholds. Never-switch plan R5000 wins329 (+2); no match reaches5000. Its Wasm code section matches R150 exactly. Both plan4/6 R150 and the joint actual/never-switch pair have **zero R100 checkpoint differences** on the480 real-map cells when compared against the corresponding common hook. This supports a common preactivation path at recorded checkpoints, without claiming exact decision-trace identity. [Control evidence](K005/activation-controls.json), [native examples](K005/no-trigger-examples.json), [Wasm sections](K005/plan-wasm-sections.json), [correction concerning body counts](../msgs/0004-no-trigger-native-evidence.md). Dedicated trigger counters are the smallest recommended future diagnostic. Status: activation attribution uncertain; no strategic rejection.

## 4. Joint caution has a negative measured interaction

The job-selected AF5/W400 gives 335/596 wins, plan4/R150 gives 347, BP gives 327, and their joint setting gives 306. The factorial contrast is `306 - 335 - 347 + 327 = -49` wins, paired map interaction -8.22 percentage points, bootstrap 95% [-14.60, -1.85]. This is an exploratory selected-setting interaction, not evidence that every combination fails.

Code inspection finds shared territory controls and compounded aggression scaling: plan4 multiplies aggression by 0.65, AF by 0.6 (joint 0.39), with AF retreat/danger changes as well. This supports a conflict hypothesis but does not prove its mechanism. Joint never-switch wins328; actual joint306 changes -22, while plan actual347 versus never-switch329 changes +18. The hook-controlled interaction is therefore **-40 wins**, paired -6.71 pp, map95 [-12.58,-0.84]. A common plan hook alone does not explain that selected-setting non-additivity. AF/history/compilation context still differs between strata. Recommended R3 work: verify triggers, then jointly tune caution/thresholds instead of multiplying independently selected settings. Status: requires joint tuning / retry pending.

## 5. Siege floors change cache use as well as fuel

The LOS cache is accepted when `complete || !X1_SIEGE_STRICT`. With default strict=0, a higher floor can leave a partial LOS union in use. Nonzero SIEGEFUEL also selects a different cache-write path, so its result is not a pure numeric fuel-floor effect. BP+strict wins325/596; siege65+strict319, versus original BP327/siege65 319. The factorial is +2 wins, map95 [-1.17,1.85] pp: **no demonstrated interaction** and no rescue of the regression. These controls do not repair the algorithm or prove partial-cache use harmless. Next useful R0 is a partial/full LOS-union diagnostic on changed decision cases; avoid a large finer-floor grid first. Status: dependency uncertainty / retry pending.

## 6. Secure/burst-hold ablations and fuel attempts

On P3, secure gives318 versus320 (-2), burst-hold316 (-4), both314 (-6). The observed per-map win interaction is zero, interval [0,0]. This supports additivity of the measured win changes on this fixed pool, not universal independence. Secure's TTK estimate counts allies within attack range+2 while the bonus comment describes a kill this round. That inherited reach approximation may be optimistic about allies who must still move; it is not a confirmed bug. Smallest R0: log ready/in-range contributing damage and inspect secure-bonus decisions on changed loss cases, then retest a switchable correction if needed. HIDEREC and bush dependencies above apply to both stacks.

The preregistered P4/R150+siege45 retry gives340/596 versus BP327 (+13), real fuel212 versus BP206 and parent227. It reduces the parent fuel cost but still fails styled/fuel R1; the declared rule correctly stops before extra validation. Original K007's P100/WR12 gives412/716 (+19), real fuel185 versus BP206 and passes exploration, then loses8 wins in standard robustness (456 versus464). Fresh131 versus120 is inconclusive and does not erase that failure. WALKTAIL supplied attempt2/addendum results are kept in [K009](K009.md), with separate source and map pools. None of these results is a successful repair claim for the bush/visibility issues.

## Interpretation and limits

R0 binary activation is checked through effective source and SHA identity. Intended triggering remains weaker where dedicated counters are absent. R1 measures the specified frozen implementation. K005 grids supply meaningful variants; targeted controls and the declared feature-specific fuel attempt provide focused follow-ups. Main PC retains integration/rejection authority. No feature is permanently rejected from one failed gate.

All uncertainty intervals use maps as sampling units, clustering sides/opponents. They are descriptive and unadjusted for grid selection or related map templates. The frozen 40-map holdout reuses official components; its maximum bush component is 80, so it does not independently cover the largest official forests. An optional forest extension failed structural generation and produced no claimed evaluation set. No ladder activity or external bot upload occurred.
