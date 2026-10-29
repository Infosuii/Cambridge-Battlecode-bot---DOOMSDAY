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

def sample_at(runs, sample):
    """Native RLE sample value. Never extrapolate past the recorded match."""
    if sample < 0: raise ValueError('negative sample')
    start = 0
    for segment in runs:
        duration = int(segment['duration'])
        if duration <= 0: raise ValueError('invalid RLE duration')
        if sample < start + duration: return float(segment['value'])
        start += duration
    return None

def checkpoints(summary, side):
    me = 'team'+side
    result = {}
    for requested in (100,250,500):
        actual = min(requested, int(summary['match']['roundsStarted']))
        values = dict(collected=0., gold=0., deaths=0., banked=0.)
        available = set()
        for row in summary.get('championTimelines', []):
            key = {'collectedGems':'collected','earnedGold':'gold','deaths':'deaths'}.get(row['metric'])
            if not key or row['owner']['team'] != me: continue
            value = sample_at(row['runs'], actual)
            if value is not None: values[key] += value; available.add(key)
        for row in summary.get('teamTimelines', []):
            if row['owner'] == me and row['metric'] == 'submittedGems':
                value = sample_at(row['runs'], actual)
                if value is not None: values['banked'] = value; available.add('banked')
        result[str(requested)] = dict(round=actual, ended_before_checkpoint=actual < requested,
            **{k:(v if k in available else None) for k,v in values.items()})
    return result

def diagnostic_checks(stdout, fixture):
    if fixture == 'fingerprint':
        records=re.findall(r'CT27_FIELD ([\w.]+) (u32|f32|f64) ([0-9a-f]+)',stdout)
        fields={key:kind+':'+value for key,kind,value in records}
        canonical=json.dumps(fields,sort_keys=True,separators=(',',':')).encode()
        digest=hashlib.sha256(canonical).hexdigest()
        reference=ROOT/'research/dz/ENGINE_FINGERPRINT.json'
        expected=json.loads(reference.read_text()) if reference.exists() else None
        return dict(passed=bool(expected and fields==expected['fields'] and len(records)==len(fields)
                    and 'CT27_COMPLETE schema=1' in stdout and 'ERROR' not in stdout),
                    schema=1,field_count=len(fields),sha256=digest,reference_present=bool(expected))
    if fixture == 'reset':
        match=re.search(r'CT_CHECK name=camp_kill_resets_both_cooldowns pass=(\d)',stdout)
        after=re.search(r'CT26 second_cast_after_kill=(\d) code=(\d+)',stdout)
        return dict(passed=bool(match and int(match[1]) and after and 'ERROR' not in stdout),
                    camp_reset_observed=bool(match and int(match[1])),
                    second_cast_after_kill_accepted=bool(after and int(after[1])),second_cast_code=int(after[2]) if after else None)
    if fixture == 'capture':
        checks={name:int(value) for name,value in re.findall(r'CT_CHECK name=(\w+) pass=(\d)',stdout)}
        required={'split_primary_low_handle_remainder','split_partner_share','occupied_spawn_delays_respawn','vacated_spawn_respawns'}
        return dict(passed=not(required-checks.keys()) and all(checks.values()) and 'ERROR' not in stdout and 'CT_SETUP_FAILURE' not in stdout,
                    checks=checks,missing=sorted(required-checks.keys()))
    if fixture == 'visibility':
        records={name:dict(accepted=int(ok),value=int(value),code=int(code)) for name,ok,value,code in
                 re.findall(r'CT_QUERY name=(\w+) accepted=(\d) value=(\d+) code=(\d+)',stdout)}
        required={'hidden_alive','hidden_gems','hidden_items','hidden_cooldown','visible_alive','visible_gems',
                  'visible_items','visible_cooldown0','visible_cooldown1'}
        visible_ok=all(records.get(name,{}).get('accepted')==1 for name in required if name.startswith('visible_'))
        return dict(passed=not(required-records.keys()) and visible_ok and 'ERROR' not in stdout,
                    queries=records,missing=sorted(required-records.keys()))
    if fixture == 'channels':
        checks={name:int(value) for name,value in re.findall(r'CT_CHECK name=(\w+) pass=(\d)',stdout)}
        required={'recall_starts_in_camp_range','camp_damage_interrupts_recall','base_recall_duration_five',
                  'spawn_arrival_precedes_heal','one_spawn_turn_full_heal'}
        return dict(passed=not(required-checks.keys()) and all(checks.values()) and 'ERROR' not in stdout and 'CT_SETUP_FAILURE' not in stdout,
                    checks=checks,missing=sorted(required-checks.keys()))
    if fixture == 'actions':
        checks = {name:int(value) for name,value in re.findall(r'CT_CHECK name=(\w+) pass=(\d)',stdout)}
        required = {'ranged_move_blocks_attack','ranged_attack_blocks_move','reset_restores_attack','one_cast_per_turn',
                    'move_blocks_exclusive_cast','exclusive_cast_blocks_move','melee_move_then_attack','melee_attack_then_move'}
        if 'CT7_ACTOR type=12' in stdout: required.add('shield_then_move')
        return dict(passed=not(required-checks.keys()) and all(checks.values()) and 'ERROR' not in stdout,
                    checks=checks,missing=sorted(required-checks.keys()))
    if fixture != 'camps': return {'automated_fixture_checks': 'not yet implemented'}
    rows = re.findall(r'CT11 round=(\d+) hp=([\d.]+) delta=([-\d.]+) active=(\d+) incoming=([\d.]+)', stdout)
    consecutive = best = 0; previous = None; hits = []
    for raw in rows:
        round, hp, delta, active, incoming = map(float, raw)
        matches = incoming > 0 and delta > 0 and abs(delta-incoming) < .01
        consecutive = consecutive+1 if matches and previous is not None and round == previous+1 else int(matches)
        best = max(best, consecutive); previous = round
        if matches: hits.append(dict(round=int(round), delta=delta, in_range_strength=incoming))
    return dict(passed=best>=5 and 'ERROR' not in stdout, consecutive_full_strength_damage_rounds=best,
                matching_hits=len(hits), first_hits=hits[:10], setup_reached_damage=bool(hits),
                conclusion='full in-range camp strength lost every round in this fixture; targeting not isolated')

def match(candidate, opponent, map_path, side, folder, diagnostic=False, diagnostic_rounds=12, fixture='kernel', existing=False):
    if not existing:
        folder.mkdir(parents=True, exist_ok=False)
        a, b = (candidate, opponent) if side == 'A' else (opponent, candidate)
        command = [CLI, 'run', a, b, '--map', map_path, '--out-dir', folder,
                   '--statistics', folder/'summary.json', '--json', '--release']
        if diagnostic: command += ['--rounds', str(diagnostic_rounds)]
        log = run(command, timeout=300)
        (folder/'runner.log').write_text(log, encoding='utf-8')
    bundle = next(folder.glob('*.repl26a'))
    if diagnostic:
        budgets, fuel = fuel_values(bundle, side)
        with zipfile.ZipFile(bundle) as z:
            stdout = z.read(f'team-{side.lower()}.stdout').replace(b'\0', b'').decode('utf-8', 'replace')
        (folder/'candidate.stdout').write_text(stdout, encoding='utf-8')
        result = dict(map=map_path.stem, map_sha256=sha(map_path), side=side, diagnostic=True,
            rounds=diagnostic_rounds, outcome='unfinished-diagnostic', banked=0, opponent_banked=0, collected=0, gold=0,
            deaths=0, faults=0, faults_measured=False, opponent_faults=0, fuel_outs=sum(x>=100000 for x in fuel[20:]),
            fuel_budgets=budgets, candidate_sha256=sha(candidate), opponent_sha256=sha(opponent), replay_sha256=sha(bundle))
        result['diagnostic_checks'] = diagnostic_checks(stdout, fixture)
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
    draft_turns = sum(row['team'] == me for row in d['roster']['draft'])
    boosted_turns = len(champs)
    prefix = draft_turns + boosted_turns
    ordinary = fuel[prefix:]
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
    result.update(fuel_prefix_excluded=prefix, checkpoints=checkpoints(d, side))
    with zipfile.ZipFile(bundle) as z:
        stdout = z.read(f'team-{side.lower()}.stdout').replace(b'\0', b'').decode('utf-8', 'replace')
    (folder/'candidate.stdout').write_text(stdout, encoding='utf-8')
    if 'DZ_COUNTS' in stdout:
        result['caught_action_errors']=len(re.findall(r'DZ_ACTION_ERROR ',stdout))
        result['caught_module_errors']=len(re.findall(r'DZ_MODULE_ERROR ',stdout))
    write(folder/'receipt.json', result)
    return result, ordinary

def experiment(args):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.name): raise ValueError('name must use letters, digits, dash or underscore')
    out = TMP / args.name
    out.mkdir(parents=True, exist_ok=False)
    fixtures = {'kernel':'conformance','camps':'camp_probe','actions':'actions_probe','channels':'channel_probe','visibility':'visibility_probe','capture':'capture_probe','reset':'reset_probe','fingerprint':'fingerprint_probe'}
    source = ROOT / (f'tests/dz/{fixtures[args.fixture]}' if args.command == 'conformance' else 'bots/dz')
    frozen = out / 'build/candidate'
    shutil.copytree(source/'src', frozen/'src')
    if args.trace:
        config = frozen/'src/config.h'
        config.write_text(config.read_text().replace('#define DZ_TRACE 0', '#define DZ_TRACE 1'))
    for definition in args.set:
        name,separator,value=definition.partition('=')
        if not separator or not re.fullmatch(r'DZ_[A-Z0-9_]+',name) or not re.fullmatch(r'[01]',value): raise ValueError('expected DZ_FLAG=0 or 1')
        config=frozen/'src/config.h'; source=config.read_text()
        source,count=re.subn(r'^#define '+name+r'\s+[^\n]+', '#define '+name+' '+value,source,flags=re.MULTILINE)
        if count!=1: raise ValueError('unknown or ambiguous define: '+name)
        config.write_text(source,encoding='utf-8',newline='\n')
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
    rows, fuel, errors = [], [], []
    with cf.ThreadPoolExecutor(max_workers=min(4, args.workers)) as executor:
        futures = [executor.submit(match, candidate, opponent, p, side, out/'games'/f'{p.stem}-{side}', diagnostic, args.diagnostic_rounds, args.fixture) for p,side in jobs]
        for future in cf.as_completed(futures):
            try: row, used = future.result()
            except Exception as error: errors.append(str(error)); continue
            rows.append(row); fuel.extend(used)
            print(f"{len(rows)}/{len(jobs)} {row['map']} {row['side']} banked={row['banked']} faults={row['faults']} fuel_outs={row['fuel_outs']}", flush=True)
    if errors:
        write(out/'runner_failures.json', errors)
        raise RuntimeError(f'{len(errors)} cells could not be analyzed; raw evidence retained for recover: '+errors[0])
    finish_report(args.name, out, rows, fuel, diagnostic)

def finish_report(name, out, rows, fuel, diagnostic):
    rows.sort(key=lambda r:(r['map'],r['side'])); fuel.sort()
    result = dict(games=len(rows), wins=sum(r['outcome']=='team'+r['side'] for r in rows),
        faults=sum(r['faults'] for r in rows), opponent_faults=sum(r['opponent_faults'] for r in rows),
        fuel_outs=sum(r['fuel_outs'] for r in rows),
        mean_collected=sum(r['collected'] for r in rows)/len(rows),
        mean_banked=sum(r['banked'] for r in rows)/len(rows),
        fuel_mean=sum(fuel)/max(1,len(fuel)), fuel_p99=fuel[min(len(fuel)-1,int(.99*len(fuel)))] if fuel else None,
        fuel_quantile_policy='diagnostics: omit 20 entries; full matches: omit exactly own draft picks + first boosted turn per body', per_game=rows)
    write(out/'results.json', result)
    dest = ROOT/'research/dz/runs'/name; dest.mkdir(parents=True, exist_ok=False)
    for name in ('results.json','provenance.json'): shutil.copyfile(out/name, dest/name)
    # Complete fresh-system evidence, compressed below normal Git file limits on
    # starter runs. Large campaigns should split capsules before committing.
    with zipfile.ZipFile(dest/'evidence.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in out.rglob('*'):
            if p.is_file() and '.cambc' not in p.parts and not p.name.endswith('.obj'):
                z.write(p, p.relative_to(out))
    print(json.dumps({k:v for k,v in result.items() if k!='per_game'}, indent=2), flush=True)
    if result['faults'] or (not diagnostic and (result['fuel_outs'] or any(
            r.get('caught_action_errors',0) or r.get('caught_module_errors',0) for r in rows))):
        raise SystemExit('runtime gate failed; evidence preserved')
    if diagnostic and any(row.get('diagnostic_checks',{}).get('passed') is False for row in rows):
        raise SystemExit('diagnostic assertions failed; complete evidence preserved')

def recover(args):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.name): raise ValueError('invalid run name')
    out = TMP/args.name
    if (out/'results.json').exists() or (ROOT/'research/dz/runs'/args.name).exists():
        raise ValueError('finished experiments are immutable; recover only incomplete analysis')
    provenance = json.loads((out/'provenance.json').read_text())
    candidate, opponent = out/'candidate.wasm', out/'opponent.wasm'
    if sha(candidate) != provenance['candidate_sha256'] or sha(opponent) != provenance['opponent_sha256']:
        raise ValueError('frozen binaries changed')
    rows, fuel = [], []
    for name,digest in sorted(provenance['maps'].items()):
        path = MAPS/(name+'.map26a')
        if sha(path) != digest: raise ValueError('map changed')
        for side in ('A','B'):
            row, used = match(candidate,opponent,path,side,out/'games'/f'{name}-{side}',existing=True)
            rows.append(row); fuel.extend(used)
    write(out/'analysis_recovery.json',dict(parser_sha256=sha(Path(__file__)),
        note='Completed raw matches reanalyzed after parser correction; no engine rerun, source or binary change'))
    finish_report(args.name,out,rows,fuel,False)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('host')
    sub.add_parser('build')
    sub.add_parser('verify')
    p = sub.add_parser('recover'); p.add_argument('--name',required=True)
    for name in ('smoke','conformance'):
        p = sub.add_parser(name); p.add_argument('--name', required=True)
        p.add_argument('--maps', nargs='+', default=['00collision'])
        p.add_argument('--pool', action='store_true'); p.add_argument('--workers', type=int, default=4)
        p.add_argument('--opponent', default='idle81'); p.add_argument('--opponent-wasm')
        p.add_argument('--trace', action='store_true')
        p.add_argument('--fixture', choices=['kernel','camps','actions','channels','visibility','capture','reset','fingerprint'], default='kernel')
        p.add_argument('--diagnostic-rounds', type=int, default=12)
        p.add_argument('--set', action='append', default=[], help='override one DZ boolean flag in the frozen copy only')
    args = parser.parse_args()
    if args.command == 'host': host_tests()
    elif args.command == 'verify': verify_evidence()
    elif args.command == 'recover': recover(args)
    elif args.command == 'build': print(build(ROOT/'bots/dz', TMP/'dz.wasm'))
    else: experiment(args)

if __name__ == '__main__': main()
