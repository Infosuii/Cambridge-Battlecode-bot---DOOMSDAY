# EXP-007 result

MEASURED: unsubmitted `codex-bruiser` release SHA-256 `75fe2a47d4af2b44b66b227615b444bbf34d13b2a047a4c311d0413b420dd981` reproduced in two independent build directories. `CODEX_BRUISER=0` reproduced platform v80 / repo v92's local release `5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47`. Source copies and conditions are reproduced by `prepare_bruiser.py`.

The [frozen development screen](BRUISER_DEV.json) has 256 matched cells, 16 maps, two own-score noise seeds, four opponents and both sides. Candidate 190 wins versus base 193: −1.172 pp, map-cluster bootstrap 95% CI [−3.125, +0.781]. Per-opponent deltas: v92 −4.688 pp, x3inv −1.562 pp, p65pack +1.562 pp, public-khiri 0. Fuel-outs 377 versus 378; one cell increased. Zero faults and zero round-one suspensions in either arm.

Native purchase/combination events show 699 versus 661 Bruiser shards and 126 versus 119 completed emblems. Neither arm bought any Bruiser shards by round 300. The mechanism moved late, but did not address the early item timing found in Discovery. The source deliberately keeps farming and mitigation purchases first; the result does not support a stronger timing claim.

Verdict: reject this frozen candidate under the pre-registered safety rule. No official-pool, full L1, L2, holdout or ladder gate is claimed. No upload, activation, duel b/c/z or quota use. A different item order would be a new structural experiment, not a retune of this result. Runtime work continues from development traces.
