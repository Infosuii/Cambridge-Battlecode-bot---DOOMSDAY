"""Candidate fuel-outs of x1_gate.sh lines split by round (< R and >= R) from the games' native summaries.

usage: python tools/x1_fuel_split.py ROUND TAG [TAG ...]      (run from the checkout that played the gates)
Reads artifacts/tmp/dz/x1g-TAG-KIND-OPP-01/games/*/summary.json (fuelExhausted entries of the candidate's team).
"""
import glob, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def split(tag, rd):
    early = late = games = 0
    for cell in glob.glob(str(ROOT/'artifacts/tmp/dz'/f'x1g-{tag}-*-01')):
        for p in glob.glob(cell + '/games/*/summary.json'):
            side = os.path.basename(os.path.dirname(p))[-1]
            d = json.load(open(p, encoding='utf-8')); games += 1
            for e in d['events']:
                if e['kind'] != 'fuelExhausted' or e['owner']['team'] != 'team' + side: continue
                for entry in e['entries']:
                    if entry['timestamp']['round'] < rd: early += 1
                    else: late += 1
    return games, early, late


def main():
    rd = int(sys.argv[1])
    print(f'| line | games | fuel-outs < R{rd} | fuel-outs >= R{rd} |\n|---|---|---|---|')
    for tag in sys.argv[2:]:
        g, a, b = split(tag, rd)
        print(f'| {tag} | {g} | {a} | {b} |')


if __name__ == '__main__': main()
