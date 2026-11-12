"""Exploratory examined-only recall-restart proxy; not every proxy flag is M1's source bug."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deep_preflight import ROOT
from deep_detector_report import wilson,save


def expand(native):
    rows={}
    for s in native['championTimelines']:
        if s['metric']=='gems':rows[s['owner']['id']]=[int(r['value']) for r in s['runs'] for _ in range(r['duration'])]
    team={s['owner']:[int(r['value']) for r in s['runs'] for _ in range(r['duration'])] for s in native['teamTimelines'] if s['metric']=='submittedGems'}
    return rows,team


def episodes(actions, native, minimum=3):
    bags,banked=expand(native);teams={c['id']:c['team'] for c in native['roster']['champions']}
    grouped=defaultdict(list)
    for a in actions:grouped[a['actor'],a['r']].append(a['kind'])
    eligible=defaultdict(list)
    for (actor,r),kinds in grouped.items():
        if 16 in kinds and 11 in kinds and not any(k in kinds for k in (4,5,6,22)):eligible[actor].append(r)
    result=[]
    for actor,rounds in eligible.items():
        run=[]
        def close():
            if len(run)>=minimum:
                winning=[banked[teams[actor]][max(0,r-1)]+bags[actor][max(0,r-1)]>=1000 for r in run]
                result.append({'actor':actor,'team':teams[actor],'start':run[0],'end':run[-1],'turns':len(run),
                               'previous_round_winning_bag_every_round':all(winning)})
        for r in sorted(set(rounds)):
            if run and r!=run[-1]+1:close();run=[]
            run.append(r)
        close()
    return result


def summarize(rows):
    n=len(rows);k=sum(bool(r['episodes']) for r in rows);w=sum(r['winning_bag_loop'] for r in rows)
    return {'n':n,'flagged':k,'occurrence':k/n if n else None,'wilson95':wilson(k,n),
            'winning_bag_flagged':w,'winning_bag_occurrence':w/n if n else None,'winning_bag_wilson95':wilson(w,n),
            'episodes':sum(len(r['episodes']) for r in rows),'restart_turns':sum(e['turns'] for r in rows for e in r['episodes']),
            'accepted_recall_starts':sum(r['recall_starts'] for r in rows)}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);a=ap.parse_args()
    study=ROOT/'research/deep-2026-10-28';local=ROOT/'artifacts/local-only/deep-2026-10-28'
    receipt=json.loads((a.run/'run.json').read_text(encoding='utf-8'));assert receipt['partition']=='examined' and receipt['passed']==385 and not receipt['failed']
    spec=study/'M1_SPEC.json';rows=[];refs=[]
    catalog=[r for r in json.loads((local/'restored-catalog.json').read_text(encoding='utf-8')) if r['partition']=='examined']
    for meta in catalog:
        mid=meta['match_id'];game=json.loads((a.run/(mid+'.json')).read_text(encoding='utf-8'))
        native=json.loads((local/'replays/examined'/(mid+'.summary.json')).read_text(encoding='utf-8'))
        found=episodes(game['actions'],native)
        if meta['source']=='top-v-top':refs.append({'match_id':mid,'episodes':found});continue
        team='teamA' if meta['side']=='a' else 'teamB';actors={c['id'] for c in native['roster']['champions'] if c['team']==team}
        own=[e for e in found if e['actor'] in actors]
        rows.append({k:meta[k] for k in ('match_id','cohort','map','opponent','opponent_id','result')}|
                    {'episodes':own,'winning_bag_loop':any(e['previous_round_winning_bag_every_round'] for e in own),
                     'recall_starts':sum(a['kind']==11 and a['actor'] in actors for a in game['actions'])})
    groups={'All':rows}|{c:[r for r in rows if r['cohort']==c] for c in sorted({r['cohort'] for r in rows})}
    result={'status':'exploratory examined screen; proxy is not exact bank-timer cause', 'spec_sha256':hashlib.sha256(spec.read_bytes()).hexdigest(),
            'hands_off_used':0,'summary':{g:{out:summarize([r for r in rs if r['result']==out]) for out in ('loss','win')} for g,rs in groups.items()},
            'rows':rows,'top_references':refs}
    save(study/'M1_EXAMINED.json',result);print(json.dumps({'summary':result['summary'],'hands_off_used':0}))


if __name__=='__main__':main()
