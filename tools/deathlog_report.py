"""Summarise APEX_DEATHLOG output (the bot's own last four notes before each death) from bench game folders.

Usage: python tools/deathlog_report.py <bench2 out prefix> [label for side-A bot] [label for side-B bot]
Candidate = bot_match --a. For each death: the last note's mode, the modes seen in the last four notes, hp four turns
earlier, visible enemies, allies within 4, distance to spawn, gems carried.
"""
from collections import Counter, defaultdict
import glob
from pathlib import Path
import re
import sys
import zipfile

NOTE = re.compile(r'R(\d+) (\S+) p\((\d+),(\d+)\) hp(\d+)/(\d+) g(\d+) mode=(\S+) G(-?\d+) enemies=(\d+) near=(\d+) ehp=(\d+) allies4=(\d+) spawn=(\d+)')


def deaths(text):
    out, cur = [], None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('DEATH '):
            cur = {'line': line, 'notes': []}
            out.append(cur)
        elif cur is not None and line.startswith('R'):
            m = NOTE.match(line)
            if m:
                cur['notes'].append(m.groups())
    return [d for d in out if d['notes']]


def main():
    prefix = sys.argv[1]
    by = defaultdict(list)
    for f in glob.glob(prefix + '-seed*-s*/games/*/*.repl26a'):
        p = Path(f)
        cand_side = 'a' if p.parent.name.endswith('-A') else 'b'
        z = zipfile.ZipFile(p)
        for side in 'ab':
            who = 'cand' if side == cand_side else 'opp'
            for d in deaths(z.read(f'team-{side}.stdout').decode('latin-1').replace(chr(0), '')):
                by[(p.parent.name.rsplit('-', 1)[0], who)].append(d)
                by[('ALL', who)].append(d)
    for key in sorted(by):
        ds = by[key]
        last = Counter(d['notes'][-1][7] for d in ds)
        any_fight = sum(1 for d in ds if any(n[7].startswith('fight') or n[7] == 'cmicro' for n in d['notes']))
        flee_last = sum(1 for d in ds if d['notes'][-1][7].startswith('flee'))
        hp0 = [int(d['notes'][0][4]) / max(1, int(d['notes'][0][5])) for d in ds]
        out_n = sum(1 for d in ds if int(d['notes'][-1][9]) > int(d['notes'][-1][12]) + 1)
        alone = sum(1 for d in ds if int(d['notes'][-1][12]) == 0)
        gems = sum(int(d['notes'][-1][6]) for d in ds)
        print(f'{key[0]:16s} {key[1]:4s} deaths {len(ds):4d}  fought-in-last-4 {any_fight / len(ds):.2f}  fleeing-at-death {flee_last / len(ds):.2f}  '
              f'hp4-before {sum(hp0) / len(hp0):.2f}  outnumbered {out_n / len(ds):.2f}  no-ally-within-4 {alone / len(ds):.2f}  gems lost {gems}')
        print('      last mode:', ', '.join(f'{m} {c}' for m, c in last.most_common(6)))


if __name__ == '__main__':
    main()
