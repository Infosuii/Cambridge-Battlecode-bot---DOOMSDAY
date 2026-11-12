"""Enumerate every loss, overlapping observed failure flags, counterexamples and follow-up checks.

Flags are explicit triage thresholds, not causal proof or mutually exclusive labels.
"""
from collections import Counter,defaultdict
import csv
import statistics as st
from collect import ROOT,OUT,ME,read,save

RULES={
 'early-economy-deficit':'R200 collected gems <75% of opponent (opponent >=20), or earned gold <75% (opponent >=200).',
 'collection-deficit':'Final collected gems trail by >=150; includes pickups and recycled dropped gems, not pure farming.',
 'death-imbalance':'At least eight deaths and at least twice the opponent deaths.',
 'pvp-bag-loss':'At least 100 gems lost to champions and at least twice the opponent PvP gem losses.',
 'camp-mortality':'At least two camp deaths, accounting for >=25% of our deaths.',
 'zero-bank-with-resources':'Collected >=300 gems, submitted zero.',
 'unconverted-winning-total':'Final held gems plus banked gems >=1000, banked <1000. Does not establish safe bank access or a missed legal winning turn.',
 'conversion-deficit':'Collected >=90% of opponent, submitted <70% of opponent; opponent banked >=200.',
 'late-race-loss':'We banked >=800, opponent >=1000.',
 'zero-zero-gold-loss':'Both teams banked zero and outcome was the gold tiebreak.',
 'early-bruiser-mismatch':'Opponent bought >=5 Bruiser shards by R300 while we bought zero. Different builds can be valid; needs an intervention test.',
 'same-hero-economy-gap':'A shared Vesper/Marcella earns <60% of its opposite number, whose gold >=750.',
 'boss-gate-unresolved':'boss_battle zero-bank-with-resources and no camp-clear event for our team on group16.',
 'stampede-no-gems':'stampede: our collected gems zero and opponent collected >=160.',
 'fuel-exhaustion-observed':'At least one fuel-exhausted event; zero runtime faults does not make fuel exhaustion a proven cause.',
 'isolated-outnumbered-deaths':'At least two deaths with no ally and >=2 enemies within eight tiles in omniscient replay; visibility at decision time is not inferred.',
 'repeat-deaths-after-respawn':'At least three deaths within 60 rounds of a detected respawn (initial deployment excluded).',
 'near-home-death-pressure':'At least three deaths within Chebyshev15 of observed spawn tiles, with an enemy within eight.',
 'cooldowns-spent-on-camps-before-contact':'At least three visible-contact entries where an offensive ability remained on cooldown after an observed camp-targeted cast.',
 'contact-with-no-offensive-ready':'At least ten contact entries; >=35% have no offensive ability ready and exceed opponent rate by >=10 percentage points. Ready does not mean legal or useful.',
 'long-stationary-interval':'At least one >=80-round stationary interval outside spawn without observed movement, attacks, casts or bank/recall starts. Could be deliberate camping/capture; manual review required.',
}

def rate(n,d):return round(n/max(1,d),4)
def mean(xs):
    xs=list(xs);return round(st.fmean(xs),3) if xs else None

def main():
    rows=read(OUT/'metrics.json')
    fights={r['id']:r for r in read(OUT/'all-loss-fights.json')} if (OUT/'all-loss-fights.json').exists() else {}
    result=[]
    for r in rows:
        if r['win']:continue
        u,t=r['us'],r['them'];a,b=u['final'],t['final'];flags=[]
        add=lambda test,label:flags.append(label) if test else None
        cu,ct=u['curve'].get('200'),t['curve'].get('200')
        add(cu and ct and ((ct['collectedGems']>=20 and cu['collectedGems']<.75*ct['collectedGems']) or (ct['earnedGold']>=200 and cu['earnedGold']<.75*ct['earnedGold'])),'early-economy-deficit')
        add(b['collectedGems']-a['collectedGems']>=150,'collection-deficit')
        add(a['deaths']>=8 and a['deaths']>=2*b['deaths'],'death-imbalance')
        add(u['lostPvP']>=100 and u['lostPvP']>=2*t['lostPvP'],'pvp-bag-loss')
        add(u['deathContexts'].get('camp',0)>=2 and u['deathContexts'].get('camp',0)>=.25*a['deaths'],'camp-mortality')
        add(a['collectedGems']>=300 and a['submittedGems']==0,'zero-bank-with-resources')
        add(a['gems']+a['submittedGems']>=1000 and a['submittedGems']<1000,'unconverted-winning-total')
        add(a['collectedGems']>=.9*b['collectedGems'] and a['submittedGems']<.7*b['submittedGems'] and b['submittedGems']>=200,'conversion-deficit')
        add(a['submittedGems']>=800 and b['submittedGems']>=1000,'late-race-loss')
        add(a['submittedGems']==0 and b['submittedGems']==0 and r['endReason']=='tiebreak_gold','zero-zero-gold-loss')
        bru=lambda x:sum(v for k,v in x['buys300'].items() if k.startswith('Bruiser Shard'))
        add(bru(u)==0 and bru(t)>=5,'early-bruiser-mismatch')
        uh={h['name']:h for h in u['heroes']};th={h['name']:h for h in t['heroes']}
        add(any(th[h]['earnedGold']>=750 and uh[h]['earnedGold']<.6*th[h]['earnedGold'] for h in ['Vesper Vale','Marcella'] if h in uh and h in th),'same-hero-economy-gap')
        add(r['map']=='00stampede' and a['collectedGems']==0 and b['collectedGems']>=160,'stampede-no-gems')
        add(u['fuelOuts']>0,'fuel-exhaustion-observed')
        gate={}
        if r['map']=='01boss_battle':
            d=read(ROOT/r['source']['summary']);side='team'+r['side'].upper()
            gate={who:[dict(round=x['timestamp']['round'],champion=e['owner'].get('name')) for e in d['events'] if e['kind']=='campClear' and e['owner'].get('team')==team for x in e['entries'] if x['target'].get('id')==16] for who,team in [('us',side),('them','teamB' if side=='teamA' else 'teamA')]}
            add('zero-bank-with-resources' in flags and not gate['us'],'boss-gate-unresolved')
        audit=None
        f=fights.get(r['matchId'])
        if f:
            k=0 if r['side']=='a' else 1
            ds=[x for x in f['deaths'] if x['team']==k]
            ts=[x for x in f['deaths'] if x['team']!=k]
            isolated=sum(x['allies8']==0 and x['enemies8']>=2 for x in ds)
            repeats=sum(x.get('sinceRespawn') is not None and x['sinceRespawn']<=60 for x in ds)
            home=sum(x['spawnDist']<=15 and x['enemies8']>0 for x in ds)
            ss=f['spellAudit'][k];oo=f['spellAudit'][1-k]
            stalls=[x for x in f['stagnations'] if x['team']==k]
            add(isolated>=2,'isolated-outnumbered-deaths')
            add(repeats>=3,'repeat-deaths-after-respawn')
            add(home>=3,'near-home-death-pressure')
            add(ss['entryWithCampCooldown']>=3,'cooldowns-spent-on-camps-before-contact')
            add(ss['offensiveEntries']>=10 and rate(ss['entryNoOffensiveReady'],ss['offensiveEntries'])>=.35 and rate(ss['entryNoOffensiveReady'],ss['offensiveEntries'])>=rate(oo['entryNoOffensiveReady'],oo['offensiveEntries'])+.1,'contact-with-no-offensive-ready')
            add(bool(stalls),'long-stationary-interval')
            audit=dict(isolatedDeaths=isolated,repeatDeathsWithin60=repeats,nearHomeDeaths=home,ourDeathSamples=len(ds),theirDeathSamples=len(ts),
                nativeDeaths=a['deaths'],nativeOpponentDeaths=b['deaths'],spellUs=ss,spellThem=oo,stagnations=stalls,
                contactUs=f['teams'][k],contactThem=f['teams'][1-k])
        result.append(dict(matchId=r['matchId'],opponent=r['opponent'],rank=r['rank'],map=r['map'],engine=r['engine'],kind=r['kind'],arm=r['arm'],side=r['side'],
            createdAt=r['createdAt'],margin=r['margin'],flags=flags or ['needs-individual-outcome-review'],us=u,them=t,gateClears=gate,replayAudit=audit))
    save(OUT/'failure-ledger.json',result)
    counter=Counter(flag for r in result if r['engine']=='2.0.0' for flag in r['flags'])
    save(OUT/'failure-counts.json',dict(currentEngineLosses=sum(r['engine']=='2.0.0' for r in result),historicalLosses=sum(r['engine']!='2.0.0' for r in result),
        currentDecoded=sum(r['engine']=='2.0.0' and r['replayAudit'] is not None for r in result),counts=dict(counter),rules=RULES))
    with (OUT/'FAILURES.csv').open('w',newline='',encoding='utf8') as f:
        fields=['matchId','createdAt','opponent','rank','map','engine','kind','arm','side','margin','flags']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in result:w.writerow({k:';'.join(r[k]) if k=='flags' else r[k] for k in fields})
    lines=['# Every recorded loss: evidence ledger','',f'{len(result)} losses. Every listed match is included; historical engine1.0.3 losses are labeled separately. Overlapping flags are observations at explicit thresholds, not a claim that each flag caused the loss.','',
      '## Flag definitions and current-engine counts','','| Flag | Games | Observation / threshold |','|---|---:|---|']
    for flag,rule in RULES.items():lines.append(f'| {flag} | {counter[flag]} | {rule} |')
    lines+=['','## Match-by-match index','','| Match ID | Opponent | Map | Engine / arm | Banked ours–theirs | Deaths ours–theirs | Flags |','|---|---|---|---|---:|---:|---|']
    for r in result:
        a,b=r['us']['final'],r['them']['final']
        lines.append(f"| {r['matchId']} | {r['opponent']} | {r['map']} | {r['engine']} / {r['arm']} | {a['submittedGems']:.0f}–{b['submittedGems']:.0f} | {a['deaths']:.0f}–{b['deaths']:.0f} | {', '.join(r['flags'])} |")
    (OUT/'FAILURE_LEDGER.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print('Losses',len(result),'decoded',sum(r['replayAudit'] is not None for r in result),'current flags',dict(counter))

if __name__=='__main__':main()
