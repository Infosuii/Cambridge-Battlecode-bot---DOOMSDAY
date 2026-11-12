"""Summarise a tools/x1_farm.py run (J005): per plan and round, branches that turn a baseline loss into a win and a
win into a loss, mean banked-margin change, by map kind and opponent; prefix checks, fuel-outs, faults.

usage: python tools/x1_farm_report.py NAME [OUT.md]
"""
import json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    name = sys.argv[1]
    last = {}
    for l in (ROOT/'artifacts/tmp/x1farm'/name/'rows.jsonl').read_text(encoding='utf-8').splitlines():
        try: r = json.loads(l)
        except ValueError: continue
        last[r['key']] = r  # a replayed row (backfill) replaces the earlier one
    rows = list(last.values())
    base = {(r['opp'], r['kind'], r['map'], r['side']): r for r in rows if r['round'] < 0 and 'win' in r}
    br = [r for r in rows if r['round'] >= 0]
    played = [r for r in br if 'win' in r and (r['opp'], r['kind'], r['map'], r['side']) in base]
    def mean(d, k):
        v = [r[k] for r in d.values() if k in r]
        return f'{sum(v) / len(v):.0f}' if v else '-'
    out = [f'# Branch farm {name}', '']
    bw = sum(r['win'] for r in base.values())
    out += [f'Baselines: {len(base)} games, {bw:g} wins ({100 * bw / max(1, len(base)):.1f}%), fuel-outs '
            f'{sum(r["fuel"] for r in base.values())}, faults {sum(r["faults"] for r in base.values())}; per game: gold@R250 '
            f'{mean(base, "gold250")}, gold@R500 {mean(base, "gold500")}, deaths {mean(base, "deaths")}, '
            f'kills {mean(base, "kills")}, finish round {mean(base, "rounds")}.',
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
        acc = defaultdict(lambda: defaultdict(float))
        for r in played:
            b = base[(r['opp'], r['kind'], r['map'], r['side'])]; a = acc[keyf(r)]
            a['n'] += 1; a['lw'] += r['_lw']; a['wl'] += b['win'] == 1.0 and r['win'] == 0.0; a['bl'] += b['win'] == 0.0
            a['dm'] += (r['gems'] - r['opp_gems']) - (b['gems'] - b['opp_gems'])
            a['fo'] += max(0, r['fuel'] - b['fuel']); a['fa'] += r['faults']; a['dd'] += r['deaths'] - b['deaths']
            if 'gold500' in r and 'gold500' in b: a['g'] += 1; a['dg'] += r['gold500'] - b['gold500']
        lines = [f'## {title}', '', '| key | branches | base losses | loss→win | win→loss | net | mean margin Δ | mean gold@R500 Δ | '
                 'mean deaths Δ | new fuel-outs | faults |', '|---|---|---|---|---|---|---|---|---|---|---|']
        for k in sorted(acc):
            a = acc[k]; n = max(1, a['n'])
            g = f"{a['dg'] / a['g']:+.0f}" if a['g'] else '-'
            lines.append(f"| {k} | {a['n']:.0f} | {a['bl']:.0f} | {a['lw']:.0f} | {a['wl']:.0f} | {a['lw'] - a['wl']:+.0f} | "
                         f"{a['dm'] / n:+.1f} | {g} | {a['dd'] / n:+.2f} | {a['fo']:.0f} | {a['fa']:.0f} |")
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
