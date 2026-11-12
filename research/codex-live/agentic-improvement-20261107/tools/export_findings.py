"""Export reproducible research, with deduplicated sources and bounded ZIP parts.

Never traverses the bulk benchmark captures or local-replay cache. Selected raw
diagnostic artifacts are indexed by hash, not silently presented as exported.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone

BASE = Path(os.environ.get('BATTLECODE_ROOT', r'C:\projects\cambridge battlecode\work\agentic-improvement'))
REPO = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
DEST = Path(os.environ.get('BATTLECODE_FINDINGS', str(REPO / 'research/agentic-improvement-20261107')))
LIMIT = 48 * 1024**2
CODE = {'.py', '.ps1', '.sh', '.mjs', '.js', '.ts', '.cpp', '.h', '.hpp', '.c', '.ml', '.mli', '.rs', '.pyi', '.wat'}
ALLOWED = CODE | {'.md', '.json', '.toml', '.txt', '.csv', '.pt', '.npz', '.map26a', '.lock'}
SKIP = {'.git', '.venv', '.venv-train', '__pycache__', '.cambc', 'node_modules', 'build', 'build-release', 'replays', 'local-replays', 'bench_out'}
SECRETS = [re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'), re.compile(rb'github_pat_[A-Za-z0-9_]{40,}'), re.compile(rb'sk-(?:proj-)?[A-Za-z0-9_\-]{40,}'), re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'), re.compile(rb'eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}')]

def sha(b): return hashlib.sha256(b).hexdigest()
def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')

def walk(root):
    for parent, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.endswith('.replays'))
        for name in sorted(files):
            p = Path(parent) / name
            if p.suffix in ALLOWED and not any(s in p.name.lower() for s in ('.env', 'credential', 'session-token', 'auth-token')):
                yield p

def selected(refresh=False):
    paths = set()
    if refresh:
        for p in BASE.iterdir():
            if p.is_file() and p.suffix == '.md': paths.add(p)
        paths.update(walk(BASE / 'training/runs/bounded-delivery-retune-v1'))
        paths.update(walk(BASE / 'training/runs/delivery-parent-comparison-20261108'))
        paths.add(BASE / 'autonomy/data/experiments/bounded-retune-data-20261107/data-plan.json')
        paths.update(walk(BASE / 'autonomy/data/mistake-review'))
        for directory in (BASE / 'autonomy/data/experiments').iterdir():
            if directory.name.startswith('bounded-delivery-retune-20261107'): paths.update(walk(directory))
        for bot in (BASE / 'arena/bots').iterdir():
            if (bot / 'external-wasm.json').exists():
                spec=json.loads((bot/'external-wasm.json').read_text(encoding='utf-8'))
                frozen=(bot/spec['file']).resolve(); assert frozen.is_relative_to(bot.resolve())
                paths.add(frozen)
            if not bot.name.startswith('auto_rt7_'): continue
            paths.update(walk(bot / 'src'))
            for name in ('candidate.json','build-receipt.json'):
                if (bot / name).exists(): paths.add(bot / name)
        for name in ('brief.json','ladder.json'):
            if (BASE/'autonomy/data'/name).exists():paths.add(BASE/'autonomy/data'/name)
        if (BASE/'training/supervisor.json').exists(): paths.add(BASE/'training/supervisor.json')
        # Aggregate tables below are refreshed only for this experiment.
    else:
        return selected_full()
    paths.update(benchmark_metadata('bounded-delivery-retune-20261107'))
    paths.update(benchmark_metadata('delivery-parent-diagnostic-20261108'))
    return sorted(paths)

def benchmark_metadata(prefix=''):
    paths=set()
    for folder in sorted((BASE / 'autonomy/data/benchmarks').iterdir()):
        if not folder.is_dir() or not folder.name.startswith(prefix): continue
        for name in ['results.json', 'manifest.json', 'lineage.json', 'both-team-audit.json', 'parallel-native-audit.json',
                     'parallel-native-hashes.json', 'native-audit.json', 'native-hashes.json']:
            p = folder / name
            if p.exists(): paths.add(p)
    return paths

def selected_full():
    paths=set()
    for p in BASE.iterdir():
        if p.is_file() and p.suffix in CODE | {'.md'}: paths.add(p)
    for folder in ['autonomy', 'training']:
        for p in (BASE / folder).iterdir():
            if p.is_file() and p.suffix in ALLOWED and p.name not in {'config.json', 'state.sqlite', 'training.lock'}: paths.add(p)
    for folder in ['autonomy/data/experiments', 'autonomy/data/effective-config', 'autonomy/data/integration-audit',
                   'autonomy/data/mechanics', 'autonomy/data/mistake-review', 'autonomy/data/teammate-refresh',
                   'autonomy/data/work-notes', 'training/runs', 'training/agent2', 'training/v4',
                   'reference', 'recovered-rl', 'source-rl-env', 'evidence', 'evidence-v5', 'local-probes', 'arena/sdk']:
        paths.update(walk(BASE / folder))
    # Only aggregate tables/manifests/audits, never millions of native captures.
    paths.update(benchmark_metadata())
    # Every candidate source snapshot and recipe, deduplicated at file level.
    for bot in sorted((BASE / 'arena/bots').iterdir()):
        if not bot.is_dir(): continue
        paths.update(walk(bot / 'src'))
        for name in ['candidate.json', 'build-receipt.json', 'external-wasm.json']:
            if (bot / name).exists(): paths.add(bot / name)
        if (bot / 'external-wasm.json').exists():
            spec = json.loads((bot / 'external-wasm.json').read_text(encoding='utf-8'))
            frozen = (bot / spec['file']).resolve()
            assert frozen.is_relative_to(bot.resolve())
            paths.add(frozen)
    for directory in sorted((BASE / 'arena').iterdir()):
        if directory.is_dir() and directory.name.startswith('maps'):
            paths.update(walk(directory))
    return sorted(paths)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--refresh', action='store_true', help='Refresh only mutable delivery/observation paths; retain the original full historical snapshot')
    args=parser.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    archives = DEST / 'archives'; archives.mkdir(exist_ok=True)
    inventory_path = DEST / 'index/artifacts.json'
    previous = json.loads(inventory_path.read_text(encoding='utf-8')) if inventory_path.exists() else {}
    previous_objects = previous.get('objects', {})
    objects = dict(previous_objects)
    assert not args.refresh or previous, 'An initial full export is required before refresh'
    files = dict(previous.get('files', {})) if args.refresh else {}
    local = dict(previous.get('local_raw_artifacts', {})) if args.refresh else {}
    counts = Counter(); part = None; part_size = 0; new_objects = 0
    parts = list(previous.get('archives', []))
    def close_part():
        nonlocal part
        if part:
            path = Path(part.filename); part.close()
            assert path.stat().st_size < 95 * 1024**2
            parts.append({'file': path.relative_to(DEST).as_posix(), 'sha256': sha(path.read_bytes()), 'bytes': path.stat().st_size})
            part = None
    for i, p in enumerate(selected(args.refresh)):
        rel = p.relative_to(BASE).as_posix()
        b = p.read_bytes(); h = sha(b)
        assert not any(pattern.search(b) for pattern in SECRETS), f'Potential credential in {rel}; inspect locally'
        spec = {'sha256': h, 'bytes': len(b)}
        # Full decoded round streams and raw native events stay local. The compact
        # reports, exact selections and aggregate game rows are exported instead.
        raw = p.name.startswith('decoded-')
        if p.suffix == '.json' and not raw and len(b) > 200000:
            try:
                value = json.loads(b)
                raw = isinstance(value, dict) and {'match', 'events', 'teams'} <= set(value)
            except (ValueError, UnicodeError): pass
        if raw:
            local[rel] = {**spec, 'reason': 'Raw event/decoded replay stream retained locally; compact findings and aggregate results exported'}
            counts['local_raw_files'] += 1
            continue
        files[rel] = spec
        if h not in objects:
            if part is not None and part_size + len(b) > LIMIT: close_part(); part_size = 0
            if part is None:
                path = archives / f'objects-{len(parts)+1:04d}.zip'
                assert not path.exists(), f'Unexpected unindexed archive: {path}'
                part = zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6)
            entry = 'sha256/' + h
            info = zipfile.ZipInfo(entry, date_time=(2026,11,8,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
            part.writestr(info, b, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
            objects[h] = {'archive': Path(part.filename).relative_to(DEST).as_posix(), 'entry': entry}
            part_size += len(b); new_objects += 1
        counts['exported_files'] += 1; counts['logical_bytes'] += len(b)
        if i % 1000 == 0: print(json.dumps({'visited': i, 'unique_objects_added': new_objects}), flush=True)
    close_part()
    counts['exported_files']=len(files); counts['logical_bytes']=sum(s['bytes'] for s in files.values())
    counts['local_raw_files']=len(local)
    # Replays are not traversed; native audit receipts hold benchmark capture
    # identities. Exclusions must be explicit so the archive is not oversold.
    exclusions = ['local-replays/**', 'autonomy/data/benchmarks/*/<per-game captures and replay folders>',
                  'all .repl26a replay bundles; selected compact decoded findings remain included',
                  'autonomy/data/games/**', 'autonomy/data/agent-runs/**', 'training/v4/bench_out/**',
                  'all executable runtimes, compiler caches, virtual environments and downloaded dependencies',
                  'autonomy/config.json, session credentials, state.sqlite and local action ledgers']
    inventory = {'format': 1, 'at': datetime.now(timezone.utc).isoformat(), 'source_root': str(BASE),
                 'files': files, 'objects': objects, 'archives': parts, 'local_raw_artifacts': local,
                 'excluded': exclusions, 'summary': dict(counts), 'unique_objects': len(objects),
                 'refresh_scope': 'Delivery and current observation paths refreshed; original immutable historical snapshot retained' if args.refresh else 'Full selected historical snapshot',
                 'note': 'Exact bytes are content-addressed. Absolute paths in historical receipts identify the original local cache. Restore with restore_findings.py; rebase local receipt paths deliberately before rerunning historical audits. Do not load untrusted .pt files as executable pickle.'}
    dump(inventory_path, inventory)
    records = []
    for folder in sorted((BASE / 'autonomy/data/experiments').iterdir()):
        if not folder.is_dir(): continue
        path = folder / 'record.json'
        if path.exists(): records.append({'experiment': folder.name, **json.loads(path.read_text(encoding='utf-8'))})
    dump(DEST / 'index/experiments.json', records)
    print(json.dumps({'done': True, 'new_objects': new_objects, 'archives': len(parts), **dict(counts)}), flush=True)

if __name__ == '__main__': main()
