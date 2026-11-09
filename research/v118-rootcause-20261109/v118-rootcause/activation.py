"""Debug activation counts of the v118 fixes (H home siege, D relaxed bridge dash, R route veto) on chosen maps."""
from pathlib import Path
import sys, json, collections
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run, STYLES
from project import ROOT, save
from sw08_followup import build_from, replace
from policy_rows import stdout
import candidates

def trace(files):
    candidates.compose('HDR')(files)
    c = files['bot.cpp'].decode()
    c = replace(c, '        if (jumped) {\n            bridge_hold = 0;\n',
                '        if (jumped) {\n            debug_block({ std::printf("DXD %d %d\\n", round, slot); });\n            bridge_hold = 0;\n')
    c = replace(c, '    mode = "home-siege";\n', '    mode = "home-siege";\n    debug_block({ std::printf("HSACT %d %d\\n", round, slot); });\n')
    files['bot.cpp'] = c.encode()

def main(names):
    build_from('dx09', 'hp01', trace, debug=True)
    pool = {Path(p).stem: Path(p) for p in json.loads((HERE / 'map-split.json').read_text())['holdout'] + json.loads((HERE / 'map-split.json').read_text())['dev']}
    maps = [pool[n] for n in names]
    rows = run('v118-activation-' + '-'.join(names)[:40], ['dx09'], maps, STYLES, workers=18, debug=True)
    out = collections.defaultdict(collections.Counter)
    for r in rows:
        for l in stdout(r['replay_bundle'], r['side']).splitlines():
            t = l.split(' ', 1)[0]
            if t in ('DXD', 'HSACT', 'RV_ROUTE_BLOCK'): out[r['map']][t] += 1
        out[r['map']]['games'] += 1; out[r['map']]['score'] += r['score']
    print(json.dumps(out))
    return out

if __name__ == '__main__':
    main(sys.argv[1].split(','))
