# v58 coordinated economy research — not submitted

Base: frozen v57, live platform version56. No new mechanism passed the user's acceptance gate. Every V58 switch
remains0. The final disabled source builds byte-identically to v57 (`914b49a0…`); v57's source hashes are unchanged.
SDK/CLI3.0.5 and engine1.0.3 were retained; Sprint3 patch notes were ignored as requested.

Twenty complete development screens (28 maps, both sides, seeds1–4) produced4480 games with exact coverage and
zero native faults on both teams. One failed build was excluded, as were eight diagnostic games. No original or
fresh holdout was opened, no match groups queued and no submission made. The 15-map pool has previous v55-v57
exposure; it is not an untouched generalization set.

The research adds repeated shared clearing jobs, bounded single-owner reward handoffs, carry Treasure shopping,
a coupled supported-map draft, parallel clears, visible-power survival, action ordering, wards and timed altar
locks behind disabled switches. All64 shared bits were already used; the director reserves the unused physical
sixth claim only on teams with3–5 bodies, preserving sighting/event bits. Public draft metadata supplies the roster;
private C++ statics are never treated as shared team memory. Six-body teams and maps beyond48 groups fall back.

The final research variant D14 allowed middle camps with an enemy-side travel cost. It scored107/224 (47.8%),
+5.3 raw gems, Bayesian+12.1/P(>0)=.564; map-cluster95%[−136.7,+163.5]. P(>−50)=.775 misses incomplete-loop
non-inferiority. Earlier variants also failed; none was accepted. These are development screens, not confirmation.

| D14 mechanism | Candidate | Same-game v57 | Target |
|---|---:|---:|---:|
| Team capture gold by250 | 677.7 | 722.9 | ≥900 — missed |
| Elk-size captures by250 | 2.99 | 2.75 | ≥3.5 — missed |
| Carry capture-gold share | 44.7% | 25.9% | ≥40% — reached |
| Vesper-only Treasure median | 134 | 254 | ≤120 — missed |
| All-map carry Treasure median, censored at501 | 147 | 261.5 | ≤120 — missed |
| Deaths/game | 13.80 | 14.33 | −30% — only3.7% fewer |
| Fuel-outs/game | 1.790 | 1.589 | ≤2 — reached |

Vesper was drafted in160/224 games; its own capture share averaged44.9%. Earlier D6/D13 Vesper drafts reached
Treasure at median114.5/110 and capture share45.5%/45.8%, but their total income/strength/fuel failed. First large
capture timing also reached median43–48. The unresolved bottleneck is repeat throughput and pressure, despite
getting one carry online. No~1000-gold economy configuration existed to freeze as a Claudus proxy; optional denial
and carry hunting were therefore not implemented.

Survival reduced deaths modestly but lost too much pressure. Extra stationary casts displaced basic attacks;
post-walk resets and post-dash basics were small or neutral. More wards increased placements without reducing
deaths. More altar locks did not measurably delay completed enemy tributes. None is enabled. D13's diagnostic
planner maximum fell from22,497 to13,367 fuel, but normal-game fuel-outs still exceeded2; this does not certify D14.

No12-seed confirmation, independent active-candidate release build or bundle was justified after failed screens.
The release record lists failed and unrun conditions. Submission authorization remains conditional on every gate;
this research does not establish rank25 capability or superiority to Claudus. The user decides the next approach.

Exact snapshots, patches and hashes: `artifacts/claude_ops/V58_EXPERIMENTS.json`. Reconstruct with
`python tools/reproduce_v58.py <label> <new repo-local directory>`. All21 patches, including invalid D2, passed exact
reconstruction. Full commands, per-variant evidence, incremental comparisons and analysis limits are in
`artifacts/claude_ops/V58_BUILD_LOG.md`, `V58_RESULTS.md` and `V58_RELEASE.json`. Raw replays/builds remain local-only.


## Combined research checkpoint and patch migration (2026-10-26)

The user resumed work and requested whole-package testing, followed by Sprint3 updates and fresh v57 loss review. Round2 and round3 results supersede the stopped round1 status above. Four combined packages each completed672 games on engine1.0.3 with zero native faults. Core reached363 wins/672 (+75.4 raw gems; Bayes+101.1/P=.976), but cluster95%[-1.05,+152.96] and fuel2.299/game miss the final gate. No upload or holdout. Read V58_R2_RESULTS.md and V58_R3_RESULTS.md under artifacts/claude_ops. Exact patches are indexed in V58_EXPERIMENTS.json.

Next authorized work: preserve this checkpoint, migrate verified official CLI/SDK4.0.0 and engine2.0.0, isolate build caches by environment, implement the new item/balance rules, and analyze recently downloaded v57 losses. The core package is a development base only. Frozen v57 source remains unchanged and live as platform56.
