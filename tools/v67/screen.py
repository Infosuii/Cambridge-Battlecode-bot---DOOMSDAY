"""Development-only screening: every candidate runs the complete fixed 240-game benchmark."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CASES = [
    ('b15-winning-drafts', {'V67_OPENING': '1'}, 'Winning replay map drafts only'),
    ('b16-winning-draft-items', {'V67_OPENING': '3'}, 'Winning replay drafts and exact opening item milestones'),
    ('b17-winning-draft-routes', {'V67_OPENING': '5'}, 'Winning replay drafts and coordinated camp opening routes'),
    ('b18-public-camp-state', {'V67_CAMP_STATE': '1'}, 'Baseline with legal out-of-vision camp state and cooldown queries'),
]


def main():
    common = ROOT / 'bots/v67/src/common.h'
    original = (ROOT / 'bots/v65/src/common.h').read_bytes().decode('utf8')
    end = '\r\n' if '\r\n' in original else '\n'
    base = end.join(['#define V67_TRACE 0', '#define V67_TEAMPLAY 0', '#define V67_OPENING 0',
                     '#define V67_CAMP_STATE 0', '#define V67_META -1', '#define V67_BUILD 0', '#define V67_FIGHT 0', '']) + original
    for name, settings, note in CASES:
        common.write_bytes(base.encode('utf8'))
        args = [sys.executable, str(ROOT / 'tools/v67/run.py'), '--run', name, '--note', note]
        for key, value in settings.items():
            args += ['--set', f'{key}={value}']
        print('BEGIN', name, flush=True)
        subprocess.run(args, cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
