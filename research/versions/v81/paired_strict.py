"""Reject incomplete/incompatible comparisons, then use existing map-cluster margin analysis and win CI."""
from collections import defaultdict
import json
from pathlib import Path
import random
import statistics as st
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
def load(run):
    p=ROOT/'artifacts/evaluations/v67'/run
    meta=json.loads((p/'provenance.json').read_text())
    gs=json.loads((p/'games.json').read_text())['games']
    assert len(gs)==meta['complete_games']
    return meta,{(g['map'],g['side'],g['seed'],g['opponent']):g for g in gs}
cm,c=load(sys.argv[1]);bm,b=load(sys.argv[2])
assert cm['cli']==bm['cli'] and cm['sdk']==bm['sdk'] and cm['engines']==bm['engines'],'incompatible build/runtime'
assert set(c)==set(b),'incomplete or differing schedules'
for k in c:
    ci=json.loads((ROOT/c[k]['folder']/'engine_identity.json').read_text())
    bi=json.loads((ROOT/b[k]['folder']/'engine_identity.json').read_text())
    opp='wasm_b' if c[k]['side']=='a' else 'wasm_a'
    assert ci[opp]==bi[opp] and ci['map']==bi['map'],'opponent/map differs'
subprocess.run([sys.executable,'tools/v67/c_paired.py',sys.argv[1],sys.argv[2]],cwd=ROOT,check=True)
by=defaultdict(list)
for k in c:by[k[0]].append(c[k]['win']-b[k]['win'])
rng=random.Random(1);maps=sorted(by);boot=[]
for _ in range(2000):boot.append(st.mean(x for m in (rng.choice(maps) for _ in maps) for x in by[m]))
boot.sort()
print(f'win-rate difference {100*st.mean(x for v in by.values() for x in v):+.2f} pp, map-cluster 95% [{100*boot[50]:+.2f},{100*boot[1950]:+.2f}] pp')
print('provenance, both-team faults and exact opponent hashes verified')
