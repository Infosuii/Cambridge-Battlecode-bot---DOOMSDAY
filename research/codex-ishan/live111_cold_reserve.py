"""First-score reservation and learning, with an erased diagnostic-only fixed-state scope."""
from shutil import copytree

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import HERE,SDK_ROOT,read
from profile_live109_fine import scoped


def patch(target,enabled,case=None,require_ready=False):
    header=target/'common.h'
    flags=f'#define CODEX_COLD_RESERVE {int(enabled)}\n#define CODEX_COLD_SCOPED {int(case is not None)}\n#define CODEX_COLD_REQUIRE_READY {int(require_ready)}\n'
    if case:flags+=f"#define CODEX_COLD_TYPE {case['type']}\n#define CODEX_COLD_ROUND {case['round']}\n"
    header.write_bytes(flags.encode()+header.read_bytes())
    path=target/'nnrec.cpp'
    text=path.read_text(encoding='utf8')
    prelude='''#if CODEX_COLD_RESERVE
#if CODEX_COLD_SCOPED
#define CODEX_COLD_ACTIVE (static_cast<int>(type)==CODEX_COLD_TYPE&&round==CODEX_COLD_ROUND)
#else
#define CODEX_COLD_ACTIVE true
#endif
#endif
'''
    anchor='#include "bot.h"'
    assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'\n'+prelude)
    path.write_text(text,encoding='utf8',newline='\n')
    old='        nn_sg_need = nn_warm == 2 ? nn_est_camps + std::max<std::uint64_t>(nn_need[w.enemies.empty() ? 0 : nn_near() > 10 ? 1 : 2], A2_NN_LAZY_FLOOR) + 2000 : 0;'
    replacement='''#if CODEX_COLD_RESERVE
        const std::uint64_t cold_est=(CODEX_COLD_ACTIVE&&nn_c_camps==0&&(!CODEX_COLD_REQUIRE_READY||w.fields_ready()))?std::max<std::uint64_t>(nn_est_camps,A2_NN_NNUE_CEIL):nn_est_camps;
        nn_sg_need = nn_warm == 2 ? cold_est + std::max<std::uint64_t>(nn_need[w.enemies.empty() ? 0 : nn_near() > 10 ? 1 : 2], A2_NN_LAZY_FLOOR) + 2000 : 0;
#else
'''+old+'''
#endif'''
    apply(path,((old,replacement),))
    old='            if (!first_camps) nn_est_camps = std::max(used + used / 8, nn_est_camps - nn_est_camps / 32); // (the first carries one-time setup)'
    new='''#if CODEX_COLD_RESERVE
            if(CODEX_COLD_ACTIVE||!first_camps) nn_est_camps = std::max(used + used / 8, nn_est_camps - nn_est_camps / 32);
#else
'''+old+'''
#endif'''
    scoped(path,'void Bot::nn_lazy_score() {','#ifdef A2_NN_FCMP',((old,new),))


def prepare(target,enabled):
    source=SDK_ROOT/'bots/live111/src'
    identity=read(HERE/'LIVE111_SOURCE_VERIFIED.json')
    assert all(bench.digest(source/n)==h for n,h in identity['source_file_hashes'].items())
    copytree(source,target);patch(target,enabled,require_ready=True)
