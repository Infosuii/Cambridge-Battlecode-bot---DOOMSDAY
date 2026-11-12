"""Package existing local evidence only; never build, play, or contact the ladder."""
from pathlib import Path
import hashlib,json,shutil,zipfile,os,concurrent.futures
R=Path(__file__).resolve().parents[1]
B=R/'research/botx3-20261102'
P=R/'handoff-botx3-latest'
P.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
old=json.loads((R/'MANIFEST.json').read_text())
releases={}
for v in range(1,12):
    campaign='versions-1-2' if v<=2 else 'versions-'+str(v)
    f=B/campaign/'builds'/f'botx3_{v}'
    d=R/'bots'/f'botx3_{v}'
    identity=json.loads((f/'identity.json').read_text())
    # Verify the actual numbered source against its benchmark snapshot.
    source={p.name:sha(p) for p in (d/'src').iterdir() if p.is_file()}
    expected=identity.get('source',identity.get('source_sha256'))
    assert source==expected,(v,'source differs from frozen benchmark')
    shutil.copyfile(f/'bot.wasm',d/'bot.wasm')
    release=dict(version=v,campaign=campaign,source=source,wasm_sha256=sha(d/'bot.wasm'),features=json.loads((d/'features.json').read_text()))
    write(d/'release.json',release);releases[str(v)]=release['wasm_sha256']
for p in (B/'versions-11/opponents').glob('*.wasm'):
    q=B/'portable-opponents'/p.name;q.parent.mkdir(exist_ok=True);shutil.copyfile(p,q)
write(B/'portable-opponents/manifest.json',{p.name:sha(p) for p in (B/'portable-opponents').glob('*.wasm')})
campaigns=[p for p in B.iterdir() if p.is_dir() and (p/'summary.json').is_file() and (p/'manifest.json').is_file()]
write(R/'PAUSED_STATE.json',dict(state='Paused at user request; no experiments running',date='2026-11-03',branch='dev/botx3-team-economy-20261102',latest_full_version='botx3_11',strongest_broad_measured='botx3_1',release_hashes=releases,completed_campaigns=[p.name for p in campaigns],next='Read HANDOFF.md, SETUP_FRESH_MACHINE.md and NEXT_AGENT_PROMPT.md. Do not start games until the user resumes development.'))
files=set()
def add(p):
    p=Path(p)
    if not p.is_absolute():p=R/p
    if p.is_file() and p.resolve().is_relative_to(R.resolve()):files.add(p.relative_to(R).as_posix())
for n in old['files']:add(n)
for name in ['AGENTS.md','README.md','HANDOFF.md','SETUP_FRESH_MACHINE.md','NEXT_AGENT_PROMPT.md','FRESH_AGENT_PROMPT.md','CONTINUATION_PROMPT.md','CONTINUE_HERE.md','GITHUB_CONTINUATION.md','CLAUDE_HANDOFF.md','PAUSED_STATE.json','tools/dz.py','tools/botx3_resume.py','tools/package_botx3_pause.py','cambc.toml','.gitattributes'] :add(name)
for folder in [R/'bots/botx3']+[R/'bots'/f'botx3_{v}' for v in range(1,12)]:
    for p in folder.rglob('*'):
        if p.suffix in ['.h','.cpp','.json','.wasm']:add(p)
for p in B.iterdir():
    if p.suffix in ['.py','.cpp','.mjs','.md','.json','.zip']:add(p)
for p in (B/'portable-opponents').glob('*'):add(p)
for folder in [R/'cmake',R/'sdk',R/'tools/replay']:
    for p in folder.rglob('*'):
        if p.suffix in ['.h','.cpp','.mjs','.py','.txt','.json']:add(p)
for p in (R/'maps').rglob('*.map26a'):add(p)
for c in campaigns:
    m=json.loads((c/'manifest.json').read_text())
    for name in m.get('maps',[]):
        name=str(name).replace('\\','/')
        for marker in ['/maps/','/research/']:
            if marker in name:add(R/marker.strip('/')/name.split(marker,1)[1])
for c in B.iterdir():
    if c.is_dir() and ('maps' in c.name or 'conformance' in c.name):
        for p in c.rglob('*.map26a'):add(p)
receipt_index={}
def package_campaign(c):
    for p in c.iterdir():
        if p.is_file() and p.suffix in ['.json','.md']:add(p)
    for f in (c/'builds').glob('*'):
        for p in f.glob('*'):
            if p.is_file() and p.suffix in ['.wasm','.json','.log'] and p.name!='compile_commands.json':add(p)
        for p in (f/'src').glob('*'):add(p)
    for p in (c/'opponents').glob('*'):add(p)
    receipt_files=[]
    for folder,dirs,names in os.walk(c/'games'):
        for name in names:
            if name in ['screen.json','receipt.json','runner.log','candidate.stdout']:receipt_files.append(Path(folder)/name)
    if receipt_files:
        archive=P/'game-receipts'/(c.name+'.zip');archive.parent.mkdir(exist_ok=True)
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in receipt_files:z.write(p,p.relative_to(R).as_posix())
        receipt_index[c.name]=dict(files=len(receipt_files),bytes=archive.stat().st_size,sha256=sha(archive));add(archive)
    print('Packaged '+c.name,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    list(pool.map(package_campaign,campaigns))
# Keep selected native diagnostics/replay evidence; bulk campaign replay/summary payloads stay local.
for c in B.iterdir():
    if not c.is_dir() or c in campaigns or c.name in ['__pycache__']:continue
    if any(s in c.name for s in ['diagnostic','conformance','replay-audit','resume-audit']):
        for folder,dirs,names in os.walk(c):
            dirs[:]=[n for n in dirs if n not in ['games','.cambc','__pycache__','builds']]
            for n in names:
                p=Path(folder)/n
                if p.suffix in ['.json','.stdout','.log','.mjs','.repl26a'] and p.stat().st_size<15_000_000:add(p)
write(P/'RECEIPTS_INDEX.json',receipt_index);add(P/'RECEIPTS_INDEX.json')
write(R/'MANIFEST.json',dict(state='Paused 2026-11-03; complete numbered versions 1-11; see HANDOFF.md',files={n:dict(bytes=(R/n).stat().st_size,sha256=sha(R/n)) for n in sorted(files)}))
archive=P/'BOTX3_CONTINUATION_LATEST.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for n in sorted(files|{'MANIFEST.json'}):z.write(R/n,n)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
(P/'ARCHIVE_SHA256.txt').write_text(sha(archive)+'  '+archive.name+'\n')
print(json.dumps(dict(files=len(files),archive_bytes=archive.stat().st_size,receipt_campaigns=len(receipt_index),versions=releases),indent=2))
