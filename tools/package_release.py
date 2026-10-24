"""Package the release with the official CLI and verify it (Agent H). NEVER submits or uploads.

  python tools/package_release.py [--bot bot] [--out artifacts/release] [--name nfs-release]

Steps: refuse unless bot/src/nn_config.h is the generated `release` profile (the lead switches profiles with
tools/gen_config.py / tools/install_models.py; this tool never edits sources) -> refuse a non-flat or non-cpp/h
source tree -> `cambc bundle <bot> --output <out>/<name>.zip` -> `cambc build <bot> --release` -> SHA256SUMS + manifest.json
(cli version, profile, head modes, section hashes, model checksums, submitted=false) -> tools/verify_release.py checks
including an independent rebuild from the extracted ZIP in a fresh directory.
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nfs import engine  # noqa: E402
from nfs.evaluate import release as rel  # noqa: E402
from nfs.evaluate import wasm as wasm_mod  # noqa: E402
import verify_release  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--bot', default=str(engine.ROOT / 'bot'))
    ap.add_argument('--out', default=str(engine.ROOT / 'artifacts' / 'release'))
    ap.add_argument('--name', default='nfs-release')
    ap.add_argument('--models', default=str(engine.ROOT / 'models'))
    a = ap.parse_args()
    bot, out = Path(a.bot).resolve(), Path(a.out).resolve()
    src = bot / 'src'
    cfg_p = src / 'nn_config.h'
    if not cfg_p.exists():
        sys.exit(f'{cfg_p} missing')
    cfg = rel.parse_nn_config(cfg_p.read_text(encoding='utf-8'))
    bad = [c for c in rel.check_config(cfg) if not c['passed']]
    if bad:
        sys.exit('refusing to package: nn_config.h is not a clean release profile: ' +
                 '; '.join(f"{c['name']}={c['detail']}" for c in bad))
    policy=src/'nn_policy_config.h'
    if not policy.exists() or not all(c['passed'] for c in rel.check_direct_config(policy.read_text())):
        sys.exit('refusing to package: direct policy experiment must be disabled in this release')
    extra = [p.relative_to(src).as_posix() for p in src.rglob('*') if p.is_file() and
             (p.parent != src or p.suffix not in ('.cpp', '.h'))]
    if extra:
        sys.exit(f'refusing to package: non-flat or non-cpp/h files in {src}: {extra[:10]}')
    out.mkdir(parents=True, exist_ok=True)
    zip_path, wasm_path = out / f'{a.name}.zip', out / f'{a.name}.wasm'
    r = subprocess.run([str(engine.CLI), 'bundle', str(bot), '--output', str(zip_path)], capture_output=True,
                       text=True, cwd=engine.ROOT)
    if r.returncode or not zip_path.exists():
        sys.exit('cambc bundle failed:\n' + r.stdout + r.stderr)
    engine.official_build(bot, wasm_path, release=True)
    mod = wasm_mod.WasmModule.load(wasm_path)
    doc = verify_release.verify(zip_path, wasm_path, src, a.models, rebuild=True)
    engine.write_json(out / f'{a.name}.verification.json', doc)
    files = [zip_path, wasm_path] + sorted(src.glob('*'))
    models = Path(a.models)
    if models.exists():
        files += sorted(p for p in models.rglob('*') if p.is_file())
    sums = ''.join(f'{engine.sha256(p)}  {p.relative_to(engine.ROOT).as_posix() if p.is_relative_to(engine.ROOT) else p}\n'
                   for p in files)
    (out / 'SHA256SUMS').write_text(sums, encoding='utf-8', newline='\n')
    manifest = dict(name=a.name, created_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                    cli_version=engine.cli_version(), profile=cfg['profile'], head_modes=cfg['head_modes'],
                    flags=cfg['flags'], macros=cfg['macros'], zip=zip_path.name, zip_sha256=engine.sha256(zip_path),
                    wasm=wasm_path.name, wasm_sha256=engine.sha256(wasm_path),
                    wasm_sections=mod.section_hashes(), code_section_sha256=engine.code_section_sha(wasm_path),
                    source_tree_sha256=engine.tree_sha256(src), models=doc['info'].get('models'),
                    verification=dict(passed=doc['passed'], file=f'{a.name}.verification.json'),
                    submitted=False, note='packaged locally; this tool never submits, uploads or activates')
    engine.write_json(out / f'{a.name}.manifest.json', manifest)
    print('zip ', manifest['zip_sha256'], zip_path)
    print('wasm', manifest['wasm_sha256'], wasm_path)
    print('verification', 'PASS' if doc['passed'] else 'FAIL')
    sys.exit(0 if doc['passed'] else 1)


if __name__ == '__main__':
    main()
