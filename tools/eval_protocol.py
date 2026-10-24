"""Freeze / verify / show the evaluation protocol (Agent H).

  python tools/eval_protocol.py freeze            # writes evaluation/schedules/*.json, protocol.json, protocol.lock.json
  python tools/eval_protocol.py verify            # exit 1 if protocol or any schedule differs from the lock
  python tools/eval_protocol.py show              # partitions and schedule sizes

`freeze` is idempotent; if the rebuilt protocol differs from a frozen one it refuses unless
`--supersede-reason "..."` is given (the old hash is kept in the lock history and must be reported).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from nfs.evaluate import protocol as proto  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('command', choices=['freeze', 'verify', 'show'])
    ap.add_argument('--supersede-reason')
    a = ap.parse_args()
    if a.command == 'freeze':
        print(json.dumps(proto.freeze(a.supersede_reason), indent=2))
    elif a.command == 'verify':
        try:
            p = proto.load(verify=True)
        except Exception as exc:  # noqa: BLE001
            print('PROTOCOL VERIFY FAILED:', exc)
            sys.exit(1)
        print('protocol ok', proto.protocol_sha256(), p['protocol_version'])
    else:
        p = proto.load(verify=False)
        parts = proto.load_schedule('map_partitions', verify=False)['partitions']
        for k, v in parts.items():
            print(f'{k:10s} {len(v):2d} {", ".join(v)}')
        for k in p['schedules']:
            s = proto.load_schedule(k, verify=False)
            print(f'schedule {k:15s} cells={len(s.get("cells", []))}')


if __name__ == '__main__':
    main()
