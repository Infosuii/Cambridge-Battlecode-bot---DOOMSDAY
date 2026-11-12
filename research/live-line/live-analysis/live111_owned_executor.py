"""EXP247 current-source exclusive in-place executor, erased all-off."""
from shutil import copytree

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import HERE,SDK_ROOT,read


def patch(src,enabled):
    p=src/'common.h';p.write_bytes(f'#define CODEX_OWNED_EXEC {int(enabled)}\n'.encode()+p.read_bytes())
    (src/'codex_owned_nn_frame.h').write_bytes((HERE/'owned_nn_frame.h').read_bytes())
    (src/'codex_owned_exec_state.h').write_bytes((HERE/'owned_exec_state.h').read_bytes())
    p=src/'nnrec.cpp';data=p.read_text(encoding='utf8')
    anchor='static std::int16_t nn_lf[kNF] = {};';assert data.count(anchor)==1
    data=data.replace(anchor,anchor+'\n#if CODEX_OWNED_EXEC\n#include "codex_owned_exec_state.h"\n#endif')
    for anchor in ('static void nn_run_stages(std::uint64_t floor, int rnd) {','void Bot::nn_x_refresh(int x) {'):
        assert data.count(anchor)==1
        data=data.replace(anchor,anchor+'\n#if CODEX_OWNED_EXEC\n    if(cxowned_active)return;\n#endif')
    first=data.index('    if (nn_warm == 2 && f0 >= nn_est_camps');last=data.index('    nn_mark = bc::fuel_remaining(), nn_round0 = bc::round_number(), nn_field_fuel = 0;',first)
    data=data[:first]+'#if CODEX_OWNED_EXEC\n'+(HERE/'owned_exec_body.inc').read_text(encoding='utf8')+'\n#else\n'+data[first:last]+'#endif\n'+data[last:]
    p.write_text(data,encoding='utf8',newline='\n')
    old='        nn_sg_need = nn_warm == 2 ? nn_est_camps + std::max<std::uint64_t>(nn_need[w.enemies.empty() ? 0 : nn_near() > 10 ? 1 : 2], A2_NN_LAZY_FLOOR) + 2000 : 0;'
    new='''#if CODEX_OWNED_EXEC
        cxowned_reset(w.groups.size(),w.bridges_on,round,A2_NN_LAZY_TTL);
        nn_sg_need=(nn_warm==2&&nn_xdone==15&&w.fields_ready())?cxowned_remaining()+std::max<std::uint64_t>(nn_need[w.enemies.empty()?0:nn_near()>10?1:2],A2_NN_LAZY_FLOOR)+2000:0;
#else
'''+old+'''
#endif'''
    apply(p,((old,new),('void Bot::nn_decide() {','''void Bot::nn_decide() {
#if CODEX_OWNED_EXEC
    struct RealCoreFuel { ~RealCoreFuel(){nn_spent=0;} } real_core_fuel;
#endif'''),('    if (over) return; // already into the next round\'s fuel','''    if (over) return; // already into the next round's fuel
#if CODEX_OWNED_EXEC
    cxowned_reset(w.groups.size(),w.bridges_on,round,A2_NN_LAZY_TTL);
    if(cxowned_active)return; // preserve exclusive ownership through ordinary gameplay turns
#endif''')))
    p=src/'bot.cpp';old='hint == participants_hint && pick >= 0 && pick < static_cast<int>(w.groups.size()) &&'
    apply(p,((old,old+'\n#if CODEX_OWNED_EXEC\n        pick == target_group &&\n#endif'),))


def prepare(src,enabled):
    original=SDK_ROOT/'bots/live111/src';pins=read(HERE/'LIVE111_SOURCE_VERIFIED.json')
    assert all(bench.digest(original/n)==sha for n,sha in pins['source_file_hashes'].items())
    copytree(original,src);patch(src,enabled)
