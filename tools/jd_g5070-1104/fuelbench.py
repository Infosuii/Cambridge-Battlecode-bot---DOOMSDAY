#!/usr/bin/env python3
"""Fuel contract, baseline fuel profile and stage profile for run g5070-1104 (stdlib only, run with `py`).

  py tools/jd_g5070-1104/fuelbench.py probe --run diag-fprobe-02      -> research/jd-g5070-1104/fuel_contract.json
  py tools/jd_g5070-1104/fuelbench.py bench --run base-v92-dev-01      -> research/jd-g5070-1104/fuel_bench.json (baseline)
  py tools/jd_g5070-1104/fuelbench.py prof  --run diag-fprof-01        -> fuel_bench.json "stages" (+ perturbation)

Inputs are jdrun.py runs in the eval root (<eval>/runs/<run>/{run.json,games/}). `probe` reads the JDFP lines of a
JD_FUELPROBE build (main.cpp) from the replay's team-?.stdout and cross-checks them with the replay fuel trace;
`bench` reads only replay fuel traces (team-?.fuel: 8 settings, then fuel used per unit turn in the order draft turns,
then one turn per champion per round, dead turns included); `prof` merges the JDPF histograms of a JD_FUELPROF build.
A unit turn whose used fuel is >= its budget is a suspension (the turn ran out of fuel and lost the next one).
"""
from __future__ import annotations
import argparse
import collections
import json
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(REPO / 'tools'))
import jdrun  # noqa: E402
from dz import fuel_values  # noqa: E402

RESEARCH = REPO / 'research' / 'jd-g5070-1104'


def run_games(run, arm='cand'):
    out = jdrun.EVAL / 'runs' / run
    meta = json.loads((out / 'run.json').read_text(encoding='utf-8'))
    for c in meta['cells_list']:
        a = arm if not (arm == 'base' and meta['base_is_cand']) else 'cand'
        g = jdrun.game_id(a, c)
        st, rp = out / 'games' / f'{g}.json', out / 'games' / f'{g}.repl26a'
        if st.exists() and rp.exists():
            yield c, g, st, rp
    return meta


def game_info(st, rp, side):
    d = json.loads(st.read_text(encoding='utf-8'))
    me = 'team' + side
    m = d['match']
    budgets, fuel = fuel_values(rp, side)
    draft = sum(r['team'] == me for r in d['roster']['draft'])
    nch = sum(c['team'] == me for c in d['champions'])
    off = 0 if side == 'A' else 4
    b = list(budgets[off:off + 4])
    exhaust = [e2['timestamp']['round'] for e in d['events'] if e['kind'] == 'fuelExhausted' and e['owner']['team'] == me
               for e2 in e['entries']]
    return dict(w=int(m['width']), h=int(m['height']), rounds=m.get('roundsStarted'), draft=draft, nch=nch,
                budgets=b, fuel=list(fuel), exhaust_rounds=exhaust, outcome=m.get('outcome'))


def size_bucket(w, h):
    s = max(w, h)
    return '<=40' if s <= 40 else ('41-60' if s <= 60 else '>60')


def pct(xs, p):
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))]


def summ(xs, budget=None):
    r = dict(n=len(xs), p50=pct(xs, .5), p95=pct(xs, .95), p99=pct(xs, .99), max=max(xs) if xs else None,
             mean=round(sum(xs) / len(xs), 1) if xs else None)
    if budget:
        r['suspensions'] = sum(v >= budget for v in xs)
    return r


def phases(gi):
    """(phase, round, slot, used, budget) per unit turn of one side's trace."""
    bd, bdl, bf, bo = gi['budgets']
    out = []
    for i, v in enumerate(gi['fuel']):
        if i < gi['draft']:
            out.append(('draft_first' if i == 0 else 'draft_later', 0, i, v, bd if i == 0 else bdl))
        else:
            k = i - gi['draft']
            rnd, slot = k // gi['nch'] + 1, k % gi['nch']
            out.append(('first_champion_turn' if rnd == 1 else 'ordinary', rnd, slot, v, bf if rnd == 1 else bo))
    return out


def stdout_lines(rp, side):
    with zipfile.ZipFile(rp) as z:
        raw = z.read(f'team-{side.lower()}.stdout').decode('utf-8', errors='replace')
    # Turn output is NUL-padded and two turns' lines can share a physical line: split on both.
    return [ln.strip(' \r') for ln in re.split(r'[\n\x00]+', raw) if ln.strip(' \r')]


# ---------------------------------------------------------------------------------------------------------- probe
JDFP = re.compile(r'JDFP ([DCXRO]) (\d+) r(-?\d+) in (\d+) out (\d+)(?: sus (\d+) t (-?\d+))?(?: dm (\d+))?')


def cmd_probe(a):
    rows = collections.defaultdict(list)
    globals_seen, hosts, draft_hosts, cells, cross = [], [], [], [], []
    after_sus, settings = [], []
    for c, g, st, rp in run_games(a.run):
        gi = game_info(st, rp, c['side'])
        settings.append(gi['budgets'])
        cells.append(dict(game=g, map=c['map'], opp=c['opp'], side=c['side'], w=gi['w'], h=gi['h']))
        lines = stdout_lines(rp, c['side'])
        per_type = collections.defaultdict(list)
        probe_draft = []
        for ln in lines:
            m = JDFP.match(ln)
            if m:
                ph, k, r, fin, fout, sus, t, dm = m.groups()
                rec = dict(k=int(k), r=int(r), fin=int(fin), fout=int(fout), sus=int(sus or 0), t=t, game=g)
                rows[ph].append(rec)
                if ph == 'D':
                    probe_draft.append(rec)
                else:
                    per_type[t].append(rec)
            elif ln.startswith('JDFP G'):
                p = ln.split()
                globals_seen.append(dict(marker=p[3], dm=int(p[5]), b0=int(p[7]), draft_turns_in_vm=int(p[9]), game=g))
            elif ln.startswith('JDFP H draft-map-error'):
                draft_hosts.append(dict(error=ln[len('JDFP H draft-map-error '):], game=g))
            elif ln.startswith('JDFP H'):
                p = ln.split()
                kv = {p[i]: int(p[i + 1]) for i in range(2, len(p) - 1, 2)}
                (draft_hosts if not per_type else hosts).append(dict(kv, game=g))
        # what the turn after a suspension sees: entry fuel and the round gap
        for t, recs in per_type.items():
            recs.sort(key=lambda x: x['k'])
            for x, y in zip(recs, recs[1:]):
                if x['sus']:
                    after_sus.append(dict(next_in=y['fin'], round_gap=y['r'] - x['r'], game=g))
        # trace cross-check: draft first turn used (trace) vs probe in/out; first champion turn startup overhead
        tr = phases(gi)
        if probe_draft:
            d0 = min(probe_draft, key=lambda x: x['k'])
            cross.append(dict(game=g, draft_first_trace_used=tr[0][3], draft_first_budget=gi['budgets'][0],
                              probe_in=d0['fin'], probe_used=d0['fin'] - d0['fout'],
                              startup_before_main=gi['budgets'][0] - d0['fin']))
    cfirst = rows['C']
    contract = dict(
        generated_by='tools/jd_g5070-1104/fuelbench.py probe --run ' + a.run,
        build='JD_FUELPROBE=1 (diagnostic; main.cpp prints one JDFP line per unit turn)',
        engine='cambc 4.0.0 / engine 2.0.0 (official fuel, no --fuel-quantum)',
        cells=cells,
        settings_block=dict(note='replay team-?.fuel settings (per side: draft first, draft later, first champion turn, ordinary)',
                            values=sorted({tuple(x) for x in settings})),
        phases=dict(
            draft_first=dict(budget_entry=summ([x['fin'] for x in rows['D'] if x['k'] == 0]),
                             used_by_v92_logic=summ([x['fin'] - x['fout'] for x in rows['D'] if x['k'] == 0]),
                             trace_used=summ([x['draft_first_trace_used'] for x in cross]),
                             startup_before_main=summ([x['startup_before_main'] for x in cross])),
            draft_later=dict(budget_entry=summ([x['fin'] for x in rows['D'] if x['k'] > 0]),
                             used=summ([x['fin'] - x['fout'] for x in rows['D'] if x['k'] > 0]),
                             draft_turns_per_vm=max((x['k'] for x in rows['D']), default=-1) + 1),
            first_champion_turn=dict(budget_entry=summ([x['fin'] for x in cfirst]),
                                     used=summ([x['fin'] - x['fout'] for x in cfirst if not x['sus']]),
                                     suspended=sum(x['sus'] > 0 for x in cfirst), n=len(cfirst)),
            respawn_first_turn=dict(budget_entry=summ([x['fin'] for x in rows['R']]),
                                    used=summ([x['fin'] - x['fout'] for x in rows['R'] if not x['sus']]),
                                    suspended=sum(x['sus'] > 0 for x in rows['R'])),
            dead_turn=dict(budget_entry=summ([x['fin'] for x in rows['X']]),
                           used=summ([x['fin'] - x['fout'] for x in rows['X'] if not x['sus']]),
                           suspended=sum(x['sus'] > 0 for x in rows['X'])),
            ordinary=dict(budget_entry=summ([x['fin'] for x in rows['O']]),
                          used=summ([x['fin'] - x['fout'] for x in rows['O'] if not x['sus']]),
                          suspended=sum(x['sus'] > 0 for x in rows['O']), n=len(rows['O'])),
        ),
        after_suspension=dict(n=len(after_sus), next_turn_entry=summ([x['next_in'] for x in after_sus]),
                              round_gap=dict(collections.Counter(x['round_gap'] for x in after_sus))),
        carry_over=dict(ordinary_entries_above_100k=sum(x['fin'] > 100000 for x in rows['O']),
                        ordinary_entries_below_99990=sum(x['fin'] < 99990 for x in rows['O'])),
        draft_vm=dict(draft_turns_seen_by_one_vm=max((x['k'] for x in rows['D']), default=-1) + 1,
                      gameplay_vms=len(globals_seen),
                      gameplay_sees_draft_global=sum(x['marker'] != '0' for x in globals_seen),
                      gameplay_draft_turns_in_vm=sorted({x['draft_turns_in_vm'] for x in globals_seen}),
                      draft_memory_size_in_gameplay=sorted({x['dm'] for x in globals_seen}),
                      draft_memory_byte0_in_gameplay=sorted({x['b0'] for x in globals_seen})),
        host_calls_gameplay=dict(n=len(hosts), fuel_remaining=summ([x['fr'] for x in hosts]),
                                 walls_ref=summ([x['walls'] for x in hosts]), bitboard_or=summ([x['or'] for x in hosts]),
                                 distance_field_full=summ([x['df'] for x in hosts]),
                                 df_per_chunk=summ([round(x['df'] / max(1, x['chunks']), 1) for x in hosts]),
                                 by_map=sorted({(x['w'], x['h'], x['chunks'], x['df']) for x in hosts})[:12]),
        host_calls_draft=draft_hosts[:8],
        draft_trace_cross_check=cross[:8],
        agent2_E120=dict(draft_first=10_000_000, first_champion_turn=200_000, ordinary=100_000, carry_over=False,
                         v92_median=56_000, v92_p10_p90=[25_000, 71_000]),
    )
    (RESEARCH / 'fuel_contract.json').write_text(json.dumps(contract, indent=1), encoding='utf-8')
    print(json.dumps(contract['phases'], indent=1))
    print(json.dumps({k: contract[k] for k in ('after_suspension', 'carry_over', 'draft_vm', 'host_calls_gameplay')}, indent=1))
    print('draft hosts', draft_hosts[:3])


# ---------------------------------------------------------------------------------------------------------- bench
def bench_run(run, arm='cand'):
    by = collections.defaultdict(list)
    sus_round = collections.Counter()
    sus_map = collections.Counter()
    sus_cells = collections.Counter()
    games = 0
    exhaust = 0
    for c, g, st, rp in run_games(run, arm):
        gi = game_info(st, rp, c['side'])
        games += 1
        exhaust += len(gi['exhaust_rounds'])
        sb = size_bucket(gi['w'], gi['h'])
        for ph, rnd, slot, v, b in phases(gi):
            by[(ph, sb)].append((v, b))
            by[(ph, 'all')].append((v, b))
            if b and v >= b:
                sus_round[(rnd // 100) * 100] += 1
                sus_map[c['map']] += 1
                sus_cells[(c['map'], c['opp'].split('-')[0], c['side'], rnd)] += 1
    table = {}
    for (ph, sb), vals in sorted(by.items()):
        b = vals[0][1]
        table.setdefault(ph, {})[sb] = summ([v for v, _ in vals], b) | dict(budget=b)
    return dict(run=run, arm=arm, games=games, engine_fuel_exhausted=exhaust, per_phase=table,
                suspensions_total=sum(sus_map.values()),
                suspensions_by_round=dict(sorted(sus_round.items())),
                suspensions_by_map=dict(sus_map.most_common(15)),
                top_suspension_rounds=[dict(map=k[0], opp=k[1], side=k[2], round=k[3], n=n) for k, n in sus_cells.most_common(15)])


def load_bench():
    p = RESEARCH / 'fuel_bench.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}


def save_bench(b):
    (RESEARCH / 'fuel_bench.json').write_text(json.dumps(b, indent=1), encoding='utf-8')


def cmd_bench(a):
    b = load_bench()
    r = bench_run(a.run, a.arm)
    b.setdefault('baseline', {})[f'{a.run}:{a.arm}'] = r
    save_bench(b)
    for ph, t in r['per_phase'].items():
        for sb, s in t.items():
            print(f'{ph:20s} {sb:6s} {json.dumps(s)}')
    print('suspensions', r['suspensions_total'], 'engine fuelExhausted', r['engine_fuel_exhausted'])
    print('by round', r['suspensions_by_round'])
    print('by map', r['suspensions_by_map'])
    print('top', r['top_suspension_rounds'][:8])


# ----------------------------------------------------------------------------------------------------------- prof
JDPF = re.compile(r'JDPF R(\d+) t(-?\d+) (\S+) (\d+) n (\d+) sum (\d+) max (\d+):(.*)')
STAGE = {
    'claims': 'claims_decode', 'init': 'first_turn_init', 'refresh': 'observe', 'w_update': 'observe', 'world': 'observe',
    'episode': 'observe', 'sight': 'observe', 'events': 'observe',
    'w_vis': 'observe', 'w_groups': 'observe', 'w_hot': 'observe', 'w_champs': 'observe', 'w_ward': 'observe', 'w_sight': 'observe',
    'shop': 'shop', 'support': 'support_casts', 'wardrev': 'vision', 'ambush': 'vision',
    'enemies': 'contact', 'td0': 'tactical_decide', 'td1': 'tactical_decide',
    'd_farm': 'farm_route', 'd_opp': 'farm_route', 'decide': 'decide_other', 'score0': 'farm_route', 'route0': 'farm_route',
    'route1': 'farm_route', 'farm0': 'farm_route', 'farmsel': 'farm_route', 'farmmove': 'farm_route', 'field': 'farm_route',
    'tail': 'tail', 'fields': 'tail_fields', 'bushpre': 'tail', 'end': 'tail_end', 'TURN': 'TURN',
}
PHASE = {0: 'first_turn', 1: 'ordinary', 2: 'contact', 3: 'dead', 4: 'crossed_round'}


def stage_of(name):
    if name in STAGE:
        return STAGE[name]
    if name.startswith('e_'):
        return 'contact'
    if name.startswith(('c_', 's_', 'sg_', 'f_')):
        return 'farm_route'
    if name.startswith(('wt_', 'cc_')):
        return 'walk'
    return 'other'


def hist_pct(h, p):
    n = sum(h.values())
    if not n:
        return None
    k, acc = 0, 0
    for b in sorted(h):
        acc += h[b]
        if acc >= p * n:
            return (b + 1) * 1000  # upper edge of the 1k bin
    return (max(h) + 1) * 1000


def cmd_prof(a):
    agg = {}
    for c, g, st, rp in run_games(a.run):
        for ln in stdout_lines(rp, c['side']):
            m = JDPF.match(ln)
            if not m:
                continue
            _, _, name, ph, n, s, mx, bins = m.groups()
            for key in ((name, int(ph)), (stage_of(name) + '*', int(ph))):
                e = agg.setdefault(key, dict(n=0, sum=0, max=0, h=collections.Counter()))
                e['n'] += int(n)
                e['sum'] += int(s)
                e['max'] = max(e['max'], int(mx))
                for kv in bins.split():
                    b, _, cnt = kv.partition('=')
                    if b.isdigit() and cnt.isdigit():
                        e['h'][int(b)] += int(cnt)
    rows = []
    for (name, ph), e in sorted(agg.items(), key=lambda kv: (kv[0][1], -kv[1]['sum'])):
        rows.append(dict(name=name, phase=PHASE.get(ph, ph), n=e['n'], mean=round(e['sum'] / max(1, e['n'])),
                         p50=hist_pct(e['h'], .5), p95=hist_pct(e['h'], .95), p99=hist_pct(e['h'], .99), max=e['max']))
    # Profiler perturbation: profiled (cand) vs unprofiled (base) per-turn fuel on the same cells, from replay traces.
    pert = {}
    for arm in ('cand', 'base'):
        vals, sus, ex = [], 0, 0
        for c, g, st, rp in run_games(a.run, arm):
            gi = game_info(st, rp, c['side'])
            ex += len(gi['exhaust_rounds'])
            for ph, rnd, slot, v, b in phases(gi):
                if ph == 'ordinary':
                    vals.append(v)
                    sus += v >= b
        pert[arm] = dict(summ(vals), suspensions=sus, engine_fuel_exhausted=ex)
    b = load_bench()
    b['stages'] = dict(run=a.run, note='1k-fuel histogram percentiles (upper bin edge); "stage*" rows aggregate names; '
                       'value = fuel from the previous checkpoint to this one', rows=rows, perturbation=pert)
    save_bench(b)
    for r in rows:
        if r['name'].endswith('*') or r['name'] == 'TURN':
            print(json.dumps(r))
    print('perturbation', json.dumps(pert))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    for n, f in (('probe', cmd_probe), ('bench', cmd_bench), ('prof', cmd_prof)):
        p = sp.add_parser(n)
        p.add_argument('--run', required=True)
        p.add_argument('--arm', default='cand')
        p.set_defaults(fn=f)
    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
