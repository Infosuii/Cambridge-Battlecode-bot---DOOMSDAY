"""Single fixed aggregate confirmation. No held-out trajectories or retuning."""
import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from deep_preflight import ROOT
from deep_detector_report import save, wilson, comparison
from puppet.screen_recall_loops import episodes, summarize
S=ROOT/'research/deep-2026-10-28';L=ROOT/'artifacts/local-only/deep-2026-10-28'


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def d3(native):
    found=[];deaths=0
    for series in native['events']:
        if series['kind']!='death':continue
        entries=sorted(series['entries'],key=lambda e:e['timestamp']['ordinal']);deaths+=len(entries)
        for i,e in enumerate(entries):
            r=e['timestamp']['round'];prior=[p for p in entries[:i] if r-p['timestamp']['round']<=250]
            spatial=any(max(abs(p['x']-e['x']),abs(p['y']-e['y']))<=6 for p in prior)
            target=e.get('target');killer=target['id'] if target and target['kind']=='champion' and target['team']!=series['owner']['team'] else None
            repeated=killer is not None and any(p.get('target',{}).get('kind')=='champion' and p['target']['id']==killer for p in prior)
            if spatial or repeated:found.append((series['owner']['id'],r))
    return sorted(found),deaths


def native_final(native,team):
    banked=int(next(t['submittedGems'] for t in native['teams'] if t['team']==team))
    series={s['owner']['id']:s for s in native['championTimelines'] if s['metric']=='gems'}
    carried=sum(int(series[c['id']]['runs'][-1]['value']) for c in native['roster']['champions'] if c['team']==team)
    receipts=sum(int(v['value']) for e in native['events'] if e['kind']=='gemCollection' and e['owner'].get('team')==team for v in e['entries'])
    lost=sum(int(v['value']) for e in native['events'] if e['kind']=='gemLoss' and e['owner'].get('team')==team for v in e['entries'])
    assert receipts==banked+lost+carried
    return {'banked':banked,'collected':receipts,'lost':lost,'carried':carried}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['validate','confirm']);a=ap.parse_args()
    part='examined' if a.mode=='validate' else 'hands-off';run=L/('final-'+part+'-v1');receipt=json.loads((run/'run.json').read_text(encoding='utf-8'))
    meta=[r for r in json.loads((L/'restored-catalog.json').read_text(encoding='utf-8')) if r['partition']==part]
    expected=385 if part=='examined' else 165;assert receipt['passed']==len(meta)==expected and not receipt['failed']
    rows=[];d3rows=[];timeline={r['match_id']:r for r in json.loads((S/'TIMELINE_DATA.json').read_text(encoding='utf-8'))['rows']} if a.mode=='validate' else None
    for m in meta:
        mid=m['match_id'];game=json.loads((run/(mid+'.json')).read_text(encoding='utf-8'));native=json.loads((L/'replays'/part/(mid+'.summary.json')).read_text(encoding='utf-8'))
        assert game['action_code_sha256']==receipt['action_code_sha256'] and game['plan_sha256']==receipt['plan_sha256']
        assert game['final']['round']==native['match']['roundsStarted'] and game['final']['input']==native['match']['finalInput']
        eps=episodes(game['actions'],native);keys,_=d3(native)
        if a.mode=='validate':
            old=json.loads((L/'timeline-examined-v3'/(mid+'.json')).read_text(encoding='utf-8'))
            assert eps==episodes(old['actions'],native),(mid,'M1 episodes')
            assert sum(x['kind']==11 for x in game['actions'])==sum(x['kind']==11 for x in old['actions']),(mid,'recall count')
            det=json.loads((L/'detector-examined-v3'/(mid+'.json')).read_text(encoding='utf-8'))
            oldkeys=sorted((c['id'],e['start']) for c in det['actors'] for e in c['detectors']['D3']['events'])
            assert keys==oldkeys,(mid,'D3')
        if m['source']=='top-v-top':continue
        team='teamA' if m['side']=='a' else 'teamB';ids={c['id'] for c in native['roster']['champions'] if c['team']==team};own=[e for e in eps if e['actor'] in ids]
        us=native_final(native,team);them=native_final(native,'teamB' if team=='teamA' else 'teamA')
        if timeline is not None:
            assert all(us[f]==timeline[mid]['final']['us'][f] and them[f]==timeline[mid]['final']['them'][f] for f in us),(mid,'accounting')
        actors=[]
        for c in native['roster']['champions']:
            if c['id'] not in ids:continue
            deaths=sum(len(e['entries']) for e in native['events'] if e['kind']=='death' and e['owner']['id']==c['id'])
            events=[{'start':r,'end':r,'turns':0} for actor,r in keys if actor==c['id']]
            actors.append({'id':c['id'],'denominators':{'native_deaths':deaths},'detectors':{'D3':{'events':events}}})
        row={k:m[k] for k in ('match_id','cohort','map','opponent','opponent_id','result')}
        row.update(episodes=own,winning_bag_loop=any(e['previous_round_winning_bag_every_round'] for e in own),recall_starts=sum(x['kind']==11 and x['actor'] in ids for x in game['actions']),us=us,them=them)
        row['final_margin']=us['banked']-them['banked'];row['income_margin']=us['collected']-them['collected'];row['preservation_margin']=them['lost']-us['lost'];row['carry_margin']=them['carried']-us['carried']
        rows.append(row);d3rows.append(row|{'won':m['result']=='win','actors':actors})
    if a.mode=='validate':
        cal=json.loads((L/'final-calibration-excluded-v1/run.json').read_text(encoding='utf-8'));assert cal['passed']==5 and cal['failed']==0 and cal['action_code_sha256']==receipt['action_code_sha256']
        save(S/'FINAL_VALIDATION.json',{'passed':385,'calibration_passed':5,'m1_equivalent':True,'d3_equivalent':True,'native_accounting_equivalent':True,'own_accounting_games':360,'hands_off_used':0,'action_code_sha256':receipt['action_code_sha256'],'plan_sha256':receipt['plan_sha256'],'confirmation_code_sha256':digest(Path(__file__))})
        print('385 M1/D3 equivalence checks and 360 accounting checks passed; 5 calibration extracts passed.');return
    locked=json.loads((S/'FINAL_VALIDATION.json').read_text(encoding='utf-8'));assert locked['confirmation_code_sha256']==digest(Path(__file__)), 'Confirmation code changed after validation'
    summary={}
    for cohort in ['All',*sorted({r['cohort'] for r in rows})]:
        subset=[r for r in rows if cohort=='All' or r['cohort']==cohort];ds=[r for r in d3rows if cohort=='All' or r['cohort']==cohort]
        groups={out:[r for r in subset if r['result']==out] for out in ('loss','win')}
        summary[cohort]={'D3':comparison(ds,'D3',20261028),'M1_proxy':{out:summarize(rs) for out,rs in groups.items()},'accounting':{out:{'n':len(rs),**{f:sum(r[f] for r in rs)/len(rs) if rs else None for f in ('final_margin','income_margin','preservation_margin','carry_margin')}} for out,rs in groups.items()}}
    compact=[{k:r[k] for k in ('match_id','cohort','map','opponent','opponent_id','result','winning_bag_loop','recall_starts','final_margin','income_margin','preservation_margin','carry_margin')}|{'loop_episodes':len(r['episodes']),'restart_turns':sum(e['turns'] for e in r['episodes']),'repeated_deaths':sum(len(c['detectors']['D3']['events']) for c in d['actors']),'deaths':sum(c['denominators']['native_deaths'] for c in d['actors'])} for r,d in zip(rows,d3rows)]
    save(S/'FINAL_CONFIRMATION.json',{'evidence':'fixed final frequency confirmation; no causal policy effect','plan_sha256':receipt['plan_sha256'],'action_code_sha256':receipt['action_code_sha256'],'games_processed':165,'own_games':len(rows),'reference_games_not_used_in_contrasts':5,'summary':summary,'rows':compact,'no_retuning':True})
    print(json.dumps(summary,ensure_ascii=True))


if __name__=='__main__':
    main()
