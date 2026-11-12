from pathlib import Path
import sys, json
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run
from project import ROOT, save
from sw08_followup import build_from, load, replace
from policy_rows import stdout
import trace_islands2

def trace(files):
    trace_islands2.trace(files)
    c = files['bot.cpp'].decode()
    anchor = '        debug_block({ if (DXT) std::printf("TDB'
    assert c.count(anchor) == 1
    c = c.replace(anchor, (HERE / 'tdg_snippet.inc').read_text() + anchor)
    files['bot.cpp'] = c.encode()

def main():
    build_from('dx08', 'hp01', trace, debug=True)
    pool = {m['name']: Path(m['file']) for m in load(ROOT / 'published-maps.json')}
    m = pool['01islands']
    sched = [('dx08', o, str(m), s) for o, s in [('teammate_john_nnfinal', 'a'), ('teammate_max_gx', 'a'), ('ref_x3ctr', 'a')]]
    rows = run('v118-islands-trace3', ['dx08'], [m], ['teammate_john_nnfinal', 'teammate_max_gx', 'ref_x3ctr'], workers=4, debug=True, schedule=sched)
    for r in rows:
        print('==', r['opponent'])
        print('\n'.join(l for l in stdout(r['replay_bundle'], r['side']).splitlines() if l.startswith('TDG'))[:3000])

if __name__ == '__main__':
    main()
