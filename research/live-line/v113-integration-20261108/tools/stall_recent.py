import json,subprocess,zipfile,time,re,concurrent.futures,collections,os
from pathlib import Path
from project import ROOT,save,sha,check_stop
from ladder_transport import cli,TEAM,detail,now
WD=ROOT/'stall-audit';WD.mkdir(exist_ok=True)

def read(*args,parse=True):
    for i in range(6):
        try:return cli(*args,parse=parse)
        except RuntimeError as e:
            msg=str(e)
            if not any(k in msg for k in ('429','409','503','502','504')):raise
            wait=re.search(r'retry after\s+(\d+)',msg,re.I);time.sleep(min(60,int(wait[1])+1 if wait else 4*(i+1)))
    raise RuntimeError('Read-only replay download still rate limited')

def download(m):
    mid=m['matchId'];d=WD/'live'/mid;d.mkdir(parents=True,exist_ok=True);save(d/'metadata.json',m)
    src=d/'summary.json';z=d/'bundle.zip';rep=d/'replay.repl26a'
    if not src.exists():read('matches','summary',mid,'--json','-o',src,parse=False)
    if not z.exists():read('matches','download',mid,'-o',z,parse=False)
    if not rep.exists():
        with zipfile.ZipFile(z) as bundle:rep.write_bytes(bundle.read('replay.repl26a'))
    d0=json.loads(src.read_text());assert d0['match']['engineVersion']=='3.0.0' and d0['diagnostics']['detailedCaptureComplete']
    side=next(t['side'] for t in m['teams'] if t['teamId']==TEAM)
    spec={'match':mid,'map':m['map'],'side':0 if side=='a' else 1,'version':m['audit_version'],'replay':str(rep),'summary':str(src),'sha256':sha(rep),'summary_sha256':sha(src)}
    save(d/'spec.json',spec);return d

def decode(d):
    check_stop();out=d/'stall.json'
    if not out.exists():
        p=subprocess.run(['node',str(ROOT/'stall_replay.mjs'),str(d/'spec.json'),str(out)],capture_output=True,text=True,encoding='utf-8',timeout=300)
        if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-1500:])
    return json.loads(out.read_text())

if __name__=='__main__':
    snap=WD/'live-plan.json'
    if snap.exists():plan=json.loads(snap.read_text())
    else:
        d=detail();active=d['active'];cut=active['statusAt'];matches=[]
        for kind,limit in [('ranked',16),('unranked',8)]:
            data=read('matches','list','--team','me','--kind',kind,'--limit','40','--json')['matches']
            available=[m for m in data if m.get('status')=='finished' and m['createdAt']>=cut][:limit]
            for m in available:matches.append({**m,'audit_version':'post-activation v'+str(active['version'])+' (time inferred)'})
        if len(matches)<8:
            older=read('matches','list','--team','me','--kind','ranked','--limit','24','--json')['matches']
            seen={m['matchId'] for m in matches}
            matches.extend({**m,'audit_version':'recent pre-activation comparison; version unknown'} for m in older[:12] if m['matchId'] not in seen and m.get('status')=='finished')
        assert matches
        plan={'at':now(),'active':active,'matches':matches,'sampling':'Most recent finished ranked and unranked since active timestamp, regardless of outcome; short sample supplemented with older ranked games labeled separately.'};save(snap,plan)
    pending=[];rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for i,m in enumerate(plan['matches']):
            check_stop();d=download(m);pending.append(ex.submit(decode,d))
            if (i+1)%4==0:print(json.dumps({'downloaded':i+1,'total':len(plan['matches'])}),flush=True)
        for f in pending:rows.append(f.result())
    allstalls=[{**z,'match':r['match'],'map':r['map'],'version':r['version'],'side':r['side']} for r in rows for z in r['stalls']]
    total=collections.Counter();[total.update(r['counts']) for r in rows]
    report={'games':len(rows),'counts':dict(total),'fuel_events':sum(r['fuel_events'] for r in rows),'top_stalls':sorted(allstalls,key=lambda z:z['end']-z['start'],reverse=True)[:40],'game_reports':rows,'scope':'Recent ladder observation; version inferred where API lacks source ID. Stall flags are not causal proof; inspect exact substeps before repairs.'}
    save(WD/'live-report.json',report)
    print(json.dumps({'games':len(rows),'counts':dict(total),'fuel_events':report['fuel_events'],'top':[{'map':z['map'],'body':z['champion'],'rounds':[z['start'],z['end']],'pos':z['position'],'fuel':z['fuel_rounds'],'blocked':z['blocked_rounds'],'spawn':z['spawn_near_camp_rounds'],'enemy':z['enemy_near_rounds'],'trailing':z['trailing_rounds'],'match':z['match']} for z in report['top_stalls'][:8]]},indent=2),flush=True)
