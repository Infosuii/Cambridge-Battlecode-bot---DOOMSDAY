"""Bundle exactly the audited selected source and tested Wasm; no network actions."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile

BASE = Path(os.environ.get('BATTLECODE_ROOT', r'C:\projects\cambridge battlecode\work\agentic-improvement'))
sys.path.insert(0, str(BASE / 'autonomy'))
import benchmark
from store import CLI, now

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path, obj): path.write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('candidate'); ap.add_argument('selection', type=Path)
    args = ap.parse_args()
    selection = json.loads(args.selection.read_text(encoding='utf-8'))
    assert selection['candidate'] == args.candidate and selection['approved_for_delivery'] is True
    assert selection['rationale'] and selection['limitations']
    final = BASE / 'training/runs/bounded-delivery-retune-v1'
    assert json.loads((final / 'runtime.json').read_text(encoding='utf-8'))['status'] == 'complete'
    outcomes = json.loads((final / 'outcomes.json').read_text(encoding='utf-8'))
    parent_run = BASE / 'training/runs/delivery-parent-comparison-20261108'
    parent_names = ('auto_bank_arrive_original', 'auto_bank_arrive_learned')
    assert args.candidate in outcomes or args.candidate == 'v111' or args.candidate in parent_names
    evidence_path = final / 'outcomes.json'
    if args.candidate in parent_names:
        assert json.loads((parent_run / 'runtime.json').read_text(encoding='utf-8'))['status']=='complete'
        assert args.candidate in json.loads((parent_run / 'outcomes.json').read_text(encoding='utf-8'))['candidates']
        evidence_path = parent_run / 'outcomes.json'
    root = benchmark.ARENA / 'bots' / args.candidate; src = root / 'src'
    wasm = benchmark.build(args.candidate)
    source_hash = benchmark.digest(src); wasm_hash = sha(wasm)
    if args.candidate in outcomes:
        frozen = json.loads((final / 'frozen-finalists.json').read_text(encoding='utf-8'))['identities'][args.candidate]
        assert source_hash == frozen['source'] and wasm_hash == frozen['wasm']
    elif args.candidate in parent_names:
        frozen = json.loads((parent_run / 'frozen-plan.json').read_text(encoding='utf-8'))['parents'][args.candidate]
        assert source_hash == frozen['source'] and wasm_hash == frozen['wasm']
    release = BASE / 'release' / ('delivery-20261108-' + args.candidate)
    release.mkdir(parents=True, exist_ok=True)
    bundle = release / (args.candidate + '-source.zip')
    if not bundle.exists():
        subprocess.run([str(CLI), 'bundle', 'bots/' + args.candidate, '--output', str(bundle)], cwd=benchmark.ARENA, check=True, capture_output=True)
    with zipfile.ZipFile(bundle) as z:
        assert z.testzip() is None
        expected = {p.relative_to(root).as_posix(): p for p in src.rglob('*') if p.is_file()}
        actual = {name for name in z.namelist() if not name.endswith('/')}
        assert actual == set(expected), (actual - set(expected), set(expected) - actual)
        for name, path in expected.items(): assert z.read(name) == path.read_bytes(), name
    dest_wasm = release / 'bot-injected.wasm'
    if dest_wasm.exists(): assert sha(dest_wasm) == wasm_hash
    else: shutil.copy2(wasm, dest_wasm)
    shutil.copy2(args.selection, release / 'selection.json')
    manifest = {'at': now(), 'candidate': args.candidate, 'source_digest': source_hash,
                'source_zip': {'file': bundle.name, 'sha256': sha(bundle), 'bytes': bundle.stat().st_size},
                'wasm': {'file': dest_wasm.name, 'sha256': wasm_hash, 'bytes': dest_wasm.stat().st_size},
                'sdk_digest': benchmark.digest(benchmark.ARENA / 'sdk/cpp'), 'cli_sha256': sha(CLI),
                'build_receipt': json.loads((root / 'build-receipt.json').read_text(encoding='utf-8')),
                'final_outcomes_sha256': sha(evidence_path), 'validation_evidence': str(evidence_path.relative_to(BASE)),
                'registered_retune_outcomes_sha256': sha(final / 'outcomes.json'), 'selection_sha256': sha(args.selection),
                'engine': benchmark.CONFIG['engine'], 'normal_fuel': True,
                'warning': 'Source bundle matches the tested source byte for byte. The platform compiles the source independently; identical server Wasm and ladder performance are not established by local testing.'}
    dump(release / 'manifest.json', manifest)
    (release / 'README.md').write_text('# Battlecode delivery\n\n' + selection['rationale'] + '\n\n' + selection['limitations'] +
        '\n\nUpload the source ZIP using the official platform. The included Wasm is the exact local tested release. All hashes and engine/build identities are in manifest.json. Complete evidence is on the research/agentic-improvement-20261107 GitHub branch.\n', encoding='utf-8')
    print(json.dumps({'release': str(release), 'manifest': manifest}))

if __name__ == '__main__': main()
