"""Auditable native-summary comparison; cohort labels use saved group IDs, not guessed activation times."""
import collections as co
import csv
import json
from pathlib import Path
import statistics as st
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collect import ROOT,OUT,ME,read,save

MARKS=[100,200,300,500,800]
METRICS=['earnedGold','collectedGems','submittedGems','deaths','kills','gems','championDamageDone','monsterDamageDone','spentGold','gold']

def avg(xs):
    xs=[x for x in xs if x is not None]
    return round(st.fmean(xs),2) if xs else None

def at(t,r):
    # Native sampled timelines: sample 0 is the opening, then one sample per round.
    cursor=0
    for run in t['runs']:
        cursor+=run['duration']
        if r<cursor:return float(run['value'])
    return float(t['runs'][-1]['value']) if t['runs'] else 0

def stats(d,team):
    cs=[c for c in d['champions'] if c['team']==team]
    events=[(e,x) for e in d['events'] if e['owner'].get('team')==team for x in e['entries']]
    banks=[x for e,x in events if e['kind']=='gemSubmission']
    deaths=[x for e,x in events if e['kind']=='death']
    final={f:sum(float(c['metrics'].get(f,0)) for c in cs) for f in METRICS}
    return dict(final=final,
        curve={str(r):{f:sum(at(t,r) for t in d['championTimelines'] if t['owner'].get('team')==team and t['metric']==f) for f in METRICS} for r in MARKS if r<=d['match']['roundsCompleted']},
        lostPvP=sum(float(x['value']) for e,x in events if e['kind']=='gemLoss' and x['context']=='champion'),
        lostPvE=sum(float(x['value']) for e,x in events if e['kind']=='gemLoss' and x['context']!='champion'),
        earlyDeaths=sum(x['timestamp']['round']<300 for x in deaths),
        deathContexts=dict(co.Counter(x['context'] for x in deaths)),
        bankCount=len(banks),firstBank=min((x['timestamp']['round'] for x in banks),default=None),
        bankMean=avg(float(x['value']) for x in banks),
        firstDeath=min((x['timestamp']['round'] for x in deaths),default=None),
        firstClear=min((x['timestamp']['round'] for e,x in events if e['kind']=='campClear'),default=None),
        earlyCampClears=sum(e['kind']=='campClear' and x['timestamp']['round']<300 for e,x in events),
        faults=d['diagnostics']['botFaults'].get(team,0),
        fuelOuts=sum(e['kind']=='fuelExhausted' for e,x in events),
        heroes=[dict(name=c['name'],**{f:float(c['metrics'].get(f,0)) for f in METRICS},items=c['itemsBought']) for c in cs],
        buys300=dict(co.Counter({name:sum(float(x['value']) for e,x in events if e['kind']=='buyItem' and x['timestamp']['round']<=300 and x['target']['name']==name) for name in {x['target']['name'] for e,x in events if e['kind']=='buyItem' and x['timestamp']['round']<=300}})))

def summarize(rows):
    out=dict(n=len(rows),wins=sum(r['win'] for r in rows),losses=sum(not r['win'] for r in rows))
    for side in ['us','them']:
        out[side]={f:avg(r[side]['final'][f] for r in rows) for f in METRICS}
        out[side].update({f:avg(r[side][f] for r in rows) for f in ['lostPvP','lostPvE','earlyDeaths','bankCount','firstBank','firstClear','earlyCampClears']})
        out[side]['curve']={str(m):dict(n=sum(str(m) in r[side]['curve'] for r in rows),**{f:avg(r[side]['curve'][str(m)][f] for r in rows if str(m) in r[side]['curve']) for f in METRICS}) for m in MARKS}
    return out

def main():
    manifest=read(OUT/(sys.argv[1] if len(sys.argv)>1 else 'manifest.json'))
    metas={m['matchId']:m for m in read(OUT/'finished-top25.json')}
    ladder={t['teamId']:t for t in read(OUT/'ladder.json')['teams']}
    groupmap={}
    for p in [OUT/'duel-plan-snapshot.json']:
        d=read(p)
        for arm,a in d.get('arms',{}).items():
            for i,g in enumerate(a.get('groups',[])):
                groupmap[g]=(arm,a['version'],i)
    rows=[]
    for entry in manifest['matches']:
        m=metas[entry['matchId']];d=read(ROOT/entry['summary'])
        us=next(t for t in m['teams'] if t['teamId']==ME);opp=next(t for t in m['teams'] if t['teamId']!=ME)
        u='team'+us['side'].upper();t='teamB' if u=='teamA' else 'teamA'
        arm,version,pair=groupmap.get(m['groupId'],('unattributed',None,None))
        a,b=stats(d,u),stats(d,t)
        rows.append(dict(matchId=m['matchId'],createdAt=m['createdAt'],map=m['map'],kind=m['kind'],groupId=m['groupId'],position=m['position'],
            arm=arm,platform=version,pair=pair,side=us['side'],opponent=opp['name'],rank=ladder[opp['teamId']]['rank'],
            engine=d['match']['engineVersion'],win=us['result']=='win',rounds=d['match']['roundsCompleted'],endReason=m['endReason'],
            margin=a['final']['submittedGems']-b['final']['submittedGems'],us=a,them=b,source=entry))
    rows.sort(key=lambda r:r['createdAt'])
    save(OUT/'metrics.json',rows)
    current=[r for r in rows if r['engine']=='2.0.0']
    losses=[r for r in current if not r['win']]
    cohorts={'all-current-engine':current,'losses-current-engine':losses,'wins-current-engine':[r for r in current if r['win']],
             'post-1811-losses':[r for r in losses if r['createdAt']>='2026-10-26T18:11:03Z']}
    for arm in ['v60','v61','v62c']:
        cohorts[arm]=[r for r in current if r['arm']==arm]
        cohorts[arm+'-losses']=[r for r in losses if r['arm']==arm]
    for kind in ['ranked','unranked']:
        cohorts[kind]=[r for r in current if r['kind']==kind]
    summary={k:summarize(v) for k,v in cohorts.items()}
    save(OUT/'aggregates.json',summary)
    with (OUT/'match-index.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['matchId','createdAt','opponent','rank','map','kind','arm','platform','side','engine','win','rounds','margin']
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in rows)
    lines=['# Recent losses to top teams — 26 October 2026','',
      'Window: 25 October 20:24:26 to 26 October 20:24:26 London time (UTC). Top teams means ranks 1–25 in the saved current ladder, including development teams. Ranks at match time are unavailable.',
      '',f"Collected {len(metas)} finished games, including {sum(not (next(t for t in m['teams'] if t['teamId']==ME)['result']=='win') for m in metas.values())} losses. Native summaries available for {len(rows)}; see manifest.json for download errors. Engine 2.0.0 analysis includes {len(current)} games ({len(losses)} losses). Older-engine matches remain in the index and are excluded from current conclusions.",
      '', 'This pool mixes bot versions, maps, and deliberately strong challenge opponents. It measures the selected encounters, not an unbiased ranked win rate. Known version labels come from duel group IDs; unattributed games are never assigned a version from creation time alone.',
      '', '## Coverage and known versions','', '| Cohort | Wins / games | Mean gem margin |','|---|---:|---:|']
    for label,rr in cohorts.items():
        if not label.endswith('-losses') and label not in ['losses-current-engine','wins-current-engine','post-1811-losses']:
            lines.append(f"| {label} | {sum(r['win'] for r in rr)}/{len(rr)} | {avg(r['margin'] for r in rr)} |")
    lines+=['','## Opponents (current engine)','', '| Rank | Opponent | Wins / games | Losses | Mean margin |','|---:|---|---:|---:|---:|']
    for name in sorted({r['opponent'] for r in current},key=lambda n:min(r['rank'] for r in current if r['opponent']==n)):
        rr=[r for r in current if r['opponent']==name]
        lines.append(f"| {rr[0]['rank']} | {name} | {sum(r['win'] for r in rr)}/{len(rr)} | {sum(not r['win'] for r in rr)} | {avg(r['margin'] for r in rr)} |")
    for cohort in ['losses-current-engine','post-1811-losses','v60-losses','v61-losses','v62c-losses']:
        d=summary[cohort]
        lines+=['',f"## {cohort} ({d['n']} games)",'','| Per game | DOOMSDAY | Opponent |','|---|---:|---:|']
        for field in ['earnedGold','collectedGems','submittedGems','deaths','kills','championDamageDone','monsterDamageDone','lostPvP','lostPvE','earlyDeaths','bankCount','firstBank','firstClear','earlyCampClears']:
            lines.append(f"| {field} | {d['us'][field]} | {d['them'][field]} |")
        lines+=['','| Round | Games reaching round | Gold ours / theirs | Collected ours / theirs | Banked ours / theirs | Deaths ours / theirs |','|---:|---:|---:|---:|---:|---:|']
        for r in MARKS:
            a,b=d['us']['curve'][str(r)],d['them']['curve'][str(r)]
            lines.append(f"| {r} | {a['n']} | {a['earnedGold']} / {b['earnedGold']} | {a['collectedGems']} / {b['collectedGems']} | {a['submittedGems']} / {b['submittedGems']} | {a['deaths']} / {b['deaths']} |")
    lines+=['','## Same-map, same-side duel comparisons','', 'These compare known arms on the same planned opponent/map/side slots. Enemy submissions may change between groups; this is not proof of the opponent binary being fixed.','']
    for a,b in [('v60','v61'),('v61','v62c'),('v60','v62c')]:
        aa={(r['pair'],r['position']):r for r in current if r['arm']==a};bb={(r['pair'],r['position']):r for r in current if r['arm']==b}
        keys=aa.keys()&bb.keys();pairs=[(aa[k],bb[k]) for k in keys if (aa[k]['map'],aa[k]['side'],aa[k]['opponent'])==(bb[k]['map'],bb[k]['side'],bb[k]['opponent'])]
        lines.append(f"- {a} → {b}, {len(pairs)} paired games: wins {sum(x['win'] for x,y in pairs)} → {sum(y['win'] for x,y in pairs)}, mean margin change {avg(y['margin']-x['margin'] for x,y in pairs)}, mean deaths {avg(x['us']['final']['deaths'] for x,y in pairs)} → {avg(y['us']['final']['deaths'] for x,y in pairs)}.")
    lines+=['','## Maps with at least five current-engine games','','| Map | Wins / games | Mean margin |','|---|---:|---:|']
    maps=co.defaultdict(list)
    for r in current:maps[r['map']].append(r)
    for name,rr in sorted(maps.items(),key=lambda x:avg(r['margin'] for r in x[1])):
        if len(rr)>=5:lines.append(f"| {name} | {sum(r['win'] for r in rr)}/{len(rr)} | {avg(r['margin'] for r in rr)} |")
    lines+=['','## Measurement limits','',
      '- Loss-only averages describe what winners did in these losses; they do not establish why an intervention would improve results. Winning controls are retained in aggregates.json.',
      '- Claudus Maximus is heavily oversampled. Use per-opponent and known-version tables before generalizing pooled numbers.',
      '- Early economic timeline samples use native round indices; partial final rounds are excluded from curve samples. Later checkpoints contain survivors to that round and may be selected.',
      '- First-bank and first-clear mean timings exclude games where that event never happened; they are conditional means, not complete-cohort timing estimates.',
      '- Camp-clear events credit the final clear, not all contributors. Collection includes recaptured/dropped gems and is not pure neutral-camp farming.',
      '- Raw replays stay local-only. Summary SHA256 values and original match IDs are preserved in manifest.json. No bot changes, submissions, activations, or match requests were made by this review.']
    (OUT/'DATA_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({k:{'n':v['n'],'wins':v['wins'],'usDeaths':v['us']['deaths'],'oppDeaths':v['them']['deaths'],'usGold':v['us']['earnedGold'],'oppGold':v['them']['earnedGold']} for k,v in summary.items()},indent=1))

if __name__=='__main__':main()
