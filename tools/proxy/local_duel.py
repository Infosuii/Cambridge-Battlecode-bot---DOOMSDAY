"""Proxy opponent, step 3: the ladder duel's schedule played locally against a proxy instead of the real top teams.

  python tools/proxy/local_duel.py --plan research/v59/duel_top1.json --bot bots/v65 --name v65
         --proxy bots/proxy [--per-team] | --proxy-map research/proxy/opponents.json  [--seeds 1 2] [--workers 12]
         --out artifacts/evaluations/proxy-duel/<run>

Every (group, slot) of the plan is one game on the same map with our bot on the same side as on the ladder; the
opponent is one proxy bot; with --per-team, that bot built once per top team with PROXY_TEAM set to the team's row in
its proxy_tables.h (its drafts and items); or any bot per team (--proxy-map: {"team name": "bots/<dir>", ...}). Several seeds
replay the whole schedule with different NOVA_SEED values in both bots, to average over the bots' own randomness.

Output: <out>/games.json (one row per game, the same fields as research/proxy/ladder_arms.json), and with --replays
the unpacked replays and an index for tools/proxy/fight_style.mjs and style_report.py (<out>/replays/index.json).
Builds are cached by the content of the seeded source tree and the CLI under artifacts/tmp/wasm-cache/proxy.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine  # noqa: E402

MAPS = ROOT / 'maps/local-benchmarks'  # byte-identical to the current platform pool (checked 2026-10-27)
CACHE = ROOT / 'artifacts/tmp/wasm-cache/proxy'


def map_path(name):
    p = MAPS / (name.replace('_', '-') + '.map26a')
    if not p.is_file():
        raise SystemExit('no local copy of ' + name)
    return p


def proxy_team_index(bot_dir, name):
    """PROXY_TEAM for a team: its row in the bot's proxy_tables.h, minus one (row 0 is the pooled table)."""
    text = (Path(bot_dir) / 'src/proxy_tables.h').read_text(encoding='utf8')
    body = text[text.index('kTeams['):]
    names = re.findall(r'^    \{"([^"]*)",', body, re.M)
    if name not in names:
        raise SystemExit(f'{name} has no row in {bot_dir}/src/proxy_tables.h')
    return names.index(name) - 1


def build(bot_dir, seed, work, label, defines=None):
    """The bot with NOVA_SEED set to `seed` (and any other `#define NAME value` lines replaced), built once per distinct
    source tree, copied to <work>/<label>-s<seed>.wasm. Short names matter: the engine names each replay after both
    wasm files, and Windows paths stop at 260 characters."""
    src = Path(bot_dir).resolve() / 'src'
    tmp = work / f'src-{label}-s{seed}'
    shutil.copytree(src, tmp / 'src', ignore=shutil.ignore_patterns('.cambc', 'compile_commands.json'),
                    copy_function=shutil.copyfile)  # sources may be read-only; the copy must not be
    common = tmp / 'src/common.h'
    text = common.read_bytes().decode('utf-8')  # bytes: the file keeps its own line ends
    lines = text.splitlines(keepends=True)
    hits = [i for i, l in enumerate(lines) if l.rstrip('\r\n') == '#define NOVA_SEED 1']
    if len(hits) != 1:
        raise SystemExit(f'{bot_dir}: expected one "#define NOVA_SEED 1" line')
    lines[hits[0]] = lines[hits[0]].replace('NOVA_SEED 1', f'NOVA_SEED {seed}')
    for name, value in (defines or {}).items():
        at = [i for i, l in enumerate(lines) if re.match(rf'#define {name}\b', l)]
        if len(at) != 1:
            raise SystemExit(f'{bot_dir}: expected one "#define {name}" line')
        end = '\r\n' if lines[at[0]].endswith('\r\n') else '\n'
        lines[at[0]] = f'#define {name} {value}{end}'
    common.write_bytes(''.join(lines).encode('utf-8'))
    h = hashlib.sha256((ROOT / 'tools/vendor/cambc.exe').read_bytes())
    for p in sorted((tmp / 'src').iterdir()):
        if p.is_file():
            h.update(p.name.encode() + b'\0' + p.read_bytes())
    key = h.hexdigest()
    cached = CACHE / f'{key}.wasm'
    if not cached.is_file():
        CACHE.mkdir(parents=True, exist_ok=True)
        out = engine.official_build(tmp, work / f'{key}.wasm')
        shutil.copyfile(out, cached.with_suffix('.tmp'))
        cached.with_suffix('.tmp').replace(cached)
    local = work / f'{label}-s{seed}.wasm'  # the seeded tree also stays under <out>/build
    shutil.copyfile(cached, local)
    return local


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--plan', required=True)
    ap.add_argument('--bot', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--proxy')
    ap.add_argument('--proxy-map')
    ap.add_argument('--per-team', action='store_true')
    ap.add_argument('--seeds', type=int, nargs='+', default=[1])
    ap.add_argument('--workers', type=int, default=12)
    ap.add_argument('--replays', action='store_true')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    if bool(a.proxy) == bool(a.proxy_map):
        raise SystemExit('give exactly one of --proxy and --proxy-map')
    out = Path(a.out).resolve()
    if not out.is_relative_to(ROOT / 'artifacts') or out.exists():
        raise SystemExit('fresh output directory inside artifacts/ required')
    out.mkdir(parents=True)
    plan = json.loads(Path(a.plan).read_text(encoding='utf8'))
    opp_of = json.loads(Path(a.proxy_map).read_text(encoding='utf8')) if a.proxy_map else {}
    teams = sorted({g['opponent'] for g in plan['groups']})
    opp_dir = {t: (ROOT / opp_of[t]) if a.proxy_map else Path(a.proxy).resolve() for t in teams}
    # One opponent build per distinct (bot dir, defines): with --per-team, the proxy for each team.
    opp_key = {t: (str(opp_dir[t]), proxy_team_index(opp_dir[t], t) if a.per_team else None) for t in teams}
    work = out / 'build'
    work.mkdir()
    wasm = {}
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        futs = {}
        for s in a.seeds:
            futs[ex.submit(build, a.bot, s, work, 'bot')] = ('bot', s)
            for i, key in enumerate(sorted(set(opp_key.values()), key=str)):
                defines = {} if key[1] is None else {'PROXY_TEAM': key[1]}
                futs[ex.submit(build, key[0], s, work, f'p{i}', defines)] = (key, s)
        for f in cf.as_completed(futs):
            wasm[futs[f]] = f.result()
    jobs = []
    for s in a.seeds:
        for gi, g in enumerate(plan['groups']):
            for k, (m, side) in enumerate(zip(g['maps'], g['sides'])):
                ours, theirs = wasm[('bot', s)], wasm[(opp_key[g['opponent']], s)]
                team_k = opp_key[g['opponent']][1]
                jobs.append(dict(seed=s, group=gi, slot=k + 1, map=m, side=side, opponent=g['opponent'],
                                 proxy=opp_dir[g['opponent']].name + ('' if team_k is None else f'#{team_k}'),
                                 A=ours if side == 'a' else theirs,
                                 B=theirs if side == 'a' else ours, folder=out / 'games' / f's{s}-g{gi:02d}-{k + 1}'))

    def play(j):
        r = engine.run_match(j['A'], j['B'], map_path(j['map']), j['folder'], candidate_side=j['side'].upper())
        return j, r.row()

    rows = []
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        for f in cf.as_completed([ex.submit(play, j) for j in jobs]):
            j, r = f.result()
            rows.append(dict(arm=a.name, seed=j['seed'], group=j['group'], slot=j['slot'], map=j['map'], side=j['side'],
                             opponent=j['opponent'], proxy=j['proxy'], win=r['win'] == 1.0, draw=r['win'] == 0.5,
                             margin=r['gems'] - r['opponent_gems'], deaths=r['deaths'], gold=r['gold'],
                             faults=r['faults'], fuel=r['fuel_exhausted'], opp_fuel=r['opponent_fuel_exhausted'],
                             folder=str(Path(j['folder']).relative_to(ROOT).as_posix())))
            if len(rows) % 40 == 0:
                print('games', len(rows), '/', len(jobs), flush=True)
    rows.sort(key=lambda r: (r['seed'], r['group'], r['slot']))
    meta = dict(plan=a.plan, bot=a.bot, name=a.name, proxy=a.proxy, per_team=a.per_team, proxy_map=opp_of, seeds=a.seeds)
    (out / 'games.json').write_text(json.dumps(dict(meta, games=rows), indent=1) + '\n', encoding='utf8', newline='\n')
    if a.replays:
        rdir = out / 'replays'
        rdir.mkdir()
        index = {}
        for r in rows:
            bundle = engine.replay_bundle(ROOT / r['folder'])
            mid = Path(r['folder']).name
            with zipfile.ZipFile(bundle) as z:
                (rdir / f'{mid}.repl26a').write_bytes(z.read('replay.repl26a'))
            us, them = a.name, 'proxy:' + r['proxy']
            index[mid] = dict(source='local', map=r['map'], bots=dict(a=us if r['side'] == 'a' else them,
                                                                       b=them if r['side'] == 'a' else us))
        (rdir / 'index.json').write_text(json.dumps(index, indent=1), encoding='utf8', newline='\n')
    n = len(rows)
    print(f"{a.name}: {n} games, {sum(r['win'] for r in rows)} wins, {sum(r['draw'] for r in rows)} draws, "
          f"margin {sum(r['margin'] for r in rows) / max(1, n):+.1f}, faults {sum(r['faults'] for r in rows)}, "
          f"fuel-outs {sum(r['fuel'] for r in rows)} (proxy {sum(r['opp_fuel'] for r in rows)})")


if __name__ == '__main__':
    main()
