"""Map categories from atlas features: k-means on standardised features (k chosen by silhouette), then a shallow
decision tree (CART, Gini) fitted to the clusters so each category is a readable rule on features the bot can
compute at game start. The rules, not the clusters, define the categories (they also classify unseen maps).
  python tools/mapatlas/categorise.py [--atlas research/x3/atlas/atlas.csv] [--k 4-9] [--depth 3]
writes research/x3/atlas/categories.json ({map: category}), categories_rules.json and CATEGORIES.md.
"""
import argparse, csv, json, math, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Features used for categories: shape and scale, where the gems are, how concentrated, terrain.
FEATS = {
    'log_area': lambda r: math.log(float(r['area'])),
    'team': lambda r: float(r['team']),
    'contested': lambda r: float(r['contested_gem_share']),
    'centre': lambda r: float(r['centre_gem_share']),
    'top3': lambda r: float(r['top3_share']),
    'log_density': lambda r: math.log(1 + float(r['gem_density'])),
    'groups_per_champ': lambda r: float(r['groups_per_champ']),
    'harmless': lambda r: float(r['harmless_gem_share']),
    'log_maze': lambda r: math.log(max(0.3, float(r['maze_ratio']))) if float(r['maze_ratio']) > 0 else 0.0,
    'walls': lambda r: float(r['wall_density']),
    'unreachable': lambda r: float(r['unreachable_gem_share']),
    'near30': lambda r: float(r['gems_within_30']),
}

def _d2(a, b): return sum((x - y) ** 2 for x, y in zip(a, b))


def kmeans(X, k, seed, iters=100):
    rng = random.Random(seed); n = len(X)
    C = [X[rng.randrange(n)]]
    for _ in range(1, k):  # k-means++
        d = [min(_d2(x, c) for c in C) for x in X]; t = rng.random() * sum(d); acc = 0
        for i, v in enumerate(d):
            acc += v
            if acc >= t: C.append(X[i]); break
    lab = [0] * n
    for _ in range(iters):
        lab = [min(range(k), key=lambda j: _d2(x, C[j])) for x in X]
        nc = []
        for j in range(k):
            mem = [X[i] for i in range(n) if lab[i] == j]
            nc.append([sum(col) / len(mem) for col in zip(*mem)] if mem else C[j])
        if all(_d2(a, b) < 1e-12 for a, b in zip(nc, C)): break
        C = nc
    return lab, C, sum(_d2(X[i], C[lab[i]]) for i in range(n))


def silhouette(X, lab):
    n = len(X); s = []
    D = [[math.sqrt(_d2(X[i], X[j])) for j in range(n)] for i in range(n)]
    for i in range(n):
        same = [j for j in range(n) if lab[j] == lab[i] and j != i]
        if not same: s.append(0); continue
        a = sum(D[i][j] for j in same) / len(same)
        b = min(sum(D[i][j] for j in range(n) if lab[j] == c) / sum(1 for j in range(n) if lab[j] == c) for c in set(lab) if c != lab[i])
        s.append((b - a) / max(a, b))
    return sum(s) / n


def gini(y):
    n = len(y); return 1 - sum((y.count(v) / n) ** 2 for v in set(y))


def _leaf(y): return {'leaf': max(set(y), key=y.count), 'n': len(y)}


def tree(X, y, names, depth, min_leaf=3):
    if depth == 0 or len(set(y)) == 1 or len(y) < 2 * min_leaf: return _leaf(y)
    best = None
    for f in range(len(names)):
        xs = sorted(set(r[f] for r in X))
        for t in [(a + b) / 2 for a, b in zip(xs, xs[1:])]:
            L = [i for i, r in enumerate(X) if r[f] <= t]; R = [i for i in range(len(X)) if X[i][f] > t]
            if len(L) < min_leaf or len(R) < min_leaf: continue
            g = (len(L) * gini([y[i] for i in L]) + len(R) * gini([y[i] for i in R])) / len(y)
            if best is None or g < best[0]: best = (g, f, t, L, R)
    if best is None or best[0] >= gini(y) - 1e-9: return _leaf(y)
    _, f, t, L, R = best
    return {'feat': names[f], 'thr': round(t, 4), 'le': tree([X[i] for i in L], [y[i] for i in L], names, depth - 1, min_leaf),
            'gt': tree([X[i] for i in R], [y[i] for i in R], names, depth - 1, min_leaf)}


def classify(node, row):
    while 'leaf' not in node: node = node['le'] if row[node['feat']] <= node['thr'] else node['gt']
    return node['leaf']


def rules(node, path=()):
    if 'leaf' in node: return [(path, node['leaf'], node['n'])]
    return rules(node['le'], path + (f"{node['feat']} <= {node['thr']}",)) + rules(node['gt'], path + (f"{node['feat']} > {node['thr']}",))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--atlas', default='research/x3/atlas/atlas.csv'); ap.add_argument('--k', default='4-9')
    ap.add_argument('--depth', type=int, default=3); ap.add_argument('--out', default='research/x3/atlas')
    a = ap.parse_args()
    rows = list(csv.DictReader(open(ROOT / a.atlas, encoding='utf-8')))
    names = list(FEATS); raw = [[FEATS[n](r) for n in names] for r in rows]; maps = [r['map'] for r in rows]
    mu = [sum(c) / len(c) for c in zip(*raw)]; sd = [math.sqrt(sum((v - m) ** 2 for v in c) / len(c)) + 1e-9 for c, m in zip(zip(*raw), mu)]
    X = [[(v - m) / d for v, m, d in zip(r, mu, sd)] for r in raw]
    lo, hi = map(int, a.k.split('-')); best = None
    for k in range(lo, hi + 1):
        cand = min((kmeans(X, k, s) for s in range(20)), key=lambda t: t[2])
        sil = silhouette(X, cand[0]); print(f'k={k} silhouette {sil:.3f}')
        if best is None or sil > best[0]: best = (sil, k, cand)
    sil, k, (lab, C, _) = best
    print(f'chosen k={k} (silhouette {sil:.3f})')
    T = tree(raw, lab, names, a.depth)
    rule_list = rules(T)
    feats_by_map = {m: dict(zip(names, raw[i])) for i, m in enumerate(maps)}
    leaf_of = {m: classify(T, feats_by_map[m]) for m in maps}
    # A category per tree leaf (path), named by its rule; clusters only seed the tree.
    leaves = {}
    for i, (path, cl, n) in enumerate(rule_list): leaves[path] = f'C{i + 1}'
    def leaf_name(row):
        node, path = T, ()
        while 'leaf' not in node:
            if row[node['feat']] <= node['thr']: path += (f"{node['feat']} <= {node['thr']}",); node = node['le']
            else: path += (f"{node['feat']} > {node['thr']}",); node = node['gt']
        return leaves[path]
    cats = {m: leaf_name(feats_by_map[m]) for m in maps}
    agree = sum(leaf_of[m] == lab[i] for i, m in enumerate(maps)) / len(maps)
    out = ROOT / a.out
    (out / 'categories.json').write_text(json.dumps(cats, indent=1), encoding='utf-8')
    (out / 'categories_rules.json').write_text(json.dumps(dict(tree=T, features=names, leaves={v: list(k) for k, v in leaves.items()}), indent=1), encoding='utf-8')
    lines = ['# Map categories (tools/mapatlas/categorise.py)', '', f'k-means on {len(names)} standardised atlas features chose k={k} (silhouette {sil:.3f});',
             f'a depth-{a.depth} decision tree turns the clusters into readable rules (agrees with the clusters on {agree:.0%} of maps).',
             'The rules define the categories, so an unseen map is categorised from its features alone.', '']
    for path, cl, n in rule_list:
        c = leaves[path]; ms = sorted(m for m in maps if cats[m] == c)
        sub = [raw[maps.index(m)] for m in ms] or raw
        cen = [sum(c) / len(c) for c in zip(*sub)]
        lines += [f'## {c} ({len(ms)} maps)', '', 'Rule: ' + ' and '.join(path), '',
                  'Typical: ' + ', '.join(f'{n_}={v:.2f}' for n_, v in zip(names, cen)), '', 'Maps: ' + ', '.join(ms), '']
    (out / 'CATEGORIES.md').write_text('\n'.join(lines), encoding='utf-8')
    for path, cl, n in rule_list: print(leaves[path], n, ' and '.join(path))


if __name__ == '__main__':
    main()
