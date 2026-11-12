# v80: recall interpretation, retreat resets and a Treasure opening

Research candidate, 2026-10-28. **No demonstrated strength gain over v76. Not submitted or activated.**

## Changes enabled

- Treat a newly seen/restarted enemy recall as cancellable combat behavior. Mark it genuinely channelling only after
  its channel time progresses between consecutive rounds. This corrects optimistic search/kiting assumptions against
  the five top teams that repeatedly start and cancel recalls.
- Before retreating, a melee champion with a ready movement-compatible attack reset can hit an adjacent enemy, reset,
  hit again and still move. Keep the cast allowance for a ready dash and do not reset onto a corpse.
- Replace the initial Prospector shards with same-stat Treasure shards. This increases later whole-game income;
  it does not close the income deficit by R300.

Defaults: `V80_RECALL=1`, `V80_RESET_FLEE=1`, `V80_TREASURE=1`; `V80_SHARE=0`, `V80_CAST_FLEE=0`, `V79_TF=0`.
The earlier `V80-*` run names refer to the recall-only control, not these final defaults. Final runs are `V80PKG-*`.

## Rejected changes

- Loose threat sharing reduced grouped splits but increased early deaths; v65 +2.3 deaths/game. A stricter sharing
  version also lost and did not improve pooled splits.
- Forcing a healthy melee nuke/stun before retreat increased casting but lost against v61 and v58. Movement-exclusive
  casts can make escape worse. This remains off; the retained reset preserves movement.

## Validation

Seed 24, 70 maps/both sides, **140 paired games per opponent per check**. Final combined candidate versus v76's
byte-identical `Q-*-v78` comparator (common seed 24 only):

| Opponent | Wins / v76 wins | Gem margin delta, 95% map-bootstrap interval | Deaths/game delta | Whole-game gold delta |
|---|---:|---:|---:|---:|
| v65 | 89 / 91 | -12 [-119,+109] | +0.5 | +419 |
| v61 | 101 / 95 | -3 [-92,+84] | -1.2 | +427 |
| v58 | 98 / 98 | +52 [-38,+138] | -1.2 | +764 |
| proxy per team | 109 / 112 | -5 [-94,+90] | -0.5 | +411 |

397/560 wins vs 396/560. Every margin interval includes zero. Candidate runtime faults: zero. Fuel exhaustion:
0.49–0.60/game. The four-opponent controls, isolated changes and package have separate result files in research/v75.

Pooled replay metrics use the original ladder split, contact and farming scripts plus `c_engage`'s early-fight clustering.
Contact casts rise about 0.6–1.1 percentage points versus recall-only; split and early-even-fight results remain mixed.
Farm gold/camp-target round remains about 3.8. Exact native R300 income changes -30/+2/+1/-6 gold versus recall-only;
R500 -26/+35/+90/+35. Do not describe later gold growth as fixing the early economy gap.

The existing 120 ladder replays were also audited for actual turn-start cooldowns, actions, capture transitions and
isolated payouts. The main remaining economy targets are larger-value opening captures and converting damaged camps
into secured rewards. The main remaining fight problem is inconsistent contact participation without sacrificing escape.

## Reproducibility and limits

Full analysis and commands: research/v75/TEAMFIGHT.md and HANDOFF_V80.md. Detailed final results:
`v80_package_vs_v76.txt`, `v80_package_replay_pooled.txt`, `v80_package_native_windows.txt`.

Clean official build matches the tested package byte for byte. Wasm SHA256:
`8d11f97cfa7269736330acf119e3c61b08123530220455a5f558aa51e0903c73`.
Review source archive and per-file manifest: artifacts/tmp/v67/v80-review/ (33 source files, 971,791 bytes).

Local lineage/proxy results cannot establish performance against the actual top 12. A paired v76/v80 ladder test is
the next proposed external measurement, conditional on explicit submission approval. No live selection is authorized.
