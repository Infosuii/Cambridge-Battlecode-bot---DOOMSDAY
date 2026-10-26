"""Download native summaries and replays for every v58 game in a listing; never queues matches or downloads source.

Usage: python tools/replay/fetch_v59_review.py --listing data/ladder/v58_since_live.json
       --out-root artifacts/local-only/v58-ladder --manifest research/v59/V59_LADDER_MANIFEST.json
Each match gets <out-root>/<matchId>/summary.json and replay.repl26a. Raw data stay local-only.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def run(cli, args, log):
    r = subprocess.run([str(cli)] + args, capture_output=True, text=True, encoding='utf8', errors='replace', timeout=180)
    log.write_text(r.stdout + r.stderr, encoding='utf8')
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--listing', required=True)
    ap.add_argument('--out-root', required=True)
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--cli', default='tools/vendor/cambc.exe')
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--no-replay', action='store_true', help='summaries only')
    ap.add_argument('--kind', help='only this match kind (ranked/unranked)')
    args = ap.parse_args()
    out = (ROOT / args.out_root).resolve()
    if not out.is_relative_to(ROOT / 'artifacts/local-only'):
        raise SystemExit('raw match destination must be local-only')
    cli = (ROOT / args.cli).resolve()
    games = [g for g in json.loads((ROOT / args.listing).read_text(encoding='utf8')) if g['status'] == 'finished' and (not args.kind or g['kind'] == args.kind)]
    # Losses first (ranked before unranked), so an interrupted fetch still covers what the review needs most.
    ours = lambda g: next(t for t in g['teams'] if t['name'] == 'DOOMSDAY')
    games.sort(key=lambda g: (ours(g)['result'] == 'win', g['kind'] != 'ranked', g['createdAt']))
    out.mkdir(parents=True, exist_ok=True)

    def fetch(game):
        key = game['matchId']
        folder = out / key
        folder.mkdir(exist_ok=True)
        summary, replay = folder / 'summary.json', folder / 'replay.repl26a'
        for attempt in range(5):
            if not summary.exists() or summary.stat().st_size == 0:
                run(cli, ['matches', 'summary', key, '--json', '--output', str(summary)], folder / 'summary.log')
            if not replay.exists() and not args.no_replay:
                run(cli, ['matches', 'download', key, '--output', str(replay)], folder / 'replay.log')
            try:
                data = json.loads(summary.read_text(encoding='utf8'))
                ok = data['match']['engineVersion'] == '2.0.0'
            except (OSError, ValueError, KeyError):
                summary.unlink(missing_ok=True)
                ok = False
            try:
                ok = ok and (args.no_replay or zipfile.ZipFile(replay).testzip() is None)
            except (OSError, zipfile.BadZipFile):
                replay.unlink(missing_ok=True)
                ok = False
            if ok:
                break
            time.sleep((attempt + 1) * 3.0)
        else:
            raise RuntimeError('unavailable after retries: ' + key)
        us = next(t for t in game['teams'] if t['name'] == 'DOOMSDAY')
        them = next(t for t in game['teams'] if t['name'] != 'DOOMSDAY')
        return dict(matchId=key, map=game['map'], kind=game['kind'], createdAt=game['createdAt'], endReason=game['endReason'],
                    side=us['side'], win=us['result'] == 'win', opponent=them['name'], opponentId=them['teamId'],
                    ourDraft=us['draftPicks'], theirDraft=them['draftPicks'],
                    summary=summary.relative_to(ROOT).as_posix(), replay=replay.relative_to(ROOT).as_posix(),
                    sha256=hashlib.sha256(summary.read_bytes()).hexdigest())

    rows, errors = [], []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
        futures = {pool.submit(fetch, g): g['matchId'] for g in games}
        for future in as_completed(futures):
            try:
                rows.append(future.result())
            except Exception as error:
                errors.append(dict(matchId=futures[future], error=str(error)))
            if (len(rows) + len(errors)) % 25 == 0:
                print('fetched', len(rows), '/', len(games), 'errors', len(errors), flush=True)
    rows.sort(key=lambda r: r['createdAt'])
    (ROOT / args.manifest).write_text(json.dumps(dict(listing=args.listing, matches=rows, errors=errors), indent=1) + '\n', encoding='utf8')
    print('done', len(rows), 'errors', len(errors))


if __name__ == '__main__':
    main()
