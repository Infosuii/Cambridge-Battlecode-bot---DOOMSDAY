"""Gate verdicts for tools/x1_gate.sh runs (research/x1/RETRY_QUEUE.md R1), candidate vs base on the same cells.

usage: python tools/x1_gate_report.py RUNS_DIR BASE_TAG TAG [TAG ...] [--base-map ladder-x2=x1e-cw-ladder-x2-01 ...]
Cells are x1g-TAG-KIND-OPP-01 (KIND ladder/styled/maze, OPP x2/x2-s2). --base-map names a base cell by another run
(e.g. the PC's x1e-cw-* evals). Prints a markdown table per tag with wins, fuel-outs, faults, mean gold@R250 /
gold@R500 (earned), deaths per game and finish round, and the verdict:
  pass = total wins >= base total on the same cells, no map kind (both opponents pooled) more than 2 points of win
  rate below the base, ladder + styled fuel-outs <= base (totals; per-game fuel-outs are not paired once games
  diverge), zero faults. Maze cells (pc/msgs/0009): fuel-outs reported apart; they fail a line only if they rise by
  more than 25% while ladder + styled fuel-outs rise too.
"""
import json, sys
from pathlib import Path

KINDS, OPPS = ('ladder', 'styled', 'maze'), ('x2', 'x2-s2')


def load(path):
    p = Path(path)/'results.json'
    return json.loads(p.read_text()) if p.exists() else None


def stats(r):
    g = r['per_game']; n = len(g)
    cp = lambda rd: sum(x['checkpoints'][rd]['gold'] or 0 for x in g) / n
    return dict(games=n, wins=r['wins'], fuel=r['fuel_outs'], faults=r['faults'], gold250=cp('250'), gold500=cp('500'),
                deaths=sum(x['deaths'] for x in g) / n, rounds=sum(x['rounds'] for x in g) / n,
                sha=g[0]['candidate_sha256'][:12])


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    args = sys.argv[1:]; base_map = {}
    if '--base-map' in args:
        i = args.index('--base-map'); base_map = dict(a.split('=', 1) for a in args[i + 1:]); args = args[:i]
    runs, base_tag, tags = Path(args[0]), args[1], args[2:]
    def cell(tag, kind, opp):
        if tag == base_tag and f'{kind}-{opp}' in base_map: return load(runs/base_map[f'{kind}-{opp}'])
        return load(runs/f'x1g-{tag}-{kind}-{opp}-01')
    base = {(k, o): cell(base_tag, k, o) for k in KINDS for o in OPPS}
    out = []
    for tag in [base_tag] + tags:
        rows, tot, btot, kind_ok, fuel, bfuel, faults = [], 0, 0, True, 0, 0, 0
        mfuel = mbfuel = 0  # maze cells: fuel-outs reported apart (pc/msgs/0009)
        for k in KINDS:
            kw = kb = kn = 0
            for o in OPPS:
                c, b = cell(tag, k, o), base[(k, o)]
                if c is None or b is None: continue
                s, sb = stats(c), stats(b)
                rows.append(f"| {k} | {o} | {s['wins']}/{s['games']} | {s['wins'] - sb['wins']:+d} | {s['fuel']} ({s['fuel'] - sb['fuel']:+d}) | "
                            f"{s['faults']} | {s['gold250']:.0f} | {s['gold500']:.0f} | {s['deaths']:.2f} | {s['rounds']:.0f} | {s['sha']} |")
                kw += s['wins']; kb += sb['wins']; kn += s['games']; faults += s['faults']
                if k == 'maze': mfuel += s['fuel']; mbfuel += sb['fuel']
                else: fuel += s['fuel']; bfuel += sb['fuel']
            if kn:
                tot += kw; btot += kb
                if 100 * (kw - kb) / kn < -2: kind_ok = False
        # Maze fuel-outs fail a line only if they rise by more than 25% while ladder + styled fuel-outs rise too.
        maze_fuel_ok = not (mbfuel and mfuel > 1.25 * mbfuel and fuel > bfuel)
        ok = tot >= btot and kind_ok and fuel <= bfuel and maze_fuel_ok and faults == 0
        verdict = 'base' if tag == base_tag else ('**pass**' if ok else '**fail**') + (
            f" (total {tot - btot:+d}{'' if kind_ok else ', a map kind < -2 points'}"
            f"{'' if fuel <= bfuel else f', fuel-outs {fuel - bfuel:+d}'}{'' if maze_fuel_ok else ', maze fuel-outs > +25%'}"
            f"{'' if faults == 0 else f', faults {faults}'})")
        if mbfuel or mfuel: verdict += f'; maze fuel-outs {mfuel} vs {mbfuel} (reported)'
        out += [f'### {tag}: {tot} wins vs base {btot}; verdict {verdict}', '',
                '| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |',
                '|---|---|---|---|---|---|---|---|---|---|---|'] + rows + ['']
    print('\n'.join(out))


if __name__ == '__main__': main()
