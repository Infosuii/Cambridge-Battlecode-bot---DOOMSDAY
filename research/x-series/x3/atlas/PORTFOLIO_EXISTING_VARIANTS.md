# Per-category choice among the existing 30 variants does not transfer (3 Nov 2026)

Data: counter search (30 variants = base, 13 team plans, 16 knob vectors; x 4 opponents x 86 maps x 2 sides).
Categories: research/x3/atlas/categories.json (8 rule-based categories). Tool: tools/mapatlas/portfolio_eval.py.

| margin to switch | in-sample | unseen maps | unseen opponents | both unseen |
|---|---|---|---|---|
| 0 | +24 | -29 | -14 | -27 |
| 2 | +22 | -23 | -16 | -27 |
| 4 | +15 | -19 | -13 | -21 |

(688 games, base 418.) With one category for all maps the base is the best variant. Conclusion: the existing
variants differ only by game-to-game chaos, not by strategy that depends on map type; a portfolio needs genuinely
different strategies (built from what the 2000+ teams that beat us did: tools/ladder/losses_recent.py, loss_study.py).
