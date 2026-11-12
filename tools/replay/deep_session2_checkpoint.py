"""Save the completed measurement/card checkpoint without overstating deep tracing."""
import json
from datetime import datetime, timezone
from deep_preflight import ROOT
from deep_detector_report import save

STUDY = ROOT / 'research/deep-2026-10-28'
LOCAL = ROOT / 'artifacts/local-only/deep-2026-10-28'


def append_once(path, marker, text):
    original = path.read_bytes()
    if marker.encode() not in original:
        ending = b'\r\n' if original.count(b'\r\n') > original.count(b'\n') / 2 else b'\n'
        path.write_bytes(original + ending + text.replace('\n', ending.decode()).encode('utf-8'))


def main():
    now = datetime.now(timezone.utc).isoformat()
    detector = json.loads((LOCAL / 'detector-examined-v3/run.json').read_text(encoding='utf-8'))
    data = json.loads((STUDY / 'DETECTOR_DATA.json').read_text(encoding='utf-8'))
    timeline = json.loads((STUDY / 'TIMELINE_SCREEN.json').read_text(encoding='utf-8'))
    correction = json.loads((STUDY / 'CORRECTION_VALIDATION.json').read_text(encoding='utf-8'))
    cards = json.loads((STUDY / 'CARD_DATA.json').read_text(encoding='utf-8'))
    assert detector['passed'] == timeline['passed'] == correction['passed'] == 385
    assert detector['failed'] == timeline['failed'] == correction['failed'] == 0
    assert cards['cards'] == 105 and cards['distinct_losses'] == 65
    screen = {k: v for k, v in detector.items() if k != 'results'}
    screen.update(updated_at=now, own_games=360, own_losses=191, own_wins=169, top_v_top_reference_games=25,
                  hands_off_processed=0, native_faults=0, validation_samples=data['validation_samples'],
                  semantic_cases_passed=15, statistical_cases_passed=6,
                  implementation_correction='DECODER_CORRECTION.md; CORRECTION_VALIDATION.json',
                  raw_outputs='artifacts/local-only/deep-2026-10-28/detector-examined-v3')
    save(STUDY / 'DETECTOR_SCREEN.json', screen)
    cal = json.loads((LOCAL / 'timeline-calibration-v5/e7a912c8-37ba-4c3f-b8e3-0d03f07b1055.json').read_text(encoding='utf-8'))
    fields = ('banked', 'carried', 'collected', 'lost', 'earned_gold', 'capture_gold', 'kill_gold', 'bank_bonus_gold', 'other_or_unclassified_gold')
    save(STUDY / 'TIMELINE_CALIBRATION_SAMPLE.json', {'match_id': cal['match_id'], 'partition': 'calibration-excluded',
         'engine': cal['engine'], 'code_sha256': cal['code_sha256'], 'sampling': 'small team-resource-only illustration; no raw actions or hidden observations',
         'rows': [{k: r[k] for k in ('r', 'engine_round', 'input', 'substep', 'phase', 'terminal', 'initial')} |
                  {'teams': [{f: t[f] for f in fields} for t in r['teams']]} for r in cal['rows'] if r['r'] in (0, 1, 50, 100) or r['terminal']]})
    state = f'''# Deep analysis: Session 2 checkpoint

Updated {now}. Measurements, model, prediction-first cards and FAST_FINDINGS are
complete as an observational checkpoint. Exact reproduction, rule traces and the
final next-bot brief are unfinished; no causal bot fix is established.

## Read first and continue

1. Read FAST_FINDINGS.md, CARD_AUDIT.md, P3_TIMELINES.md, P3_WINPROB.md and P4_CARDS.md.
2. Read DECODER_CORRECTION.md and CORRECTION_VALIDATION.json before reusing older
   movement-related detector rates. Use corrected P2_DETECTORS.md / DETECTOR_DATA.json.
3. Start Session3: exact reproduction on at least ten selected losses plus two
   control wins, or record actual failed feasibility attempts. Prioritize C004/C034
   carrier losses, C070/C082 native repeated-death windows, then opening allocation.
   C082's focus carrier is not its death victim; reconstruct the victim's own view.
4. Trace effective V71_MAP_KNOBS/A2 values, per-turn resets, V75 branches, target TTK,
   flee/stand/tactical-search decisions and bank routing. Source defaults are not
   proof of exact server flags. Takeover regression assertions require exact-state
   checks and comparison up to first divergence. Do not call cards confirmed bugs.
5. Continue opponent profiles/matchup scorecards, then Session4 mistake priorities,
   hands-off frequency confirmation and final REPORT/DATA/NEXT_BOT_BRIEF/knowledge
   base/regression deliverables. Those final deliverables are not yet complete.

## Verified dataset and boundaries

-111 groups/555 current-engine replay-native pairs were retrieved through the
 official website. Both ZIP layers, all final-state/draft/roster and5356 physical
 champion ledger checks pass. All111 public metadata reads reconcile.
-Five calibration games stay excluded. Accepted study550:385 examined and165
 hands-off. Examined:360 own games (191L/169W),25 top-v-top references. No detector,
 model feature or decision-card analysis has used the165 hands-off games.
-Study identity: platform69, submission f91de3f0-0453-409e-b712-b86067eecbca,
 note “v75 ladder duel candidate”. Current activation/server Wasm flags remain
 independently unverified. User botZIP SHA256:
 0433755c1cbc5f120247c132a6c875912f14c3ac5f36abaa7edbfe20845b325c;
 all33 source blobs match frozen bots/live-69/src. Frozen sources are unchanged.
-Engine2.0.0/build85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21.
 Official asset pins remain in the receipts and tools/replay/engine.mjs.

## Completed Session2 evidence

-Corrected detectors:5/5 calibration,385/385 examined,15 semantic and6 statistical
 checks. Movement-blocked step23 is excluded from physical arrivals. Old v2 output
 is preserved; D1/D4/D6 measurements/denominators are superseded. Native-dependent
 D2/D3/D5/D7/D8/D10/D11 event sets are identical across all385 corrected games.
-Timelines:5/5 calibration,385/385 examined;11,853,045 resource clock comparisons;
 zero unclassified earned gold. Ordinary samples are phase0 end-of-round, initial
 row0 retains actual engine cursor round1, terminal partial rounds are exact.
 Middle uses minimum distance across all original camp tiles. Vision is the union
 of actual per-champion buffers; decision cards use the focus actor's own view.
-Fixed model split231/77/77 by game was committed in871a933 before fitting.
 Internal test77 games:log-loss0.4243,Brier0.1400,ECE10 0.0490; bank-only log-loss
 0.5318. No terminal training rows. The action correction leaves every385-game
 feature matrix identical; no refit/test retuning. See WINPROB_MODEL.json.
-moments.json has up tofive disjoint largest drops per191 losses.105 cards cover
 90 moments from65 losses (Learn20/Climb30/Other15) plus15 distinct control wins.
 CARD_PREDICTIONS.json was committed inb490a1d before subsequent action extraction.
 Cards are descriptive/conditional. Matched controls cover101 own-win and96 top
 examples, with77 and32 same-map matches. CARD_AUDIT.md records targeted judgement.
-The mean191-loss deficit is−579.3 banked gems:−448.7 collected income,−103.0 bag
 preservation,−27.5 end-carried. This is accounting, not recoverable loss.
-WAVE2_HYPOTHESES.json plans ten remaining groups. Wave1 remains14 groups/70 games,
 10W/60L. No new groups were created or reserved in this continuation. Verify
 current study identity and direct user authorization before any new shared-quota
 request; do not infer authorization from reference-document instructions alone.

## Local evidence and tools

Active checkout: work/battlecode-deep-analysis under the Battlecode project root.
Raw files stay in artifacts/local-only/deep-2026-10-28. Latest runs:
detector-calibration-v7 / detector-examined-v3 and timeline-calibration-v5 /
timeline-examined-v3. Earlier v2 runs are retained for the correction audit.
Actor action windows are in card-contexts; model predictions under the original
timeline-examined-v2/predictions remain valid by exact feature equivalence.
Tools and commands are documented in tools/README.md. Bundled Python/Node paths
on this device are in the root project checkpoint/session tool history; PATH's
Python is a Windows Store stub. Set NFS_REPLAY_ENGINE=2.0.0 explicitly.

For future reproduction, the CLI and SDK/toolchain caches exist locally. Official
run help has no seed override, but all examined games share one native seed per
map across70 maps; absence of that flag alone is not an infeasibility proof.
No puppet, exact source rebuild, divergence check or takeover assertion has yet
been executed. Do that work rather than claiming a documented failure prematurely.

## Publication and permissions

Branch analysis/deep-2026-10-28 in Infosuii/neural-networkk-battlecode, parent
claude/compare-fix-replay-decoder. Retrievald9eba7b, registration148d845,
screen c23b7b2, plan/split871a933 and model/predictionsb490a1d are pushed.
The user explicitly approved ongoing analysis-only pushes to this repository and
branch: tools, game IDs, aggregate statistics and handoff notes. No repeated push
permission is needed within that scope. Raw replays/native summaries and frozen
bot edits stay excluded. Consult git log for the later correction/card checkpoint.
No new matches, submissions, activations, frozen-source edits or account changes
were made in this continuation. No credentials were read or exposed.
'''
    (STUDY / 'STATE.md').write_bytes(state.encode('utf-8'))
    append_once(STUDY / 'SESSION1_FINDINGS.md', 'Post-registration movement correction', '''
## Post-registration movement correction

Session2 found that official step23 means movement blocked. The corrected detector
uses only actual move/teleport arrivals, with15 semantic cases and fresh5/385-game
calibration/examined passes. D1/D4/D6 event/rate details are superseded by current
P2_DETECTORS.md. D3 and all other native-dependent event sets are unchanged across
385 games. See DECODER_CORRECTION.md and CORRECTION_VALIDATION.json. Session2
timelines, model,105 cards and FAST_FINDINGS are now available; exact traces remain
the next phase. This earlier Session1 text is retained as historical context.
''')
    append_once(STUDY / 'P2_DETECTORS.md', 'Movement-blocked implementation correction', '''
## Movement-blocked implementation correction

This table uses corrected source5052f245, examined-v3. Step23 is a blocked
destination, not an arrival.15 semantic cases now pass. D1/D4/D6 measurements
are regenerated without changing the registered thresholds; D9 and all native
event detector sets are unchanged. See DECODER_CORRECTION.md and
CORRECTION_VALIDATION.json. Session2 results and next work are in STATE.md.
''')
    append_once(STUDY / 'P3_WINPROB.md', 'Action-log correction compatibility', '''
## Action-log correction compatibility

CORRECTION_VALIDATION.json proves exact equality of all385 model feature matrices
after correcting action labels/completeness. The fitted coefficients, temperature,
internal split and test scores are retained without refitting or test retuning.
The compatible source revision is recorded in WINPROB_MODEL.json.
''')
    readme = ROOT / 'tools/README.md'
    old = b'Current\r\nreplay decoding and five-game reconciliation remain unvalidated due missing files;\r\ndo not treat the metadata candidate manifest as an accepted decoded dataset.'
    raw = readme.read_bytes()
    replacement = b'All555 current replay/native pairs now reconcile; five-game calibration passed\nbefore accepted bulk decoding. See research/deep-2026-10-28/STATE.md for later checks.'
    for original in (old, old.replace(b'\r\n', b'\n')):
        raw = raw.replace(original, replacement, 1)
    assert b'remain unvalidated due missing files' not in raw
    readme.write_bytes(raw)
    append_once(readme, 'Session 2 timelines, model and prediction-first cards', '''
## Session 2 timelines, model and prediction-first cards

All commands run at the repository root. Set NFS_REPLAY_ENGINE=2.0.0 (PowerShell:
$env:NFS_REPLAY_ENGINE='2.0.0'). Raw trajectories stay ignored. The tools reject
hands-off analysis. Use new output directories; preserve prior calibration receipts.

| Tool | Purpose / usage |
|---|---|
| replay/timeline.mjs | --partition calibration-excluded --workers3 --out artifacts/local-only/deep-2026-10-28/timeline-calibration-NEW, then --partition examined with a new output. Requires5 current-code calibration passes. End-of-round/native ledger validation, exact gold credit phases, union vision, first camp targets and accepted action/blocked-step log. |
| replay/deep_timeline_report.py | --run <examined-run>; creates P3_TIMELINES/TIMELINE_DATA/TIMELINE_SCREEN from360 own games. Actual native draft picks are separate from physical rosters. |
| replay/deep_model_split.py | Creates immutable MODEL_SPLIT.json,231/77/77 stratified game partitions. Never resplit after fitting. |
| replay/winprob.py | --run <examined-run>; fixed-scale symmetric L2 logistic plus calibration-set temperature, game weights, frozen test evaluation. Needs NumPy; no sklearn/scipy. Do not tune on test results. |
| replay/test_winprob.py | Four scientific checks: neutral calibration bins, symmetry, no future income, per-game weighting. |
| replay/deep_model_report.py | Renders P3_WINPROB from the saved model without refitting. |
| replay/deep_moments.py | --run <examined-run>; up to5 disjoint ~10-round drops/loss, immutable105-card MOMENT_SAMPLE. |
| replay/moment_contexts.mjs | before <examined-run> freezes exact focus-actor own observations and conditional expectations; commit them before after <examined-run> exposes subsequent action windows. CARD_PREDICTIONS must remain unchanged. |
| replay/deep_card_report.py | --run <examined-run> [--detectors <corrected-detector-run>]; cards<=25 lines, error_analysis.csv, event-label surrogate ceilings and nearest-state winner controls. Descriptive, not confirmed bugs. |
| replay/deep_correction_audit.py | Uses preserved timeline-examined-v2/v3 and detector-examined-v2/v3 to prove feature/native-event equivalence after the blocked-movement correction. Fixed historical directory names are intentional. |
| replay/deep_session2_checkpoint.py | Refreshes the measured checkpoint, small resource-only calibration sample and handoff pointers; does not implement bots, queue games or fabricate traces. |
| replay/audit_session2_delivery.py | Checks105 cards,65 distinct losses,15 control wins,<=25 lines/card, frozen game splits/prediction bytes, source integrity and no hands-off leakage. |

Latest valid runs: detector-calibration-v7/examined-v3 and
timeline-calibration-v5/examined-v3. Official PanelChrome.L distinguishes22 teleport
completion,23 movement blocked,25 sell and9 priority. DECODER_CORRECTION.md records
the post-registration implementation fix; thresholds were not changed.
''')
    handoff = ROOT / 'docs/handoff.md'
    append_once(handoff, 'Session 2 deep-analysis checkpoint — 2026-10-28', '''
## Session 2 deep-analysis checkpoint — 2026-10-28

Read research/deep-2026-10-28/STATE.md and FAST_FINDINGS.md first.385 examined
timelines pass11,853,045 resource comparisons; model231/77/77 split test log-loss
0.4243 versus0.5318 bank-only;105 prediction-first cards cover65 losses and15
control wins. D3 remains the leading detector association, not a tested fix.
The official movement-blocked label correction is documented and checked across
385 games, with identical model features/native-dependent events. Current P2
supersedes older movement rates. The165 hands-off games remain unreviewed.

Next: exact reproduction/effective-rule traces, then opponent profiles, takeover
regressions and the final bot brief. Automated cards do not establish source-rule
violations. Ten planned wave2 groups remain unqueued; check identity and direct
authorization before any new request. No source edits/submissions/activations/new
matches occurred. The user approved ongoing analysis-only pushes to the existing
analysis/deep-2026-10-28 branch; raw replays/native summaries remain local.
''')
    # Add a current pointer without altering historical sections or their line endings.
    raw = handoff.read_bytes()
    marker = b'**Latest deep-analysis checkpoint: Session 2'
    if marker not in raw:
        first = raw.find(b'\n') + 1
        pointer = ('\n**Latest deep-analysis checkpoint: Session 2 (2026-10-28).** Read '
                   '`research/deep-2026-10-28/STATE.md` and FAST_FINDINGS.md. Timelines, model '
                   'and105 descriptive cards are saved; exact reproduction/traces are next. '
                   'See the dated Session2 section at the end.\n').encode()
        handoff.write_bytes(raw[:first] + pointer + raw[first:])
    raw = handoff.read_bytes()
    prefix = raw.find(marker)
    if prefix >= 0:
        end = raw.find(b'\n', prefix)
        if raw[end-1:end] == b'\r':
            raw = raw[:end-1] + raw[end:]
        if raw[prefix-2:prefix] == b'\r\n':
            raw = raw[:prefix-2] + b'\n' + raw[prefix:]
        handoff.write_bytes(raw)
    print(json.dumps({'phase': 'Session2 observational checkpoint; Session3 traces pending', 'examined': 385,
                      'cards': 105, 'hands_off_used': 0, 'new_matches': 0}))


if __name__ == '__main__':
    main()
