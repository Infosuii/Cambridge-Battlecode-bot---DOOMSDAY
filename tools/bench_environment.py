"""Fingerprint the official build environment; source hashes alone cannot identify a Wasm build."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def describe():
    config = json.loads((ROOT / 'config/paths.json').read_text(encoding='utf8'))
    sdk = Path(config['sdk_cpp'])
    compiler = Path(config['wasi_sdk']) / 'bin'
    inputs = [('cli', Path(config['cli'])), ('workspace', ROOT / 'cambc.toml')]
    inputs += [('sdk/' + p.relative_to(sdk).as_posix(), p) for p in sorted(sdk.rglob('*')) if p.is_file()]
    inputs += [('cmake/' + p.relative_to(ROOT / 'cmake').as_posix(), p) for p in sorted((ROOT / 'cmake').rglob('*')) if p.is_file()]
    inputs += [('toolchain/' + name, compiler / name) for name in ['clang.exe', 'clang++.exe', 'wasm-ld.exe']]
    hashes = {name: hashlib.sha256(p.read_bytes()).hexdigest() for name, p in inputs}
    payload = dict(schema=1, inputs=hashes, cli_version=config['expected']['cli_version'], engine_version=config['expected']['engine_version'], fuel=config['expected']['fuel_per_turn'])
    payload['fingerprint'] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return payload


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--json', required=True)
    ap.add_argument('--verify', action='store_true')
    args = ap.parse_args()
    current = describe()
    target = Path(args.json)
    if args.verify:
        if json.loads(target.read_text()) != current:
            raise SystemExit('Build environment changed during benchmark')
    else:
        if target.exists() and json.loads(target.read_text()) != current:
            raise SystemExit('Output prefix belongs to a different environment; choose a fresh prefix')
        target.write_text(json.dumps(current, indent=1) + '\n', encoding='utf8')
    print(current['fingerprint'])
