# Mimic research prototype

New executor and replay-trained policies; no v65 gameplay code. The core is shared with the WASI replay extractor
for byte-identical features. Per-team draft/item tables are reused from proxy.

Current weights: v9, trained on 1,177 replays after correcting post-recall-cancellation action permissions in both
runtime and extraction. Includes surviving-camp pathing, capture ownership, respawn availability and camp/crew
interactions. Native and WASI/SIMD core regressions pass; pooled and recall-trick parity have zero mismatches.

Not submitted. Still loses every game against v65 (240 games, -912.6 gems); six-arm margin ordering agrees with
14/15 existing ladder pairs, with substantial limitations. Full method, negative experiments, results and commands:
`research/mimic/README.md`.
