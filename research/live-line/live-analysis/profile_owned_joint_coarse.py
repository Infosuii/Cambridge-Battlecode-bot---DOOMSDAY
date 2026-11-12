"""EXP255: six short-circuit guarded policy boundaries, no graph cost hooks."""
from engine3_pool import HERE,read
from profile_owned_joint_minimal import prepare as minimal
from profile_live109_target import main
from profile_live111_first import exact_build

def prepare(src,enabled,case):
    minimal(src,enabled,case)
    p=src/'bot.cpp';data=p.read_text(encoding='utf8')
    data=data.replace('#include "bot.h"','#include "bot.h"\n#include "codex_min_trace.h"')
    for name in ('world','enemies','farm0','farmsel','farmmove','decide'):
        anchor=f'PROF_CHECK("{name}");';assert data.count(anchor)==1
        data=data.replace(anchor,anchor+f'''\n#if CODEX_MIN_TRACE
    if(codex_trace::active)codex_trace::mark("{name}",0,0,nn_spent,field_calls);
#endif''')
    p.write_text(data,encoding='utf8',newline='\n')

if __name__=='__main__':
    plan=read(HERE/'LIVE111_OWNED_JOINT_REGRESSION_PLAN.json')
    main(label='ownedjointcoarse111',cases=[plan['case']],prepare_fn=prepare,build_fn=exact_build,
         expected_hash=plan['source_build'],project_prefix='live111-owned-joint-coarse')
