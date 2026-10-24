"""Tables and gate verdicts from evaluation results (Agent H).

  python tools/eval_report.py evaluation/results/<label>/results.json                 # per-opponent table
  python tools/eval_report.py <cand>/results.json --baseline <ref>/results.json         # paired, map-cluster CIs
  python tools/eval_report.py <cand>/results.json --baseline <ref>/results.json --gate final [--incumbent <inc>]
      -> writes <cand dir>/gate-<mode>.json and prints PASS/FAIL with every failed check (also logged in the ledger
         for mode final). The gate never selects among candidates; it judges one candidate against the protocol.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from nfs import engine  # noqa: E402
from nfs.evaluate import gate as gate_mod  # noqa: E402
from nfs.evaluate import ledger as ledger_mod  # noqa: E402
from nfs.evaluate import protocol as proto  # noqa: E402
from nfs.evaluate import stats  # noqa: E402


def fmt_ci(d):
    return f"{d['point']:+.3f} [{d['ci95'][0]:+.3f}, {d['ci95'][1]:+.3f}] lb{d['one_sided_lower']:+.3f}"


def table(doc) -> str:
    rows = doc['rows']
    t = stats.opponent_table(rows)
    lines = [f"## {doc['label']} ({doc['schedule']}; {doc['labels'].get('schedule_label') or doc['labels'].get('claim', '')})",
             f"candidate {doc['provenance']['candidate_sha256'][:16]} profile {doc['provenance'].get('profile')} "
             f"engine {','.join(doc['provenance']['engine_versions'])}; maps: {proto.MAP_LABEL}",
             '', '| opponent | games | wins | win rate | Wilson 95% (naive) | mean margin | A wins | B wins | fuelEx entries | games w/ fuelEx | faults |',
             '|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|']
    for o, r in t.items():
        lines.append(f"| {o} | {r['games']} | {r['wins']:g} | {r['win_rate']:.3f} | "
                     f"[{r['wilson95_naive'][0]:.3f}, {r['wilson95_naive'][1]:.3f}] | {r['mean_margin']:.1f} | "
                     f"{r['by_side'].get('A', {}).get('wins', 0):g} | {r['by_side'].get('B', {}).get('wins', 0):g} | "
                     f"{r['fuel_exhausted_entries']} | {r['games_with_fuel_exhaustion']} | {r['faults']} |")
    return '\n'.join(lines)


def paired(cand, base, g) -> str:
    tab = stats.paired_table(cand['rows'], base['rows'], g['n_boot'], g['seed'], g['alpha_one_sided'])
    lines = ['', f"### paired vs {base['label']} (map clusters: {tab['win']['__pooled__']['n_map_clusters']}; "
                 f"point [95% CI] one-sided {g['alpha_one_sided']:.0%} lower bound)",
             '| opponent | d win rate | d gem margin | worst maps (d win) |', '|---|---|---|---|']
    for o in sorted(k for k in tab['win'] if k != '__pooled__') + ['__pooled__']:
        worst = ', '.join(f"{w['map']} {w['d_win']:+.2f}" for w in tab['worst_maps_by_d_win'].get(o, []))
        lines.append(f"| {o} | {fmt_ci(tab['win'][o])} | {fmt_ci(tab['margin'][o])} | {worst} |")
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('results')
    ap.add_argument('--baseline')
    ap.add_argument('--incumbent')
    ap.add_argument('--gate', choices=['final', 'selection'])
    a = ap.parse_args()
    p = proto.load(verify=True)
    cand = json.loads(Path(a.results).read_text(encoding='utf-8'))
    print(table(cand))
    if a.baseline:
        base = json.loads(Path(a.baseline).read_text(encoding='utf-8'))
        print(paired(cand, base, p['gate']))
    if a.gate:
        if not a.baseline:
            sys.exit('--gate needs --baseline (the original in the candidate seat on the same schedule)')
        res = gate_mod.evaluate_files(a.results, a.baseline, a.incumbent, a.gate)
        out = Path(a.results).parent / f'gate-{a.gate}.json'
        engine.write_json(out, res.as_dict())
        print(f"\nGATE ({a.gate}): {'PASS' if res.passed else 'FAIL'}")
        for r in res.reasons:
            print('  -', r)
        if a.gate == 'final':
            led = ledger_mod.Ledger(proto.LEDGER, p['gate']['override_reason_min_chars'])
            sha = cand['provenance']['candidate_sha256']
            resv = led.reservation(sha)
            if resv:
                led.record_verdict(resv['seq'], sha, res.passed, hashlib.sha256(out.read_bytes()).hexdigest(),
                                   res.reasons)
        print('wrote', out)
        sys.exit(0 if res.passed else 2)


if __name__ == '__main__':
    main()
