"""Build local puppets, check both-script fidelity, then test the frozen source.

Official CLI/default fuel only. No platform requests. All generated source,
Wasm, logs and replay bundles stay under ignored artifacts.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deep_preflight import ROOT
from gen_puppet import generate

STUDY = ROOT / 'research/deep-2026-10-28'
LOCAL = ROOT / 'artifacts/local-only/deep-2026-10-28'
CLI = ROOT / 'tools/vendor/cambc.exe'
ENGINE_BUILD = '85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run_command(args, logfile, timeout=300):
    r = subprocess.run([str(a) for a in args], cwd=ROOT, capture_output=True, timeout=timeout)
    logfile.parent.mkdir(parents=True, exist_ok=True)
    logfile.write_bytes(r.stdout + r.stderr)
    if r.returncode:
        raise RuntimeError(f'Local command failed{r.returncode}; see{logfile.relative_to(ROOT)}: {(r.stdout+r.stderr)[-1200:].decode("utf-8", "replace")}')


def build(script, side, folder):
    identity = generate(script, side, folder)
    wasm = folder.with_suffix('.wasm')
    receipt = folder / 'build-receipt.json'
    if receipt.exists():
        old = json.loads(receipt.read_text(encoding='utf-8'))
        assert old['source_sha256'] == identity['source_sha256'] and old['wasm_sha256'] == sha(wasm)
    else:
        run_command([CLI, 'build', folder, '--release', '--output', wasm], folder / 'build.log')
        receipt.write_bytes((json.dumps(identity | {'wasm_sha256': sha(wasm)}, indent=2) + '\n').encode())
    return wasm


def match(a, b, map_path, out, original):
    identity = {'a': sha(a), 'b': sha(b), 'map': sha(map_path), 'release': True, 'fuel': 'official default'}
    identity_path = out / 'run-identity.json'
    out.mkdir(parents=True, exist_ok=True)
    if identity_path.exists():
        assert json.loads(identity_path.read_text(encoding='utf-8')) == identity
    else:
        identity_path.write_bytes((json.dumps(identity, indent=2) + '\n').encode())
    summary = out / 'summary.json'
    if not summary.exists():
        run_command([CLI, 'run', a, b, '--map', map_path, '--out-dir', out, '--statistics', summary, '--json', '--release', '--log-limit', 16777216], out / 'run.log')
    bundles = [p for p in out.glob('*.repl26a') if zipfile.is_zipfile(p)]
    assert len(bundles) == 1
    with zipfile.ZipFile(bundles[0]) as z:
        assert z.testzip() is None
        raw = z.read('replay.repl26a')
        stdout = {s: z.read(f'team-{s}.stdout').replace(b'\0', b'').decode('utf-8', 'replace') for s in ('a', 'b')}
    rawfile = out / 'game-raw.repl26a'
    rawfile.write_bytes(raw)
    native = json.loads(summary.read_text(encoding='utf-8'))
    assert native['match']['engineVersion'] == '2.0.0' and native['match']['engineBuildHash'] == ENGINE_BUILD
    expected = original.read_bytes()
    first = next((i for i, (x, y) in enumerate(zip(raw, expected)) if x != y), None)
    if first is None and len(raw) != len(expected):
        first = min(len(raw), len(expected))
    return {'replay_bytes_identical': raw == expected, 'original_sha256': hashlib.sha256(expected).hexdigest(),
            'actual_sha256': hashlib.sha256(raw).hexdigest(), 'first_different_byte': first,
            'rounds': native['match']['roundsStarted'], 'outcome': native['match']['outcome'],
            'faults': native['diagnostics']['botFaults'], 'puppet_rejection_messages': {s: stdout[s].count('puppet rejected') for s in stdout},
            'stdout_nonempty': {s: bool(stdout[s]) for s in stdout}, 'raw_replay': rawfile.relative_to(ROOT).as_posix(),
            'wasm_a_sha256': identity['a'], 'wasm_b_sha256': identity['b'], 'map_sha256': identity['map']}


def case_run(case, suite):
    mid = case['match_id']
    script = json.loads((LOCAL / 'replay-inputs' / (mid + '.json')).read_text(encoding='utf-8'))
    assert script['partition'] == 'examined' and script['validation']['replay_bytes_identical']
    folder = suite / case['card_id']
    a, b = (build(script, t, folder / ('puppet-' + str(t))) for t in (0, 1))
    map_path, original = ROOT / script['map_file'], LOCAL / 'replays/examined' / (mid + '.repl26a')
    both = match(a, b, map_path, folder / 'both-scripted', original)
    own = 0 if case['side'] == 'a' else 1
    live = ROOT / 'artifacts/tmp/deep-repro/live69-plain.wasm'
    actual = match(live if own == 0 else a, b if own == 0 else live, map_path, folder / 'live-source', original)
    return case | {'compiled_script_control': both, 'frozen_source_test': actual,
                   'source_wasm_sha256': sha(live), 'input_api_validation_round_states': script['validation']['round_states_identical']}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--suite', default='artifacts/tmp/deep-repro/suite-v1')
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--cards', nargs='*')
    a = ap.parse_args()
    suite = (ROOT / a.suite).resolve()
    assert suite.is_relative_to(ROOT / 'artifacts') and 1 <= a.workers <= 4
    plan = json.loads((STUDY / 'REPRO_PLAN.json').read_text(encoding='utf-8'))
    cases = [r for r in plan['rows'] if not a.cards or r['card_id'] in a.cards]
    assert cases
    result_path = STUDY / 'REPRO_RESULTS.json'
    results = []
    if result_path.exists():
        results = json.loads(result_path.read_text(encoding='utf-8'))['rows']
    def save():
        payload = {'engine': '2.0.0', 'engine_build': ENGINE_BUILD, 'hands_off_used': 0,
                   'source': 'unchanged frozen33-file source copied to ignored artifacts',
                   'server_wasm_hash': 'unavailable; behavioral fidelity independently tested',
                   'cases_completed': len(results), 'both_script_byte_exact': sum(r['compiled_script_control']['replay_bytes_identical'] for r in results),
                   'source_byte_exact': sum(r['frozen_source_test']['replay_bytes_identical'] for r in results),
                   'rows': sorted(results, key=lambda r: r['card_id'])}
        result_path.write_bytes((json.dumps(payload, indent=2) + '\n').encode())
    with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures = {pool.submit(case_run, c, suite): c for c in cases}
        for f in cf.as_completed(futures):
            row = f.result()
            results = [r for r in results if r['match_id'] != row['match_id']] + [row]
            save()
            print(json.dumps({'card': row['card_id'], 'completed': len(results),
                              'both_script_exact': row['compiled_script_control']['replay_bytes_identical'],
                              'source_exact': row['frozen_source_test']['replay_bytes_identical'],
                              'source_rounds': row['frozen_source_test']['rounds']}), flush=True)


if __name__ == '__main__':
    main()
