"""Frozen EXP-007 development stress screen, using hash-verified archived base cells."""
import argparse
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import ablate_dev as h

OUT = h.CACHE / 'bruiser-dev-v1'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=('prepare', 'run'))
    a = p.parse_args()
    if a.stage == 'prepare':
        OUT.mkdir()
        for seed in h.SEEDS:
            dst = OUT / f'candidate-{seed}' / 'src'
            shutil.copytree(h.ROOT / 'bots/codex-bruiser/src', dst)
            file = dst / 'common.h'
            src = file.read_bytes()
            for old, new in ((b'#define NOVA_SEED 1', f'#define NOVA_SEED {seed}'.encode()),
                             (b'#define NOVA_SEED_EPS 0.04f', b'#define NOVA_SEED_EPS 0.005f')):
                assert src.count(old + b'\n') == 1 or src.count(old + b'\r\n') == 1
                src = src.replace(old, new, 1)
            file.write_bytes(src)
        return
    prior = json.loads((Path(__file__).parent / 'ABLATIONS.json').read_bytes())
    base_rows = [r for r in json.loads((h.OUT / 'rows.json').read_bytes()) if r['arm'] == 'base']
    for seed in h.SEEDS:
        assert h.digest(h.OUT / f'base-{seed}/bot.wasm') == prior['binaries'][f'base-{seed}']
    for name, (file, expected) in h.OPPS.items():
        assert h.digest(h.CACHE / file) == expected, name
    maps = sorted((h.CACHE / 'jd-sets/conf').glob('*.map26a'))
    import hashlib
    md = hashlib.sha256('\n'.join(f'{h.digest(m)} {m.name}' for m in maps).encode()).hexdigest()
    assert len(maps) == 16 and md == prior['map_digest']
    h.OUT = OUT
    (OUT / 'games').mkdir()
    binaries = {seed: OUT / f'candidate-{seed}/bot.wasm' for seed in h.SEEDS}
    hashes = {seed: h.digest(wasm) for seed, wasm in binaries.items()}
    jobs = [('candidate', seed, opp, mp, side, binaries[seed])
            for seed in h.SEEDS for mp in maps for opp in h.OPPS for side in 'AB']
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(h.one, jobs):
            rows.append(r)
            if len(rows) % 32 == 0:
                print(f'{len(rows)}/{len(jobs)}', flush=True)
    key = lambda r: tuple(r[k] for k in ('noise_seed', 'opponent', 'map', 'side'))
    base = {key(r): r for r in base_rows}
    assert len(base) == len(rows) == 256
    pairs = [(base[key(r)], r) for r in rows]
    behavior = {'base': [], 'candidate': []}
    for arm, root, arm_rows in [('base', h.CACHE / 'ablations-v2', base_rows), ('candidate', OUT, rows)]:
        for r in arm_rows:
            name = f"{arm}-{r['noise_seed']}-{r['opponent']}-{r['map']}-{r['side']}"
            s = json.loads((root / 'games' / name / 'native.json').read_bytes())
            purchases = [e for event in s['events'] if event['kind'] == 'buyItem' and
                         event['owner']['team'] == 'team' + r['side'] for e in event['entries']
                         if 'Bruiser Shard' in e.get('target', {}).get('name', '')]
            combinations = [e for event in s['events'] if event['kind'] == 'itemCombination' and
                            event['owner']['team'] == 'team' + r['side'] for e in event['entries']
                            if 'Bruiser Emblem' in e.get('target', {}).get('name', '')]
            behavior[arm].append({'cell': key(r), 'bruiser_shards': sum(int(e['value']) for e in purchases),
                                 'bruiser_shards_by_300': sum(int(e['value']) for e in purchases if e['timestamp']['round'] <= 300),
                                 'bruiser_emblems': len(combinations)})
    result = {'scope': '16-map development stress screen; no ladder evidence',
              'engine': h.ENGINE, 'map_digest': md, 'seeds': h.SEEDS, 'binaries': hashes,
              'overall': h.summary(pairs),
              'per_opponent': {o: h.summary([(b, c) for b, c in pairs if c['opponent'] == o]) for o in h.OPPS},
              'behavior_totals': {arm: {k: sum(r[k] for r in rs) for k in
                                  ('bruiser_shards', 'bruiser_shards_by_300', 'bruiser_emblems')}
                                  for arm, rs in behavior.items()},
              'behavior': behavior, 'candidate_rows': rows}
    out = Path(__file__).parent / 'BRUISER_DEV.json'
    with out.open('x', encoding='utf8', newline='\n') as file:
        json.dump(result, file, indent=2)
        file.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('behavior', 'candidate_rows')}, indent=2), flush=True)

if __name__ == '__main__':
    main()
