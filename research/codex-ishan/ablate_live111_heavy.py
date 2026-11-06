"""EXP209: fresh paired current-source heavy subsystem Discovery, never a release gate."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from shutil import copytree
import json
import re

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, read
from engine3_qualify import build, play
from freeze_engine3_discovery import write
from profile_live111_first import exact_build
from qualify_local import DEV, partition
from resource_live111b_discovery import ledger, margins

ARMS = {'stock': {},
        'lab_off': {'A2_LAB': ('1','0'), 'A2_RTSW': ('1','0'), 'A2_LADFIT': ('1','0'), 'A2_HYB': ('3','0'), 'LADDER_TABLES': ('1','0')},
        'a3_off': {'A3_BACKOFF': ('1','0'), 'A3_BACK_EQ': ('0.4f','0.0f'), 'A3_BIG_LINEUP': ('6','-1')},
        'duo_off': {'NOVA_DUO': ('5','0')},
        'tsearch_off': {'APEX_TS_DECIDE': ('1','0')},
        'route_off': {'APEX_ROUTE_DEPTH': ('2','1')}}
SEEDS = (54347, 57787)


def prepare(target, changes):
    source = bench.ROOT / 'bots/codex-live111-frozen/src'
    identity = read(HERE / 'LIVE111_SOURCE_VERIFIED.json')
    assert all(bench.digest(source / name) == digest for name, digest in identity['source_file_hashes'].items())
    copytree(source, target)
    header = target / 'common.h'
    data = header.read_bytes()
    for name, (old, new) in changes.items():
        pattern = rb'(?m)^#define ' + name.encode() + b' ' + re.escape(old.encode()) + rb'(?=\s|$)'
        data, count = re.subn(pattern, f'#define {name} {new}'.encode(), data, count=1)
        assert count == 1, name
    header.write_bytes(data)


if __name__ == '__main__':
    assert bench.digest(CLI) == CLI_HASH
    identity = read(HERE / 'LIVE111_SOURCE_VERIFIED.json')
    out = bench.CACHE / 'live111-heavy-discovery-20261106'
    out.mkdir()
    cats = read(HERE / 'ENGINE3_CATEGORIES_DEV.json')['maps']
    chosen = read(HERE / 'LIVE109_STELLAR_DEV_MAPS.json')
    maps = [p for p in partition('dev') if p.name in chosen]
    assert len(maps) == 12 and all(bench.digest(p) == chosen[p.name]['sha256'] == cats[p.stem]['map_hash'] for p in maps)
    opponents = {n: bench.CACHE / bench.OPPS[n][0] for n in DEV}
    hashes = {n: bench.OPPS[n][1] for n in DEV}
    opponents['live109'] = SDK_ROOT / 'bots/live109/bot.wasm'
    hashes['live109'] = read(HERE / 'LIVE109_SOURCE_VERIFIED.json')['wasm_sha256']
    assert all(bench.digest(p) == hashes[n] for n, p in opponents.items())
    write(HERE / 'LIVE111_HEAVY_PLAN.json', {'scope': 'Exploratory, no release claim', 'engine': ENGINE, 'cli': CLI_HASH,
          'changes': ARMS, 'seeds': SEEDS, 'maps': chosen, 'opponents': hashes, 'agent2_branch_checked': '6c2244e268e36aa37819e4f6002b8820ba21e48a', 'games': 1440})
    sources = {}
    for arm, changes in ARMS.items():
        source = out / (arm + '-source')
        prepare(source, changes)
        sources[arm] = source
    def release(arm):
        results = []
        for suffix in ('', '-rebuild') if arm != 'stock' else ('',):
            p = SDK_ROOT / 'bots' / ('live111-heavy-' + arm + suffix)
            results.append(bench.digest(exact_build(sources[arm], p, 1)))
        assert len(set(results)) == 1
        print('release', arm, results[0], flush=True)
        return arm, results[0]
    with ThreadPoolExecutor(max_workers=2) as pool:
        releases = dict(pool.map(release, ARMS))
    assert releases['stock'] == identity['wasm_sha256'] and len(set(releases.values())) == len(ARMS)
    write(HERE / 'LIVE111_HEAVY_RELEASES.json', {'releases': releases, 'sources': {a: {p.name: bench.digest(p) for p in s.iterdir() if p.is_file()} for a, s in sources.items()}})
    binaries = {(arm, seed): build(src, SDK_ROOT / 'bots' / f'live111-heavy-{arm}-{seed}', seed) for arm, src in sources.items() for seed in SEEDS}
    write(HERE / 'LIVE111_HEAVY_BINARIES.json', {f'{a}-{s}': bench.digest(p) for (a,s),p in binaries.items()})
    for seed in SEEDS:
        for opp in opponents:
            (out / f'{seed}-{opp}').mkdir()
    jobs = [(arm, seed, opp, mp, side, binaries[arm, seed], ref, out / f'{seed}-{opp}', cats[mp.stem]['category'])
            for mp in maps for opp, ref in opponents.items() for side in 'AB' for seed in SEEDS for arm in ARMS]
    def run(job):
        row = play(job)
        arm, seed, opp, mp, side, _, _, output, _ = job
        path = output / f'{mp.stem}-{side}-{arm}' / 'native.json'
        doc = read(path)
        us = 'team' + side
        them = 'teamB' if us == 'teamA' else 'teamA'
        a, b = ledger(doc, us), ledger(doc, them)
        return {**row, 'native_sha256': bench.digest(path), 'draft': doc['roster']['draft'], 'resource': {'ours': a, 'rival': b, **margins(a,b)}}
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(run, jobs):
            rows.append(row)
            if len(rows) % 60 == 0:
                print(f'{len(rows)}/{len(jobs)}', flush=True)
    write(out / 'rows.json', rows)
    key = lambda r: tuple(r[k] for k in ('map_hash', 'side', 'opponent', 'noise_seed', 'engine_seed'))
    stock = {key(r): r for r in rows if r['arm'] == 'stock'}
    results = {}
    for arm in ARMS:
        if arm == 'stock':
            continue
        pairs = [(stock[key(r)], r) for r in rows if r['arm'] == arm]
        strata = {}
        for field in ('opponent', 'category', 'size'):
            groups = defaultdict(list)
            for a,b in pairs:
                groups[a[field]].append((a,b))
            strata[field] = {name: bench.summary(v) for name,v in sorted(groups.items())}
        results[arm] = {'overall': bench.summary(pairs), 'strata': strata,
                        'draft_changes': sum(a['draft'] != b['draft'] for a,b in pairs),
                        'error_cells': sum(bool(r['faults'] or r['opponent_faults'] or r['diagnostic_codes']) for p in pairs for r in p),
                        'mean_paired_resource_changes': {k: sum(b['resource']['components'][k] - a['resource']['components'][k] for a,b in pairs) / len(pairs) for k in ('production','fights','camp_loss','conversion')}}
    result = {'scope': 'EXP209 exploratory multiple-arm Discovery; no superiority/release decision', 'engine': ENGINE, 'releases': releases, 'seeds': SEEDS, 'games': len(rows), 'results': results}
    write(HERE / 'LIVE111_HEAVY_RESULT.json', result)
    print(json.dumps({a: {k:v for k,v in r.items() if k != 'strata'} for a,r in results.items()}, indent=2), flush=True)
