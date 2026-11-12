"""Reproduce the narrative's paired uncertainty, deathless counterexample and item-timing evidence."""
import random
import statistics as st
from collect import ROOT,OUT,read,save

def mean(xs):
    xs=list(xs);return st.fmean(xs) if xs else None

def main():
    rows=read(OUT/'metrics.json')
    rr=[r for r in rows if r['arm']=='v62c' and not r['win']]
    early=[r for r in rr if r['us']['curve']['100']['deaths']==0 and r['them']['curve']['100']['deaths']==0]
    timing={}
    for label in ['us','them']:
        first=[];appearances=0;details=[]
        for r in rr:
            d=read(ROOT/r['source']['summary'])
            team='team'+(r['side'].upper() if label=='us' else ('B' if r['side']=='a' else 'A'))
            cs=[c for c in d['champions'] if c['team']==team];appearances+=len(cs)
            for c in cs:
                rounds=[x['timestamp']['round'] for e in d['events'] if e['kind']=='buyItem' and e['owner'].get('team')==team and e['owner'].get('id')==c['id'] for x in e['entries'] if x['target']['name'].startswith('Bruiser')]
                if rounds:
                    first.append(min(rounds));details.append(dict(matchId=r['matchId'],champion=c['name'],firstRound=min(rounds)))
        timing[label]=dict(appearances=appearances,everBought=len(first),boughtBy300=sum(r<=300 for r in first),medianFirstConditionalOnBuying=st.median(first) if first else None,details=details)
    aa={(r['pair'],r['position']):r for r in rows if r['arm']=='v61'}
    bb={(r['pair'],r['position']):r for r in rows if r['arm']=='v62c'}
    keys=aa.keys()&bb.keys()
    assert len(keys)==120
    for k in keys:assert (aa[k]['opponent'],aa[k]['map'],aa[k]['side'])==(bb[k]['opponent'],bb[k]['map'],bb[k]['side'])
    delta=[mean(bb[k]['margin']-aa[k]['margin'] for k in keys if bb[k]['opponent']==o) for o in sorted({bb[k]['opponent'] for k in keys})]
    rng=random.Random(26);boot=sorted(mean(rng.choices(delta,k=len(delta))) for _ in range(5000))
    save(OUT/'paired-uncertainty.json',dict(comparison='v62c minus v61',games=len(keys),clusters=len(delta),cluster='opponent',meanMarginChange=mean(delta),percentileBootstrap95=[boot[125],boot[4874]],seed=26,resamples=5000))
    save(OUT/'additional-evidence.json',dict(cohort='known v62c duel losses',games=len(rr),firstBruiserTiming=timing,
        bothDeathlessAt100=dict(games=len(early),matchIds=[r['matchId'] for r in early],
            metrics={s:{f:mean(r[s]['curve']['100'][f] for r in early) for f in ['earnedGold','collectedGems']} for s in ['us','them']}),
        currentEngineDeathlessLosses=[r['matchId'] for r in rows if not r['win'] and r['engine']=='2.0.0' and r['us']['final']['deaths']==0]))
    print('paired games',len(keys),'deathless R100',len(early),'early Bruiser ours/theirs',timing['us']['boughtBy300'],timing['them']['boughtBy300'])

if __name__=='__main__':main()
