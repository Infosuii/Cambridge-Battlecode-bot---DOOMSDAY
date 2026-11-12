"""Banking trace: champions carrying >= 60 gems, every 5 rounds (mode, win_now, nn gate, altar distance, stuck/off timers)."""
from pathlib import Path
import sys, json
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run, STYLES
from project import ROOT
from sw08_followup import build_from
from policy_rows import stdout
import candidates

def trace(files):
    candidates.compose('HDR')(files)
    c = files['bot.cpp'].decode()
    anchor = '    PROF_CHECK("decide");\n'
    assert c.count(anchor) == 1
    c = c.replace(anchor, anchor + (HERE / 'bag_snippet.inc').read_text())
    files['bot.cpp'] = c.encode()

def main(label, maps, opps):
    build_from('dx10', 'hp01', trace, debug=True)
    pool = {Path(p).stem: Path(p) for k in ('dev', 'holdout') for p in json.loads((HERE / 'map-split.json').read_text())[k]}
    rows = run(label, ['dx10'], [pool[m] for m in maps], opps, workers=18, debug=True)
    return rows

if __name__ == '__main__':
    rows = main('v118-bag-trace', sys.argv[1].split(','), sys.argv[2].split(','))
    for r in rows:
        if r['score'] == 0:
            lines = [l for l in stdout(r['replay_bundle'], r['side']).splitlines() if l.startswith('BAG')]
            print('==', r['map'], r['opponent'], r['side'], r['rounds'], len(lines))
            print('\n'.join(lines[-25:]))
