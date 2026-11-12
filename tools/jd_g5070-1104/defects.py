"""FEAT-004 defect trace: per champion-turn contact and movement defects from engine-2.0.0 replays of a jdrun run.

  py tools/jd_g5070-1104/defects.py extract --run base-v92-dev-01 [--arm cand] [--jobs 10]
  py tools/jd_g5070-1104/defects.py report --run base-v92-dev-01 [--arm cand] [--md research/jd-g5070-1104/DEFECTS.md]
  py tools/jd_g5070-1104/defects.py compare --base RUN[:arm] --cand RUN[:arm]   (same cells, metric deltas)

extract unpacks each game's inner replay and runs defects.mjs (official replay engine 2.0.0, pinned assets) in
parallel; the per-game rows go to <eval>/runs/<run>/defects_<arm>.jsonl. report aggregates OUR side (the arm's bot)
and the OPPONENT side of the same games, overall, by result, opponent and map size. All analysis is offline and
omniscient; nothing here is a bot input.

Defects (per champion, our side unless 'opp'):
  kill deaths         deaths with an enemy champion within 5 tiles the round before (others: camp/other deaths)
  no hit back         kill deaths with no basic attack on a champion in the last 5 alive rounds
  flee deaths         kill deaths whose last >= 1 alive rounds were retreat moves (distance to the nearest enemy grew)
  late flee           flee deaths whose flee started with the nearest enemy already within 2 tiles
  retreat w/o hit     contact rounds with a retreat move, an enemy within the mover's basic-attack reach (melee 1,
                      ranged: largest attack distance observed for that type) and no basic attack that round
  outnumbered         contact rounds (enemy within 4) with more enemies than allies (incl. self) within 5
  no-progress         out-of-contact rounds inside 8-round windows with >= 4 moves and net displacement <= 2
  oscillation         out-of-contact rounds whose position equals the one two rounds earlier (A-B-A)
  idle                out-of-contact runs of >= 10 rounds without moving or acting, away from spawn and camps
"""
import argparse, collections, json, os, re, subprocess, sys, tempfile, zipfile, shutil, math, random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jdrun  # noqa: E402

HERE = Path(__file__).resolve().parent
MJS = HERE / 'defects.mjs'
MELEE = {0, 2, 4, 7, 9, 10, 12}
TYPES = ['ryth', 'vesper', 'vendetta', 'cassi', 'issac', 'stellar', 'prism', 'marcella', 'willow', 'ren', 'varg', 'tavi', 'heart']


def run_games(run, arm):
    out = jdrun.EVAL / 'runs' / run
    res = json.loads((out / 'results.json').read_text(encoding='utf-8'))
    for g in res['games']:
        if g['arm'] != arm:
            continue
        gid = jdrun.game_id(arm, g)
        rp = out / 'games' / f'{gid}.repl26a'
        if rp.exists():
            yield gid, g, rp


def cmd_extract(a):
    out = jdrun.EVAL / 'runs' / a.run
    dst = out / f'defects_{a.arm}.jsonl'
    games = list(run_games(a.run, a.arm))
    tmp = Path(tempfile.mkdtemp(prefix='jddef_', dir=str(jdrun.EVAL)))
    try:
        inner = []
        for gid, g, rp in games:
            p = tmp / f'{gid}.repl26a'
            with zipfile.ZipFile(rp) as z:
                p.write_bytes(z.read('replay.repl26a'))
            inner.append(p)
        chunks = [inner[i::a.jobs] for i in range(a.jobs)]
        env = dict(os.environ, NFS_REPLAY_ENGINE='2.0.0')

        def work(i):
            if not chunks[i]:
                return ''
            o = tmp / f'part{i}.jsonl'
            r = subprocess.run(['node', '--disable-warning=MODULE_TYPELESS_PACKAGE_JSON', str(MJS), str(o)] + [str(x) for x in chunks[i]],
                               capture_output=True, text=True, env=env)
            if r.returncode:
                raise RuntimeError(r.stderr[-2000:])
            return o.read_text(encoding='utf-8')
        with ThreadPoolExecutor(a.jobs) as ex:
            parts = list(ex.map(work, range(a.jobs)))
        rows = [ln for p in parts for ln in p.splitlines() if ln.strip()]
        dst.write_text('\n'.join(rows) + '\n', encoding='utf-8')
        print(json.dumps(dict(run=a.run, arm=a.arm, games=len(games), rows=len(rows), out=str(dst))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def load(run, arm):
    out = jdrun.EVAL / 'runs' / run
    meta = {gid: g for gid, g, _ in run_games(run, arm)}
    rows = {}
    for ln in (out / f'defects_{arm}.jsonl').read_text(encoding='utf-8').splitlines():
        if ln.strip():
            d = json.loads(ln)
            rows[d['id']] = d
    return meta, rows


def reach_table(rows):
    rng = collections.Counter()
    for d in rows.values():
        for t, v in d['atk_dist'].items():
            rng[int(t)] = max(rng[int(t)], v)
    return {t: (1 if t in MELEE else max(rng.get(t, 3), 2)) for t in range(13)}


def team_metrics(t, reach):
    deaths = t['deaths']
    kill = [x for x in deaths if x['enemies'] > 0 or x['pvp'] > 0 or x['nd'] <= 5]
    flee = [x for x in kill if x['flee_len'] >= 1]
    m = dict(
        deaths=len(deaths), kill_deaths=len(kill), other_deaths=len(deaths) - len(kill),
        no_hit_back=sum(1 for x in kill if x['pvp'] == 0),
        flee_deaths=len(flee), late_flee=sum(1 for x in flee if x['flee_nd'] is not None and x['flee_nd'] <= 2),
        outn_deaths=sum(1 for x in kill if x['outn']), lone_deaths=sum(1 for x in kill if x['allies'] == 0),
        carrier_deaths=sum(1 for x in kill if x['gems'] >= 25),
        gems_lost=sum(x['gems'] for x in deaths), kill_gems_lost=sum(x['gems'] for x in kill),
        dead_rounds=sum(x['dead_rounds'] or 0 for x in deaths),
        nohit_gems=sum(x['gems'] for x in kill if x['pvp'] == 0), nohit_dead_rounds=sum(x['dead_rounds'] or 0 for x in kill if x['pvp'] == 0),
        contact_rounds=t['contact_rounds'], outn_rounds=t['outn_rounds'], outn2_rounds=t['outn2_rounds'],
        noprog_rounds=t['noprog_rounds'], noprog_runs=t['noprog_runs'], osc_rounds=t['osc_rounds'],
        idle_rounds=t['idle_rounds'], idle_runs=t['idle_runs'], idle_camp_rounds=t['idle_camp_rounds'],
        quiet_rounds=t['quiet_rounds'], alive_rounds=t['alive_rounds'])
    rw = rwh = rwm = rwr = retreats = 0
    for k, n in t['contact'].items():
        typ, nd, ret, pvp, cast = (int(v) for v in k.split('|'))
        if ret != 1:
            continue
        retreats += n
        if nd <= reach[typ] and not pvp:
            rw += n
            if typ in MELEE:
                rwm += n
            else:
                rwr += n
        if nd <= reach[typ] and pvp:
            rwh += n
    m.update(retreat_rounds=retreats, retreat_nohit=rw, retreat_nohit_melee=rwm, retreat_nohit_ranged=rwr, retreat_hit=rwh)
    return m


def aggregate(meta, rows, reach, filt=lambda g: True):
    us, them = collections.Counter(), collections.Counter()
    n = 0
    for gid, g in meta.items():
        d = rows.get(gid)
        if d is None or not filt(g):
            continue
        n += 1
        mine = '0' if g['side'] == 'A' else '1'
        other = '1' if mine == '0' else '0'
        us.update(team_metrics(d['teams'][mine], reach))
        them.update(team_metrics(d['teams'][other], reach))
    return n, us, them


def per_game(n, c, k):
    return round(c[k] / n, 2) if n else None


def share(c, k, base):
    return f"{100 * c[k] / c[base]:.0f}%" if c[base] else '-'


KEYS = [('kill deaths', 'kill_deaths'), ('  no hit back', 'no_hit_back'), ('  flee deaths', 'flee_deaths'),
        ('  late flee (enemy <= 2 at flee start)', 'late_flee'), ('  outnumbered in last 5 rounds', 'outn_deaths'),
        ('  no ally within 5', 'lone_deaths'), ('  carrier (>= 25 gems)', 'carrier_deaths'), ('other deaths (camps)', 'other_deaths'),
        ('gems lost on death', 'gems_lost'), ('  of which no-hit-back deaths', 'nohit_gems'), ('rounds dead', 'dead_rounds'),
        ('  of which no-hit-back deaths', 'nohit_dead_rounds'),
        ('contact rounds (enemy <= 4)', 'contact_rounds'), ('  outnumbered rounds', 'outn_rounds'), ('  outnumbered by >= 2', 'outn2_rounds'),
        ('retreat moves in contact (enemy <= 5)', 'retreat_rounds'), ('  in reach, no basic attack', 'retreat_nohit'),
        ('    melee', 'retreat_nohit_melee'), ('    ranged', 'retreat_nohit_ranged'), ('  in reach, with a basic attack', 'retreat_hit'),
        ('out-of-contact rounds', 'quiet_rounds'), ('  no-progress rounds', 'noprog_rounds'), ('  no-progress runs', 'noprog_runs'),
        ('  A-B-A oscillation rounds', 'osc_rounds'), ('  idle rounds (>= 10, away from spawn/camps)', 'idle_rounds'),
        ('  idle rounds at a camp', 'idle_camp_rounds')]


def table(title, groups):
    """groups: list of (label, n, us, them)."""
    out = [f'### {title}', '', '| metric (per game) | ' + ' | '.join(f'{l} us | {l} opp' for l, *_ in groups) + ' |',
           '|---|' + '---:|---:|' * len(groups)]
    for lab, k in KEYS:
        cells = []
        for _, n, us, them in groups:
            cells += [str(per_game(n, us, k)), str(per_game(n, them, k))]
        out.append(f'| {lab} | ' + ' | '.join(cells) + ' |')
    out.append('| games | ' + ' | '.join(f'{n} | {n}' for _, n, *_ in groups) + ' |')
    return '\n'.join(out)


def cmd_report(a):
    meta, rows = load(a.run, a.arm)
    reach = reach_table(rows)
    res = {}
    groups = []
    for lab, f in (('all', lambda g: True), ('losses', lambda g: g['score'] == 0), ('wins', lambda g: g['score'] == 1)):
        n, us, them = aggregate(meta, rows, reach, f)
        groups.append((lab, n, us, them))
        res[lab] = dict(n=n, us=dict(us), opp=dict(them))
    opp_groups = []
    for o in sorted({g['opp'] for g in meta.values()}):
        n, us, them = aggregate(meta, rows, reach, lambda g, o=o: g['opp'] == o and g['score'] == 0)
        opp_groups.append((o.split('-')[0] + ' L', n, us, them))
        res[f'losses_{o}'] = dict(n=n, us=dict(us), opp=dict(them))
    size_groups = []
    for s in ('small', 'medium', 'large'):
        n, us, them = aggregate(meta, rows, reach, lambda g, s=s: jdrun.size_bucket(g['area']) == s and g['score'] == 0)
        size_groups.append((s + ' L', n, us, them))
        res[f'losses_{s}'] = dict(n=n, us=dict(us), opp=dict(them))
    out = jdrun.EVAL / 'runs' / a.run / f'defects_{a.arm}_summary.json'
    out.write_text(json.dumps(dict(run=a.run, arm=a.arm, reach={TYPES[t]: r for t, r in reach.items()}, groups=res), indent=1), encoding='utf-8')
    md = [table(f'{a.run} ({a.arm}): all games, losses, wins', groups), '',
          table(f'{a.run} ({a.arm}): losses by opponent', [g for g in opp_groups if g[1]]), '',
          table(f'{a.run} ({a.arm}): losses by map size', [g for g in size_groups if g[1]])]
    text = '\n'.join(md)
    print(text)
    print('reach', {TYPES[t]: r for t, r in reach.items()})
    if a.md:
        Path(a.md).write_text(text + '\n', encoding='utf-8')


def cmd_compare(a):
    def parse(s):
        r, _, arm = s.partition(':')
        return r, arm or 'cand'
    (rb, ab), (rc, ac) = parse(a.base), parse(a.cand)
    mb, rowsb = load(rb, ab)
    mc, rowsc = load(rc, ac)
    reach = reach_table(rowsb)
    keyb = {(g['opp'], g['map'], g['side']): gid for gid, g in mb.items() if gid in rowsb}
    keyc = {(g['opp'], g['map'], g['side']): gid for gid, g in mc.items() if gid in rowsc}
    common = sorted(set(keyb) & set(keyc))
    tb, tc = collections.Counter(), collections.Counter()
    for k in common:
        gb, gc = mb[keyb[k]], mc[keyc[k]]
        tb.update(team_metrics(rowsb[keyb[k]]['teams']['0' if gb['side'] == 'A' else '1'], reach))
        tc.update(team_metrics(rowsc[keyc[k]]['teams']['0' if gc['side'] == 'A' else '1'], reach))
    n = len(common)
    print(f'matched cells {n}: {rb}:{ab} -> {rc}:{ac} (per game, our side)')
    res = {}
    for lab, k in KEYS:
        b, c = per_game(n, tb, k), per_game(n, tc, k)
        res[k] = dict(base=b, cand=c)
        print(f'  {lab:45s} {b!s:>8} -> {c!s:>8}')
    if a.out:
        Path(a.out).write_text(json.dumps(dict(base=a.base, cand=a.cand, cells=n, metrics=res), indent=1), encoding='utf-8')


NOTE = re.compile(r'R(\d+) (\S+) p\((-?\d+),(-?\d+)\) hp(-?\d+)/(\d+) g(\d+) mode=(\S+) G(-?\d+) enemies=(\d+) near=(\d+) ehp=(\d+) allies4=(\d+) spawn=(\d+)')


def cmd_deathlog(a):
    """Bot-side context of each death from an APEX_DEATHLOG=1 build: the mode of the last noted turns (legal data)."""
    import fuelbench
    out = jdrun.EVAL / 'runs' / a.run
    res = json.loads((out / 'results.json').read_text(encoding='utf-8'))
    by = collections.defaultdict(collections.Counter)
    rows = []
    for g in res['games']:
        gid = jdrun.game_id(g['arm'], g)
        rp = out / 'games' / f'{gid}.repl26a'
        if g['arm'] != a.arm or not rp.exists():
            continue
        lines = fuelbench.stdout_lines(rp, g['side'])
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln.startswith('DEATH R') and ' at(' not in ln:
                notes = []
                j = i + 1
                while j < len(lines) and NOTE.match(lines[j]):
                    m = NOTE.match(lines[j]).groups()
                    notes.append(dict(r=int(m[0]), hp=int(m[4]), max=int(m[5]), g=int(m[6]), mode=m[7], G=int(m[8]), en=int(m[9]),
                                      near=int(m[10]), allies=int(m[12]), spawn=int(m[13])))
                    j += 1
                if notes:
                    last = notes[-1]
                    rows.append(dict(game=gid, loss=g['score'] == 0, type=ln.split()[2], gems=last['g'], mode=last['mode'],
                                     seq='>'.join(n['mode'] for n in notes), hp_first=notes[0]['hp'] / max(1, notes[0]['max']),
                                     near=last['near'], allies=last['allies'], spawn=last['spawn'], en=last['en']))
                i = j
            else:
                i += 1
    for r in rows:
        k = 'loss' if r['loss'] else 'win'
        by[k + '_mode'][r['mode']] += 1
        by[k + '_type'][r['type']] += 1
        by[k + '_alone'][r['allies'] == 0] += 1
        by[k + '_carrier'][r['gems'] >= 25] += 1
        by[k + '_healthy4'][r['hp_first'] >= 0.6] += 1
        by[k + '_spawn'][('<=10' if r['spawn'] <= 10 else '11-25' if r['spawn'] <= 25 else '>25')] += 1
        by[k + '_carrier_mode'][r['mode'] if r['gems'] >= 25 else '-'] += 1
    summary = {k: dict(v.most_common()) for k, v in by.items()}
    (out / f'deathlog_{a.arm}.json').write_text(json.dumps(dict(rows=rows, summary=summary), indent=1), encoding='utf-8')
    print(f'deaths parsed {len(rows)}')
    for k, v in sorted(summary.items()):
        print(k, json.dumps(v))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('deathlog'); p.add_argument('--run', required=True); p.add_argument('--arm', default='cand'); p.set_defaults(fn=cmd_deathlog)
    p = sp.add_parser('extract'); p.add_argument('--run', required=True); p.add_argument('--arm', default='cand'); p.add_argument('--jobs', type=int, default=10); p.set_defaults(fn=cmd_extract)
    p = sp.add_parser('report'); p.add_argument('--run', required=True); p.add_argument('--arm', default='cand'); p.add_argument('--md', default=''); p.set_defaults(fn=cmd_report)
    p = sp.add_parser('compare'); p.add_argument('--base', required=True); p.add_argument('--cand', required=True); p.add_argument('--out', default=''); p.set_defaults(fn=cmd_compare)
    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
