"""Render the frozen model's evaluation; never fit or select on test results."""
import json
from deep_preflight import ROOT

STUDY = ROOT / 'research/deep-2026-10-28'


def main():
    model = json.loads((STUDY / 'WINPROB_MODEL.json').read_text(encoding='utf-8'))
    lines = ['# Win probability model', '',
             '**Predictive association.** The model uses 385 examined games only: 231 train,77 calibration,77 internal test. Each game has equal total weight; snapshots never cross folds. The external 165 hands-off games remain untouched.', '',
             'The feature plan and game split were committed before fitting (871a933). A symmetric logistic regression has no intercept and uses ten fixed-scale team-difference features. L2 strength was selected from {0.01,0.1,1,10} using calibration log-loss; a positive scalar temperature was fitted on those same calibration games. Test games were used once for the following evaluation.', '',
             '| Partition | Games | Snapshots | Model log-loss | Brier | ECE (10 bins) | Bank-only log-loss | 0.5 log-loss |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for split, r in model['metrics'].items():
        m = r['model']
        lines.append(f"| {split} | {r['games']} | {r['snapshots']} | {m['log_loss']:.4f} | {m['brier']:.4f} | {m['ece10']:.4f} | {r['bank_only']['log_loss']:.4f} | {r['constant_half']['log_loss']:.4f} |")
    lines += ['', f"Test model-minus-bank log-loss, complete-game bootstrap95% (2,000 draws,77 games): {model['test_model_minus_bank_logloss_game_bootstrap95']}. Lower is better. This interval does not model shared-map/opponent dependence.", '',
              '## Test calibration', '', '| Prediction band | Game-weighted mass | Mean prediction | Observed win fraction |', '|---|---:|---:|---:|']
    for b in model['metrics']['test']['model']['bins']:
        if b['weight']:
            lines.append(f"| {b['lo']:.1f}–{b['lo']+.1:.1f} | {b['weight']:.3f} | {b['predicted']:.3f} | {b['observed']:.3f} |")
    lines += ['', '## Test timing slices', '', '| Rounds | Games | Snapshots | Model log-loss | Brier | Bank-only log-loss |', '|---|---:|---:|---:|---:|---:|']
    for name, r in model['metrics']['test']['round_slices'].items():
        lines.append(f"| {name} | {r['games']} | {r['snapshots']} | {r['model']['log_loss']:.4f} | {r['model']['brier']:.4f} | {r['bank_only']['log_loss']:.4f} |")
    lines += ['', '## Interpretation and limits', '',
              'WINPROB_MODEL.json includes scales, coefficients, lambda scores, temperature and every calibration table. Coefficients are conditional on correlated features: a small negative middle-income or vision coefficient does not establish that either hurts winning. Inventory purchase cost is not combat power; unspent gold is omitted under the registered feature plan, so a shop visit can create a sharp prediction change.', '',
              'The internal split shares maps and opponents across folds. This is not an unseen-map performance estimate. Calibration reuses 77 games for lambda and temperature, and early-game predictions remain weak. R0 is included with its actual state; terminal rows are excluded. Last-50 income uses the last retained row at/before the start of that window (up to four extra rounds after R300).', '',
              'Four scientific checks pass: neutral probability/calibration-bin accounting, exact team-exchange complement, no future-resource access in an earlier feature, and invariance to duplicated snapshots when per-game weights are preserved.', '',
              'moments.json records the five largest disjoint positive approximately ten-round drops per examined DOOMSDAY loss. Nonterminal states are used at both ends. Feature changes are apportioned by integrating the logistic derivative along the observed segment; the components sum to the model change but are not causal credit. Single events, cards, shares and later fix priorities require that distinction.', '',
              'MOMENT_SAMPLE.json fixes 105 cards: 90 loss moments from 65 losses (20 Learn,30 Climb,15 Other) and 15 distinct control wins (2 Learn,9 Climb,4 Other). Actor-own pre-window observations and rule-based expectations are frozen separately before subsequent actions are exposed. The focus actor is selected from the pre-window state by largest bag, then lower HP fraction, then physical ID. This can omit a different victim in a team-level swing.']
    (STUDY / 'P3_WINPROB.md').write_bytes(('\n'.join(lines) + '\n').encode())


if __name__ == '__main__':
    main()
