"""Audit immutable inputs before accepting any score; summarize matched failure cells."""
import argparse, hashlib, json
from pathlib import Path

EVAL = Path(r'C:\projects\cambridge battlecode\battlecode part 2\jd-eval')

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def audit(name):
    out=EVAL/'runs'/name
    meta=json.loads((out/'run.json').read_text())
    frozen=json.loads((EVAL/'frozen.json').read_text())['bots']
    errors=[]
    for bot,want in meta['wasm'].items():
        if sha(frozen[bot]['wasm']) != want: errors.append('WASM changed: '+bot)
    for cell in meta['cells_list']:
        want=meta['map_sha256'][cell['map']]
        if sha(EVAL/'maps'/meta['maps']/(cell['map']+'.map26a')) != want: errors.append('map changed: '+cell['map'])
    results=json.loads((out/'results.json').read_text())
    if results['missing'] or results['failed']: errors.append('incomplete/failed results')
    if results['played'] != meta['games']: errors.append('game-count mismatch')
    games={ (g['arm'],g['opp'],g['map'],g['side']):g for g in results['games'] }
    regressions=[]
    diagnostic_codes={'cand':{},'base':{}}
    for cell in meta['cells_list']:
        key=(cell['opp'],cell['map'],cell['side'])
        a=games.get(('cand',*key)); b=games.get(('base',*key),a)
        if not a or not b: continue
        if a['seed'] != b['seed']: errors.append('randomness mismatch: '+str(key))
        if a['engine_hash'] != b['engine_hash'] or a['engine'] != '2.0.0': errors.append('engine mismatch: '+str(key))
        if a['map_hash'] != b['map_hash']: errors.append('engine map mismatch: '+str(key))
        for arm in ('cand','base'):
            st=out/'games'/('__'.join((arm,*key))+'.json')
            if not st.exists():continue
            codes=json.loads(st.read_text())['diagnostics']['codes']
            for code in codes:
                label=json.dumps(code,sort_keys=True)
                diagnostic_codes[arm][label]=diagnostic_codes[arm].get(label,0)+1
        df=a['fuel_outs']-b['fuel_outs']
        if df>0: regressions.append(dict(opp=key[0],map=key[1],side=key[2],extra_fuel_outs=df,score_delta=a['score']-b['score']))
    payload=dict(run=name,input_errors=sorted(set(errors)),paired=results['paired'],arms=results['arms'],
                 fuel_regression_cells=sorted(regressions,key=lambda x:-x['extra_fuel_outs']),
                 reported_diagnostic_codes=diagnostic_codes, action_rejection_coverage='Official diagnostic codes; silent API false returns are not separately instrumented',
                 decision='invalid' if errors else 'measured; promotion requires independent confirmation and behavior checks')
    (out/'integrity.json').write_text(json.dumps(payload,indent=2))
    print(json.dumps(payload,indent=2))
    if errors: raise SystemExit(1)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('name');audit(p.parse_args().name)

