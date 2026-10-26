"""Diagnostic only: per-turn fuel trace of the policy-v2 runtime in a disposable source copy (bot/src untouched).

Records, for every 20th round's champion turns: fuel at turn entry, after prepare(), before each head admission
(with its candidate bound/execution reserve and the admission result) and at turn end. Printed in idle() after gameplay.

    python research/early/experiments/fuel_trace.py --model <export> --out <name> [--source <dir>] [--maps ...]
"""
import argparse, json, re, sys, time
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'python')); sys.path.insert(0, str(ROOT / 'tools'))
from nfs import engine  # noqa: E402
from nfs.policy.operations import load_baseline  # noqa: E402
import install_policy_v2  # noqa: E402

H = ['?', 'strategy', 'objective', 'role', 'bank', 'shop', 'move', 'combat', 'engage']


def sub(text, old, new):
    if text.count(old) != 1:
        raise SystemExit('anchor not unique: ' + old[:60])
    return text.replace(old, new)


def patch(src):
    p = src / 'nn_policy_runtime.cpp'; t = p.read_text(encoding='utf-8')
    t = sub(t, 'std::uint64_t fuel() {return bc::fuel_remaining();}',
            'std::uint64_t fuel() {return bc::fuel_remaining();}\n'
            'struct TraceE{int h;std::uint64_t f,bound;std::uint32_t exec;bool adm;std::uint32_t cand=0,dec=0,act=0;};\n'
            'struct Trace{int n=0,round=-1;bool ready=false;std::uint64_t start=0,prepared=0,end=0;TraceE e[16];};\n'
            'Trace g_tr{};')
    t = sub(t, '    const auto ticket=g_core.admit(h,max_k,bound,execution,admission);',
            '    const auto trace_f0=fuel();\n    const auto ticket=g_core.admit(h,max_k,bound,execution,admission);\n'
            '    const int trace_i=g_tr.n<16?g_tr.n:-1;if(trace_i>=0)g_tr.e[g_tr.n++]={hi,trace_f0,bound,execution,ticket.admitted};')
    t = sub(t, '    g_costs[hi].candidate=std::max(g_costs[hi].candidate,candidate_cost);', '    g_costs[hi].candidate=std::max(g_costs[hi].candidate,candidate_cost);if(trace_i>=0)g_tr.e[trace_i].cand=candidate_cost;')
    t = sub(t, '    g_costs[hi].decision=std::max(g_costs[hi].decision,decision_cost);', '    g_costs[hi].decision=std::max(g_costs[hi].decision,decision_cost);if(trace_i>=0)g_tr.e[trace_i].dec=decision_cost;')
    t = sub(t, '    g_costs[hi].execution=std::max(g_costs[hi].execution,action_cost);', '    g_costs[hi].execution=std::max(g_costs[hi].execution,action_cost);if(trace_i>=0)g_tr.e[trace_i].act=action_cost;')
    t = sub(t, '    static bool turn(Bot& b) {', '    static bool turn(Bot& b) {\n        g_tr.n=0;g_tr.start=fuel();g_tr.prepared=0;')
    t = sub(t, '        try {prepare(b);}catch(...) {', '        try {prepare(b);g_tr.prepared=fuel();}catch(...) {')
    t = sub(t, '        inventory.finish(g_coverage,g_abandoned||!handled);g_inventory=nullptr;\n        return handled;',
            '        inventory.finish(g_coverage,g_abandoned||!handled);g_inventory=nullptr;\n'
            '        g_tr.end=fuel();g_tr.round=b.round;g_tr.ready=true;\n        return handled;')
    t = sub(t, '    while(g_core.flush_one()){}',
            '    if(g_tr.ready&&g_tr.round%20==0&&fuel()>15000){\n'
            '        std::printf("NPT round=%d start=%llu prepared=%llu end=%llu n=%d",g_tr.round,(unsigned long long)g_tr.start,(unsigned long long)g_tr.prepared,(unsigned long long)g_tr.end,g_tr.n);\n'
            '        for(int i=0;i<g_tr.n;++i)std::printf(" %d:%llu:%llu:%u:%d:%u:%u:%u",g_tr.e[i].h,(unsigned long long)g_tr.e[i].f,(unsigned long long)g_tr.e[i].bound,g_tr.e[i].exec,int(g_tr.e[i].adm),g_tr.e[i].cand,g_tr.e[i].dec,g_tr.e[i].act);\n'
            '        std::printf("\\n");}\n    g_tr.ready=false;\n    while(g_core.flush_one()){}')
    p.write_text(t, encoding='utf-8', newline='\n')


def main():
    a = argparse.ArgumentParser(); a.add_argument('--model', type=Path, required=True); a.add_argument('--out', required=True)
    a.add_argument('--source', type=Path, default=ROOT / 'bot/src'); a.add_argument('--relax', action='store_true'); a.add_argument('--maps', nargs='+', default=['00collision', '00elkring'])
    a = a.parse_args()
    dest = ROOT / 'artifacts/tmp/fuel_trace' / f'{a.out}-{time.time_ns()}'
    real = install_policy_v2.ROOT
    if a.source.resolve() != (ROOT / 'bot/src').resolve():  # trace a candidate source tree instead of bot/src
        install_policy_v2.ROOT = a.source.resolve().parents[1]
    try:
        install_policy_v2.install(dest / 'bot', 'direct_untrained', a.model.resolve(), 20261025)
    finally:
        install_policy_v2.ROOT = real
    patch(dest / 'bot/src')
    if a.relax:  # measurement only: halve the admission estimate so rarely admitted heads run and get measured
        c = dest / 'bot/src/nn_policy_core.h'; c.write_text(sub(c.read_text(encoding='utf-8'), '        const auto cost=estimate(k,candidate);', '        const auto cost=estimate(k,candidate)/2;'), encoding='utf-8', newline=chr(10))
    wasm = engine.official_build(dest / 'bot', dest / 'trace.wasm')
    _, baseline_wasm = load_baseline()
    rows, per_head, games = [], {}, []
    for name in a.maps:
        for side in ('A', 'B'):
            folder = dest / 'games' / f'{name}-{side}'
            r = engine.run_match(wasm if side == 'A' else baseline_wasm, baseline_wasm if side == 'A' else wasm,
                                 engine.MAPS / (name + '.map26a'), folder, candidate_side=side).row()
            text = engine.team_stdout(folder, side)
            for m in re.finditer(r'NPT round=(\d+) start=(\d+) prepared=(\d+) end=(\d+) n=(\d+)((?: \d+:\d+:\d+:\d+:\d:\d+:\d+:\d+)*)', text):
                start, prepared = int(m[2]), int(m[3])
                rows.append(dict(start=start, prepare=start - prepared if prepared else None, used=start - int(m[4])))
                for e in m[6].split():
                    h, f, bound, ex, adm, cand, dec, act = map(int, e.split(':'))
                    d = per_head.setdefault(H[h], dict(n=0, admitted=0, remaining=[], bound=[], spent_before=[], pairs=[]))
                    d['n'] += 1; d['admitted'] += adm; d['remaining'].append(f); d['bound'].append(bound); d['spent_before'].append(start - f)
                    if adm and cand and cand < 2**31: d['pairs'].append((bound, cand, dec, act))
            print(json.dumps(dict(map=name, side=side, gems=r['gems'], opp=r['opponent_gems'], fuel_exhausted=r['fuel_exhausted'], faults=r['faults'])), flush=True)
            games.append(r)
    med = lambda v: int(median(v)) if v else None
    out = dict(games=dict(n=len(games), gems=sum(g['gems'] for g in games), opponent_gems=sum(g['opponent_gems'] for g in games), wins=sum(g['win'] for g in games),
                          fuel_exhausted=sum(g['fuel_exhausted'] for g in games), faults=sum(g['faults'] for g in games)), turns=len(rows), start_median=med([r['start'] for r in rows]), prepare_median=med([r['prepare'] for r in rows if r['prepare'] is not None]),
               prepare_max=max([r['prepare'] for r in rows if r['prepare'] is not None], default=None), used_median=med([r['used'] for r in rows]),
               heads={h: dict(n=d['n'], admitted=d['admitted'], remaining_median=med(d['remaining']), spent_before_median=med(d['spent_before']),
                              bound_median=med([b for b in d['bound'] if b < 2**40]), bound_max=max([b for b in d['bound'] if b < 2**40], default=None),
                              measured=len(d['pairs']), cand_max=max([q[1] for q in d['pairs']], default=None), cand_p99=sorted(q[1] for q in d['pairs'])[int(.99*(len(d['pairs'])-1))] if d['pairs'] else None,
                              ratio_max=max([q[1]/q[0] for q in d['pairs'] if q[0] < 2**40], default=None), dec_max=max([q[2] for q in d['pairs'] if q[2] < 2**31], default=None),
                              act_max=max([q[3] for q in d['pairs'] if q[3] < 2**31], default=None))
                      for h, d in per_head.items()})
    (dest / 'trace.json').write_text(json.dumps(out, indent=1), encoding='utf-8'); print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
