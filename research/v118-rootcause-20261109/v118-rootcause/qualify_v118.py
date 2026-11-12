"""Sealed v118 holdout qualification against the pre-registered release-protocol.json. Run once, for one candidate."""
from pathlib import Path
import sys, json, collections, random
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run, STYLES
from project import save, sha


def bootstrap(diffs_by_map, n=4000, seed=118):
    rng = random.Random(seed); maps = list(diffs_by_map)
    games = sum(len(v) for v in diffs_by_map.values()); out = []
    for _ in range(n):
        pick = [rng.choice(maps) for _ in maps]
        num = sum(sum(diffs_by_map[m]) for m in pick); den = sum(len(diffs_by_map[m]) for m in pick)
        out.append(100.0 * num / max(1, den))
    out.sort(); return out[int(0.1 * n)], out[len(out) // 2]


def main(candidate, incumbent='hp01'):
    protocol = json.loads((HERE / 'release-protocol.json').read_text())
    split = json.loads((HERE / 'map-split.json').read_text())
    assert protocol['split_sha256'] == sha(HERE / 'map-split.json')
    maps = [Path(p) for p in split['holdout']]
    rows = run('v118-holdout-reference', [incumbent, candidate], maps, STYLES, workers=18)
    direct = run('v118-holdout-direct', [candidate], maps, [incumbent], workers=18)
    ref = {(r['candidate'], r['opponent'], r['map'], r['side']): r for r in rows}
    keys = [(o, m, s) for (c, o, m, s) in ref if c == candidate]
    diffs = collections.defaultdict(list); by_opp = collections.Counter(); by_map = collections.Counter()
    for k in keys:
        d = ref[(candidate, *k)]['score'] - ref[(incumbent, *k)]['score']
        diffs[k[1]].append(d); by_opp[k[0]] += d; by_map[k[1]] += d
    games = len(keys)
    cand = [ref[(candidate, *k)] for k in keys]; inc = [ref[(incumbent, *k)] for k in keys]
    p10, p50 = bootstrap(diffs)
    fuel_c = sum(r['fuel'] for r in cand + direct) / (len(cand) + len(direct)); fuel_i = sum(r['fuel'] for r in inc) / len(inc)
    direct_score = sum(r['score'] for r in direct) / len(direct)
    gates = {
        'G2_zero_faults': sum(r['faults'] for r in cand + direct) == 0,
        'G3_fuel': fuel_c <= 1.2 * fuel_i + 0.05,
        'G4_paired_nonnegative': sum(sum(v) for v in diffs.values()) >= 0,
        'G4_bootstrap_p10': p10 >= -2.0,
        'G5_direct': direct_score >= 0.5,
    }
    result = {'candidate': candidate, 'incumbent': incumbent, 'games': games,
              'reference_score': {candidate: sum(r['score'] for r in cand), incumbent: sum(r['score'] for r in inc)},
              'paired_diff_points': sum(sum(v) for v in diffs.values()), 'paired_diff_pp_bootstrap_p10_p50': [p10, p50],
              'direct_score': direct_score, 'direct_games': len(direct), 'fuel_per_game': {candidate: fuel_c, incumbent: fuel_i},
              'faults': sum(r['faults'] for r in cand + direct), 'opponent_faults': sum(r['opponent_faults'] for r in cand + direct),
              'by_opponent': dict(by_opp), 'worst_maps': by_map.most_common()[-5:], 'best_maps': by_map.most_common(5),
              'maps_losing_6_of_18': [m for m, v in by_map.items() if v <= -6], 'gates': gates}
    save(HERE / 'holdout-result.json', result)
    print(json.dumps(result, indent=1))
    return result


if __name__ == '__main__':
    main(sys.argv[1])
