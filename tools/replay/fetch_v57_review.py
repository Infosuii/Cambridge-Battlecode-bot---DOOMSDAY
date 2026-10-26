"""Download native summaries for the requested v57 loss review; never queues matches or downloads source.

Usage: python tools/replay/fetch_v57_review.py --listing data/ladder/v57_games_20261026.json --cli <official CLI4>
       --out-root artifacts/local-only/v57-latest --manifest research/v57/V57_LATEST_REVIEW_MANIFEST.json
All engine2 ranked games plus up to20 recent engine2 Claudus games are included. Raw data stay local-only.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--listing', required=True)
    ap.add_argument('--cli', required=True)
    ap.add_argument('--out-root', required=True)
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--workers', type=int, default=3)
    args = ap.parse_args()
    out = (ROOT / args.out_root).resolve()
    if not out.is_relative_to(ROOT / 'artifacts/local-only'):
        raise SystemExit('raw summary destination must be local-only')
    cli = (ROOT / args.cli).resolve()
    listing = json.loads((ROOT / args.listing).read_text(encoding='utf8'))
    current = [g for g in listing if g['status'] == 'finished' and all(t['engineVersion'] == '2.0.0' for t in g['teams'])]
    selected = {g['matchId']: g for g in current if g['kind'] == 'ranked'}
    top = [g for g in current if g['kind'] != 'ranked' and any(t['name'] == 'Claudus Maximus' for t in g['teams'])]
    selected.update({g['matchId']: g for g in top[-20:]})
    out.mkdir(parents=True, exist_ok=True)

    def fetch(game):
        key = str(uuid.UUID(game['matchId']))
        folder = out / key
        folder.mkdir(exist_ok=True)
        target = folder / 'summary.json'
        for attempt in range(6):
            if target.exists():
                try:
                    data = json.loads(target.read_text(encoding='utf8'))
                    if data['match']['engineVersion'] == '2.0.0':
                        us = next(t for t in game['teams'] if t['name'] == 'DOOMSDAY')
                        return dict(matchId=key, map=game['map'], kind=game['kind'], createdAt=game['createdAt'],
                                    engineVersion='2.0.0', side=us['side'], win=us['result'] == 'win',
                                    opponent=next(t['name'] for t in game['teams'] if t['name'] != 'DOOMSDAY'),
                                    summary=target.relative_to(ROOT).as_posix(),
                                    sha256=hashlib.sha256(target.read_bytes()).hexdigest())
                except (ValueError, KeyError):
                    pass
            r = subprocess.run([str(cli), 'matches', 'summary', key, '--json', '--output', str(target)],
                               capture_output=True, text=True, encoding='utf8', errors='replace', timeout=90)
            (folder / 'download.log').write_text(r.stdout + r.stderr, encoding='utf8')
            time.sleep(max(2.0, (attempt + 1) * 2.0))
        # Validate one final successful response without making another request.
        if target.exists():
            data = json.loads(target.read_text(encoding='utf8'))
            if data['match']['engineVersion'] == '2.0.0':
                us = next(t for t in game['teams'] if t['name'] == 'DOOMSDAY')
                return dict(matchId=key, map=game['map'], kind=game['kind'], createdAt=game['createdAt'], engineVersion='2.0.0',
                            side=us['side'], win=us['result'] == 'win',
                            opponent=next(t['name'] for t in game['teams'] if t['name'] != 'DOOMSDAY'),
                            summary=target.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(target.read_bytes()).hexdigest())
        raise RuntimeError('summary unavailable after retries: ' + key)

    rows, errors = [], []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
        futures = {pool.submit(fetch, g): key for key, g in selected.items()}
        for future in as_completed(futures):
            try:
                rows.append(future.result())
            except Exception as error:
                errors.append(dict(matchId=futures[future], error=str(error)))
            if (len(rows) + len(errors)) % 25 == 0:
                print('summaries', len(rows), '/', len(selected), 'errors', len(errors), flush=True)
    report = dict(live_submission_version=56, local_source='bots/v57', engine='2.0.0',
                  selected=len(selected), downloaded=len(rows), errors=errors, matches=sorted(rows, key=lambda r: r['createdAt']))
    (ROOT / args.manifest).write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n', encoding='utf8')
    print('complete', len(rows), 'summaries; errors', len(errors))
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
