"""Ladder duel: play two of our submitted versions on identical unranked match groups, back to back, and compare.

Match groups always play the active submission, so each arm activates its version, queues every group of the plan,
waits until all of them have finished, and only then hands over to the next arm. Both arms meet the same opponents
on the same maps and sides within the same hour, so the comparison is paired game by game.

  python tools/replay/ladder_duel.py plan --out P.json --opponents <name> ... --groups-per-opponent 2 [--seed 1]
  python tools/replay/ladder_duel.py run --plan P.json --version 58 --arm v59     # activates 58, queues, waits
  python tools/replay/ladder_duel.py report --plan P.json [--arms v59 v61] [--margins]   # margins: downloads summaries
  python tools/replay/ladder_duel.py restore --version 58                        # leave a chosen version active

The quota is 50 groups per rolling hour (`cambc match-groups quota`). Queueing and activation were approved by the
user for testing (2026-10-26).
"""
import argparse
from collections import defaultdict
import glob
import json
import math
from pathlib import Path
import random
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'tools/vendor/cambc.exe'


def cli(args, timeout=180):
    for attempt in range(8):
        r = subprocess.run([str(CLI)] + args, capture_output=True, text=True, encoding='utf8', errors='replace', timeout=timeout)
        if 'Rate limit' not in (r.stdout + r.stderr):
            return r
        time.sleep(3 + 2 * attempt)
    return r


def team_ids():
    ids = {}
    for path in glob.glob(str(ROOT / 'data/ladder/duel/ladder_20261103_p*.json')) + glob.glob(str(ROOT / 'data/ladder/ladder_20261026_p*.json')):
        for t in json.load(open(path, encoding='utf8'))['teams']:
            ids.setdefault(t['name'], t['teamId'])
    return ids


def pool_maps():
    d = cli_json(['match-groups', 'quota', '--json'])
    return [m['name'] for m in d['maps']]


def cli_json(args):
    for attempt in range(10):
        r = cli(args)
        try:
            return json.loads(r.stdout)
        except ValueError:
            time.sleep(5 + 3 * attempt)  # throttled or transient: the CLI sometimes returns an empty body
    raise SystemExit('no JSON from cambc ' + ' '.join(args) + ': ' + (r.stdout + r.stderr)[-300:])


def wait_for_quota():
    # Team lock caps this worker at 45 groups in the platform's rolling hour.
    # Reading the shared count also avoids spending another worker's headroom.
    for _ in range(180):
        if cli_json(['match-groups', 'quota', '--json'])['quota']['used'] < 45:
            return
        time.sleep(30)
    raise SystemExit('rolling match-group budget did not clear')


def pinned_version():
    state = cli_json(['submissions', 'list', '--json'])
    active = (state.get('active') or {}).get('version')
    selected = (state.get('selected') or {}).get('version')
    if state.get('pinned') is True and active == selected:
        return active
    return None


def activate(version):
    if pinned_version() == version:
        return
    r = cli(['submissions', 'activate', str(version)])
    print('activate', version, 'exit', r.returncode, flush=True)
    for _ in range(60):
        if pinned_version() == version:
            return
        time.sleep(10)
    raise SystemExit(f'version {version} did not become active and pinned')


def finished_groups(group_ids, previous=None):
    """Read the requested groups by ID; retain completed groups across polls."""
    by = {}
    for gid in sorted(group_ids):
        cached = (previous or {}).get(gid, [])
        if len(cached) == 5 and all(m['status'] == 'finished' for m in cached):
            by[gid] = cached
            continue
        d = cli_json(['match-groups', 'show', gid, '--json'])
        if d.get('groupId') != gid or d.get('nextCursor'):
            raise SystemExit(f'unexpected match group response for {gid}')
        matches = d['matches']
        if any(m['groupId'] != gid for m in matches):
            raise SystemExit(f'match from a different group in response for {gid}')
        by[gid] = matches
    return by


def required_pin_sources(plan, arm):
    pin_arm = plan.get('pin_arm', 'v92')
    size = len(plan['groups'])
    if arm == pin_arm:
        return [None] * size
    ids = plan['arms'].get(pin_arm, {}).get('groups', [])
    if len(ids) != size or not all(isinstance(gid, str) and gid for gid in ids) or len(set(ids)) != size:
        raise SystemExit(f'{arm}: complete unique pin sources from {pin_arm} required before activation')
    return ids


def gem_margin(match_id, side):
    # Submitted-gem margin from the native summary, cached local-only.
    cache = ROOT / 'artifacts/local-only/duels' / f'{match_id}.json'
    cache.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(4):
        if not cache.exists() or cache.stat().st_size == 0:
            cli(['matches', 'summary', match_id, '--json', '--output', str(cache)])
        try:
            teams = {t['team']: float(t['submittedGems']) for t in json.loads(cache.read_text(encoding='utf8'))['teams']}
            us = 'team' + side.upper()
            return teams[us] - teams['teamB' if us == 'teamA' else 'teamA']
        except (OSError, ValueError, KeyError):
            cache.unlink(missing_ok=True)
            time.sleep(5)
    return None


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('action', choices=['plan', 'run', 'report', 'restore'])
    ap.add_argument('--plan')
    ap.add_argument('--out')
    ap.add_argument('--opponents', nargs='+')
    ap.add_argument('--groups-per-opponent', type=int, default=2)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--version', type=int)
    ap.add_argument('--arm')
    ap.add_argument('--arms', nargs='+')
    ap.add_argument('--margins', action='store_true', help='also compare submitted-gem margins (downloads each summary once)')
    a = ap.parse_args()

    if a.action == 'restore':
        activate(a.version)
        print('active and pinned', pinned_version())
        return

    if a.action == 'plan':
        ids = team_ids()
        maps = pool_maps()
        rng = random.Random(a.seed)
        groups = []
        for name in a.opponents:
            if name not in ids:
                raise SystemExit('unknown team ' + name)
            for k in range(a.groups_per_opponent):
                chosen = rng.sample(maps, 5)
                sides = ['a', 'b', 'a', 'b', 'a'] if k % 2 == 0 else ['b', 'a', 'b', 'a', 'b']
                groups.append(dict(opponent=name, opponentId=ids[name], maps=chosen, sides=sides))
        Path(a.out).write_text(json.dumps(dict(groups=groups, arms={}), indent=1) + '\n', encoding='utf8')
        print(len(groups), 'groups ->', a.out)
        return

    plan = json.loads(Path(a.plan).read_text(encoding='utf8'))
    if a.action == 'run':
        pin_sources = required_pin_sources(plan, a.arm)
        activate(a.version)
        since = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - 60))
        ids = []
        for i, g in enumerate(plan['groups']):
            gid = None
            for attempt in range(6):
                # Pin the opponent's bot to the one it ran in the base arm's group (--source-group): an active team can
                # upload a new version between arms, which would break the pairing.
                pin = ['--source-group', pin_sources[i]] if pin_sources[i] else []
                wait_for_quota()
                r = cli(['match-groups', 'create', g['opponentId'], '--maps', ','.join(g['maps']), '--sides', ','.join(g['sides']), '--json'] + pin)
                try:
                    gid = json.loads((r.stdout or '').strip().splitlines()[0])['groupId']
                    break
                except (ValueError, IndexError, KeyError):
                    text = r.stdout + r.stderr
                    wait = re.search(r'retry after (\d+) seconds', text)
                    if wait:  # rolling 50-groups-per-hour quota: wait it out and try the same group again
                        print(f'quota: waiting {wait.group(1)} s before {g["opponent"]}', flush=True)
                        time.sleep(int(wait.group(1)) + 5)
                        continue
                    print('queue failed for', g['opponent'], text[-300:], flush=True)
                    break
            ids.append(gid)
        plan['arms'][a.arm] = dict(version=a.version, groups=ids, since=since)
        Path(a.plan).write_text(json.dumps(plan, indent=1) + '\n', encoding='utf8')
        want = {g for g in ids if g}
        print(f'arm {a.arm}: queued {len(want)} groups; waiting for them to finish', flush=True)
        by = {}
        for _ in range(240):
            by = finished_groups(want, by)
            done = sum(1 for gid in want if len(by.get(gid, [])) == 5 and all(m['status'] == 'finished' for m in by[gid]))
            if done == len(want):
                break
            time.sleep(30)
        print(f'arm {a.arm}: {done}/{len(want)} groups finished', flush=True)
        if done != len(plan['groups']):
            raise SystemExit(f'arm {a.arm} incomplete: {done}/{len(plan["groups"])} groups finished')
        return

    # report
    arms = a.arms or list(plan['arms'])
    results, margins = {}, {}
    for arm in arms:
        info = plan['arms'][arm]
        want = {g for g in info['groups'] if g}
        by = finished_groups(want)
        res = {}
        for i, gid in enumerate(info['groups']):
            for m in by.get(gid, []):
                if m['status'] != 'finished':
                    continue
                us = next(t for t in m['teams'] if t['name'] == 'DOOMSDAY')
                res[(i, m['position'])] = us['result'] == 'win'
                if a.margins:
                    margins.setdefault(arm, {})[(i, m['position'])] = gem_margin(m['matchId'], us['side'])
        results[arm] = res
    for arm in arms:
        r = results[arm]
        print(f'{arm:10} version {plan["arms"][arm]["version"]}: {sum(r.values())}/{len(r)} = {sum(r.values()) / max(1, len(r)):.3f}')
    if len(arms) == 2:
        x, y = (results[arms[0]], results[arms[1]])
        keys = sorted(set(x) & set(y))
        only_x = sum(1 for k in keys if x[k] and not y[k])
        only_y = sum(1 for k in keys if y[k] and not x[k])
        n = only_x + only_y
        z = (only_y - only_x) / math.sqrt(n) if n else 0.0
        print(f'paired games {len(keys)}: {arms[0]} only {only_x}, {arms[1]} only {only_y}; sign-test z = {z:+.2f} (positive favours {arms[1]})')
        per = defaultdict(lambda: [0, 0, 0])
        for k in keys:
            opp = plan['groups'][k[0]]['opponent']
            per[opp][0] += x[k]
            per[opp][1] += y[k]
            per[opp][2] += 1
        for opp, (wx, wy, n2) in sorted(per.items()):
            print(f'  {opp[:22]:22} {arms[0]} {wx}/{n2}  {arms[1]} {wy}/{n2}')
        if a.margins:
            mx, my = margins.get(arms[0], {}), margins.get(arms[1], {})
            both = [k for k in keys if mx.get(k) is not None and my.get(k) is not None]
            diffs = [my[k] - mx[k] for k in both]
            if diffs:
                mean = sum(diffs) / len(diffs)
                sd = math.sqrt(sum((d - mean) ** 2 for d in diffs) / max(1, len(diffs) - 1))
                print(f'gem margin: {arms[0]} {sum(mx[k] for k in both) / len(both):+.1f}, {arms[1]} {sum(my[k] for k in both) / len(both):+.1f}; '
                      f'paired difference {mean:+.1f} +/- {sd / math.sqrt(len(diffs)):.1f} over {len(diffs)} games')


if __name__ == '__main__':
    main()
