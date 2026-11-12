"""Release-build incident reproduction: Homonoliths home capture timing and Islands stationary stalls."""
from pathlib import Path
import sys, json, collections
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run, read_native, STYLES
from project import ROOT, save
from sw08_followup import load
import stall_campaign

def first_caps(rows, home):
    out = collections.defaultdict(list)
    for r in rows:
        n = read_native(r['summary']); us = 'team' + r['side'].upper()
        caps = sorted(v['timestamp']['round'] for e in n['events'] if e['kind'] == 'gemCollection' and e['owner']['team'] == us
                      for v in e['entries'] if float(v['value']) and (v.get('target') or {}).get('kind') == 'campGroup' and v['target']['id'] == home[r['side']])
        out[r['candidate']].append((r['opponent'], r['side'], r['score'], caps[0] if caps else None, r['fuel']))
    return out

def main():
    pool = {m['name']: Path(m['file']) for m in load(ROOT / 'published-maps.json')}
    hom = run('v118-incident-homonoliths', ['hp01', 'v18H', 'v18HDR'], [pool['03homonoliths']], STYLES, workers=16)
    fc = first_caps(hom, {'a': 2, 'b': 3})
    summ = {k: {'score': sum(x[2] for x in v), 'games': len(v), 'median_first_home': sorted(x[3] or 9999 for x in v)[len(v) // 2],
                'captured_by_600': sum((x[3] or 9999) <= 600 for x in v), 'fuel': sum(x[4] for x in v), 'rows': v} for k, v in fc.items()}
    isl = run('v118-incident-islands', ['hp01', 'v18D', 'v18R', 'v18DR', 'v18HDR'], [pool['01islands']], STYLES, workers=16)
    stall_campaign.analyze('v118-incident-islands', isl)
    rep = json.loads((stall_campaign.WD / 'v118-incident-islands.json').read_text())
    isum = {}
    for k, v in rep.items():
        rs = [r for r in isl if r['candidate'] == k]
        isum[k] = {'score': sum(r['score'] for r in rs), 'fuel': sum(r['fuel'] for r in rs), 'counts': v['counts'],
                   'worst': [(s['end'] - s['start'], s.get('opponent'), s.get('side')) for s in v['worst'][:5]]}
    save(HERE / 'incident-checks.json', {'homonoliths': summ, 'islands': isum})
    for k, v in summ.items(): print('HOM', k, {x: v[x] for x in ('score', 'games', 'median_first_home', 'captured_by_600', 'fuel')})
    for k, v in isum.items(): print('ISL', k, v['score'], v['fuel'], v['counts'].get('trailing_quiet_pairs'), v['worst'])

if __name__ == '__main__':
    main()
