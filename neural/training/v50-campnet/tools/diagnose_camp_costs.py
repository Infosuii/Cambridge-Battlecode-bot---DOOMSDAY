"""Measure release-only lab logging and observation-order costs; no training."""
from pathlib import Path
import json
import shutil
import train

PARENT=train.ROOT;ROOT=PARENT/'diagnosis-phase2';train.ROOT=ROOT
protocol=json.loads((PARENT/'phase2-two-hours/protocol.json').read_text())
maps=sorted(map(Path,protocol['training_maps']+protocol['selection_maps']+protocol['final_holdout_maps']))
variants=['trained-no-lab-log','trained-deferred-features-no-lab-log']
train.write(ROOT/'cost-protocol.json',dict(variants=variants,maps=[str(p) for p in maps],purpose='Diagnostic only; weights unchanged, no promotion or upload.'))
scores={}
for label in variants:
    src=ROOT/label/'src'
    if not src.exists():shutil.copytree(PARENT/'phase2-two-hours/release/bot_neural/src',src)
    p=src/'bot.cpp';s=(PARENT/'phase2-two-hours/release/bot_neural/src/bot.cpp').read_text(encoding='utf-8')
    marker='#if A2_LAB\n    if (lab::cn_cfg[2] < lab::kCnLogMax) {'
    s=s.replace(marker,'#if 0 // Diagnostic: remove camp laboratory memory logging in release\n    if (lab::cn_cfg[2] < lab::kCnLogMax) {',1)
    if label.startswith('trained-deferred') and 'Diagnostic deferred observations' not in s:
        begin=s.index('            int elks = 0, wolves = 0, big = 0;',s.index('if (score > 0.0f && n_cn < kCnMax'))
        end=s.index('        }\n#endif',begin)
        feature_code=s[begin:end]
        s=s[:begin]+'            c.f[16] = camp_taken_mult; // Diagnostic deferred observations\n'+s[end:]
        needle='        float* f = cn[k].f;'
        populate='''        {
            CnCand& c = cn[k];
            const auto& g = w.groups[static_cast<std::size_t>(c.gi)];
            const int need = c.need;
            const float camp_taken_mult = c.f[16];
'''+feature_code+'        }\n'
        s=s.replace(needle,populate+needle,1)
    p.write_text(s,encoding='utf-8')
    wasm=train.compile_bot(src,ROOT/f'builds/{label}.wasm',20)
    score,_=train.evaluate_artifact(wasm,label,maps,[PARENT/'phase2-two-hours/opponents/original.wasm'],20)
    scores[label]=score;print(label,json.dumps(score),flush=True)
train.write(ROOT/'cost-ablation.json',scores)
