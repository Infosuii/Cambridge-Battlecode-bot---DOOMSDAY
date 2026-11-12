"""Frozen offline ablations and training audits; no training or deployment."""
import copy
import json
import random
import shutil
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch
import train

PARENT = train.ROOT
PHASE = PARENT / 'phase2-two-hours'
ROOT = PARENT / 'diagnosis-phase2'
ROOT.mkdir(exist_ok=True)
train.ROOT = ROOT

def read(path): return json.loads(Path(path).read_text())
def save(name, data): train.write(ROOT/name, data)

def metrics(rows):
    return dict(games=len(rows),wins=sum(r['win'] for r in rows),
        margin=float(np.mean([r['gems']-r['opponent_gems'] for r in rows])),
        fuel=sum(r['fuel'] for r in rows),faults=sum(r['faults'] for r in rows))

def audit():
    protocol=read(PHASE/'protocol.json')
    partitions={Path(p).stem:k for k in ['training_maps','selection_maps','final_holdout_maps'] for p in protocol[k]}
    rows=read(PHASE/'evaluation/all-maps-vs-original.json')['rows']
    results={k:metrics([r for r in rows if partitions[r['map']]==k]) for k in set(partitions.values())}
    sides={s:metrics([r for r in rows if r['side']==s]) for s in ['A','B']}
    totals=Counter(); fuel_rounds=[]; with_fuel=[]; without_fuel=[]; maps=[]
    for r in rows:
        d=read(Path(r['folder'])/'summary.json'); own='team'+r['side']; other='teamB' if own=='teamA' else 'teamA'
        for c in d['champions']:
            prefix='ours_' if c['team']==own else 'opponent_'
            for k in ['deaths','earnedGold','collectedGems','submittedGems']:
                totals[prefix+k]+=int(c['metrics'].get(k,0))
        for e in d['events']:
            if e['kind']=='fuelExhausted' and e['owner']['team']==other:
                totals['opponent_fuel']+=len(e['entries'])
        (with_fuel if r['fuel'] else without_fuel).append(r)
    for m in sorted({r['map'] for r in rows}):
        rr=[r for r in rows if r['map']==m];maps.append(dict(map=m,**metrics(rr)))
    maps.sort(key=lambda r:r['margin'])
    events=[json.loads(x) for x in (PHASE/'progress.jsonl').read_text().splitlines()]
    selections=[e for e in events if e['stage']=='selection']
    windows={}
    for lo,hi in [(0,600),(600,1200),(1200,1800),(1800,2400),(2400,3600),(3600,5400),(5400,7201)]:
        subset=[e for e in selections if lo <= (float(__import__('datetime').datetime.fromisoformat(e['time']).timestamp())-float(__import__('datetime').datetime.fromisoformat(read(PHASE/'training-clock.json')['started_utc']).timestamp())) < hi]
        if subset:windows[f'{lo//60}-{hi//60}min']=dict(evaluations=len(subset),mean_wins=float(np.mean([e['score']['wins'] for e in subset])),max_wins=max(e['score']['wins'] for e in subset))
    updates=[e for e in events if e['stage']=='training_update']
    best_iteration=read(PHASE/'report.json')['selected_iteration']
    best_event=next(e for e in selections if e['iteration']==best_iteration)
    initial=read(PHASE/'evaluation/selection-initial.json')['rows']
    best=read(PHASE/f'evaluation/selection-{best_iteration:04d}.json')['rows']
    pool={}
    for i,label in enumerate(['original','v47','first-hour','proxy-0','proxy-1']):
        def take(rr):return [r for r in rr if f'-o{i}-' in Path(r['folder']).name]
        pool[label]=dict(initial=metrics(take(initial)),selected=metrics(take(best)))
    cp=torch.load(PHASE/'checkpoints/best.pt',map_location=train.DEVICE,weights_only=False)
    policy=train.Policy().to(train.DEVICE);policy.load_state_dict(cp['policy'])
    sample=[]; traced_games=0
    for iteration in [780,792,804,1800,1818]:
        for folder in sorted((PHASE/f'runs/train-{iteration:04d}').glob('*')):
            if not (folder/'summary.json').exists():continue
            side=folder.name.rsplit('-',1)[-1]
            records,_=train.bundle_records(folder,side)
            if records:traced_games+=1;sample.extend(records)
    observations=np.stack([r['obs'] for r in sample]);counts=np.array([r['n'] for r in sample]);actions=np.array([r['pick'] for r in sample])
    x=torch.tensor(observations,device=train.DEVICE);n=torch.tensor(counts,device=train.DEVICE)
    with torch.no_grad():
        logits=policy(x,n);p=logits.softmax(-1);argmax=logits.argmax(-1)
        residual=policy.residual(x);valid=torch.arange(8,device=train.DEVICE)[None,:]<n[:,None]
        p_base=p[:,0].cpu().numpy()
        # Constant inputs or saturated corrections can make a larger network unhelpful.
        observations_report=dict(games=traced_games,decisions=len(sample),
            observed_stochastic_off_base_rate=float(np.mean(actions!=0)),
            selected_policy_argmax_off_base_rate=float((argmax!=0).float().mean()),
            selected_policy_mean_off_base_probability=float((1-p[:,0]).mean()),
            selected_policy_residual_abs_mean=float(residual[valid].abs().mean()),
            selected_policy_residual_near_limit_fraction=float((residual[valid].abs()>3.8).float().mean()),
            mean_candidate_count=float(np.mean(counts)),
            note='Recorded states from five sampled training batches; retrospective selected-policy evaluation, not a fresh win test.')
    # Map-cluster bootstrap for the observed 36/80 result vs original.
    rng=np.random.default_rng(20261024)
    map_wins=np.array([np.mean([r['win'] for r in rows if r['map']==m]) for m in sorted({r['map'] for r in rows})])
    ci=np.quantile(map_wins[rng.integers(0,len(map_wins),size=(20000,len(map_wins)))].mean(1),[.025,.975]).tolist()
    result=dict(partitions=results,sides=sides,champion_totals=dict(totals),
        with_fuel=metrics(with_fuel),without_fuel=metrics(without_fuel),worst_maps=maps[:10],
        selection_windows=windows,selection_evaluations=len(selections),
        best_iteration=best_iteration,best_time=best_event['time'],
        selection_by_opponent=pool,trace_audit=observations_report,
        direct_original_winrate_map_bootstrap_95ci=ci,
        warning='Fuel/win association is descriptive; ablation is required for causation.')
    save('audit.json',result)
    print(json.dumps(result,indent=2),flush=True)
    return protocol

def ablations(protocol):
    release=PHASE/'release/bot_neural/src'
    variants=['campnet-off','zero-residual']
    maps=sorted(map(Path,protocol['training_maps']+protocol['selection_maps']+protocol['final_holdout_maps']))
    frozen=dict(variants=variants,maps=[str(p) for p in maps],opponent_sha256=train.sha(PHASE/'opponents/original.wasm'),
                release_sha256=train.sha(PHASE/'release/bot_neural.wasm'),purpose='Diagnostic only: no checkpoint selection or promotion',fuel='Official default release')
    if (ROOT/'protocol.json').exists() and read(ROOT/'protocol.json')!=frozen:raise ValueError('Diagnostic schedule changed')
    save('protocol.json',frozen)
    summary={}
    for variant in variants:
        src=ROOT/variant/'src'
        if not src.exists():shutil.copytree(release,src)
        if variant=='campnet-off':
            p=src/'common.h';s=p.read_text();p.write_text(s.replace('#define A2_CAMPNET 1','#define A2_CAMPNET 0',1))
        else:
            p=src/'neural_weights.h';s=p.read_text();start=s.index('inline constexpr float kWeights[321]');s=s[:start]+'inline constexpr float kWeights[321] = {};\n}\n';p.write_text(s)
        wasm=train.compile_bot(src,ROOT/f'builds/{variant}.wasm',20)
        score,_=train.evaluate_artifact(wasm,variant,maps,[PHASE/'opponents/original.wasm'],20)
        summary[variant]=score
        print('ABLATION',variant,json.dumps(score),flush=True)
    trained=read(PHASE/'evaluation/all-maps-vs-original.json')
    comparisons={}
    for variant in variants:
        rr=read(ROOT/f'evaluation/{variant}.json')['rows'];lookup={(r['map'],r['side']):r for r in rr}
        paired=[]
        for r in trained['rows']:
            b=lookup[r['map'],r['side']]
            paired.append(dict(map=r['map'],side=r['side'],trained_win=r['win'],control_win=b['win'],trained_fuel=r['fuel'],control_fuel=b['fuel'],
                trained_margin=r['gems']-r['opponent_gems'],control_margin=b['gems']-b['opponent_gems']))
        comparisons[variant]=dict(summary=summary[variant],paired=paired)
    save('ablations.json',dict(trained=trained['summary'],controls=comparisons))

if __name__=='__main__':
    protocol=audit();ablations(protocol)
