from pathlib import Path
import subprocess,json,hashlib,shutil
r=Path(__file__).resolve().parents[1];project=r/'native-contact-probe';out=r/'runs/native-contact-shadow01';assert not out.exists();out.mkdir();cli=r/'.venv/bin/cambc'
with open(out/'compile.log','w') as log:p=subprocess.run([str(cli),'build','submission','--release','--output',str(project/'compiled.wasm')],cwd=project,stdout=log,stderr=subprocess.STDOUT);assert p.returncode==0
wasm=out/'probe.wasm';shutil.copyfile(project/'compiled.wasm',wasm);src=project/'bots/submission/src';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=hashlib.sha256(''.join(p.name+':'+sha(p)+'\n' for p in sorted(src.iterdir()) if p.is_file()).encode()).hexdigest();(out/'manifest.json').write_text(json.dumps(dict(wasm_sha256=sha(wasm),source_tree_sha256=source_sha,scope='Shadow contact probe; no verdict/action override, timing perturbed; not strength evidence'),indent=2)+'\n')
for name,side in [('02fields.map26a','A'),('00reverse-spiral.map26a','B')]:
 directory=out/(Path(name).stem+'-'+side);stats=directory.with_suffix('.json');a=['--label','contact-shadow','--language','cpp',str(wasm)];b=['--label','v92','--language','cpp',str(r/'mac-project/bots/jd-v92-mac/.cambc/build-release/bot-injected.wasm')]
 if side=='B':a,b=b,a
 cmd=[str(cli),'__run-match','--rounds','2000','--map',str(r/'mac-project/maps'/name),'--outdir',str(directory),'--statistics',str(stats),'--json','--fuel-quantum','100000','--log-limit','8388608',*a,'--',*b];p=subprocess.run(cmd,capture_output=True);assert p.returncode==0,p.stderr;print(directory,flush=True)
