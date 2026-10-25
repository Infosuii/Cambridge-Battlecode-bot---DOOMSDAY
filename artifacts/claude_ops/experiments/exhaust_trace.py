"""Diagnostic only: where do fuel-exhausted policy-v2 turns stop? (disposable copy; bot/src untouched)

A persistent stage marker is updated through the turn (entry, prepare, per-head admit/build/decide/execute, dispatch
end, each idle job). A turn cut off by fuel exhaustion never reaches the end marker, so the next turn entry counts the
stage where it stopped. The histogram is printed after gameplay as `NPX stage=count ...`.
Stage codes: 1 entry, 2 prepared, 10+h admit, 20+h built, 30+h decided, 40+h executed, 3 dispatch done,
5 idle fields, 6 idle prepare_strategy, 7 idle prepare_tactics, 8 idle flush, 9 done.

    python artifacts/claude_ops/experiments/exhaust_trace.py --model <export> --out <name> --maps 00quadrants
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fuel_trace as T  # noqa: E402
from nfs import engine  # noqa: E402


def patch(src):
    r = src / 'nn_policy_runtime.cpp'; v = r.read_text(encoding='utf-8')
    v = T.sub(v, 'std::uint64_t fuel() {return bc::fuel_remaining();}',
              'std::uint64_t fuel() {return bc::fuel_remaining();}\nint g_stage=9;std::uint32_t g_cut[64]{};\n'
              '#define STG(x) do{g_stage=(x);if(bc::round_number()%8==5)std::printf("S%d r%u c%u f%llu\\n",int(x),'
              'unsigned(bc::round_number()),unsigned(static_cast<bc::handle_champion_t>(bc::self())),(unsigned long long)bc::fuel_remaining());}while(0)')
    v = T.sub(v, '    static bool turn(Bot& b) {', '    static bool turn(Bot& b) {\n        if(g_stage!=9&&g_stage<64)++g_cut[g_stage];STG(1);')
    v = T.sub(v, '        try {prepare(b);}catch(...) {', '        try {prepare(b);STG(2);}catch(...) {')
    v = T.sub(v, '    const auto ticket=g_core.admit(', '    STG(10+hi);\n    const auto ticket=g_core.admit(')
    v = T.sub(v, '    const bool built=build(b,g_state,decision);', '    const bool built=build(b,g_state,decision);STG(20+hi);')
    v = T.sub(v, '    const auto result=g_core.decide(ticket,decision,option,', '    STG(30+hi);const auto result=g_core.decide(ticket,decision,option,')
    v = T.sub(v, '    try {actual=execute(b,g_state,result.action);} catch(...) {actual={true,false,false};}',
              '    try {actual=execute(b,g_state,result.action);} catch(...) {actual={true,false,false};}STG(40+hi);')
    v = T.sub(v, '        try {handled=dispatch(b);}catch(...) {handled=fallback();}', '        try {handled=dispatch(b);}catch(...) {handled=fallback();}STG(3);')
    v = T.sub(v, '    if(bc::is_draft())return; // There is no acting champion in the draft VM.\n    warmup();',
              '    if(bc::is_draft())return; // There is no acting champion in the draft VM.\n    STG(4);warmup();')
    v = T.sub(v, '    if(g_bot){nn_policy_access::fields(*g_bot);nnp::prepare_strategy(*g_bot,16000);nnp::prepare_tactics(*g_bot,g_state,16000);}\n'
                 '    // Record output and coverage output consume only fuel remaining after gameplay.\n    while(g_core.flush_one()){}',
              '    if(g_bot){STG(5);nn_policy_access::fields(*g_bot);STG(6);nnp::prepare_strategy(*g_bot,16000);STG(7);nnp::prepare_tactics(*g_bot,g_state,16000);}\n'
              '    STG(8);\n    while(g_core.flush_one()){}\n'
              '    if(bc::round_number()%100==0&&fuel()>20000){std::printf("NPX");for(int i=0;i<64;++i)if(g_cut[i])std::printf(" %d=%u",i,g_cut[i]);std::printf("\\n");}\n'
              '    STG(9);')
    r.write_text(v, encoding='utf-8', newline='\n')


def main():
    import argparse, time
    a = argparse.ArgumentParser(); a.add_argument('--model', type=Path, required=True); a.add_argument('--out', required=True)
    a.add_argument('--maps', nargs='+', default=['00quadrants']); a = a.parse_args()
    dest = T.ROOT / 'artifacts/tmp/exhaust_trace' / f'{a.out}-{time.time_ns()}'
    T.install_policy_v2.install(dest / 'bot', 'direct_evaluation', a.model.resolve(), 20261025)
    patch(dest / 'bot/src')
    wasm = engine.official_build(dest / 'bot', dest / 'x.wasm')
    _, baseline_wasm = T.load_baseline()
    for name in a.maps:
        for side in ('A', 'B'):
            folder = dest / 'games' / f'{name}-{side}'
            row = engine.run_match(wasm if side == 'A' else baseline_wasm, baseline_wasm if side == 'A' else wasm,
                                   engine.MAPS / (name + '.map26a'), folder, candidate_side=side).row()
            hist = re.findall(r'NPX[^\n]*', engine.team_stdout(folder, side))
            print(name, side, 'fuel_exhausted', row['fuel_exhausted'], 'gems', row['gems'], hist[-1] if hist else 'NPX none', flush=True)


if __name__ == '__main__':
    main()
