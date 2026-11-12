"""Contact-turn behaviour by bot mode from an A2_MICLOG run (MT lines in our team's stdout).

Usage: c_miclog.py RUN [RUN ...]
For every turn that starts with an enemy champion within 4 (nd0 <= 4): the mode that ended the turn, whether it attacked
(attack possible at turn start, not after), cast a spell, walked, and the share of such turns per mode; "wasted" turns
walk without attacking or casting. Also the ladder yardsticks (research/v75/TEAMFIGHT.md): health share lost per contact turn
(next logged turn of the same champion one round later) and toward/away reversals per contact episode (consecutive
contact turns of one champion; walking turns that change the distance to the nearest enemy).
"""
import collections
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
NAMES = 'ryth vesper vendetta cassi issac stellar prism marcella willow ren varg tavi heart'.split()


def main():
    tot = collections.Counter()
    by = collections.defaultdict(collections.Counter)
    by_type = collections.defaultdict(collections.Counter)
    for run in sys.argv[1:]:
        games = json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']
        seen = set()
        for g in games:
            key = (g['map'], g['side'], g['seed'])
            if key in seen:
                continue
            seen.add(key)
            bundle = next((ROOT / g['folder']).glob('*.repl26a'))
            with zipfile.ZipFile(bundle) as z:
                text = z.read(f"team-{g['side']}.stdout").replace(b'\0', b'').decode('utf8', 'replace')
            prev = {}
            for line in text.splitlines():
                if not line.startswith('MT '):
                    continue
                p = line.split()
                if len(p) < 18:
                    continue
                rnd, slot, typ, hpf, nd0, nd, inr, mode = int(p[1]), p[2], int(p[3]), float(p[4]), int(p[5]), int(p[6]), int(p[7]), p[8]
                used, can0, can1, walked = int(p[11]), int(p[12]), int(p[13]), int(p[14])
                pv = prev.get(slot)
                if nd0 > 4:
                    if pv and pv[2]:
                        tot['episodes'] += 1
                        tot['reversals'] += sum(1 for a, b in zip(pv[2], pv[2][1:]) if a != b)
                    prev[slot] = (rnd, hpf, [])
                    continue
                if pv and pv[0] == rnd - 1:
                    tot['hp_pairs'] += 1
                    tot['hp_lost'] += max(0.0, pv[1] - hpf)
                dirs = pv[2] if pv and pv[0] >= rnd - 2 else []
                if pv and pv[2] and not dirs:
                    tot['episodes'] += 1
                    tot['reversals'] += sum(1 for a, b in zip(pv[2], pv[2][1:]) if a != b)
                attacked = can0 and not can1
                cast = used >= 0
                k = by[mode]
                k['n'] += 1
                k['att'] += attacked
                k['cast'] += cast
                k['walk'] += walked
                waste = walked and not attacked and not cast
                k['waste'] += waste
                k['away'] += waste and nd > nd0
                k['inr_waste'] += waste and inr > 0
                k['idle'] += not walked and not attacked and not cast
                if walked and nd != nd0:
                    dirs = dirs + [1 if nd > nd0 else -1]
                prev[slot] = (rnd, hpf, dirs)
                tot['n'] += 1
                tot['waste'] += waste
                tot['idle'] += not walked and not attacked and not cast
                tot['act'] += attacked or cast
                t = by_type[NAMES[typ] if 0 <= typ < 13 else str(typ)]
                t['n'] += 1; t['waste'] += waste; t['act'] += attacked or cast
    n = tot['n']
    print(f'contact turns {n}: act {100*tot["act"]/n:.1f}%  walk without acting {100*tot["waste"]/n:.1f}%  nothing {100*tot["idle"]/n:.1f}%  '
          f'health lost per contact turn {100*tot["hp_lost"]/max(1,tot["hp_pairs"]):.1f}% of max  reversals per episode {tot["reversals"]/max(1,tot["episodes"]):.2f} ({tot["episodes"]} episodes)')
    print(f'{"mode":16s} {"share":>6s} {"attack":>7s} {"cast":>6s} {"walk":>6s} {"wasted":>7s} {"of all":>7s} {"away":>6s} {"in-range":>8s} {"nothing":>8s}')
    for mode, k in sorted(by.items(), key=lambda kv: -kv[1]['n']):
        m = k['n']
        if m < n * 0.003:
            continue
        print(f'{mode:16s} {100*m/n:5.1f}% {100*k["att"]/m:6.0f}% {100*k["cast"]/m:5.0f}% {100*k["walk"]/m:5.0f}% {100*k["waste"]/m:6.0f}% '
              f'{100*k["waste"]/n:6.1f}% {100*k["away"]/max(1,k["waste"]):5.0f}% {100*k["inr_waste"]/max(1,k["waste"]):7.0f}% {100*k["idle"]/m:7.0f}%')
    print('by champion: act / wasted')
    for t, k in sorted(by_type.items(), key=lambda kv: -kv[1]['n']):
        print(f'  {t:9s} {k["n"]:6d} {100*k["act"]/k["n"]:4.0f}% {100*k["waste"]/k["n"]:4.0f}%')


if __name__ == '__main__':
    main()
