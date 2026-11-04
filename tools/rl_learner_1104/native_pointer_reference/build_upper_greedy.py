"""Build matched logging-disabled upper initial/final policies in own project."""
from pathlib import Path
import shutil,re,subprocess,json,hashlib
r=Path(__file__).resolve().parents[1];here=Path(__file__).parent;project=r/'native-upper-greedy';assert not project.exists();(project/'bots/submission').mkdir(parents=True)
src=project/'bots/submission/src';shutil.copytree(r/'native-upper-actor/bots/submission/src',src)
for n in ('sdk','cmake'):(project/n).symlink_to(r/'mac-project'/n,target_is_directory=True)
f=src/'common.h';s=f.read_text();assert '#define JD_NATIVE_LOG 1' in s;s=s.replace('#define JD_NATIVE_LOG 1','#define JD_NATIVE_LOG 0');s=s.replace('#define JD_NATIVE_DET 0','#define JD_NATIVE_DET 1');f.write_text(s)
f=src/'nnrec.cpp';s=re.sub(r'#define CLNA_SEED \d+ // JD_CYCLE_SEED','#define CLNA_SEED 110401 // JD_CYCLE_SEED',f.read_text());f.write_text(s)
f=src/'nn_infer.h';s=f.read_text();start='    std::copy(h0,h0+kTrunk,lv.jd_h0);';stop='lv.jd_h1_at=static_cast<int>(bc::round_number());';a=s.index(start);b=s.index(stop,a)+len(stop);s=s[:a]+'#if JD_NATIVE_LOG\n'+s[a:b]+'\n#endif'+s[b:];f.write_text(s)
status=json.loads((r/'runs/native-upper-continuation-01/status.json').read_text());assert status['stage']=='complete'
variants={'upper0_greedy':here/'upper_u0_header.h','upper5_greedy':Path(status['latest_header'])};rep={}
for name,header in variants.items():
 shutil.copyfile(header,src/'nn_weights.h')
 with open(here/(name+'_deploy_compile.log'),'w') as log:p=subprocess.run([str(r/'.venv/bin/cambc'),'__compile-bot',str(project)],stdout=log,stderr=subprocess.STDOUT)
 assert p.returncode==0
 target=here/(name+'_deploy.wasm');assert not target.exists();shutil.copyfile(project/'compiled.wasm',target)
 rep[name]=dict(wasm_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),header_sha256=hashlib.sha256(header.read_bytes()).hexdigest(),path=str(target))
report=dict(artifacts=rep,seed=110401,temperature=.5,v92_bonus=2,guard=18000,logging=False,deterministic_argmax=True,diagnostic_hidden_copies=False,note='Same deployment source/seed, only trained header differs; no playing strength claim')
(here/'upper_greedy_artifacts.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
