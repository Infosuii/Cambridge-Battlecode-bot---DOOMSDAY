"""Portable, local-only botx3 continuation. No network/ladder commands."""
from pathlib import Path
import argparse, concurrent.futures, hashlib, importlib.util, json, os, re, shutil, subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/botx3-20261102'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+'.tmp');t.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8');t.replace(p)
def path(p):
    p=Path(p);return p.resolve() if p.is_absolute() else (ROOT/p).resolve()
def portable(p):
    """Historical absolute paths are provenance; remap to this checkout."""
    p=str(p).replace('\\','/')
    if Path(p).is_file(): return Path(p)
    for marker in ['/maps/','/research/']:
        if marker in p:
            q=ROOT/marker.strip('/')/p.split(marker,1)[1]
            if q.is_file(): return q
    raise FileNotFoundError(p)
def dz_module():
    spec=importlib.util.spec_from_file_location('dz_resume',ROOT/'tools/dz.py')
    d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d);return d
def output(name):
    if not re.fullmatch(r'[A-Za-z0-9_-]+',name):raise ValueError('Use a new name containing letters, digits, dash or underscore')
    return ROOT/'artifacts/local-only/botx3-resume'/name
def verify():
    m=json.loads((ROOT/'MANIFEST.json').read_text())
    bad=[]
    for name,r in m['files'].items():
        p=ROOT/name
        if not p.is_file() or sha(p)!=r['sha256']:bad.append(name)
    if bad:raise RuntimeError('Manifest mismatch: '+', '.join(bad[:20]))
    for v in range(1,12):
        b=ROOT/'bots'/f'botx3_{v}';r=json.loads((b/'release.json').read_text())
        assert sha(b/'bot.wasm')==r['wasm_sha256'],v
        for n,h in r['source'].items():assert sha(b/'src'/n)==h,(v,n)
    print('Verified',len(m['files']),'handoff files and all 11 runnable bot versions. No games started.')
def build(a):
    d=dz_module();out=output(a.name)
    if out.exists():raise FileExistsError('Frozen build name already exists: '+str(out))
    source=path(a.bot);shutil.copytree(source/'src',out/'src')
    p=out/'src/x1_config.h';text=p.read_text(encoding='utf-8')
    for value in a.set:
        k,v=value.split('=',1)
        if not re.fullmatch(r'[A-Z][A-Z0-9_]*',k):raise ValueError(k)
        text,n=re.subn(r'^#define '+k+r'\s+[^\n]+','#define '+k+' '+v,text,flags=re.M)
        if not n:text+='\n#ifndef '+k+'\n#define '+k+' '+v+'\n#endif\n'
    p.write_text(text,encoding='utf-8');d.build(out,out/'bot.wasm')
    write(out/'identity.json',dict(source_bot=str(source.relative_to(ROOT)),overrides=a.set,
          source={p.name:sha(p) for p in (out/'src').iterdir() if p.is_file()},wasm_sha256=sha(out/'bot.wasm'),cli_sha256=sha(d.CLI)))
    print(out/'bot.wasm',sha(out/'bot.wasm'))
def match(a):
    d=dz_module();out=output(a.name)
    if out.exists():raise FileExistsError(out)
    r,_=d.match(path(a.candidate),path(a.opponent),path(a.map),a.side,out)
    write(out/'screen.json',r);print(json.dumps(r,indent=2))
def benchmark(a):
    d=dz_module();out=output(a.name)
    if out.exists() and not a.resume:raise FileExistsError('Use a new name or --resume: '+str(out))
    out.mkdir(parents=True,exist_ok=True)
    if a.suite=='dev':
        manifest=json.loads((BASE/'versions-11/manifest.json').read_text())
    else:manifest=json.loads((BASE/'versions-broad-10/manifest.json').read_text())
    maps=[portable(p) for p in manifest['maps']]
    arms={'candidate':path(a.candidate),'control':path(a.reference)}
    if a.include_original:arms['original']=BASE/'builds/off/bot.wasm'
    opps={o:BASE/'portable-opponents'/(o+'.wasm') for o in ['x1','x2','v86h','v92']}
    provenance=dict(scope='Local paired continuation; all supplied dev/broad maps are spent',suite=a.suite,
       candidates={k:sha(p) for k,p in arms.items()},opponents={k:sha(p) for k,p in opps.items()},
       maps={str(p.relative_to(ROOT)):sha(p) for p in maps},cli_sha256=sha(d.CLI))
    prior=out/'manifest.json'
    if prior.exists():assert json.loads(prior.read_text())==provenance,'Resume inputs changed'
    write(prior,provenance)
    jobs=[(arm,o,c,opp,m,side,out/'games'/arm/o/(m.stem+'-'+side))
       for arm,c in arms.items() for o,opp in opps.items() for m in maps for side in ['A','B']]
    def play(j):
        arm,o,c,opp,m,side,folder=j;receipt=folder/'screen.json'
        if receipt.exists():r=json.loads(receipt.read_text())
        else:
            if folder.exists() and not (folder/'summary.json').exists():
                incomplete=out/'incomplete'/folder.relative_to(out/'games')
                assert folder.resolve().is_relative_to(out.resolve()) and incomplete.resolve().is_relative_to(out.resolve())
                if incomplete.exists():raise RuntimeError('Inspect existing incomplete cell before resuming: '+str(incomplete))
                incomplete.parent.mkdir(parents=True,exist_ok=True);folder.rename(incomplete)
            r,_=d.match(c,opp,m,side,folder,existing=(folder/'summary.json').exists())
        assert (r['candidate_sha256'],r['opponent_sha256'],r['map_sha256'],r['side'])==(sha(c),sha(opp),sha(m),side)
        assert r['engine']=='2.0.0','Wrong engine'
        r.update(arm=arm,opponent=o);write(receipt,r);return r
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        for r in pool.map(play,jobs):
            rows.append(r);write(out/'rows.json',rows)
            print(len(rows),'/',len(jobs),r['arm'],r['opponent'],r['map'],r['side'],r['banked'],flush=True)
    summary={}
    for arm in arms:
        q=[r for r in rows if r['arm']==arm]
        summary[arm]=dict(games=len(q),wins=sum(r['outcome']=='team'+r['side'] for r in q),
            faults=sum(r['faults'] for r in q),fuel_outs=sum(r['fuel_outs'] for r in q),
            banked=sum(r['banked'] for r in q)/len(q),collected=sum(r['collected'] for r in q)/len(q))
    write(out/'summary.json',summary);print(json.dumps(summary,indent=2))
def host_tests():
    cxx=os.environ.get('DZ_CXX') or shutil.which('g++') or shutil.which('clang++')
    if not cxx:raise RuntimeError('Install a C++20 compiler or set DZ_CXX')
    out=ROOT/'artifacts/local-only/botx3-resume/host';out.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ);env['PATH']=str(Path(cxx).parent)+os.pathsep+env.get('PATH','')
    for name in ['cycle_test','team_scheduler_test','bank_commit_test','draft_alias_test','camp_exposure_test','feed_control_test']:
        exe=out/(name+('.exe' if os.name=='nt' else ''))
        subprocess.run([cxx,'-std=c++20','-O2','-Wall','-Wextra','-Werror','-I',str(ROOT/'bots/botx3/src'),str(BASE/(name+'.cpp')),'-o',str(exe)],check=True,env=env)
        subprocess.run([str(exe)],check=True,env=env)
def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    s.add_parser('verify');s.add_parser('host-tests')
    b=s.add_parser('build');b.add_argument('--bot',required=True);b.add_argument('--name',required=True);b.add_argument('--set',action='append',default=[])
    m=s.add_parser('match');m.add_argument('--candidate',required=True);m.add_argument('--opponent',required=True);m.add_argument('--map',required=True);m.add_argument('--side',choices=['A','B'],default='A');m.add_argument('--name',required=True)
    b=s.add_parser('benchmark');b.add_argument('--candidate',required=True);b.add_argument('--reference',required=True);b.add_argument('--suite',choices=['dev','broad'],default='dev');b.add_argument('--name',required=True);b.add_argument('--workers',type=int,choices=range(1,9),default=4);b.add_argument('--resume',action='store_true');b.add_argument('--include-original',action='store_true')
    a=p.parse_args()
    if a.command=='verify':verify()
    elif a.command=='host-tests':host_tests()
    elif a.command=='build':build(a)
    elif a.command=='match':match(a)
    else:benchmark(a)
if __name__=='__main__':main()
