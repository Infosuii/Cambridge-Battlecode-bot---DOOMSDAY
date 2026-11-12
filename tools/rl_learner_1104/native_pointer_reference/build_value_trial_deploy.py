"""Build release-only greedy zero/value policies; preserve uploaded v107 source."""
from pathlib import Path
import json,shutil,subprocess,hashlib,zipfile
r=Path(__file__).resolve().parents[1];here=Path(__file__).parent;state=json.loads((r/'runs/native-value-paired-01/status.json').read_text());assert state['stage']=='complete'
project=r/'native-value-trial-deploy';assert not project.exists();(project/'bots/submission').mkdir(parents=True);src=project/'bots/submission/src';shutil.copytree(r/'native-upper-greedy/bots/submission/src',src)
with zipfile.ZipFile(r.parent.parent/'outputs/rl-execution/JD-upper5-greedy-test.zip') as z:
 for n in z.namelist():assert z.read(n)==(src/n.removeprefix('src/')).read_bytes()
for n in ('sdk','cmake'):(project/n).symlink_to(r/'mac-project'/n,target_is_directory=True)
shutil.copyfile(r/'mac-project/cambc.toml',project/'cambc.toml');rep={}
for arm in ['zero','value']:
 header=Path(state['arms'][arm]['header']);shutil.copyfile(header,src/'nn_weights.h');out=here/('value_trial_'+arm+'_greedy.wasm');assert not out.exists()
 with open(here/('value_trial_'+arm+'_compile.log'),'w') as log:p=subprocess.run([str(r/'.venv/bin/cambc'),'build','submission','--release','--output',str(out)],cwd=project,stdout=log,stderr=subprocess.STDOUT,timeout=900)
 assert p.returncode==0
 rep[arm]=dict(path=str(out),wasm_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),header_sha256=hashlib.sha256(header.read_bytes()).hexdigest())
(here/'value_trial_deployment_artifacts.json').write_text(json.dumps(dict(artifacts=rep,mode='SDK release, greedy target command, no training critic inactor',baseline_code='Exact44files fromverifiedv107ZIP excepttrainednn_weights.h'),indent=2)+'\n');print(json.dumps(rep),flush=True)
