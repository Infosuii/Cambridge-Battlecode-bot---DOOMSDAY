"""Mimic parity check: the bot and the offline extractor must compute the same observation, memory and features.

  python tools/mimic/parity.py [--maps 00quadrants 01fracture ...] [--out artifacts/evaluations/mimic-parity/<run>]

Builds bots/mimic with MIMIC_PARITY 1 (each turn the bot prints hashes of its observation, its memory and every
candidate list with features; once, its map; and each distance field it builds), plays it against itself on each
map, then runs tools/mimic/extract.mjs --parity on the game's replay, restricted to the turns the bot observed, and
compares hash by hash. Decision hashes are compared once the bot has built all its fields (before that it uses
Chebyshev fallbacks on purpose). Writes <out>/parity.json and prints a summary; exits non-zero on any mismatch.
Shared-memory inputs come from the bot's actual read snapshots: a fuel-suspended turn may write later than an
ideal uninterrupted replay simulation. Every byte is retained; no observation mismatches are waived.
"""
import argparse
import collections
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine  # noqa: E402

DEFAULT_MAPS = ['00quadrants', '01fracture', '00monolith', '02arena', 'adgato_gemcombat1']


def build_parity(work, team):
    src = work / 'bot'
    if src.exists():
        shutil.rmtree(src)
    shutil.copytree(ROOT / 'bots/mimic/src', src / 'src', ignore=shutil.ignore_patterns('.cambc', 'compile_commands.json'),
                    copy_function=shutil.copyfile)
    common = src / 'src/common.h'
    text = common.read_bytes().decode('utf8')
    assert text.count('#define MIMIC_PARITY 0') == 1
    text = text.replace('#define MIMIC_PARITY 0', '#define MIMIC_PARITY 1')
    assert text.count('#define MIMIC_TEAM -1') == 1
    common.write_bytes(text.replace('#define MIMIC_TEAM -1', f'#define MIMIC_TEAM {team}').encode('utf8'))
    return engine.official_build(src, work / 'mimic-parity.wasm')


dumps = {}


def parse(out, team):
    maps, fields, turns = {}, {}, {}
    # The engine cuts a turn's output at its size limit, newline included: start every record on its own line.
    out = re.sub(r'(?<!\n)(MP(?:MAP|DMAP|FIELD|DOBS)? )', lambda m: '\n' + m.group(1), out)
    for line in out.splitlines():
        p = line.split()
        if not p:
            continue
        if p[0] == 'MPMAP':
            maps[int(p[1])] = (int(p[2]), [int(v) for v in p[3:7]])
        elif p[0] == 'MPDMAP':
            dumps[('map', int(p[1]))] = line.split(' ', 2)[2]
        elif p[0] == 'MPDOBS':
            dumps[('obs', int(p[1]), int(p[2]))] = line.split(' ', 3)[3]
        elif p[0] == 'MPFIELD':
            fields[(int(p[1]), int(p[2]))] = int(p[3])
        elif p[0] == 'MP':
            turns[(int(p[1]), int(p[2]))] = dict(obs=int(p[3]), mem=int(p[4]), dec=int(p[5]), built=int(p[6]), team=team,
                                                 parts=[int(v) for v in p[7:12]], shared=[int(v) for v in p[12:14]])
    return maps, fields, turns


def first_diff(a, b, width=160):
    a, b = a or '', b or ''
    i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
    lo = max(0, i - 40)
    return dict(at=i, bot=a[lo:lo + width], kernel=b[lo:lo + width])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--maps', nargs='+', default=DEFAULT_MAPS)
    ap.add_argument('--team', type=int, default=-1, help='team index, including recall-trick teams for regression checks')
    ap.add_argument('--out', default=str(ROOT / 'artifacts/evaluations/mimic-parity/latest'))
    a = ap.parse_args()
    work = Path(a.out).resolve()
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    wasm = build_parity(work, a.team)
    report = {}
    bad = 0
    for name in a.maps:
        mp = ROOT / 'maps/local-benchmarks' / (name.replace('_', '-') + '.map26a')
        folder = work / name
        engine.run_match(wasm, wasm, mp, folder, log_limit=64 << 20)
        bundle = engine.replay_bundle(folder)
        rdir = folder / 'replay'
        rdir.mkdir()
        with zipfile.ZipFile(bundle) as z:
            (rdir / 'game.repl26a').write_bytes(z.read('replay.repl26a'))
        maps, fields, turns = {}, {}, {}
        dumps.clear()
        for team, side in ((0, 'a'), (1, 'b')):
            m, f, t = parse(engine.team_stdout(folder, side), team)
            maps.update({k: (team, v) for k, v in m.items()})
            fields.update({k: (team, v) for k, v in f.items()})
            turns.update(t)
        observed = collections.defaultdict(list)
        for (r, c) in turns:
            observed[c].append(r)
        (folder / 'observed.json').write_text(json.dumps(observed), encoding='utf8')
        snapshots = {f'{r}:{c}': t['shared'] for (r, c), t in turns.items()}
        if not turns or any(len(v) != 2 for v in snapshots.values()):
            raise SystemExit('parity output missing complete shared-memory snapshots')
        (folder / 'shared.json').write_text(json.dumps(snapshots), encoding='utf8')
        (folder / 'index.json').write_text(json.dumps({'game': {'source': 'local', 'map': name}}), encoding='utf8')
        env = dict(os.environ, NFS_REPLAY_ENGINE='2.0.0')
        p = subprocess.run(['node', '--no-warnings', str(ROOT / 'tools/mimic/extract.mjs'), '--index', str(folder / 'index.json'),
                            '--replays', str(rdir), '--teams', str(ROOT / 'research/v59/duel_top1.json'), '--out',
                            str(folder / 'rows'), '--workers', '1', '--parity', str(folder / 'kernel.jsonl'),
                            '--observed', str(folder / 'observed.json'), '--shared-snapshots', str(folder / 'shared.json')],
                           capture_output=True, text=True, env=env)
        if p.returncode:
            raise SystemExit(p.stdout + p.stderr)
        k_maps, k_fields, k_turns, k_dumps = {}, {}, {}, {}
        for line in (folder / 'kernel.jsonl').read_text(encoding='utf8').splitlines():
            r = json.loads(line)
            if 'map' in r:
                k_maps[r['team']] = (r['map'], r['parts'])
                k_dumps[('map', r['team'])] = r['dump']
            elif 'field' in r:
                k_fields[(r['team'], r['field'])] = r['hash']
            else:
                k_turns[(r['round'], r['c'])] = r
                if r.get('dump'):
                    k_dumps[('obs', r['round'], r['c'])] = r['dump']
        res = collections.Counter()
        examples = []
        names_map = ['terrain', 'camps', 'groups', 'altars_spawn']
        for c, (team, (h, parts)) in maps.items():
            kh, kparts = k_maps.get(team, (None, [None] * 4))
            res['map_ok' if kh == h else 'map_bad'] += 1
            for i, nm in enumerate(names_map):
                if parts[i] != kparts[i]:
                    res['map_part_bad_' + nm] += 1
        for (c, which), (team, h) in fields.items():
            res['field_ok' if k_fields.get((team, which)) == h else 'field_bad'] += 1
        n_fields = {}
        for (team, which) in k_fields:
            n_fields[team] = n_fields.get(team, 0) + 1
        for key, t in sorted(turns.items()):
            k = k_turns.get(key)
            if not k:
                res['turn_missing'] += 1
                continue
            for part in ('obs', 'mem'):
                ok = k[part] == t[part]
                res[f'{part}_{"ok" if ok else "bad"}'] += 1
                if not ok and len(examples) < 8:
                    examples.append(dict(round=key[0], c=key[1], part=part))
            for i, nm in enumerate(['me', 'allies', 'enemies', 'camps', 'groups']):
                if k['parts'][i] != t['parts'][i]:
                    res['obs_part_bad_' + nm] += 1
            if t['built'] >= n_fields.get(t['team'], 0):
                ok = k['dec'] == t['dec']
                res[f'dec_{"ok" if ok else "bad"}'] += 1
                if not ok and len(examples) < 8:
                    examples.append(dict(round=key[0], c=key[1], part='dec'))
            else:
                res['dec_skipped_fields'] += 1
        # Readable differences: the first map pair and a few observation pairs that disagree.
        diffs = []
        for c, (team, _) in maps.items():
            mine, theirs = dumps.get(('map', c)), k_dumps.get(('map', team))
            if mine != theirs:
                diffs.append(dict(what='map', c=c, bot=first_diff(mine, theirs)))
                break
        for key, v in sorted(dumps.items(), key=lambda kv: str(kv[0])):
            if key[0] == 'obs' and k_dumps.get(key) != v and len(diffs) < 6:
                diffs.append(dict(what='obs', round=key[1], c=key[2], bot=first_diff(v, k_dumps.get(key))))
        (folder / 'diffs.json').write_text(json.dumps(diffs, indent=1), encoding='utf8')
        mismatches = sum(v for k, v in res.items() if k.endswith('_bad') or k == 'turn_missing')
        if not res['map_ok'] or not res['field_ok'] or not res['obs_ok'] or not res['dec_ok']:
            mismatches += 1
            res['coverage_bad'] += 1
        bad += mismatches
        report[name] = dict(counts=dict(res), examples=examples)
        print(name, dict(res), examples[:3], flush=True)
    (work / 'parity.json').write_text(json.dumps(report, indent=1) + '\n', encoding='utf8', newline='\n')
    print('PARITY', 'OK' if bad == 0 else f'FAILED ({bad} mismatches)')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
