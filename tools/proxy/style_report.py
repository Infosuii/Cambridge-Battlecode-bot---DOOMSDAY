"""Proxy opponent, step 2: a team's fight style as numbers, from tools/proxy/fight_style.mjs rows.

  python tools/proxy/style_report.py --style A.jsonl --index A/index.json [--style B.jsonl --index B/index.json ...]
         --json research/proxy/style.json [--md research/proxy/STYLE.md]

Every replay side gets a class from its index entry:
  duel games (source "duel"): "us:<arm>" for our side, "top@<arm>" for the top team that played it;
  top-vs-top games (source "top"): "top" (and per-team rows "team:<name>");
  local games (source "local"): the bot names given in the entry ("bots": {"a": name, "b": name}).
The fingerprint (one value per class) is what the proxy is fitted to and checked against:
  per game  deaths, kills, gold, contact rounds (champion rounds with an enemy within 8)
  rates     attack when an enemy is in range; walk in (step closer) when an enemy is 2-6 away and none in range;
            back off (step away) in contact, by health band and local numbers; the target picked when two or more
            enemies are in reach; focus fire (another ally hit the same enemy); alone in contact; death within 5
            rounds of a contact round; a recall started in contact (five top teams start one every turn and cancel
            it at the start of the next)
  off spawn (alive, not within 1 of the own spawn): share of rounds below 50% / 30% health and with an ally within 5;
            health fraction when arriving at spawn (home_hp)
Bands: health below 30%, 30-60%, 60%+; numbers = friends within 5 (40%+ health, self included) minus foes within 6.
"""
import argparse
import collections as co
import json
from pathlib import Path

ROUND, TEAM, TYPE, ID, HP, MAXHP, GEMS, D, FOES6, FRIENDS5, HPRATIO, REACH, ATK, CAST, CAMP, STEP, RECALL, PICK, SHARED, DIED, ALONE8, HITDIST, INRANGE = range(23)


def band(hp):
    return 'low' if hp < 30 else 'mid' if hp < 60 else 'high'


def numbers(r):
    k = r[FRIENDS5] - r[FOES6]
    return 'down' if k < 0 else 'even' if k == 0 else 'up'


def sides(info):
    """{team index: [class, ...]} for one replay's index entry; team 0 is side a."""
    src = info['source']
    if src == 'duel':
        ours = 0 if info['ourSide'] == 'a' else 1
        return {ours: ['us:' + info['arm']], 1 - ours: ['top@' + info['arm'], 'opp:' + info['opponent']]}
    if src == 'top':
        return {0: ['top', 'team:' + info['teamA']], 1: ['top', 'team:' + info['teamB']]}
    if src == 'local':
        return {0: [info['bots']['a']], 1: [info['bots']['b']]}
    raise ValueError(src)


class Acc:
    def __init__(self):
        self.games = 0
        self.wins = 0
        self.margin = 0.0
        self.sum = co.Counter()
        self.num = co.Counter()
        self.den = co.Counter()

    def rate(self, key, hit, cond=True):
        if cond:
            self.den[key] += 1
            self.num[key] += bool(hit)

    def out(self):
        g = max(1, self.games)
        d = dict(games=self.games, win_rate=self.wins / g, margin=self.margin / g)
        for k in ('deaths', 'kills', 'gold', 'contact'):
            d[k] = self.sum[k] / g
        for k in sorted(self.den):
            d[k] = self.num[k] / self.den[k]
            d[k + '#'] = self.den[k]
        return d


def add(acc, game, t, rows):
    acc.games += 1
    gems = game['submittedGems']
    acc.wins += game['outcome'] == t + 1
    acc.margin += gems[t] - gems[1 - t]
    tm = game['teams'][t]
    acc.sum['deaths'] += tm['deaths']
    acc.sum['kills'] += tm['kills']
    acc.sum['gold'] += tm['gold']
    acc.sum['contact'] += tm['contactRounds']
    if 'offSpawn' in tm:
        acc.num['hurt50_off_spawn'] += tm['hurt50']; acc.den['hurt50_off_spawn'] += tm['offSpawn']
        acc.num['hurt30_off_spawn'] += tm['hurt30']; acc.den['hurt30_off_spawn'] += tm['offSpawn']
        acc.num['grouped_off_spawn'] += tm['grouped5']; acc.den['grouped_off_spawn'] += tm['offSpawn']
        acc.num['home_hp'] += tm['homeHp']; acc.den['home_hp'] += tm['homeArrivals']
    for r in rows:
        if r[TEAM] != t:
            continue
        b, n = band(r[HP]), numbers(r)
        close = r[D] <= 5
        acc.rate('attack|in_range', r[ATK], r[INRANGE])
        acc.rate('attack|reach', r[ATK], r[REACH])
        walk = 2 <= r[D] <= 6 and not r[INRANGE]
        acc.rate('walk_in', r[STEP] < 0, walk)
        acc.rate(f'walk_in|{b}', r[STEP] < 0, walk)
        acc.rate(f'walk_in|{n}', r[STEP] < 0, walk)
        acc.rate('back_off', r[STEP] > 0, close)
        acc.rate(f'back_off|{b}', r[STEP] > 0, close)
        acc.rate(f'back_off|{n}', r[STEP] > 0, close)
        acc.rate(f'back_off|{b}|{n}', r[STEP] > 0, close)
        acc.rate('alone_in_contact', r[ALONE8], close)
        acc.rate('outnumbered_in_contact', n == 'down', close)
        acc.rate('died5|contact', r[DIED], close)
        acc.rate(f'died5|{b}', r[DIED], close)
        acc.rate(f'died5|{n}', r[DIED], close)
        acc.rate('recall_start|contact', r[RECALL], close)
        acc.rate('camp|contact', r[CAMP], close)
        if r[PICK] >= 0 and r[REACH] >= 2:  # a real choice: two or more enemies in reach
            acc.rate('pick_lowest_frac', r[PICK] & 1)
            acc.rate('pick_closest', r[PICK] & 2)
            acc.rate('pick_lowest_hp', r[PICK] & 4)
        if r[SHARED] >= 0:
            acc.rate('focus_shared', r[SHARED])


def load(styles, indexes):
    games = []
    for sp, ip in zip(styles, indexes):
        index = json.loads(Path(ip).read_text(encoding='utf8'))
        with open(sp, encoding='utf8') as f:
            for line in f:
                g = json.loads(line)
                info = index.get(g['match'])
                if info is None:
                    raise SystemExit(f'{g["match"]} missing from {ip}')
                games.append((g, info))
    return games


def fingerprint(games):
    accs = co.defaultdict(Acc)
    for g, info in games:
        for t, classes in sides(info).items():
            for c in classes:
                add(accs[c], g, t, g['rows'])
    return {c: a.out() for c, a in sorted(accs.items())}


# The style keys shown in the report and used as the distance between two fingerprints.
KEYS = ['deaths', 'kills', 'gold', 'contact', 'attack|in_range', 'walk_in', 'walk_in|low', 'walk_in|high', 'walk_in|down',
        'walk_in|up', 'back_off', 'back_off|low', 'back_off|mid', 'back_off|high', 'back_off|down', 'back_off|even',
        'back_off|up', 'alone_in_contact', 'outnumbered_in_contact', 'died5|contact', 'died5|low', 'died5|down',
        'recall_start|contact', 'camp|contact', 'hurt50_off_spawn', 'hurt30_off_spawn', 'grouped_off_spawn', 'home_hp',
        'pick_lowest_frac', 'pick_closest', 'pick_lowest_hp', 'focus_shared']


def markdown(fp, cols):
    L = ['| Measure | ' + ' | '.join(cols) + ' |', '|---|' + '---:|' * len(cols)]
    L.append('| games | ' + ' | '.join(str(fp[c]['games']) for c in cols) + ' |')
    L.append('| win rate | ' + ' | '.join(f"{fp[c]['win_rate']:.2f}" for c in cols) + ' |')
    L.append('| gem margin | ' + ' | '.join(f"{fp[c]['margin']:+.0f}" for c in cols) + ' |')
    for k in KEYS:
        cells = []
        for c in cols:
            v = fp[c].get(k)
            cells.append('-' if v is None else f'{v:.0f}' if k in ('gold', 'contact') else f'{v:.1f}' if k in ('deaths', 'kills') else f'{v:.3f}')
        L.append(f'| {k} | ' + ' | '.join(cells) + ' |')
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--style', action='append', required=True)
    ap.add_argument('--index', action='append', required=True)
    ap.add_argument('--json', required=True)
    ap.add_argument('--md')
    ap.add_argument('--cols', nargs='+', help='classes shown in the markdown table (default: all non-team classes)')
    a = ap.parse_args()
    if len(a.style) != len(a.index):
        raise SystemExit('one --index per --style')
    fp = fingerprint(load(a.style, a.index))
    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.json).write_text(json.dumps(fp, indent=1) + '\n', encoding='utf8', newline='\n')
    cols = a.cols or [c for c in fp if not c.startswith(('team:', 'opp:'))]
    table = markdown(fp, cols)
    print(table)
    if a.md:
        Path(a.md).write_text(table + '\n', encoding='utf8', newline='\n')


if __name__ == '__main__':
    main()
