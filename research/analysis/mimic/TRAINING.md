# Mimic training report

Rows: artifacts/local-only/mimic/rows-v9; held out: matches with number % 10 == 0.

| Decision | Train rows | Held-out rows | Accuracy, pooled | Accuracy, per team | NLL pooled / per team | Rule baseline |
|---|---:|---:|---:|---:|---:|---:|
| obj | 427638 | 47043 | 0.613 | 0.621 | 1.222 / 1.192 | 0.539 |
| move | 1480327 | 162196 | 0.670 | 0.683 | 1.418 / 1.369 | 0.463 |
| tgt | 2246881 | 253546 | 0.937 | 0.943 | 0.235 / 0.219 | 0.764 |
| recall | 7814819 | 853513 | 0.988 | 0.988 | 0.054 / 0.054 | always no: 0.988 |
| trib | 89850 | 9452 | 0.676 | 0.715 | 0.603 / 0.558 | always no: 0.487 |
| cast | 2441719 | 265087 | 0.909 | 0.919 | 0.248 / 0.219 | 0.885 |
