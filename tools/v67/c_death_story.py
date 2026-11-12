"""Print the rounds before one death, round by round, for every champion within 10 tiles of the victim.

Usage: c_death_story.py MATCH_PREFIX ROUND CHAMP_ID [--before 12] [--folder artifacts/local-only/v67-ranked]
Each line: round, then per champion  T<team><hero>#id@(x,y) hp/max g<gems> s<shards> [actions], with actions
m=move a=attack c=cast(slot) r=recall x=cancel t=tribute b=buy w=ward d=dash; an attack/cast on a champion tile
shows the target id (a>7), otherwise the target tile.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAMES = 'Ryth Vesp Vend Cass Issa Stel Pris Marc Will Ren Varg Tavi Hear'.split()
K = {4: 'm', 5: 'a', 6: 'c', 11: 'r', 12: 't', 13: 'b', 14: 'w', 16: 'x', 18: 'T', 23: 'd', 25: 's'}


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('match')
    ap.add_argument('round', type=int)
    ap.add_argument('champ', type=int)
    ap.add_argument('--before', type=int, default=12)
    ap.add_argument('--radius', type=int, default=10)
    ap.add_argument('--folder', default='artifacts/local-only/v67-ranked')
    a = ap.parse_args()
    f = next((ROOT / a.folder).glob(a.match + '*/timeline.json'))
    tl = json.loads(f.read_text())
    champs = {c['id']: c for c in tl['champs']}
    idx = {fr[0]: i for i, fr in enumerate(tl['frames'])}
    end = idx[a.round]
    for fr in tl['frames'][max(0, end - a.before):end + 1]:
        rnd, rows, hurt = fr
        by = {r[0]: r for r in rows}
        v = by[a.champ]
        vp = (v[1], v[2])
        parts = []
        for r in sorted(rows, key=lambda r: (champs[r[0]]['team'] != champs[a.champ]['team'], r[0])):
            if not r[5] or cheb(vp, (r[1], r[2])) > a.radius:
                continue
            acts = []
            for act in (r[9] if len(r) > 9 else []):
                kind, tx, ty, slot = act
                tag = K.get(kind, str(kind))
                if kind in (5, 6):
                    tgt = next((q[0] for q in rows if q[5] and (q[1], q[2]) == (tx, ty)), None)
                    acts.append(f'{tag}{slot if kind == 6 else ""}>{tgt}' if tgt is not None else f'{tag}{slot if kind == 6 else ""}@{tx},{ty}')
                elif kind in (4, 23):
                    acts.append(f'{tag}{tx},{ty}')
                else:
                    acts.append(tag)
            c = champs[r[0]]
            star = '*' if r[0] == a.champ else ''
            parts.append(f"{star}T{c['team']}{NAMES[c['type']]}#{r[0]}@{r[1]},{r[2]} {r[3]}/{r[4]} g{r[7]} s{r[8]} [{' '.join(acts)}]")
        print(f'R{rnd}: ' + ' | '.join(parts))
        if hurt:
            near = [(k, hp) for k, hp in hurt if cheb(vp, (tl['camps'][k]['x'], tl['camps'][k]['y'])) <= a.radius]
            if near:
                print('      camps hurt: ' + ' '.join(f"{tl['camps'][k]['x']},{tl['camps'][k]['y']}:{hp}" for k, hp in near))


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
