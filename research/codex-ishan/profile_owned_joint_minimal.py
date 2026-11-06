"""EXP254: leave all production graph cost samples free of profiler hooks."""
from shutil import copytree

import ablate_dev as bench
from engine3_pool import HERE,SDK_ROOT,read
from profile_live109_target import HEADER,main
from profile_live111_first import exact_build
from profile_owned_joint_regression import REFERENCE

def prepare(src,enabled,case):
    identity=read(HERE/(REFERENCE.upper()+'_SOURCE_VERIFIED.json'))
    original=SDK_ROOT/'bots'/REFERENCE/'src'
    assert all(bench.digest(original/name)==value for name,value in identity['source_file_hashes'].items())
    copytree(original,src)
    p=src/'common.h';p.write_bytes(f'#define CODEX_MIN_TRACE {int(enabled)}\n#define CODEX_FINE 0\n'.encode()+p.read_bytes())
    h=HEADER.replace('#if CODEX_FINE','#if CODEX_MIN_TRACE')
    h=h.replace('inline unsigned count = 0;','inline unsigned count = 0;\ninline bool active=false;')
    h=h.replace('if (type != CODEX_TARGET_TYPE || round != CODEX_TARGET_ROUND || count >= 96)','if (!active || count >= 96)')
    (src/'codex_min_trace.h').write_text(f"#define CODEX_TARGET_TYPE {case['type']}\n#define CODEX_TARGET_ROUND {case['round']}\n"+h,encoding='utf8',newline='\n')
    p=src/'main.cpp';data=p.read_text(encoding='utf8');data=data.replace('#include "bot.h"','#include "bot.h"\n#include "codex_min_trace.h"')
    anchor='                bot.play_turn();';assert data.count(anchor)==2
    data=data.replace(anchor,'''#if CODEX_MIN_TRACE
                if(bc::round_number()==CODEX_TARGET_ROUND && static_cast<int>(bc::self().champion_name())==CODEX_TARGET_TYPE){
                    codex_trace::active=true;CODEX_FINE_MARK("main_begin",0,0);
                }
#endif
                bot.play_turn();
                CODEX_FINE_MARK("main_play_end",0,0);''')
    anchor='                bot.nn_turn_end();';assert data.count(anchor)==2
    data=data.replace(anchor,anchor+'\n                CODEX_FINE_MARK("main_nn_end",0,0);')
    anchor='        bc::end_turn();';assert data.count(anchor)==1
    data=data.replace(anchor,'''#if CODEX_MIN_TRACE
        if(codex_trace::count){bc::end_turn();codex_trace::flush();bc::resign();}
#endif
'''+anchor)
    p.write_text(data,encoding='utf8',newline='\n')

if __name__=='__main__':
    plan=read(HERE/'LIVE111_OWNED_JOINT_REGRESSION_PLAN.json')
    main(label='ownedjointminimal111',cases=[plan['case']],prepare_fn=prepare,build_fn=exact_build,
         expected_hash=plan['source_build'],project_prefix='live111-owned-joint-minimal')
