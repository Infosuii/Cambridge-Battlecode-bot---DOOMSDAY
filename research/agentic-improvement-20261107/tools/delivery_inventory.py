from pathlib import Path
import os
import json
from collections import Counter

BASE = Path(r'C:\projects\cambridge battlecode\work\agentic-improvement')
SKIP = {'.git', '.venv', '.venv-train', '__pycache__', '.cambc', 'node_modules', 'build', 'build-release', 'replays', 'local-replays'}

def walk(root):
    for parent, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.endswith('.replays'))
        for name in sorted(files): yield Path(parent) / name

def main():
    reports = {}
    for folder in ['autonomy/data/experiments', 'training/runs', 'evidence', 'evidence-v5', 'local-probes', 'recovered-rl', 'source-rl-env', 'training/agent2', 'training/v4']:
        sizes = Counter(); counts = Counter(); largest = []
        for p in walk(BASE / folder):
            size = p.stat().st_size
            counts[p.suffix] += 1; sizes[p.suffix] += size
            if size > 8 * 1024**2: largest.append([p.relative_to(BASE).as_posix(), round(size/1024**2, 2)])
        reports[folder] = {'count': sum(counts.values()), 'MiB': round(sum(sizes.values())/1024**2, 2), 'extensions': {s: [counts[s], round(sizes[s]/1024**2,2)] for s in sizes}, 'large': sorted(largest, key=lambda x:-x[1])[:8]}
    print(json.dumps(reports, indent=2))

if __name__ == '__main__': main()
