"""Copy replays where both teams are top-rated out of the platform archives (read-only), in batches.

    python tools/replay/select_top_replays.py --replays <folder with replays-*-part*.zip> --ratings <team_ratings.json>
           --top 75 --count 12000 --batches 6 --out artifacts/tmp/<dir>

Matches are chosen in SHA-256(replay name) order among those whose team A and team B are both within the top `--top`
ratings. Files keep the decoded names (`p<part>_<kind>_<match id>.repl26a`) so rows can be joined back to ratings.
"""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMBER = re.compile(r'^(?:.*/)?(?P<kind>[a-z]+)_(?P<match>[0-9a-f-]{36})_')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--replays', type=Path, required=True); p.add_argument('--ratings', type=Path, required=True)
    p.add_argument('--top', type=int, default=75); p.add_argument('--count', type=int, default=12000)
    p.add_argument('--batches', type=int, default=6); p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    out = a.out.resolve()
    if not out.is_relative_to(ROOT / 'artifacts') or out.exists():
        raise SystemExit('fresh output directory inside artifacts/ required')
    d = json.loads(a.ratings.read_text(encoding='utf-8'))
    rating = {t: v['rating'] for t, v in d['ratings'].items()}
    cut = sorted(rating.values(), reverse=True)[a.top - 1]
    pool = sorted((n for n, v in d['replays'].items() if min(rating[v['team_a']], rating[v['team_b']]) >= cut),
                  key=lambda n: hashlib.sha256(n.encode()).digest())[:a.count]
    by_part = {}
    for i, name in enumerate(pool):
        by_part.setdefault(int(re.match(r'p(\d+)_', name)[1]), []).append((i % a.batches, name))
    for b in range(a.batches):
        (out / f'batch{b}').mkdir(parents=True)
    for part, items in sorted(by_part.items()):
        z = zipfile.ZipFile(next(a.replays.glob(f'replays-*-part{part}.zip')))
        members = {MEMBER.match(m)['match']: m for m in z.namelist() if MEMBER.match(m)}
        for batch, name in items:
            match = re.match(r'p\d+_[a-z]+_(.+)\.repl26a$', name)[1]
            (out / f'batch{batch}' / name).write_bytes(z.read(members[match]))
    print(json.dumps(dict(out=str(out), replays=len(pool), rating_cut=cut, top=a.top, batches=a.batches)))


if __name__ == '__main__':
    main()
