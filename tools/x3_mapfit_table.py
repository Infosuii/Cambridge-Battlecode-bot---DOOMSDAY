"""Build bots/x3/src/x1_mapfit.h from research/x3/es/mapfit-<map>.json (best mean per map; maps whose best is the
untouched start are left out).  python tools/x3_mapfit_table.py [--min-gain 0.05]"""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/mapgen'))
import mapio  # noqa: E402
ap = argparse.ArgumentParser(); ap.add_argument('--min-gain', type=float, default=0.05)
ap.add_argument('--fp', default=str(ROOT / 'research/x3/counter_fp.json'),
                help='map fingerprints printed by the bot, {map-side: [w, h, groups, gems, team]} (the file holds only the authored half)')
a = ap.parse_args()
fps = json.loads(Path(a.fp).read_text()) if Path(a.fp).exists() else {}
eng = mapio.new_engine(); rows = []
for f in sorted((ROOT / 'research/x3/es').glob('mapfit-*.json')):
    st = json.loads(f.read_text()); name = f.stem[len('mapfit-'):]
    if not st['iters']: continue
    start = st['iters'][0]['mean_fit'] / st['iters'][0]['games']
    if st['best']['iter'] <= 0 or st['best']['fit'] - start < a.min_gain:
        print(f'{name}: keep v92 (start {start:.3f}, best {st["best"]["fit"]:.3f})'); continue
    fp = fps.get(f'{name}-A')
    if fp:  # the runtime key (w.width, w.height, w.groups.size(), sum of group gems), as the bot prints it
        w_, h_, groups_, gems = fp[0], fp[1], fp[2], fp[3]
    else:  # fallback: the map file's authored half, which does not match the runtime key on most maps
        m = mapio.read_map(eng, (ROOT / 'maps/ladder-pool' / f'{name}.map26a').read_bytes())
        w_, h_, groups_, gems = m['w'], m['h'], len(m['groups']), sum(g['gems'] for g in m['groups'])
        print(f'{name}: WARNING no runtime fingerprint, key from the map file')
    d = ', '.join(f'{x:.4f}f' for x in st['best']['kd'])
    rows.append(f"    {{{w_}, {h_}, {groups_}, {gems}u, {{{d}}}}}, // {name}: {start:.3f} -> {st['best']['fit']:.3f}")
    print(f'{name}: fit {start:.3f} -> {st["best"]["fit"]:.3f}')
p = ROOT / 'bots/x3/src/x1_mapfit.h'; t = p.read_text()
head, _, _ = t.partition('inline constexpr Row kRows[] = ')
body = '{\n' + '\n'.join(rows) + '\n    {0, 0, 0, 0u, {}}};\n} // namespace x1_mapfit\n' if rows else '{{0, 0, 0, 0u, {}}};\n} // namespace x1_mapfit\n'
p.write_text(head + 'inline constexpr Row kRows[] = ' + body, newline='\n')
print(len(rows), 'rows written')
