"""Evaluate a single frozen executable across the pool and generated layouts."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random
from statistics import quantiles

from compare import load, pair, summarise

POOL = ('v92', 'v86h', 'x1bru')
GENERATED = ('styled', 'maze')
GEN_OPPS = ('v92', 'x1bru')
ALT_OPPS = ('x2', 'v86h-s2', 'v81hl-s3', 'gxspar1', 'gxspar2', 'gxspar3')


def build_report(root, tag):
    def path(tag, scenario, opp):
        return root / f'gx-{tag}-{scenario}-{opp}' / 'results.json'

    digests = set()
    by_map = Counter()
    pool = Counter()
    matches = {}
    for s, opps in (
            ('pool', POOL + ('x3mf',) + ALT_OPPS),
            *((s, GEN_OPPS) for s in GENERATED)):
        for opp in opps:
            b, c = (path(t,s,opp) for t in ('base', tag))
            if not b.is_file() or not c.is_file():
                continue
            before, after = load(b), load(c)
            digests.add(next(iter(after.values()))['candidate_sha256'])
            m = pair(before, after)
            matches[f'{s}/{opp}'] = summarise(m)
            if s == 'pool' and opp in POOL:
                pool.update(m)
                for key, orig in before.items():
                    new = after[key]
                    outcome = 'team' + key[1]
                    by_map[key[0]] += int(new['outcome'] == outcome) - int(orig['outcome'] == outcome)

    if len(digests) > 1:
        raise ValueError('Candidate bytes changed between sets')
    expected_pool = [f'pool/{opp}' for opp in POOL]
    expected_generated = [f'{s}/{opp}' for s in GENERATED for opp in GEN_OPPS]
    pool_complete = all(key in matches and matches[key]['games'] == 172 for key in expected_pool)
    generated_complete = all(key in matches for key in expected_generated)
    p = summarise(pool) if pool else None
    bootstrap = None
    if pool_complete:
        if len(by_map) != 86:
            raise ValueError('Pool maps do not match the release set')
        sample = [by_map[x] for x in sorted(by_map)]
        rng = random.Random(2602)
        # Resample whole layouts, keeping their two sides and three opponents together.
        sums = [sum(rng.choices(sample, k=len(sample))) for _ in range(10000)]
        q = quantiles(sums, n=40, method='inclusive')
        bootstrap = dict(draws=len(sums), maps=len(sample), interval95=[q[0], q[-1]])
    pool_pass = bool(pool_complete and p['delta'] >= 10 and p['z'] >= 1.5 and
        p['faults'] == 0 and 10*p['fuel_outs'] <= 11*p['base_fuel_outs'] and
        all(matches[key]['delta'] >= -3 for key in expected_pool))
    generated_pass = generated_complete and all(
        matches[key]['delta'] >= -3 and matches[key]['faults'] == 0 for key in expected_generated)
    return dict(tag=tag,candidate_sha256=next(iter(digests),None),matches=matches,pool=p,
        pool_complete=pool_complete,pool_pass=pool_pass,pool_bootstrap=bootstrap,
        generated_complete=generated_complete,generated_pass=generated_pass,
        head_to_head=matches.get('pool/x3mf'),candidate_ready=pool_pass and generated_pass)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('runs',type=Path)
    p.add_argument('tag')
    args=p.parse_args()
    print(json.dumps(build_report(args.runs,args.tag),indent=2))


if __name__ == '__main__':
    main()
