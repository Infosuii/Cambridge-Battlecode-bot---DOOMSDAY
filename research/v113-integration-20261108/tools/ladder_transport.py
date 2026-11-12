"""Explicit one-cycle ladder operations with durable intent/receipts; no continuous-controller changes."""
import json,os,subprocess,datetime,time
from pathlib import Path
from project import ROOT,BASE,CLI,save,check_stop
TEAM='fcf5f666-ea55-4da0-b8d4-97c64bb37236'
WD=ROOT/'ladder-cycle';WD.mkdir(exist_ok=True)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def cli(*args,parse=True):
    check_stop()
    p=subprocess.run([str(CLI),*map(str,args)],cwd=BASE/'arena',capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180,env={**os.environ,'CAMBC_NO_UPDATE_CHECK':'1'})
    if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-1500:])
    return json.loads(p.stdout) if parse else p.stdout
def detail():
    d=cli('submissions','list','--json');assert d['team']['id']==TEAM and not d['team']['banned'] and not d['frozen'];return d
def group(opponent,maps,sides,expected,path,source=None):
    path=Path(path)
    if path.exists():
        old=json.loads(path.read_text());assert old['conditions']==dict(opponent=opponent,maps=maps,sides=sides,expected=expected,source=source)
        assert old['phase']=='created','Uncertain external request must be reconciled, never blindly repeated'
        return old['group']
    assert detail()['active']['version']==expected,'Active bot changed; preserve teammate selection'
    conditions=dict(opponent=opponent,maps=maps,sides=sides,expected=expected,source=source)
    request={'phase':'creating','conditions':conditions,'at':now()};save(path,request)
    args=['match-groups','create',opponent,'--maps',','.join(maps),'--sides',','.join(sides),'--json']
    if source:args+=['--source-group',source]
    try:
        result=cli(*args);gid=result.get('groupId') or result.get('id') or result.get('group',{}).get('id');assert gid
        request.update(phase='created',group=gid,result=result,at=now());save(path,request);return gid
    except BaseException as e:
        request.update(phase='uncertain',error=str(e),at=now());save(path,request);raise
def collect(gid,timeout=1800):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        d=cli('match-groups','show',gid,'--json');matches=d.get('matches',[])
        if len(matches)==5 and all(m.get('status')=='finished' for m in matches):return d
        assert not any(m.get('status') in ('error','failed','cancelled') for m in matches),'Remote game failed; retain group receipt'
        time.sleep(8)
    raise RuntimeError('Remote group still pending; ID retained '+gid)
