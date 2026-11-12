"""Diagnostic only: which `return` in policy-v2 dispatch() ends each turn (disposable copy; bot/src untouched).

Every `return X;` inside dispatch() becomes `return (g_exit=__LINE__, X);`. For rounds >= 300 a histogram of exit lines
(plus the turn's intent/objective/engagement) is kept and printed every 100 rounds after gameplay as `NPE ...`.

    python research/early/experiments/dispatch_exits.py --model <export> --map 00collision
"""
import argparse, re, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fuel_trace as T  # noqa: E402
from nfs import engine  # noqa: E402


def patch(src):
    r = src / 'nn_policy_runtime.cpp'; v = r.read_text(encoding='utf-8')
    start = v.index('    static bool dispatch(Bot& b) {')
    end = v.index('\n    }\n', start)
    body = re.sub(r'return ([^;]+);', r'return (g_exit=__LINE__,\1);', v[start:end])
    v = v[:start] + body + v[end:]
    v = T.sub(v, 'std::uint64_t fuel() {return bc::fuel_remaining();}',
              'std::uint64_t fuel() {return bc::fuel_remaining();}\nint g_exit=0;std::uint32_t g_exits[1024]{};std::uint32_t g_intents[8]{};')
    v = T.sub(v, '        try {handled=dispatch(b);}catch(...) {handled=fallback();}',
              '        g_exit=0;try {handled=dispatch(b);}catch(...) {handled=fallback();g_exit=1;}\n'
              '        if(b.round>=300){if(g_exit>=0&&g_exit<1024)++g_exits[g_exit];if(g_state.intent>=-1&&g_state.intent<7)++g_intents[g_state.intent+1];}')
    v = T.sub(v, '    while(g_core.flush_one()){}',
              '    if(bc::round_number()%100==0&&bc::round_number()>=400&&fuel()>20000){std::printf("NPE r=%u",unsigned(bc::round_number()));'
              'for(int i=0;i<1024;++i)if(g_exits[i])std::printf(" L%d=%u",i,g_exits[i]);std::printf(" intents");'
              'for(int i=0;i<8;++i)std::printf(" %u",g_intents[i]);std::printf(" obj=%d\\n",g_state.objective);}\n'
              '    while(g_core.flush_one()){}')
    # Movement decisions after round 300: calls, can_move false, built K, chosen kind (0 walk, 1/2 dash, 3 hold).
    v = T.sub(v, 'int g_exit=0;', 'int g_exit=0;std::uint32_t g_mv_calls=0,g_mv_cant=0,g_mv_k[17]{},g_mv_kind[5]{},g_mv_fail=0,g_mv_reason[16]{};std::uint64_t g_mv_cost=0,g_mv_bound=0,g_mv_n=0,g_mv_cost_max=0;')
    v = T.sub(v, '        if(bc::self().can_move()) {\n            if(!choose(b,H::move,',
              '        if(b.round>=300&&!bc::self().can_move())++g_mv_cant;\n        if(bc::self().can_move()) {\n            if(b.round>=300)++g_mv_calls;\n            if(!choose(b,H::move,')
    v = T.sub(v, '    const auto candidate_cost=elapsed(candidate_start,candidate_round);',
              '    const auto candidate_cost=elapsed(candidate_start,candidate_round);\n'
              '    if(h==H::move&&bc::round_number()>=300&&candidate_cost<UINT32_MAX){g_mv_cost+=candidate_cost;g_mv_bound+=bound;++g_mv_n;if(candidate_cost>g_mv_cost_max)g_mv_cost_max=candidate_cost;}')
    v = T.sub(v, '    if(!built){decision.head=h;decision.K=0;}',
              '    if(!built){decision.head=h;decision.K=0;}\n    if(h==H::move&&bc::round_number()>=300)++g_mv_k[std::min(16,std::max(0,static_cast<int>(decision.K)))];')
    v = T.sub(v, '    if(result.choice<0){g_inventory->record(h,false);++g_costs[hi].refused;return false;}',
              '    if(result.choice<0){if(h==H::move&&bc::round_number()>=300)++g_mv_reason[std::min(15,int(result.reason))];g_inventory->record(h,false);++g_costs[hi].refused;return false;}')
    v = T.sub(v, '    const auto before=fuel();nnp::Execution actual{};',
              '    if(h==H::move&&bc::round_number()>=300)++g_mv_kind[std::min<std::uint32_t>(4,result.action>>30)];\n    const auto before=fuel();nnp::Execution actual{};')
    v = T.sub(v, '    if(h==H::move&&bc::round_number()>=300)++g_mv_kind[',
              '    if(h==H::move&&bc::round_number()>=300&&bc::round_number()%50==0&&fuel()>8000){std::printf("NPF r=%u K=%d ctx=%d choice=%d",unsigned(bc::round_number()),int(decision.K),int(decision.context),int(result.choice));'
              'for(int k=0;k<decision.K;++k){std::printf(" |");for(int j=0;j<12;++j)std::printf(" %.3f",double(decision.feat[k*12+j]));}std::printf("\\n");}\n'
              '    if(h==H::move&&bc::round_number()>=300)++g_mv_kind[')
    v = T.sub(v, 'std::printf(" obj=%d\\n",g_state.objective);}',
              'std::printf(" obj=%d mv calls=%u cant=%u kinds=%u/%u/%u/%u K:",g_state.objective,g_mv_calls,g_mv_cant,g_mv_kind[0],g_mv_kind[1],g_mv_kind[2],g_mv_kind[3]);'
              'for(int i=0;i<17;++i)if(g_mv_k[i])std::printf(" %d=%u",i,g_mv_k[i]);std::printf(" cost=%llu bound=%llu max=%llu why:",(unsigned long long)(g_mv_n?g_mv_cost/g_mv_n:0),(unsigned long long)(g_mv_n?g_mv_bound/g_mv_n:0),(unsigned long long)g_mv_cost_max);'
              'for(int i=0;i<16;++i)if(g_mv_reason[i])std::printf(" %d=%u",i,g_mv_reason[i]);std::printf("\\n");}')
    r.write_text(v, encoding='utf-8', newline='\n')
    return src / 'nn_policy_runtime.cpp'


def main():
    a = argparse.ArgumentParser(); a.add_argument('--model', type=Path, required=True); a.add_argument('--map', default='00collision')
    a = a.parse_args()
    dest = T.ROOT / 'artifacts/tmp/dispatch_exits' / str(time.time_ns())
    T.install_policy_v2.install(dest / 'bot', 'direct_evaluation', a.model.resolve(), 20261025)
    patched = patch(dest / 'bot/src')
    wasm = engine.official_build(dest / 'bot', dest / 'x.wasm')
    _, baseline_wasm = T.load_baseline()
    folder = dest / 'games' / f'{a.map}-A'
    row = engine.run_match(wasm, baseline_wasm, engine.MAPS / (a.map + '.map26a'), folder, candidate_side='A').row()
    lines = re.findall(r'NPE[^\n]*', engine.team_stdout(folder, 'A'))
    print('gems', row['gems'], 'rounds', row['rounds'], 'lines', len(lines))
    for l in lines[-6:]: print(l)
    print('PATCHED', patched)


if __name__ == '__main__':
    main()
