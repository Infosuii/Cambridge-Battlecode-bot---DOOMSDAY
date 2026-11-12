"""Four-arm weights comparison for the repaired bot (HDR) on maps the training never saw.

incumbent  hp01 (v117)
frozen     v18HDR (v117 network, repaired behavior)
retuned    v18HDRm (50% native-parameter blend of initial and trained network; mx500-style damping)
fresh      v18HDRt (best trained checkpoint by the trainer's own selection maps)
Evaluation cells: 19 selection maps x 9 styles x 2 sides + 113 stability generated maps x 5 styles x 2 sides.
"""
from pathlib import Path
import os, sys, json, subprocess, collections, random, shutil
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
os.environ.update(TRAIN_SOURCE='v18HDR', TRAIN_CAMPAIGN_NAME='v118-hdr', TRAIN_PREFIX='v18t',
                  TRAIN_PLAN=str(HERE / 'training-plan.json'))
import torch
import train_v118 as T
from local_panel import run, STYLES
from project import ROOT, save, sha
import dev_panel

WD = ROOT / 'training/v118-hdr'


def weights():
    complete = json.loads((WD / 'complete.json').read_text())
    best = complete['selected']
    it = best['iteration']
    trained_pt = WD / f'student_{it}.pt' if it else None
    if it == 0:  # trainer kept the initial weights: use the best later checkpoint as the trained arm anyway
        evals = [json.loads((WD / f'eval_{i}.json').read_text()) for i in (2, 4, 6) if (WD / f'eval_{i}.json').exists()]
        it = max(evals, key=lambda e: e['score'])['iteration']; trained_pt = WD / f'student_{it}.pt'
    original = torch.load(ROOT / 'training/initial-v113.pt', map_location='cpu', weights_only=True)
    current = torch.load(trained_pt, map_location='cpu', weights_only=True)
    mixed = {k: (v * 0.5 + current[k] * 0.5 if v.is_floating_point() else v) for k, v in original.items()}
    mpt = WD / 'blend_050.pt'; mh = WD / 'blend_050.h'; torch.save(mixed, mpt)
    subprocess.run([sys.executable, '-P', str(T.LAB / 'nn_export.py'), str(mpt), 'student', str(mh)], check=True, capture_output=True)
    th = WD / f'student_{it}.h'
    T.actor('v18HDRt', th); T.actor('v18HDRm', mh)
    info = {'trained_iteration': it, 'trained_pt_sha256': sha(trained_pt), 'trained_header_sha256': sha(th),
            'blend_pt_sha256': sha(mpt), 'blend_header_sha256': sha(mh), 'trainer_selected': best}
    save(HERE / 'weights-arms.json', info); return info


def main():
    info = weights()
    plan = json.loads((HERE / 'training-plan.json').read_text())
    select = [Path(p) for p in plan['maps']['dev']]
    gen = sorted((ROOT / 'arena/maps_v113_stability').glob('*.map26a'))
    C = ['hp01', 'v18HDR', 'v18HDRm', 'v18HDRt']
    a = run('v118-arms-select', C, select, STYLES, workers=18)
    b = run('v118-dev-c-generated-arms', ['v18HDRm', 'v18HDRt'], gen, dev_panel.DEV_STYLES, workers=18)
    old = json.loads((ROOT / 'panels/v118-dev-c-generated/results.json').read_text())
    rows = a + b + [r for r in old if r['candidate'] in ('hp01', 'v18HDR')]
    s = dev_panel.summary(rows)
    save(HERE / 'weights-arms-summary.json', {'weights': info, 'summary': s})
    for k, v in s.items(): print(k, {x: v[x] for x in ('games', 'score', 'paired_diff', 'faults', 'fuel')})


if __name__ == '__main__':
    main()
