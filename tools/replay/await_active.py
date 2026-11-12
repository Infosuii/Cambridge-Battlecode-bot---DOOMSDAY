"""Wait until a submitted platform version is active, print the activation time, then exit (read-only polling).

Usage: python tools/replay/await_active.py <platform version> [--timeout-min 240]
"""
import argparse
import json
from pathlib import Path
import subprocess
import time

CLI = Path(__file__).resolve().parents[2] / 'tools/vendor/cambc.exe'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('version', type=int)
    ap.add_argument('--timeout-min', type=float, default=240)
    a = ap.parse_args()
    end = time.time() + a.timeout_min * 60
    while time.time() < end:
        r = subprocess.run([str(CLI), 'submissions', 'list', '--json'], capture_output=True, text=True, encoding='utf8', errors='replace')
        try:
            d = json.loads(r.stdout)
            sub = next((s for s in d['submissions'] if s['version'] == a.version), None)
            if d['active']['version'] == a.version:
                print('ACTIVE', a.version, d['active']['statusAt'], flush=True)
                return
            if sub and sub['status'] not in ('queued', 'compiling', 'building', 'active', 'inactive'):
                print('STATUS', a.version, sub['status'], flush=True)
                if 'fail' in sub['status'] or 'error' in sub['status']:
                    raise SystemExit(1)
        except (ValueError, KeyError):
            pass
        time.sleep(60)
    print('TIMEOUT waiting for version', a.version)
    raise SystemExit(2)


if __name__ == '__main__':
    main()
