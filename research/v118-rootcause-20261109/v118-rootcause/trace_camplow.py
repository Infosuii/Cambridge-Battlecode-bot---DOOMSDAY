"""Camp-death trace: every turn a champion below 40% health is inside the range of a live camp of an alive group."""
from pathlib import Path
import sys, json, collections
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run, STYLES
from sw08_followup import build_from
from policy_rows import stdout
import candidates

def trace(files):
    candidates.compose('HDR')(files)
    c = files['bot.cpp'].decode()
    anchor = '    PROF_CHECK("decide");\n'
    c = c.replace(anchor, anchor + (HERE / 'camplow_snippet.inc').read_text())
    files['bot.cpp'] = c.encode()

if __name__ == '__main__':
    build_from('dx11', 'hp01', trace, debug=True)
    pool = {Path(p).stem: Path(p) for k in ('dev', 'holdout') for p in json.loads((HERE / 'map-split.json').read_text())[k]}
    maps = sys.argv[1].split(',')
    rows = run(sys.argv[2] if len(sys.argv) > 2 else "v118-camplow-trace", ["dx11"], [pool[m] for m in maps], STYLES, workers=18, debug=True)
    modes = collections.Counter(); per_map = collections.defaultdict(collections.Counter); ctype = collections.Counter(); ex = []
    for r in rows:
        last = {}
        for l in stdout(r['replay_bundle'], r['side']).splitlines():
            if not l.startswith('CAMPLOW'): continue
            p = l.split()
            key = (p[2], int(p[1]) // 3)  # episode per champion per 3 rounds
            if key in last: continue
            last[key] = 1
            modes[p[4]] += 1; per_map[r['map']][p[4]] += 1; ctype[p[10]] += 1
            if len(ex) < 30: ex.append([r['map'], r['opponent'], r['side']] + p[1:])
    out = {'games': len(rows), 'modes': modes.most_common(), 'camp_types': ctype.most_common(), 'per_map': {m: c.most_common(6) for m, c in per_map.items()}, 'examples': ex}
    json.dump(out, open(HERE / 'camplow-trace.json', 'w'), indent=1)
    print(json.dumps({k: out[k] for k in ('games', 'modes', 'camp_types', 'per_map')}))
