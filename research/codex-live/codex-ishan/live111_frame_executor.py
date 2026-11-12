"""EXP232 global real-budget frame executor; all-off reproduces exact111."""
from shutil import copytree

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import HERE,SDK_ROOT,read


def patch(src,enabled):
    header=src/'common.h';header.write_bytes(f'#define CODEX_FRAME_EXEC {int(enabled)}\n'.encode()+header.read_bytes())
    (src/'codex_coherent_nn_frame.h').write_bytes((HERE/'coherent_nn_frame_v2.h').read_bytes())
    (src/'codex_frame_exec_state.h').write_bytes((HERE/'frame_exec_state.h').read_bytes())
    path=src/'nnrec.cpp';data=path.read_text(encoding='utf8')
    anchor='void Bot::nn_lazy_score() {';assert data.count(anchor)==1
    data=data.replace(anchor,'#if CODEX_FRAME_EXEC\n#include "codex_frame_exec_state.h"\n#endif\n'+anchor)
    first=data.index('    if (nn_warm == 2 && f0 >= nn_est_camps');last=data.index('    nn_mark = bc::fuel_remaining(), nn_round0 = bc::round_number(), nn_field_fuel = 0;',first)
    old=data[first:last]
    data=data[:first]+'#if CODEX_FRAME_EXEC\n'+(HERE/'frame_exec_body.inc').read_text(encoding='utf8')+'\n#else\n'+old+'#endif\n'+data[last:]
    path.write_text(data,encoding='utf8',newline='\n')
    old='        nn_sg_need = nn_warm == 2 ? nn_est_camps + std::max<std::uint64_t>(nn_need[w.enemies.empty() ? 0 : nn_near() > 10 ? 1 : 2], A2_NN_LAZY_FLOOR) + 2000 : 0;'
    new='''#if CODEX_FRAME_EXEC
        cxframe_reset(w.groups.size(),w.bridges_on);
        nn_sg_need=(nn_warm==2&&nn_xdone==15&&w.fields_ready())?cxframe_remaining()+std::max<std::uint64_t>(nn_need[w.enemies.empty()?0:nn_near()>10?1:2],A2_NN_LAZY_FLOOR)+2000:0;
#else
'''+old+'''
#endif'''
    apply(path,((old,new),('void Bot::nn_decide() {','''void Bot::nn_decide() {
#if CODEX_FRAME_EXEC
    struct RealCoreFuel { ~RealCoreFuel(){nn_spent=0;} } real_core_fuel;
#endif''')))
    path=src/'bot.cpp'
    old='hint == participants_hint && pick >= 0 && pick < static_cast<int>(w.groups.size()) &&'
    new=old+'''
#if CODEX_FRAME_EXEC
        pick == target_group &&
#endif'''
    apply(path,((old,new),))


def prepare(src,enabled):
    original=SDK_ROOT/'bots/live111/src';identity=read(HERE/'LIVE111_SOURCE_VERIFIED.json')
    assert all(bench.digest(original/n)==h for n,h in identity['source_file_hashes'].items())
    copytree(original,src);patch(src,enabled)
