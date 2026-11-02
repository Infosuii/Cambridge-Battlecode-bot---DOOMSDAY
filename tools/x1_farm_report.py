"""Summarise a tools/x1_farm.py run (J005): per plan and round, branches that turn a baseline loss into a win and a
win into a loss, mean banked-margin change, by map kind and opponent; prefix checks, fuel-outs, faults.

usage: python tools/x1_farm_report.py NAME [OUT.md]
"""
import json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    name = sys.argv[1]
    rows = [json.loads(l) for l in (ROOT/'artifacts/tmp/x1farm'/name/'rows.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    base = {(r['opp'], r['kind'], r['map'], r['side']): r for r in rows if r['round'] < 0 and 'win' in r}
    br = [r for r in rows if r['round'] >= 0]
    played = [r for r in br if 'win' in r and (r['opp'], r['kind'], r['map'], r['side']) in base]
    out = [f'# Branch farm {name}', '']
    bw = sum(r['win'] for r in base.values())
    out += [f'Baselines: {len(base)} games, {bw:g} wins ({100 * bw / max(1, len(base)):.1f}%), fuel-outs '
            f'{sum(r["fuel"] for r in base.values())}, faults {sum(r["faults"] for r in base.values())}.',
            f'Branches: {len(br)} rows, {len(played)} played, {sum("skipped" in r for r in br)} skipped (game over before '
            f'the round). Prefix check (branch equals its baseline before the switch round): '
            f'{sum(r.get("prefix_ok") is True for r in played)} ok, {sum(r.get("prefix_ok") is False for r in played)} '
            f'violations, {sum("prefix_ok" not in r for r in played)} unchecked.', '']
    bad = [r for r in played if r.get('prefix_ok') is False]
    if bad:
        out += ['Prefix violations (first 10): ' + ', '.join(f'{r["key"]} diverge {r["diverge"]}' for r in bad[:10]), '']

    def lw(r):
        b = base[(r['opp'], r['kind'], r['map'], r['side'])]
        return b['win'] == 0.0 and r['win'] == 1.0
    for r in played: r['_lw'] = lw(r)

    def table(keyf, title):
        acc = defaultdict(lambda: [0, 0, 0, 0.0, 0, 0, 0])
        for r in played:
            b = base[(r['opp'], r['kind'], r['map'], r['side'])]; a = acc[keyf(r)]
            a[0] += 1; a[1] += r['_lw']; a[2] += b['win'] == 1.0 and r['win'] == 0.0
            a[3] += (r['gems'] - r['opp_gems']) - (b['gems'] - b['opp_gems'])
            a[4] += max(0, r['fuel'] - b['fuel']); a[5] += r['faults']; a[6] += b['win'] == 0.0
        lines = [f'## {title}', '', '| key | branches | base losses | loss→win | win→loss | net | mean margin Δ | new fuel-outs | faults |',
                 '|---|---|---|---|---|---|---|---|---|']
        for k in sorted(acc):
            n, a_lw, wl, dm, fo, fa, bl = acc[k]
            lines.append(f'| {k} | {n} | {bl} | {a_lw} | {wl} | {a_lw - wl:+d} | {dm / max(1, n):+.1f} | {fo} | {fa} |')
        return lines + ['']

    out += table(lambda r: f'plan {r["plan"]} @ R{r["round"]}', 'By plan and round (all kinds, both opponents)')
    out += table(lambda r: f'plan {r["plan"]} @ R{r["round"]} {r["kind"]}', 'By plan, round and map kind')
    out += table(lambda r: f'plan {r["plan"]} @ R{r["round"]} {r["opp"]}', 'By plan, round and opponent')
    # Oracle: baseline losses that at least one branch wins
    games = defaultdict(list)
    for r in played: games[(r['opp'], r['kind'], r['map'], r['side'])].append(r)
    losses = [g for g, b in base.items() if b['win'] == 0.0]
    saved = [g for g in losses if any(r['win'] == 1.0 for r in games[g])]
    out += [f'Oracle: {len(saved)} of {len(losses)} baseline losses are won by at least one branch played so far.', '']
    text = '\n'.join(out)
    if len(sys.argv) > 2: Path(sys.argv[2]).write_text(text, encoding='utf-8', newline='\n')
    print(text)


if __name__ == '__main__': main()
