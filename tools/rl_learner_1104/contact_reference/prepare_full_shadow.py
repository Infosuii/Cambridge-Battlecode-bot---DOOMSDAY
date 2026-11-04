from pathlib import Path
import shutil,subprocess,json,hashlib
r=Path(__file__).resolve().parents[1];project=r/'native-contact-full-shadow';assert not project.exists();(project/'bots/submission').mkdir(parents=True);src=project/'bots/submission/src';shutil.copytree(r/'native-contact-probe/bots/submission/src',src)
for name in ('sdk','cmake'):(project/name).symlink_to(r/'mac-project'/name,target_is_directory=True)
shutil.copyfile(r/'mac-project/cambc.toml',project/'cambc.toml')
p=src/'jd_contact_probe.h';s=p.read_text().replace('inline int calls=','inline volatile std::int16_t score_sink[3]={};\ninline int calls=');p.write_text(s)
p=src/'jd_contact_features.inc';s=p.read_text().replace('jd_contact::records<8 && ','').replace('            const auto f0=bc::fuel_remaining();\n','').replace('                const auto f1=bc::fuel_remaining();jd_contact::score(q,z);const auto f2=bc::fuel_remaining();','                jd_contact::score(q,z);')
a=s.index('                const bool valid[3]');b=s.index('\n            }',a);s=s[:a]+'                for(int i=0;i<3;++i)jd_contact::score_sink[i]=z[i]; // prevent dead-code elimination; no action override\n'+s[b:];p.write_text(s)
out=r/'contact_reference/contact_shadow_full.wasm';assert not out.exists()
with open(r/'contact_reference/full_compile.log','w') as log:p=subprocess.run([str(r/'.venv/bin/cambc'),'build','submission','--release','--output',str(out)],cwd=project,stdout=log,stderr=subprocess.STDOUT);assert p.returncode==0
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();manifest=dict(wasm_sha256=sha(out),source_tree_sha256=hashlib.sha256(''.join(p.name+':'+sha(p)+'\n' for p in sorted(src.iterdir()) if p.is_file()).encode()).hexdigest(),native_header_sha256=sha(src/'nn_weights.h'),policy='No action override; shadow features and nontrainedhead at EVERY fresh contact<=6 with25kreserve; no capped/in-game logging',compiler='SDKrelease',computation_forced='Volatile3-score sink prevents optimizer deleting unused head; softmax/sampling/logging costs NOT included')
(r/'contact_reference/full_shadow_artifact.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)
