# What the champion could see before a casualty

Read actual champion-perspective snapshots in 216 baseline pool matches. At most one observation per body per ten rounds, with at least one visible enemy within eight tiles. Label a casualty when the body was killed by a champion within eight rounds of the snapshot. Training used x3mf bodies vs v86h and x1bru on one group of layouts. The strict test uses 2,603 x3mf observations against v92 on twelve layouts absent from training.

| Signals | ROC AUC | Average precision | Alert precision | Casualties flagged |
| --- | ---: | ---: | ---: | ---: |
| Lanchester difference | 0.783 | 0.132 | 16.0% | 19.7% |
| Health, numbers, distance, bag and Lanchester difference | 0.911 | 0.509 | 47.7% | 53.0% |
| Also cooldowns, support reach, camp damage and shared area pressure | 0.925 | 0.488 | 49.2% | 54.7% |

The alert threshold was frozen at the 95th percentile of training scores. The compact model flagged 130 of the 2,603 strict test observations, including 62 of 117 casualties. The larger model's small changes do not justify extra host queries. These labels describe what happened under the existing policy. The model does not tell us whether fleeing would have saved the champion. Carrier-specific evidence is thin (six strict-test casualties), so measure the actual response against an inactive build and keep independent opponents for confirmation.

See [contact-prognosis.json](contact-prognosis.json) for coefficients, splits and metrics.
