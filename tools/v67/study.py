"""Cache opening-route evidence for every available engine-2 replay, then report all pool maps."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'proxy'))
from compile_proxy import milestones

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    index = json.loads((ROOT/'artifacts/local-only/proxy/replays/index.json').read_text())
    ids = sorted(index)[:a.limit or None]
    out = ROOT/'artifacts/local-only/v67/map-study'
    out.mkdir(parents=True, exist_ok=True)
    batches = [ids[i:i+8] for i in range(0,len(ids),8)]
    env = dict(os.environ,NFS_REPLAY_ENGINE='2.0.0')
    def extract(batch):
        p=out/(batch[0]+'.json')
        if not p.exists():
            files=[str(ROOT/'artifacts/local-only/proxy/replays'/(mid+'.repl26a')) for mid in batch]
            subprocess.run(['node','--no-warnings','tools/v67/openings.mjs',str(p),*files],cwd=ROOT,env=env,capture_output=True,check=True)
        return json.loads(p.read_text())
    openings=[]
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for f in as_completed([ex.submit(extract,b) for b in batches]):
            openings+=f.result()
            if len(openings)%80==0: print('openings',len(openings),'/',len(ids),flush=True)
    (out/'all.json').write_text(json.dumps(openings))
    print('opening extraction complete',len(openings),flush=True)
    report(index,openings,out)


def report(index,openings,out):
    crawl=ROOT/'artifacts/local-only/meta/20261027'
    matches={m['matchId']:m for m in json.loads((crawl/'matches.json').read_text())}
    canonical=lambda s:s.replace('_','-')
    bymap=defaultdict(list)
    for mid,m in matches.items():
        if m['status']=='finished' and all(t.get('engineVersion')=='2.0.0' for t in m['teams']): bymap[canonical(m['map'])].append(m)
    summaries={}
    for directory in [crawl/'summaries',ROOT/'artifacts/local-only/duels']:
        for p in directory.glob('*.json'):
            try: summaries[p.stem]=json.loads(p.read_text(encoding='utf-8-sig'))
            except (ValueError,KeyError): pass
    opmap=defaultdict(list)
    for row in openings: opmap[canonical(index[row['id']]['map'])].append(row)
    base=json.loads((ROOT/'artifacts/evaluations/v67/b00-baseline/audit.json').read_text())['per_map']
    base={canonical(k):v for k,v in base.items()}
    hero=['Ryth','Vesper','Vendetta','Cassi','Issac','Stellar','Prism','Marcella','Willow','Ren','Varg','Tavi','Heart']
    draft=['Ryth','Vesper','Vendetta','Cassi+Issac','Stellar','Prism','Marcella','Tavi','Willow','Ren','Varg','Heart']
    lines=['# v67 map evidence','',
           'Offline study of 1,177 engine-2 replays, plus the 2026-10-27 crawl. Opening routes cover rounds 1–150.',
           'Winning replay sides count twice in route/item summaries. Draft win rates use all finished engine-2 crawl games; small samples are descriptive, not counterfactual strength.',
           'G numbers are official map-API group indices. Routes list basic-attack targets; capture may follow later. Crew is the maximum distinct same-team attackers in a 15-round interval.',
           'The spawn-occupancy measure is an opening occupation of an empty camp tile; it does not prove intentional denial. First fight means first basic attack on a champion; spells may precede it.',
           'Altar-lock use is unavailable in the native summary. No zero is inferred for this missing measurement.',
           'Baseline self-play uses the fixed seeds 1/2. External v65 results are the 120 existing top-team ladder games, never newly queued games.', '']
    evidence={}
    for mp in sorted(p.stem for p in (ROOT/'maps/local-benchmarks').glob('*.map26a')):
        ms=bymap[mp]; drafts=defaultdict(lambda:[0,0]); ends=Counter(); buys=defaultdict(Counter); banks=[]; kills=[]; losses=[]
        for m in ms:
            ends[m.get('endReason','unknown')]+=1
            for t in m['teams']:
                key=tuple(t.get('draftPicks') or [])
                if key: drafts[key][1]+=1; drafts[key][0]+=t['result']=='win'
        opening=opmap[mp]; routes=defaultdict(Counter); crew=defaultdict(list); fights=[]; contested=Counter(); blocking=Counter(); examples=[]
        for row in opening:
            inf=index[row['id']]; summary=summaries.get(row['id']);
            winner=inf.get('winner')
            if inf['source']=='duel': winner=inf['ourSide'] if inf['win'] else ('b' if inf['ourSide']=='a' else 'a')
            wt=0 if winner=='a' else 1
            if row['firstFight']: fights.append(row['firstFight'])
            for g in row['contested']: contested[g]+=1
            for key,v in row['spawnOccupancy']: blocking[key]+=v
            for actor in row['actors']:
                weight=2 if actor['team']==wt else 1
                seq=tuple(x['group'] for x in actor['route'][:8])
                if seq: routes[hero[actor['type']]][seq]+=weight
            for key,n in row['crew'].items():
                if n: crew[key.split(':')[1]].append(n)
            if summary:
                for event in summary['events']:
                    if event['owner'].get('team')!='team'+winner.upper(): continue
                    if event['kind']=='gemSubmission': banks.extend(event['entries'])
                    if event['kind']=='gemLoss': losses.extend(int(x['value']) for x in event['entries'] if x.get('context')=='champion')
                for ch in summary['champions']:
                    if ch['team']=='team'+winner.upper():
                        seq=tuple(name for name,total in milestones(summary,ch['team'],ch['id'])[:4])
                        if seq: buys[ch['name']][seq]+=2
            examples.append(dict(match=row['id'],winner=winner,source=inf['source'],actors=[x for x in row['actors'] if x['team']==wt]))
        ladder=[v for v in index.values() if v['source']=='duel' and canonical(v['map'])==mp]
        top=sorted(drafts.items(),key=lambda kv:(kv[1][0]+1)/(kv[1][1]+2)*min(1,kv[1][1]/4),reverse=True)[:3]
        dtext='; '.join('/'.join(draft[i] for i in key)+f' {w}/{n}' for key,(w,n) in top) or 'no crawl evidence'
        rtext='; '.join(h+': '+'→'.join(map(str,c.most_common(1)[0][0])) for h,c in sorted(routes.items())) or 'no opening evidence'
        ftext=f"median R{statistics.median(x['round'] for x in fights):.0f}; most common tile "+str(Counter((x['x'],x['y']) for x in fights).most_common(1)) if fights else 'no basic-attack fight by R150'
        btext=(f"{len(banks)} submissions; median bag {statistics.median(int(x['value']) for x in banks):.0f}, R{statistics.median(x['timestamp']['round'] for x in banks):.0f}; altar tiles "+str(Counter((x['x'],x['y']) for x in banks).most_common(2))) if banks else 'no cached winning-side submission events'
        itext='; '.join(h+': '+', '.join(seq.most_common(1)[0][0]) for h,seq in sorted(buys.items())) or 'no cached purchase sequence'
        baseline=base.get(mp)
        brecord=f"{baseline['wins']}/{baseline['games']}" if baseline else 'not on fixed plan'
        ext=f"{sum(v['win'] for v in ladder)}/{len(ladder)}" if ladder else 'no duel evidence'
        lines += [f'## {mp}', '', '| Measure | Observed evidence |','|---|---|',
                  f'| Coverage | {len(ms)} crawl games, {len(opening)} opening replays |',
                  f'| Drafts (wins/appearances) | {dtext} |',f'| Modal opening attack route by hero | {rtext} |',
                  f'| Crew by group (median attackers) | '+', '.join(f'{g}:{statistics.median(ns):g}' for g,ns in sorted(crew.items(),key=lambda kv:int(kv[0])))+' |',
                  f'| First fight | {ftext} |',f'| Banking | {btext} |',
                  f'| Denial evidence in opening | contested groups {contested.most_common(4)}; empty-tile occupation team:group→rounds {blocking.most_common(4)}; altar locks unmeasured |',
                  f'| Winning-side opening item milestones | {itext} |',
                  f'| Game endings | {dict(ends)}; winning-side gems lost to champions median {statistics.median(losses) if losses else "unavailable"} |',
                  f'| v65 self-play / existing top-team duel record | {brecord} / {ext} |','']
        evidence[mp]=dict(crawl_games=len(ms),opening_replays=len(opening),drafts=[dict(picks=list(key),wins=w,games=n) for key,(w,n) in top],examples=examples)
    (ROOT/'research/v67/MAPS.md').write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    (ROOT/'research/v67/MAPS.json').write_text(json.dumps(evidence,indent=1)+'\n',encoding='utf8',newline='\n')
    print('wrote map evidence for',len(evidence),'pool maps',flush=True)


if __name__=='__main__':
    main()
