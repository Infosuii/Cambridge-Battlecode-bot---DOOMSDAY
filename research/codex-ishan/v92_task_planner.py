"""EXP291 isolated original-v92 task-selector replacement; exact disabled path."""
from pathlib import Path
from shutil import copytree
import math
import ablate_dev as bench
from engine3_pool import HERE,SDK_ROOT

BASE=SDK_ROOT/'bots/v92-e3/src'
REFERENCE='5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47'


def prepare(src,mode,parameters=(1.,1.,1.,1.1)):
    assert mode in (0,1,2) and len(parameters)==4 and all(math.isfinite(v) and v>0 for v in parameters)
    repo=bench.ROOT/'bots/v92/src'
    hashes=lambda root:{p.relative_to(root).as_posix():bench.digest(p) for p in root.rglob('*') if p.is_file()}
    assert hashes(BASE)==hashes(repo) and bench.digest(BASE.parent/'bot.wasm')==REFERENCE
    copytree(BASE,src)
    def literal(v):
        s=format(v,'.9g');return s+('' if '.' in s or 'e' in s else '.0')+'f'
    macros=f'#define CODEX_TASK_MODE {mode}\n'+''.join(f'#define CODEX_TASK_{name} {literal(v)}\n' for name,v in zip(('GOLD','CREW','RISK','STICKY'),parameters))
    p=src/'common.h';p.write_bytes(macros.encode()+p.read_bytes())
    (src/'codex_task_planner.inc').write_bytes((HERE/'task_planner.inc').read_bytes())
    p=src/'bot.h';data=p.read_text(encoding='utf8');anchor='    bool farm();';assert data.count(anchor)==1
    data=data.replace(anchor,anchor+'''
#if CODEX_TASK_MODE
    int codex_task_group=-1,codex_task_round=-1000,codex_task_need=1;
    float codex_task_hp=0;
    int codex_task_pick(int& best_need,float& best_score);
#endif''')
    p.write_text(data,encoding='utf8',newline='\n')
    p=src/'bot.cpp';data=p.read_text(encoding='utf8');anchor='bool Bot::farm() {';assert data.count(anchor)==1
    data=data.replace(anchor,'''#if CODEX_TASK_MODE
#if V58_DIRECTOR
#error Task planner requires the original inactive director
#endif
#include "codex_task_planner.inc"
#endif

'''+anchor)
    begin=data.index('bool Bot::farm() {');start=data.index('    if (low_fuel) {',begin);end=data.index('    if (best != target_group) {',start)
    selector=data[start:end]
    anchor='        best = target_group;';assert selector.count(anchor)==1
    selector=selector.replace(anchor,anchor+'''
#if CODEX_TASK_MODE
        if(codex_task_group==best)best_need=codex_task_need;
#endif''')
    data=data[:start]+'''#if CODEX_TASK_MODE
    const bool codex_task_active=!low_fuel&&w.fields_ready()&&!(w.no_bank&&w.altar_gated);
    if(codex_task_active){
        no_initiate=false;duo_ignore_slot=-1;plan_bank_round=-1;
        best=codex_task_pick(best_need,best_score);
    }else{
#endif
'''+selector+'''#if CODEX_TASK_MODE
    }
#endif
'''+data[end:]
    # The legacy on-site poorer-collector handoff must reselect through this same planner.
    begin=data.index('    if (best != target_group) {',data.index('bool Bot::farm() {'))
    end=data.index('    auto& g = w.groups[best];',begin);body=data[begin:end]
    anchor='        best = score_groups(1, best_need, best_score);';assert body.count(anchor)==1
    body=body.replace(anchor,'''#if CODEX_TASK_MODE
        best=codex_task_active?codex_task_pick(best_need,best_score):score_groups(1,best_need,best_score);
#else
'''+anchor+'''
#endif''')
    data=data[:begin]+body+data[end:];p.write_text(data,encoding='utf8',newline='\n')
