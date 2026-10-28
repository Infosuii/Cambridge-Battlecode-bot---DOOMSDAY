"""Pack/restore a credential-free research checkpoint. Python standard library only.

pack reads the current Windows official tool cache; restore never overwrites Git source.
The archive is split below GitHub's normal file limit and authenticated by SHA-256.
"""
import argparse,datetime,hashlib,io,json,os,pathlib,shutil,subprocess,sys,tarfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
DEST=ROOT/'continuation/checkpoint-2026-10-28'
SKIP={'.git','.cambc','__pycache__','CMakeFiles','node_modules'}
NEW=('SEQ81','SCHED82','INT83','HOME84','OBJ85','PUBLIC81','AUD81')
FULL=('Q-proxy-v78','Q-v58-v78','Q-v61-v78','Q-v65-v78','V80PKG-')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def walk(p):
 if p.is_file():yield p;return
 if not p.exists():return
 for directory,dirs,files in os.walk(p):
  dirs[:]=sorted(d for d in dirs if d not in SKIP)
  for name in sorted(files):
   if name!='compile_commands.json':yield pathlib.Path(directory)/name
def collect():
 entries={}
 def add(p,logical=None):
  if p.is_file():entries[logical or 'repo/'+p.relative_to(ROOT).as_posix()]=p
 # Complete new research evidence and V76/V80 final comparison replays. Older V80 arms retain
 # native summaries, exact frozen build sources/Wasm and manifests; their raw games are reproducible.
 base=ROOT/'artifacts/evaluations/v67'
 for run in sorted(base.iterdir()):
  if not run.is_dir() or not (run.name.startswith(NEW+('V80','MIC80')) or run.name in FULL[:4]):continue
  complete=run.name.startswith(NEW+FULL)
  for p in run.iterdir():
   if p.is_file():add(p)
  for p in walk(run/'build'):add(p)
  for game in (run/'games').iterdir() if (run/'games').exists() else []:
   if not game.is_dir():continue
   for p in game.iterdir():
    if p.is_file() and (complete or p.name in {'summary.json','engine_identity.json'}):add(p)
 for name in ('duel-v74','mg-18208504','v81-current'):
  for p in walk(ROOT/'artifacts/local-only'/name):add(p)
 for name in ('v76-control.wasm','v80-control.wasm','v81-control.wasm','v82-control.wasm','v83-control.wasm','intent83_parity.npz','v80-review'):
  for p in walk(ROOT/'artifacts/tmp/v67'/name):add(p)
 for p in walk(ROOT/'artifacts/release'):add(p)
 # Exact official Windows build/replay runtime. No credentials, CLI settings, updates or browser profiles.
 cache=pathlib.Path(os.environ.get('LOCALAPPDATA',''))/'cambc'
 for name in ('wasi-sdk-33','cmake-3.31.8-windows-x86_64','ninja-1.12.1-windows-x86_64','assets'):
  for p in walk(cache/name):add(p,'runtime/'+p.relative_to(cache).as_posix())
 return entries
def pack():
 DEST.mkdir(parents=True,exist_ok=True)
 assert not list(DEST.glob('evidence.part*')),'refuse to overwrite checkpoint parts'
 entries=collect();rows=[];objects={}
 for n,(name,p) in enumerate(sorted(entries.items()),1):
  digest=sha(p);rows.append(dict(path=name,sha256=digest,bytes=p.stat().st_size));objects.setdefault(digest,p)
  if n%2000==0:print('hashed',n,'files',flush=True)
 manifest=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),format=1,
  source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  files=rows,objects=len(objects),logical_bytes=sum(x['bytes'] for x in rows),
  scope='New research full evidence; final V76/V80 paired replay evidence; older V80 native summaries and frozen builds; ranked v74/current/MG18208504; official Windows runtime. No credentials, venv, training corpus, generic caches or unrelated scratch.')
 archive=ROOT/'artifacts/tmp/continuation-evidence.tar.gz';archive.parent.mkdir(parents=True,exist_ok=True)
 with tarfile.open(archive,'w:gz',compresslevel=6) as t:
  for n,(digest,p) in enumerate(sorted(objects.items()),1):
   t.add(p,arcname='objects/'+digest,recursive=False)
   if n%1000==0:print('packed',n,'objects',flush=True)
 parts=[]
 with archive.open('rb') as f:
  n=0
  while b:=f.read(40*1024*1024):
   p=DEST/f'evidence.part{n:03d}';p.write_bytes(b);parts.append(dict(name=p.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()));n+=1
 manifest['parts']=parts;manifest['packed_bytes']=archive.stat().st_size
 (DEST/'manifest.json').write_text(json.dumps(manifest,indent=1)+'\n',encoding='utf8')
 print(json.dumps({k:v for k,v in manifest.items() if k not in ('files','parts')},indent=1),flush=True)
 verify(False)
class Parts(io.RawIOBase):
 def __init__(self,paths):self.paths=iter(paths);self.file=None
 def readable(self):return True
 def readinto(self,b):
  while True:
   if self.file is None:
    try:self.file=open(next(self.paths),'rb')
    except StopIteration:return 0
   n=self.file.readinto(b)
   if n:return n
   self.file.close();self.file=None
 def close(self):
  if self.file:self.file.close()
  super().close()
def verify(full=False,restore=None,install_runtime=False):
 m=json.loads((DEST/'manifest.json').read_text());paths=[]
 for part in m['parts']:
  p=DEST/part['name'];assert p.stat().st_size==part['bytes'] and sha(p)==part['sha256'],str(p);paths.append(p)
 print('All',len(paths),'archive parts verified',flush=True)
 if not (full or restore):return
 by_hash={}
 for row in m['files']:by_hash.setdefault(row['sha256'],[]).append(row)
 verified=set();written=0
 with io.BufferedReader(Parts(paths)) as stream,tarfile.open(fileobj=stream,mode='r|gz') as t:
  for member in t:
   assert member.isfile() and member.name.startswith('objects/')
   digest=member.name.split('/')[-1];assert digest in by_hash
   data=t.extractfile(member).read();assert hashlib.sha256(data).hexdigest()==digest
   verified.add(digest)
   if not restore:continue
   for row in by_hash[digest]:
    kind,rel=row['path'].split('/',1);base=pathlib.Path(restore).resolve()
    if kind=='runtime':
     base=pathlib.Path(os.environ['LOCALAPPDATA'])/'cambc' if install_runtime else base/'artifacts/portable-runtime'
    target=(base/rel).resolve();assert target.is_relative_to(base.resolve()),rel
    if target.exists():
     if sha(target)!=digest and kind=='runtime':raise RuntimeError('Existing runtime differs; preserve it and restore without --install-runtime: '+str(target))
     continue # Never replace newer Git source or frozen receipts.
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);written+=1
 assert verified==set(by_hash),'missing archive objects'
 print('Verified',len(verified),'unique objects;',len(m['files']),'logical files;',written,'files restored',flush=True)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['pack','verify','restore']);p.add_argument('--full',action='store_true');p.add_argument('--dest',default=str(ROOT));p.add_argument('--install-runtime',action='store_true');a=p.parse_args()
 if a.mode=='pack':pack()
 else:verify(a.full,a.dest if a.mode=='restore' else None,a.install_runtime)
if __name__=='__main__':main()
