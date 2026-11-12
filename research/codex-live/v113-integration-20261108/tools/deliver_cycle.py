"""One user-authorized qualified upload and activation, with receipts and no blind retries."""
import argparse,collections,concurrent.futures,json,subprocess,os,time,zipfile,re,shutil
from pathlib import Path
from project import ROOT,ARENA,CLI,save,sha,digest,check_stop
from ladder_transport import WD,TEAM,now,cli,detail,group,collect

def release():
    qualification=ROOT/'qualification-stall/result.json'
    result=json.loads(qualification.read_text());assert result['approved_for_upload'] and all(result['gates'].values()),'Independent stall and strength qualification did not pass'
    assert result['gates']['fewer_trailing_quiet_stalls'],'Stall improvement not verified'
    name=result['candidate'];path=ROOT/'release'/name;manifest=json.loads((path/'manifest.json').read_text())
    assert manifest['approved_for_upload'] and sha(qualification)==manifest['qualification_sha256']
    assert sha(CLI)==manifest['cli_sha256'] and digest(ARENA/'sdk/cpp')==manifest['sdk_digest']
    src=ARENA/'bots'/name;assert digest(src/'src')==manifest['source_digest']
    assert sha(path/manifest['source_zip']['file'])==manifest['source_zip']['sha256']
    assert sha(path/manifest['wasm']['file'])==manifest['wasm']['sha256']
    with zipfile.ZipFile(path/manifest['source_zip']['file']) as z:
        expected={p.relative_to(src).as_posix():p for p in (src/'src').rglob('*') if p.is_file()}
        assert {n for n in z.namelist() if not n.endswith('/')}==set(expected)
        for n,f in expected.items():assert z.read(n)==f.read_bytes()
    return name,path,manifest

def submission_cli(*args):
    check_stop();p=subprocess.run([str(CLI),*args],cwd=ARENA,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180,env={**os.environ,'CAMBC_NO_UPDATE_CHECK':'1'})
    if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-1500:])
    return p.stdout

def deliver(phase,expected):
    name,path,m=release();receipt=path/'ladder-receipt.json';note='codex-fixes:'+name+':'+m['source_digest'][:12]
    state=json.loads(receipt.read_text()) if receipt.exists() else {'authorization':'User: once you are satisfied push to ladder please; v114 source supplied for selective feature reuse','expected_before':expected,'note':note,'created':now(),'package_manifest_sha256':sha(path/'manifest.json')}
    assert state['expected_before']==expected and state['note']==note
    d=detail();matches=[s for s in d['submissions'] if s.get('note')==note];assert len(matches)<=1
    if phase=='upload':
        assert d['active']['version']==expected,'Concurrent teammate activation; preserve it'
        if matches:state.update(version=matches[0]['version'],phase='uploaded',reconciled=now())
        else:
            assert state.get('phase') not in ('uploading','upload_uncertain'),'Reconcile uncertain upload, do not submit twice'
            assert (path/'source.zip').stat().st_size<=d['maxBytes']
            state['before']={k:d.get(k) for k in ('active','selected','pinned')};save(receipt,state)
            # Follow-newest would otherwise activate the new bot before server
            # compilation is inspected. Pin the unchanged incumbent during upload.
            if not d.get('pinned'):
                cli('submissions','activate',str(expected),'--json')
                pinned=detail();assert pinned['active']['version']==expected and pinned['pinned']
            state.update(phase='uploading',at=now());save(receipt,state)
            try:
                response=submission_cli('submit','bots/'+name,'--note',note)
                state.update(phase='uploaded_response',response=response,at=now());save(receipt,state)
            except BaseException as e:
                state.update(phase='upload_uncertain',error=str(e),at=now());save(receipt,state);raise
            d=detail();matches=[s for s in d['submissions'] if s.get('note')==note];assert len(matches)==1,'Reconcile by unique note; never blind resubmit'
            state.update(version=matches[0]['version'],phase='uploaded')
        save(receipt,state)
    else:
        assert len(matches)==1 and state['version']==matches[0]['version']
        row=matches[0];state.update(remote=row,last_checked=now());save(receipt,state)
        if phase=='activate':
            assert row['status'] in ('active','inactive'),'Server compilation not ready'
            assert d['active']['version'] in (expected,row['version']),'Concurrent teammate change; do not override'
            if d['active']['version']!=row['version']:
                state.update(phase='activating',at=now());save(receipt,state)
                response=cli('submissions','activate',str(row['version']),'--json');state['activation_response']=response
            d=detail();assert d['active']['version']==d['selected']['version']==row['version']
            state.update(phase='active',activated=now(),active_version=row['version']);save(receipt,state)
    print(json.dumps({'phase':state.get('phase'),'version':state.get('version'),'active':d['active']['version'],'status':matches[0]['status'] if matches else None,'receipt':str(receipt)}),flush=True)

def technical():
    from stall_recent import download as download_replay, decode as decode_replay
    name,path,m=release();receipt=json.loads((path/'ladder-receipt.json').read_text());version=receipt['version'];assert receipt['phase']=='active'
    dest=WD/'challenger';dest.mkdir(exist_ok=True);planfile=dest/'plan.json'
    if planfile.exists():plan=json.loads(planfile.read_text())
    else:
        assert detail()['active']['version']==version
        teams=cli('ladder','--limit','100','--json')['teams'];me=next(t for t in teams if t['teamId']==TEAM)
        targets=sorted([t for t in teams if t['teamId']!=TEAM],key=lambda t:(abs(t['rank']-me['rank']),t['rank']))[:3]
        campaign=json.loads((ROOT/'campaign.json').read_text());pool=json.loads((ROOT/'published-maps.json').read_text());dev=set(campaign['maps']['dev'])
        maps=sorted([r for r in pool if r['file'] in dev],key=lambda r:r['name']);assert len(maps)>=15
        plan={'version':version,'at':now(),'groups':[{'opponent':t['teamId'],'name':t.get('name',t.get('teamName')),'maps':[r['mapId'] for r in maps[i*5:i*5+5]],'sides':['a' if (i+j)%2==0 else 'b' for j in range(5)]} for i,t in enumerate(targets)],'scope':'15 unranked technical deployment games, near-rank opponents, development maps. Scores descriptive only; no ELO or paired-seed claim.'}
        save(planfile,plan)
    gids=[]
    for i,g in enumerate(plan['groups']):gids.append(group(g['opponent'],g['maps'],g['sides'],version,dest/f'request-{i}.json'))
    reports=[];replays=[]
    for i,gid in enumerate(gids):
        result=collect(gid);save(dest/f'group-{i}.json',result)
        for meta in result['matches']:
            mid=meta['matchId'];p=dest/(mid+'.json')
            if not p.exists():cli('matches','summary',mid,'--json','-o',p,parse=False)
            n=json.loads(p.read_text(encoding='utf-8'));own=next(t for t in meta['teams'] if t['teamId']==TEAM);side='team'+own['side'].upper()
            assert n['diagnostics']['detailedCaptureComplete'] and n['match']['outcome'] in ('teamA','teamB','draw')
            fuel=sum(len(e['entries']) for e in n['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==side)
            reports.append({'match':mid,'group':gid,'map':meta['map'],'side':own['side'],'score':1 if n['match']['outcome']==side else .5 if n['match']['outcome']=='draw' else 0,'own_faults':n['diagnostics']['botFaults'][side],'both_team_faults':n['diagnostics']['botFaults'],'codes':n['diagnostics']['codes'],'fuel':fuel,'engine':n['match']['engineVersion'],'engine_build':n['match']['engineBuildHash'],'summary_sha256':sha(p)})
            replays.append({**meta,'audit_version':f'controlled v{version} unranked group'})
    report={'version':version,'games':len(reports),'score':sum(r['score'] for r in reports),'own_faults':sum(r['own_faults'] for r in reports),'fuel':sum(r['fuel'] for r in reports),'rows':reports,'scope':plan['scope'],'active_verified':detail()['active']['version']==version}
    save(dest/'report.json',report)
    assert not report['own_faults'] and report['active_verified'],'Deployment health requires investigation'
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        audits=[pool.submit(decode_replay,download_replay(m)) for m in replays]
        for row in audits:counts.update(row.result()['counts'])
    report['stall_audit']=dict(counts)
    save(dest/'report.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('upload','status','activate','technical'));parser.add_argument('--expected',type=int,default=114);args=parser.parse_args()
    if args.phase=='technical':technical()
    else:deliver(args.phase,args.expected)
