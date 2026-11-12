from pathlib import Path
import json,subprocess,shutil
r=Path(__file__).resolve().parents[1];p=Path(__file__).parent;state=json.loads((r/'runs/native-value-paired-01/status.json').read_text());assert state['stage']=='complete';project=r/'native-value-trial-actor';src=project/'bots/submission/src';out=r/'runs/native-value-final-replay';assert not out.exists();out.mkdir()
for arm in ['zero','value']:
 header=Path(state['arms'][arm]['header']);shutil.copyfile(header,src/'nn_weights.h')
 with open(out/(arm+'-compile.log'),'w') as log:result=subprocess.run([str(r/'.venv/bin/cambc'),'__compile-bot',str(project)],stdout=log,stderr=subprocess.STDOUT);assert result.returncode==0
 wasm=out/(arm+'.wasm');shutil.copyfile(project/'compiled.wasm',wasm);directory=out/arm;stats=out/(arm+'.json')
 cmd=[str(r/'.venv/bin/cambc'),'__run-match','--rounds','2000','--map',str(r/'mac-project/maps/02fields.map26a'),'--outdir',str(directory),'--statistics',str(stats),'--json','--fuel-quantum','100000','--log-limit','67108864','--label',arm,'--language','cpp',str(wasm),'--','--label','v92','--language','cpp',str(r/'mac-project/bots/jd-v92-mac/.cambc/build-release/bot-injected.wasm')]
 result=subprocess.run(cmd,capture_output=True);assert result.returncode==0,result.stderr
 d=json.loads(stats.read_text());assert d['diagnostics']['detailedCaptureComplete'] and not any(d['diagnostics']['botFaults'].values())
 result=subprocess.run([str(r/'.venv/bin/python'),str(p/'check_upper_live.py'),'--stdout',str(directory/'team-a.stdout'),'--header',str(header),'--out',str(r.parent.parent/'outputs/rl-execution'/('VALUE_TRIAL_'+arm.upper()+'_FINAL_REPLAY.json'))],capture_output=True,text=True);assert result.returncode==0,result.stdout+result.stderr
 print(arm+' '+result.stdout,flush=True)
