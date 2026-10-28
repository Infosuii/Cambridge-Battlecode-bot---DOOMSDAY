"""Portable DZ build, host tests, release matches, and conformance (standard library only).

No credentials or machine-specific config required. All matches are local. Fresh names
are mandatory; exact source, binaries, logs and hashes are frozen before execution.
"""
from __future__ import annotations
import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'tools/vendor/cambc.exe'
MAPS = ROOT / 'maps/local-benchmarks'
TMP = ROOT / 'artifacts/tmp/dz'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(command, timeout=900, env=None):
    p = subprocess.run([str(x) for x in command], cwd=ROOT, capture_output=True,
                       encoding='utf-8', errors='replace', timeout=timeout, env=env)
    output = p.stdout + p.stderr
    if p.returncode:
        raise RuntimeError(f'command failed ({p.returncode}): {command[:3]}\n{output[-6000:]}')
    return output

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')

def build(bot, wasm):
    wasm.parent.mkdir(parents=True, exist_ok=True)
    log = run([CLI, 'build', bot, '--release', '--output', wasm])
    wasm.with_suffix('.build.log').write_text(log, encoding='utf-8')
    if not wasm.is_file():
        raise RuntimeError('build returned success without a Wasm output')
    return wasm

def host_tests():
    cxx = os.environ.get('DZ_CXX') or shutil.which('g++')
    if not cxx and Path('C:/msys64/ucrt64/bin/g++.exe').exists():
        cxx = 'C:/msys64/ucrt64/bin/g++.exe'
    if not cxx:
        raise RuntimeError('Install a C++20 compiler and set DZ_CXX to its executable')
    out = TMP / 'host'; out.mkdir(parents=True, exist_ok=True)
    exe = out / ('core_test.exe' if os.name == 'nt' else 'core_test')
    run([cxx, '-std=c++20', '-O2', '-Wall', '-Wextra', '-Werror', '-I', ROOT/'bots/dz/src',
         ROOT/'tests/dz/host/core_test.cpp', '-o', exe])
    env = dict(os.environ); env['PATH'] = str(Path(cxx).parent) + os.pathsep + env.get('PATH', '')
    print(run([exe], env=env).strip(), flush=True)

def verify_evidence():
    count = 0
    for folder in sorted((ROOT/'research/dz/runs').glob('*')):
        if (folder/'manual-manifest.json').exists():
            manifest = json.loads((folder/'manual-manifest.json').read_text())
            with zipfile.ZipFile(folder/'evidence.zip') as z:
                if z.testzip() is not None: raise ValueError('corrupt initial evidence capsule')
                for row in manifest['files']:
                    raw = z.read(row['path'])
                    if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                        raise ValueError('initial evidence digest mismatch')
            print(f"{folder.name}: verified {len(manifest['files'])} initial evidence files (see limitations)", flush=True)
            count += 1
            continue
        if not (folder/'provenance.json').exists(): continue
        provenance = json.loads((folder/'provenance.json').read_text())
        results = json.loads((folder/'results.json').read_text())
        with zipfile.ZipFile(folder/'evidence.zip') as z:
            if z.testzip() is not None: raise ValueError(f'{folder.name}: corrupt capsule')
            def check(member, expected):
                if hashlib.sha256(z.read(member)).hexdigest() != expected:
                    raise ValueError(f'{folder.name}: digest mismatch: {member}')
            check('candidate.wasm', provenance['candidate_sha256'])
            check('opponent.wasm', provenance['opponent_sha256'])
            for name, digest in provenance['source'].items(): check('build/candidate/'+name, digest)
            if json.loads(z.read('results.json')) != results: raise ValueError('external results differ from capsule')
            if json.loads(z.read('provenance.json')) != provenance: raise ValueError('external provenance differs from capsule')
            cells = set()
            for game in results['per_game']:
                cell = game['map'], game['side']
                if cell in cells: raise ValueError('duplicate schedule cell')
                cells.add(cell)
                prefix = f"games/{game['map']}-{game['side']}/"
                if 'summary_sha256' in game: check(prefix+'summary.json', game['summary_sha256'])
                bundles = [name for name in z.namelist() if name.startswith(prefix) and name.endswith('.repl26a')]
                if len(bundles) != 1: raise ValueError('expected exactly one replay per cell')
                check(bundles[0], game['replay_sha256'])
                if game['candidate_sha256'] != provenance['candidate_sha256']: raise ValueError('candidate changed within run')
        print(f'{folder.name}: verified {len(cells)} cells, frozen source, binaries, summaries and replays', flush=True)
        count += 1
    if not count: raise ValueError('no experiment capsules found')

def fuel_values(bundle, side):
    with zipfile.ZipFile(bundle) as z:
        raw = z.read(f'team-{side.lower()}.fuel')
    if raw[:7] != b'a62leuf' or (len(raw)-13) % 8:
        raise ValueError('unknown engine fuel trace format')
    values = struct.unpack('<%dQ' % ((len(raw)-13)//8), raw[13:])
    return values[:8], values[8:]

def match(candidate, opponent, map_path, side, folder, diagnostic=False):
    folder.mkdir(parents=True, exist_ok=False)
    a, b = (candidate, opponent) if side == 'A' else (opponent, candidate)
    command = [CLI, 'run', a, b, '--map', map_path, '--out-dir', folder,
               '--statistics', folder/'summary.json', '--json', '--release']
    if diagnostic: command += ['--rounds', '12']
    log = run(command, timeout=300)
    (folder/'runner.log').write_text(log, encoding='utf-8')
    bundle = next(folder.glob('*.repl26a'))
    if diagnostic:
        budgets, fuel = fuel_values(bundle, side)
        with zipfile.ZipFile(bundle) as z:
            stdout = z.read(f'team-{side.lower()}.stdout').replace(b'\0', b'').decode('utf-8', 'replace')
        (folder/'candidate.stdout').write_text(stdout, encoding='utf-8')
        result = dict(map=map_path.stem, map_sha256=sha(map_path), side=side, diagnostic=True,
            rounds=12, outcome='unfinished-diagnostic', banked=0, opponent_banked=0, collected=0, gold=0,
            deaths=0, faults=0, faults_measured=False, opponent_faults=0, fuel_outs=sum(x>=100000 for x in fuel[20:]),
            fuel_budgets=budgets, candidate_sha256=sha(candidate), opponent_sha256=sha(opponent), replay_sha256=sha(bundle))
        write(folder/'receipt.json', result)
        return result, fuel[20:]
    d = json.loads((folder/'summary.json').read_text(encoding='utf-8'))
    me, other = 'team'+side, 'team'+('B' if side == 'A' else 'A')
    def number(value): return int(value)
    teams = {row['team']: row for row in d['teams']}
    champs = [row for row in d['champions'] if row['team'] == me]
    budgets, fuel = fuel_values(bundle, side)
    # The trace starts with draft and boosted first turns. Exclude only this
    # bounded prefix from ordinary-turn quantiles; exact exhaustions use events.
    ordinary = fuel[20:]
    exhaustions = sum(len(e['entries']) for e in d['events'] if e['kind'] == 'fuelExhausted' and e['owner']['team'] == me)
    result = dict(map=map_path.stem, map_sha256=sha(map_path), side=side,
        rounds=d['match']['roundsStarted'], outcome=d['match']['outcome'],
        banked=number(teams[me]['submittedGems']), opponent_banked=number(teams[other]['submittedGems']),
        collected=sum(number(c['metrics']['collectedGems']) for c in champs),
        gold=sum(number(c['metrics']['earnedGold']) for c in champs),
        deaths=sum(number(c['metrics']['deaths']) for c in champs),
        faults=number(d['diagnostics']['botFaults'][me]), opponent_faults=number(d['diagnostics']['botFaults'][other]),
        fuel_outs=exhaustions, engine=d['match']['engineVersion'], engine_hash=d['match']['engineBuildHash'],
        fuel_budgets=budgets, candidate_sha256=sha(candidate), opponent_sha256=sha(opponent),
        summary_sha256=sha(folder/'summary.json'), replay_sha256=sha(bundle))
    with zipfile.ZipFile(bundle) as z:
        stdout = z.read(f'team-{side.lower()}.stdout').replace(b'\0', b'').decode('utf-8', 'replace')
    (folder/'candidate.stdout').write_text(stdout, encoding='utf-8')
    write(folder/'receipt.json', result)
    return result, ordinary

def experiment(args):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.name): raise ValueError('name must use letters, digits, dash or underscore')
    out = TMP / args.name
    out.mkdir(parents=True, exist_ok=False)
    source = ROOT / ('tests/dz/conformance' if args.command == 'conformance' else 'bots/dz')
    frozen = out / 'build/candidate'
    shutil.copytree(source/'src', frozen/'src')
    if args.trace:
        config = frozen/'src/config.h'
        config.write_text(config.read_text().replace('#define DZ_TRACE 0', '#define DZ_TRACE 1'))
    candidate = build(frozen, out/'candidate.wasm')
    if args.opponent_wasm:
        opponent = out/'opponent.wasm'; shutil.copyfile(Path(args.opponent_wasm), opponent)
    else:
        source_opp = ROOT/'bots'/args.opponent
        frozen_opp = out/'build/opponent'
        shutil.copytree(source_opp/'src', frozen_opp/'src')
        opponent = build(frozen_opp, out/'opponent.wasm')
    names = sorted(p.stem for p in MAPS.glob('*.map26a')) if args.pool else args.maps
    diagnostic = args.command == 'conformance'
    jobs = [(MAPS/(name+'.map26a'), side) for name in names for side in ('A','B')]
    provenance = dict(created_utc=dt.datetime.now(dt.timezone.utc).isoformat(), command=sys.argv,
        git_head=run(['git','rev-parse','HEAD']).strip(), release=True, trace=args.trace, diagnostic=diagnostic,
        cli_sha256=sha(CLI), source={p.relative_to(frozen).as_posix():sha(p) for p in (frozen/'src').rglob('*') if p.is_file()},
        sdk={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'sdk/cpp').rglob('*') if p.is_file()},
        maps={p.stem:sha(p) for p,_ in jobs}, candidate_sha256=sha(candidate), opponent_sha256=sha(opponent),
        seed='deterministic; no seed parameter; duplicate identities are not independent samples')
    write(out/'provenance.json', provenance)
    ledger = ROOT/'research/dz/SEED_LEDGER.md'
    with ledger.open('a', encoding='utf-8', newline='\n') as f:
        f.write(f'| {args.name} | {dt.datetime.now(dt.timezone.utc).date()} | deterministic; Wasm {sha(candidate)[:12]} | {len(jobs)} cells; {args.opponent} | {args.command}; trace={args.trace} |\n')
    rows, fuel = [], []
    with cf.ThreadPoolExecutor(max_workers=min(4, args.workers)) as executor:
        futures = [executor.submit(match, candidate, opponent, p, side, out/'games'/f'{p.stem}-{side}', diagnostic) for p,side in jobs]
        for future in cf.as_completed(futures):
            row, used = future.result(); rows.append(row); fuel.extend(used)
            print(f"{len(rows)}/{len(jobs)} {row['map']} {row['side']} banked={row['banked']} faults={row['faults']} fuel_outs={row['fuel_outs']}", flush=True)
    rows.sort(key=lambda r:(r['map'],r['side'])); fuel.sort()
    result = dict(games=len(rows), wins=sum(r['outcome']=='team'+r['side'] for r in rows),
        faults=sum(r['faults'] for r in rows), opponent_faults=sum(r['opponent_faults'] for r in rows),
        fuel_outs=sum(r['fuel_outs'] for r in rows),
        mean_collected=sum(r['collected'] for r in rows)/len(rows),
        mean_banked=sum(r['banked'] for r in rows)/len(rows),
        fuel_mean=sum(fuel)/max(1,len(fuel)), fuel_p99=fuel[min(len(fuel)-1,int(.99*len(fuel)))] if fuel else None,
        fuel_prefix_excluded_per_game=20, per_game=rows)
    write(out/'results.json', result)
    dest = ROOT/'research/dz/runs'/args.name; dest.mkdir(parents=True, exist_ok=False)
    for name in ('results.json','provenance.json'): shutil.copyfile(out/name, dest/name)
    # Complete fresh-system evidence, compressed below normal Git file limits on
    # starter runs. Large campaigns should split capsules before committing.
    with zipfile.ZipFile(dest/'evidence.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in out.rglob('*'):
            if p.is_file() and '.cambc' not in p.parts and not p.name.endswith('.obj'):
                z.write(p, p.relative_to(out))
    print(json.dumps({k:v for k,v in result.items() if k!='per_game'}, indent=2), flush=True)
    if result['faults'] or (not diagnostic and result['fuel_outs']):
        raise SystemExit('runtime gate failed; evidence preserved')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('host')
    sub.add_parser('build')
    sub.add_parser('verify')
    for name in ('smoke','conformance'):
        p = sub.add_parser(name); p.add_argument('--name', required=True)
        p.add_argument('--maps', nargs='+', default=['00collision'])
        p.add_argument('--pool', action='store_true'); p.add_argument('--workers', type=int, default=4)
        p.add_argument('--opponent', default='idle81'); p.add_argument('--opponent-wasm')
        p.add_argument('--trace', action='store_true')
    args = parser.parse_args()
    if args.command == 'host': host_tests()
    elif args.command == 'verify': verify_evidence()
    elif args.command == 'build': print(build(ROOT/'bots/dz', TMP/'dz.wasm'))
    else: experiment(args)

if __name__ == '__main__': main()
