"""Copy a deliberately bounded review bundle into the repository."""
from pathlib import Path
import json
import shutil
from project import ROOT, save, sha

DEST = ROOT.parent / 'research/v113-integration-20261108'

REPORTS = (
    'starting-identities.json', 'campaign.json', 'spawn-policy-repair.json',
    'wasm-section-check.json', 'mechanism-activation.json', 'final-selection.json',
    'training/corrected-v113/complete.json', 'training/corrected-q15/complete.json',
    'retune/selection.json', 'teammate-features/all-development-selection.json',
    'qualification/protocol.json', 'qualification/result.json',
    'qualification-stall/selection.json', 'qualification-stall/protocol.json', 'qualification-stall/result.json',
    'stall-audit/live-report.json', 'stall-audit/incumbent-comparison.json',
    'stall-audit/fallthrough-development.json', 'stall-audit/targeted-development.json',
    'stall-audit/reference-development.json', 'stall-audit/clear-development.json',
    'stall-audit/sealed-stall-replay.json', 'stall-audit/sealed-v111-outcome-flips.json',
)
CODE = ('project.py', 'local_panel.py', 'merge.py', 'prepare_campaign.py', 'run_checks.py',
        'train_campaign.py', 'policy_rows.py', 'qa_records.py', 'recover_checkpoint.py',
        'blend_models.py', 'retune_campaign.py', 'retune_q15.py', 'teammate_features.py',
        'stall_recent.py', 'stall_replay.mjs', 'stall_campaign.py', 'stall_qualify.py',
        'qualify_campaign.py', 'ladder_transport.py', 'deliver_cycle.py',
        'inspect_stall_regressions.py', 'export_evidence.py')


def copy(src, dst):
    assert src.is_file() and src.stat().st_size < 20_000_000, src
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    assert sha(src) == sha(dst)


def main():
    result = json.loads((ROOT / 'qualification-stall/result.json').read_text())
    name = result['candidate']
    copy(ROOT / 'CAMPAIGN_NOTES.md', DEST / 'README.md')
    for f in REPORTS:
        copy(ROOT / f, DEST / 'evidence' / f)
    for f in CODE:
        copy(ROOT / f, DEST / 'tools' / f)
    for panel in ('stall-fallthrough-development', 'stall-targeted-development',
                  'stall-reference-development', 'stall-clear-development',
                  'stall-sealed-reference', 'stall-sealed-direct', 'stall-published-direct'):
        for f in ('manifest.json', 'scores.json'):
            copy(ROOT / 'panels' / panel / f, DEST / 'evidence/panels' / panel / f)
    for n in ('mx500', name):
        for f in ('source.zip', 'bot-injected.wasm', 'manifest.json'):
            copy(ROOT / 'release' / n / f, DEST / 'release' / n / f)
    copy(ROOT / 'training/initial-v113.pt', DEST / 'checkpoints/initial-v113.pt')
    copy(ROOT / 'training/q15-model-selection/mx500.pt', DEST / 'checkpoints/mx500.pt')
    receipts = {}
    for label in ('targeted', 'clear'):
        source = ROOT / f'stall-audit/{label}-activations.json'
        for event in json.loads(source.read_text()):
            k = f"{event['candidate']}:{event['map']}:{event['event']}"
            receipts[k] = receipts.get(k, 0) + 1
    save(DEST / 'evidence/stall-audit/activation-counts.json', receipts)
    save(DEST / 'SHA256.json', {p.relative_to(DEST).as_posix(): sha(p)
                               for p in sorted(DEST.rglob('*')) if p.is_file() and p.name != 'SHA256.json'})
    print(DEST)


if __name__ == '__main__':
    main()
