"""EXP256: instrument a diagnostic-only stateless tail, leaving earlier callees intact."""
import re

from engine3_pool import HERE,read
from profile_owned_joint_minimal import prepare as minimal
from profile_live109_target import main
from profile_live111_first import exact_build

def prepare(src,enabled,case):
    minimal(src,enabled,case)
    audit=read(HERE/'LIVE111_OWNED_TAIL_CLONE_PLAN.json')
    import ablate_dev as bench
    pre=bench.ROOT/audit['preprocessed_tail_source']
    assert bench.digest(pre)==audit['preprocessed_sha256']
    compiled=pre.read_text(encoding='utf8').split('    shared = read_shared();',1)[1]
    assert not re.search(r'\bstatic\s+',compiled)
    p=src/'bot.cpp';data=p.read_text(encoding='utf8')
    start=data.index('void Bot::play_turn() {');a=data.index('    shared = read_shared();',start)
    tail=data[a:];assert tail.rstrip().endswith('}') and tail.count('void Bot::')==0
    clone=re.sub(r'PROF_CHECK\("(\w+)"\);',lambda m:m[0]+f'\n    codex_trace::mark("{m[1]}",0,0,nn_spent,field_calls);',tail)
    anchor='        if (!farm()) mode = "nofarm";';assert clone.count(anchor)==1
    clone=clone.replace(anchor,'        codex_trace::mark("farm_begin",0,0,nn_spent,field_calls);\n'+anchor+'\n        codex_trace::mark("farm_end",0,0,nn_spent,field_calls);')
    data=data[:a]+'''#if CODEX_MIN_TRACE
    if(codex_trace::active){play_tail_profile();return;}
#endif
'''+data[a:]
    data=data.replace('#include "bot.h"','#include "bot.h"\n#include "codex_min_trace.h"')
    data+='''\n#if CODEX_MIN_TRACE
__attribute__((noinline)) void Bot::play_tail_profile(){
    auto& me=bc::self();
    codex_trace::mark("tail_begin",0,0,nn_spent,field_calls);
'''+clone+'\n#endif\n'
    p.write_text(data,encoding='utf8',newline='\n')
    p=src/'bot.h';data=p.read_text(encoding='utf8');anchor='    void play_turn();';assert data.count(anchor)==1
    data=data.replace(anchor,anchor+'\n#if CODEX_MIN_TRACE\n    void play_tail_profile();\n#endif')
    p.write_text(data,encoding='utf8',newline='\n')

if __name__=='__main__':
    plan=read(HERE/'LIVE111_OWNED_JOINT_REGRESSION_PLAN.json')
    main(label='ownedjointtail111',cases=[plan['case']],prepare_fn=prepare,build_fn=exact_build,
         expected_hash=plan['source_build'],project_prefix='live111-owned-joint-tail')
