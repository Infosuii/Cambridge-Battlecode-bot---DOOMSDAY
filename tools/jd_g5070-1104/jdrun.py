#!/usr/bin/env python3
"""Paired experiment runner for run g5070-1104 (stdlib only, run with `py`).

  py tools/jd_g5070-1104/jdrun.py freeze <bot> [--src DIR] [--defines JD_X=1,...]
  py tools/jd_g5070-1104/jdrun.py run --name <fresh> --cand <frozen> --base <frozen> --opps a,b --maps <set>
        [--limit N] [--sides AB] [--jobs 14] [--fuel-quantum N] [--timeout 900] [--background] [--holdout]
        (holdout maps pool/fresh51104/official70 and holdout opponents need --holdout: confirmation only)
  py tools/jd_g5070-1104/jdrun.py report --name <run>
  py tools/jd_g5070-1104/jdrun.py list

Eval root (outside the repo): JD_EVAL or <workspace>/jd-eval. Frozen bots live in <eval>/bots/<bot>-<srcsha12>/src and
are never overwritten; <eval>/frozen.json maps a short alias (the bot name) to its latest frozen build. A run writes
one run-batch manifest holding the candidate AND base arms on the same opponent/map/side cells (the base arm is
skipped and reused when base == cand), refuses a reused --name, and plays from the eval root. `report` decodes
every replay (fuel trace team-?.fuel via tools/dz.py fuel_values, fuelExhausted events, botFaults), pairs cells
candidate-minus-base and prints a map-clustered bootstrap 95% CI. Results: <eval>/runs/<name>/results.json and a
compact copy in research/jd-g5070-1104/runs/<name>.json.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EVAL = Path(os.environ.get('JD_EVAL', str(REPO.parent / 'jd-eval')))
CLI = EVAL / 'tools' / 'vendor' / 'cambc.exe'
A2_BOTS = EVAL / 'a2' / 'research' / 'agent2-neural' / 'rl_workspace' / 'v4' / 'bots'
RESEARCH = REPO / 'research' / 'jd-g5070-1104'
FROZEN = EVAL / 'frozen.json'
SEED = 1104
RESAMPLES = 2000
# Frozen partitions (research/jd-g5070-1104/GATES.md, hashes in RUN_MANIFEST.json).
HOLDOUT_MAPS = {'pool', 'fresh51104', 'official70'}
HOLDOUT_OPPS = {'b5_c3', 'v61_c3', 'public-decrest', 'public-wardens', 'x3mf2'}
PARTITION_OF = {'conf': 'dev', 'dev': 'dev', 'select': 'selection'}
sys.path.insert(0, str(REPO / 'tools'))
from dz import fuel_values  # noqa: E402  (replay fuel trace decoder: 8 settings, then fuel used per unit turn)


def now():
    return dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def tree_digest(src: Path):
    h = hashlib.sha256()
    for p in sorted(x for x in src.rglob('*') if x.is_file()):
        rel = p.relative_to(src).as_posix()
        h.update(rel.encode() + b'\0' + sha_file(p).encode() + b'\n')
    return h.hexdigest()


def load_frozen():
    return json.loads(FROZEN.read_text(encoding='utf-8')) if FROZEN.exists() else {'bots': {}, 'alias': {}}


def resolve(name):
    fz = load_frozen()
    if name in fz['bots']:
        return name
    if name in fz['alias']:
        return fz['alias'][name]
    raise SystemExit(f'not frozen: {name} (run `jdrun.py freeze {name}` first)')


def cmd_freeze(a):
    src = Path(a.src) if a.src else None
    if src is None:
        for cand in (REPO / 'bots' / a.bot / 'src', A2_BOTS / a.bot / 'src'):
            if cand.is_dir():
                src = cand
                break
    if src is None or not src.is_dir():
        raise SystemExit(f'no source for {a.bot}')
    defines = [d for d in (a.defines or '').split(',') if d]
    digest = tree_digest(src)
    dh = hashlib.sha256((digest + '|' + ','.join(sorted(defines))).encode()).hexdigest()
    name = f'{a.alias or a.bot}-{dh[:12]}'
    dest = EVAL / 'bots' / name
    fz = load_frozen()
    if dest.exists() or name in fz['bots']:
        raise SystemExit(f'refusing to overwrite frozen bot {name} ({dest})')
    shutil.copytree(src, dest / 'src')
    if defines:
        # Prepend switch overrides to the candidate's config header (jd_config.h if present, else common.h).
        hdr = dest / 'src' / ('jd_config.h' if (dest / 'src' / 'jd_config.h').exists() else 'common.h')
        text = hdr.read_text(encoding='utf-8')
        pre = ''.join(f'#define {d.split("=")[0]} {d.split("=", 1)[1] if "=" in d else "1"}\n' for d in defines)
        hdr.write_text(pre + text, encoding='utf-8', newline='')
    wasm = EVAL / 'wasm' / f'{name}.wasm'
    wasm.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    r = subprocess.run([str(CLI), 'build', f'bots/{name}', '--release', '--output', str(wasm)], cwd=EVAL,
                       capture_output=True, text=True, timeout=900)
    if r.returncode != 0 or not wasm.exists():
        shutil.rmtree(dest, ignore_errors=True)
        raise SystemExit(f'build failed for {name}:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}')
    for junk in (dest / 'compile_commands.json',):
        if junk.exists():
            junk.unlink()
    entry = dict(bot=a.bot, alias=a.alias or a.bot, src=str(src), src_tree_sha256=digest, defines=defines,
                 wasm=str(wasm), wasm_sha256=sha_file(wasm), build_s=round(time.time() - t0, 1), frozen_at=now())
    fz['bots'][name] = entry
    fz['alias'][a.alias or a.bot] = name
    FROZEN.write_text(json.dumps(fz, indent=1), encoding='utf-8')
    print(f'frozen {name} wasm_sha256={entry["wasm_sha256"]} src_tree={digest[:16]} defines={defines}')


def map_set(name, limit):
    d = EVAL / 'maps' / name
    if not d.is_dir():
        raise SystemExit(f'no map set {d}')
    maps = sorted(d.glob('*.map26a'))
    return maps[:limit] if limit else maps


def cells(a, maps):
    opps = [resolve(o) for o in a.opps.split(',') if o]
    out = []
    for opp in opps:
        for m in maps:
            for side in a.sides:
                out.append(dict(opp=opp, map=m.stem, map_path=str(m), side=side))
    return out


def game_id(arm, c):
    return f'{arm}__{c["opp"]}__{c["map"]}__{c["side"]}'


def cmd_run(a):
    out = EVAL / 'runs' / a.name
    if out.exists() or (RESEARCH / 'runs' / f'{a.name}.json').exists():
        raise SystemExit(f'refusing reused run name {a.name}')
    # Partition guard (GATES.md): holdout maps/opponents are never used for tuning; such runs need --holdout,
    # which is recorded in run.json so every result says which partition it came from.
    held = a.maps in HOLDOUT_MAPS or any(o == h or o.startswith(h + '-') for o in a.opps.split(',') for h in HOLDOUT_OPPS)
    if held and not a.holdout:
        raise SystemExit(f'{a.maps}/{a.opps} touches the final holdout partition; pass --holdout (confirmation only)')
    cand, base = resolve(a.cand), resolve(a.base)
    maps = map_set(a.maps, a.limit)
    cs = cells(a, maps)
    arms = {'cand': cand} if cand == base else {'cand': cand, 'base': base}
    (out / 'games').mkdir(parents=True)
    rows = []
    for c in cs:
        for arm, bot in arms.items():
            g = game_id(arm, c)
            # run-batch resolves manifest paths relative to the manifest's directory (<eval>/runs/<name>/); the eval
            # root path contains spaces, so absolute paths cannot be used in the whitespace-separated manifest.
            mp = '../../' + os.path.relpath(c['map_path'], EVAL).replace('\\', '/')
            A, B = (f'../../bots/{bot}', f'../../bots/{c["opp"]}') if c['side'] == 'A' else (f'../../bots/{c["opp"]}', f'../../bots/{bot}')
            rows.append(f'{A} {B} {mp} games/{g}.repl26a --statistics games/{g}.json --json')
    (out / 'manifest.txt').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    fz = load_frozen()['bots']
    meta = dict(name=a.name, created=now(), cand=cand, base=base, base_is_cand=cand == base, opps=a.opps.split(','),
                maps=a.maps, limit=a.limit, sides=a.sides, jobs=a.jobs, fuel_quantum=a.fuel_quantum,
                timeout=a.timeout, games=len(rows), cells=len(cs),
                partition='holdout' if held else PARTITION_OF.get(a.maps, 'other'),
                wasm={b: fz[b]['wasm_sha256'] for b in {cand, base, *[c['opp'] for c in cs]}},
                map_sha256={m.stem: sha_file(m) for m in maps}, git_head=git_head(), cli_sha256=sha_file(CLI),
                cells_list=[{k: v for k, v in c.items() if k != 'map_path'} for c in cs])
    if a.fuel_quantum:
        meta['label'] = 'DIAGNOSTIC (non-official fuel quantum)'
    (out / 'run.json').write_text(json.dumps(meta, indent=1), encoding='utf-8')
    cmd = [str(CLI), 'run-batch', f'runs/{a.name}/manifest.txt', '--jobs', str(a.jobs), '--json', '--release',
           '--color', 'never', '--log-limit', '67108864', '--timeout', str(a.timeout)]
    if a.fuel_quantum:
        cmd += ['--fuel-quantum', str(a.fuel_quantum)]
    print(f'{a.name}: {len(rows)} games ({len(cs)} cells x {len(arms)} arms), jobs {a.jobs}', flush=True)
    log = open(out / 'batch.log', 'w', encoding='utf-8')
    if a.background:
        flags = getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0) | getattr(subprocess, 'DETACHED_PROCESS', 0)
        wrapper = [sys.executable, str(Path(__file__).resolve()), '_batch', '--name', a.name, '--', *cmd]
        subprocess.Popen(wrapper, cwd=EVAL, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
        print(f'started in background; log {out / "batch.log"}')
        return
    run_batch(out, cmd, log)


def run_batch(out, cmd, log):
    t0 = time.time()
    (out / 'started.txt').write_text(now(), encoding='utf-8')
    r = subprocess.run(cmd, cwd=EVAL, stdout=log, stderr=subprocess.STDOUT)
    secs = time.time() - t0
    (out / 'done.json').write_text(json.dumps(dict(finished=now(), seconds=round(secs, 1), returncode=r.returncode)),
                                   encoding='utf-8')
    print(f'batch finished rc={r.returncode} in {secs:.0f}s', flush=True)


def cmd_batch(a):
    cmd = a.batch_cmd[1:] if a.batch_cmd and a.batch_cmd[0] == '--' else a.batch_cmd
    run_batch(EVAL / 'runs' / a.name, cmd, sys.stdout)


def git_head():
    r = subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    return r.stdout.strip()


def decode_game(stats: Path, replay: Path, side: str):
    d = json.loads(stats.read_text(encoding='utf-8'))
    me, other = 'team' + side, 'team' + ('B' if side == 'A' else 'A')
    teams = {t['team']: t for t in d['teams']}
    champs = [c for c in d['champions'] if c['team'] == me]
    m = d['match']
    winner = m.get('outcome')  # 'teamA' / 'teamB'; anything else is scored as a draw
    score = 1.0 if winner == me else (0.0 if winner == other else 0.5)
    exhaust = sum(len(e['entries']) for e in d['events'] if e['kind'] == 'fuelExhausted' and e['owner']['team'] == me)
    budgets, fuel = fuel_values(replay, side)
    draft_turns = sum(r['team'] == me for r in d['roster']['draft'])
    nchamp = len(champs)
    # Trace rule (FEAT-001): settings are (draft first, draft later, first champion turn, ordinary) per team;
    # the trace is draft turns, then each champion's first turn, then ordinary turns. A unit turn whose used fuel
    # is >= its budget counts as a suspension. Respawn first turns are not separable here (FEAT-002 measures them),
    # so trace_over is a cross-check; fuel_outs (engine fuelExhausted events) is the primary count.
    off = 0 if side == 'A' else 4
    bd, bdl, bf, bo = budgets[off:off + 4] if len(budgets) >= off + 4 else (budgets + (0,) * 8)[off:off + 4]
    over = 0
    for i, v in enumerate(fuel):
        if i < draft_turns:
            lim = bd if i == 0 else bdl
        elif i < draft_turns + nchamp:
            lim = bf
        else:
            lim = bo
        over += lim > 0 and v >= lim
    ordinary = sorted(fuel[draft_turns + nchamp:])
    q = lambda p: ordinary[min(len(ordinary) - 1, int(p * len(ordinary)))] if ordinary else 0
    return dict(winner=winner, score=score, rounds=m.get('roundsStarted'),
                banked=int(teams[me]['submittedGems']), opp_banked=int(teams[other]['submittedGems']),
                collected=sum(int(c['metrics']['collectedGems']) for c in champs),
                gold=sum(int(c['metrics']['earnedGold']) for c in champs),
                deaths=sum(int(c['metrics']['deaths']) for c in champs),
                faults=int(d['diagnostics']['botFaults'][me]), opp_faults=int(d['diagnostics']['botFaults'][other]),
                fuel_outs=exhaust, trace_over=over, fuel_budgets=list(budgets), unit_turns=len(fuel),
                fuel_p50=q(0.5), fuel_p99=q(0.99), fuel_max=ordinary[-1] if ordinary else 0,
                engine=m.get('engineVersion'), engine_hash=m.get('engineBuildHash'), seed=m.get('seed'),
                map_hash=m.get('mapHash'), area=int(m.get('width', 0)) * int(m.get('height', 0)), camp_clears=sum(len(e['entries']) for e in d['events']
                                                           if e['kind'] == 'campClear' and e['owner']['team'] == me))


def category(map_name):
    if 'pool_' in map_name:
        return 'generated'
    if map_name[:2] in ('00', '01', '02', '03'):
        return 'pool' + map_name[:2]
    return map_name.split('-')[0]


def size_bucket(area):
    return 'small' if area < 1600 else ('medium' if area < 4900 else 'large')


def bootstrap(by_map, rng):
    keys = sorted(by_map)
    if not keys:
        return None, None
    stats = []
    for _ in range(RESAMPLES):
        tot = n = 0
        for _ in keys:
            v = by_map[keys[rng.randrange(len(keys))]]
            tot += sum(v)
            n += len(v)
        stats.append(tot / n)
    stats.sort()
    return stats[int(0.025 * RESAMPLES)], stats[int(0.975 * RESAMPLES) - 1]


def cmd_report(a):
    out = EVAL / 'runs' / a.name
    meta = json.loads((out / 'run.json').read_text(encoding='utf-8'))
    arms = ['cand'] if meta['base_is_cand'] else ['cand', 'base']
    games, missing, failed = {}, [], []
    for c in meta['cells_list']:
        for arm in arms:
            g = game_id(arm, c)
            st, rp = out / 'games' / f'{g}.json', out / 'games' / f'{g}.repl26a'
            if not st.exists() or not rp.exists():
                missing.append(g)
                continue
            try:
                games[g] = dict(c, arm=arm, **decode_game(st, rp, c['side']))
            except Exception as e:  # noqa: BLE001 (record and count, never silently drop)
                failed.append(dict(game=g, error=repr(e)[:300]))
    pairs = []
    for c in meta['cells_list']:
        gc = games.get(game_id('cand', c))
        gb = games.get(game_id('base' if 'base' in arms else 'cand', c))
        if gc and gb:
            pairs.append(dict(opp=c['opp'], map=c['map'], side=c['side'], cat=category(c['map']),
                              size=size_bucket(gc['area']),
                              d_score=100 * (gc['score'] - gb['score']), d_banked=gc['banked'] - gb['banked'],
                              d_deaths=gc['deaths'] - gb['deaths'], cand_score=gc['score'], base_score=gb['score']))
    rng = random.Random(SEED)

    def summarize(ps):
        by_map = {}
        for p in ps:
            by_map.setdefault(p['map'], []).append(p['d_score'])
        lo, hi = bootstrap(by_map, rng)
        n = len(ps)
        return dict(cells=n, maps=len(by_map), cand_winrate=round(100 * sum(p['cand_score'] for p in ps) / n, 2) if n else None,
                    base_winrate=round(100 * sum(p['base_score'] for p in ps) / n, 2) if n else None,
                    d_score=round(sum(p['d_score'] for p in ps) / n, 2) if n else None,
                    ci95=[round(lo, 2), round(hi, 2)] if lo is not None else None,
                    d_banked=round(sum(p['d_banked'] for p in ps) / n, 1) if n else None)

    def arm_totals(arm):
        gs = [g for g in games.values() if g['arm'] == arm]
        n = len(gs)
        return dict(played=n, wins=sum(g['score'] == 1 for g in gs), draws=sum(g['score'] == 0.5 for g in gs),
                    faults=sum(g['faults'] for g in gs), opp_faults=sum(g['opp_faults'] for g in gs),
                    fuel_outs=sum(g['fuel_outs'] for g in gs), trace_over=sum(g['trace_over'] for g in gs),
                    fuel_out_games=sum(g['fuel_outs'] > 0 for g in gs),
                    mean_banked=round(sum(g['banked'] for g in gs) / n, 1) if n else None,
                    mean_deaths=round(sum(g['deaths'] for g in gs) / n, 2) if n else None,
                    max_ordinary_fuel=max((g['fuel_max'] for g in gs), default=0))

    res = dict(name=a.name, reported=now(), cand=meta['cand'], base=meta['base'], maps=meta['maps'],
               sides=meta['sides'], fuel_quantum=meta['fuel_quantum'], label=meta.get('label', 'official fuel'),
               expected_games=meta['games'], played=len(games), missing=len(missing), failed=len(failed),
               bootstrap=dict(resamples=RESAMPLES, seed=SEED, cluster='map'),
               arms={arm: arm_totals(arm) for arm in arms}, paired=summarize(pairs),
               per_opp={o: summarize([p for p in pairs if p['opp'] == o]) for o in sorted({p['opp'] for p in pairs})},
               per_cat={k: summarize([p for p in pairs if p['cat'] == k]) for k in sorted({p['cat'] for p in pairs})},
               per_size={k: summarize([p for p in pairs if p['size'] == k]) for k in sorted({p['size'] for p in pairs})},
               failed_list=failed[:50], missing_list=missing[:50])
    if (out / 'done.json').exists():
        res['batch'] = json.loads((out / 'done.json').read_text(encoding='utf-8'))
        if res['batch'].get('seconds'):
            res['games_per_min'] = round(len(games) / (res['batch']['seconds'] / 60), 2)
    full = dict(res, games=list(games.values()), pairs=pairs)
    (out / 'results.json').write_text(json.dumps(full, indent=1), encoding='utf-8')
    (RESEARCH / 'runs').mkdir(parents=True, exist_ok=True)
    compact = dict(res, cells=[[p['opp'], p['map'], p['side'], p['cand_score'], p['base_score'], p['d_banked']]
                               for p in pairs])
    (RESEARCH / 'runs' / f'{a.name}.json').write_text(json.dumps(compact, indent=1), encoding='utf-8')
    print(f'{a.name}: expected {res["expected_games"]} played {res["played"]} missing {res["missing"]} failed {res["failed"]}')
    for arm, t in res['arms'].items():
        print(f'  {arm}: {json.dumps(t)}')
    print(f'  paired: {json.dumps(res["paired"])}')
    for o, s in res['per_opp'].items():
        print(f'  opp {o}: {json.dumps(s)}')
    for k, s in res['per_cat'].items():
        print(f'  cat {k}: {json.dumps(s)}')
    for k, s in res['per_size'].items():
        print(f'  size {k}: {json.dumps(s)}')
    if res.get('games_per_min'):
        print(f'  throughput: {res["games_per_min"]} games/min')


def cmd_list(_a):
    fz = load_frozen()
    for n, e in fz['bots'].items():
        print(n, e['wasm_sha256'][:16], e['defines'])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    f = sp.add_parser('freeze')
    f.add_argument('bot')
    f.add_argument('--src')
    f.add_argument('--alias')
    f.add_argument('--defines', help='comma list JD_X=1,JD_Y=2 prepended to jd_config.h')
    r = sp.add_parser('run')
    r.add_argument('--name', required=True)
    r.add_argument('--cand', required=True)
    r.add_argument('--base', required=True)
    r.add_argument('--opps', required=True)
    r.add_argument('--maps', required=True)
    r.add_argument('--limit', type=int, default=0)
    r.add_argument('--sides', default='AB', choices=['A', 'B', 'AB'])
    r.add_argument('--jobs', type=int, default=14)
    r.add_argument('--fuel-quantum', type=int, default=0, help='labelled diagnostics only')
    r.add_argument('--timeout', type=int, default=900)
    r.add_argument('--background', action='store_true')
    r.add_argument('--holdout', action='store_true', help='allow final-holdout maps/opponents (confirmation only)')
    rp = sp.add_parser('report')
    rp.add_argument('--name', required=True)
    sp.add_parser('list')
    b = sp.add_parser('_batch')
    b.add_argument('--name', required=True)
    b.add_argument('batch_cmd', nargs=argparse.REMAINDER)
    a = ap.parse_args()
    if a.cmd == 'run' and a.jobs > 14:
        raise SystemExit('jobs limit is 14 on this machine')
    {'freeze': cmd_freeze, 'run': cmd_run, 'report': cmd_report, 'list': cmd_list, '_batch': cmd_batch}[a.cmd](a)


if __name__ == '__main__':
    main()
