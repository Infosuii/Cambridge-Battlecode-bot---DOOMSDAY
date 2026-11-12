"""Isolated local integration. No ladder client actions, no changes to old checkouts."""
from pathlib import Path
import json,hashlib,shutil,subprocess,datetime,os,time
ROOT=Path(__file__).resolve().parent
BASE=Path(r'C:\projects\cambridge battlecode\work\agentic-improvement')
CLI=BASE/'runtime/cambc.exe'
ARENA=ROOT/'arena'
ENGINE='3.0.0'
ENGINE_HASH='96ce858f548c14560eff737967a691a30eaf0a469afd1f4f400f125e094bd1fd'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(p):
    p=Path(p);h=hashlib.sha256()
    for f in sorted(p.rglob('*')):
        if f.is_file():h.update(f.relative_to(p).as_posix().encode()+b'\0'+f.read_bytes())
    return h.hexdigest()
def save(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(d,indent=2),encoding='utf-8')
    for attempt in range(50):
        try:temp.replace(p);return
        except PermissionError:time.sleep(.025)
    raise RuntimeError('Report is locked: '+str(p))
def check_stop():
    if (ROOT/'STOP').exists():raise RuntimeError('Local integration stopped')
    if shutil.disk_usage(ROOT).free < 150*1024**3:raise RuntimeError('Less than 150 GiB free; stop local games/training and preserve checkpoints')
def prepare():
    ARENA.mkdir(exist_ok=True)
    for folder in ('sdk/cpp','cmake'):
        dst=ARENA/folder
        if not dst.exists():shutil.copytree(BASE/'arena'/folder,dst)
    (ARENA/'cambc.toml').write_text('sdk_version = "5.0.0"\nlanguages = ["cpp"]\n',encoding='utf-8')
    origins={'b113':ROOT.parent/'v113-review-20261108/source','b112':BASE/'arena/bots/auto_bank_arrive_learned/src','b111':BASE/'arena/bots/v111/src','bterm':BASE/'arena/bots/auto_bt8_l_f3/src'}
    frozen={}
    for name,src in origins.items():
        dst=ARENA/'bots'/name/'src'
        if not dst.exists():shutil.copytree(src,dst)
        assert digest(src)==digest(dst)
        frozen[name]={'origin':str(src),'source_sha256':digest(dst)}
        if name!='b113':
            original=src.parent/'.cambc/build-release/bot-injected.wasm'
            target=dst.parent/'frozen.wasm'
            if not target.exists():shutil.copy2(original,target)
            assert sha(target)==sha(original);frozen[name]['wasm_sha256']=sha(target)
    identity={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cli_sha256':sha(CLI),'sdk_sha256':digest(ARENA/'sdk/cpp'),'engine':ENGINE,'engine_build':ENGINE_HASH,'origins':frozen,'scope':'Local source merge, repairs, correctness checks, retraining and retuning authorized by user. No official mutations or publication. Original controller STOP remains untouched.'}
    p=ROOT/'starting-identities.json'
    if p.exists():assert json.loads(p.read_text())['origins']==frozen
    else:save(p,identity)
    return identity
def build(name,debug=False):
    check_stop();bot=ARENA/'bots'/name
    out=bot/('.cambc/build/bot-injected.wasm' if debug else '.cambc/build-release/bot-injected.wasm')
    identity={'source':digest(bot/'src'),'sdk':digest(ARENA/'sdk/cpp'),'cli':sha(CLI),'debug':debug}
    receipt=bot/('debug-build.json' if debug else 'release-build.json')
    if out.exists() and receipt.exists():
        d=json.loads(receipt.read_text())
        if d['inputs']==identity and d['wasm_sha256']==sha(out):return out
    args=[str(CLI),'build','bots/'+name]+([] if debug else ['--release'])
    p=subprocess.run(args,cwd=ARENA,capture_output=True,encoding='utf-8',errors='replace',timeout=300,
                     env={**os.environ,'CAMBC_NO_UPDATE_CHECK':'1'})
    (bot/('debug-build.log' if debug else 'release-build.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
    if p.returncode or not out.exists():raise RuntimeError('Build failed '+name+': '+(p.stdout+p.stderr)[-1800:])
    save(receipt,{'inputs':identity,'wasm_sha256':sha(out)});return out
if __name__=='__main__':
    print(json.dumps(prepare(),indent=2));print('v113 full build:',build('b113'))
