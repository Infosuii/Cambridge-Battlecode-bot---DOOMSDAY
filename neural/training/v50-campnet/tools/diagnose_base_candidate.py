"""Check whether truncated/fuel-filtered candidates omit the heuristic's choice."""
from pathlib import Path
import json
import shutil
import zipfile
import train

PARENT=train.ROOT
ROOT=PARENT/'diagnosis-phase2'
train.ROOT=ROOT
src=ROOT/'zero-residual-base-guard/src'
if not src.exists():shutil.copytree(ROOT/'zero-residual/src',src)
p=src/'bot.cpp';s=p.read_text(encoding='utf-8')
needle='    const int mode = ngp::training() ? 1 : 0;'
replacement=needle+'''
    bool diagnostic_has_base = false;
    for (int k = 0; k < n; ++k) diagnostic_has_base |= cn[k].gi == base;
    if (!diagnostic_has_base) {
        std::printf("NGP_MISSING_BASE %d %d %d\\n", round, base, n);
        return base;
    }
'''
if 'NGP_MISSING_BASE' not in s:p.write_text(s.replace(needle,replacement,1),encoding='utf-8')
protocol=json.loads((PARENT/'phase2-two-hours/protocol.json').read_text())
maps=sorted(map(Path,protocol['training_maps']+protocol['selection_maps']+protocol['final_holdout_maps']))
train.write(ROOT/'base-candidate-protocol.json',dict(purpose='Diagnostic guard and counter only; no promotion.',maps=[str(m) for m in maps],variant='zero-residual-base-guard',source_sha256=train.sha(p)))
wasm=train.compile_bot(src,ROOT/'builds/zero-residual-base-guard.wasm',20)
score,_=train.evaluate_artifact(wasm,'zero-residual-base-guard',maps,[PARENT/'phase2-two-hours/opponents/original.wasm'],20)
count=0;games=0
for folder in (ROOT/'runs/zero-residual-base-guard').glob('*'):
    side=folder.name.rsplit('-',1)[-1].lower()
    files=list(folder.glob('*.repl26a'))
    if not files:continue
    with zipfile.ZipFile(files[0]) as z:
        n=z.read('team-'+side+'.stdout').count(b'NGP_MISSING_BASE')
        count+=n;games+=bool(n)
result=dict(summary=score,missing_base_events=count,games_with_missing_base=games,
            caveat='Guard and diagnostic logging have a small fuel cost; results are diagnostic, not a release.')
train.write(ROOT/'base-candidate.json',result)
print(json.dumps(result,indent=2))
