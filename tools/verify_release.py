"""Release verification (Agent H). Never submits anything.

  python tools/verify_release.py --zip artifacts/release/nfs.zip --wasm artifacts/release/nfs.wasm [--src bot/src]
         [--models models] [--out artifacts/release/verification.json] [--no-rebuild]

Checks (all must pass):
  ZIP      only flat src/*.cpp|*.h members, no traversal/absolute/backslash/duplicates/symlinks, CRC ok, member set
           and bytes equal to the source tree, source tree itself flat cpp/h only.
  REBUILD  extract the ZIP (validated names only) into a fresh directory, build with the official CLI --release,
           compare to --wasm: identical sha256, or identical non-custom sections (reported which).
  CONFIG   the shipped src/nn_config.h: kProfile == "release", kTraining/kTelemetry/kSelfTest/kFuelCredit false,
           NN_TRAINING/NN_TELEMETRY 0, no shadow heads, kAnyHead consistent.
  WASM     no 'NFS1'/'NFT1' bytes in the data section or any executable section; if lab strip is selected
           (NN_STRIP_LAB 1 / kStripLab) no lab_* exports (otherwise lab exports are reported, as in the original).
  MODELS   registry statuses consistent: no untrained/teacher_initialized model active, every active head has a
           validated model; sha256 of every model file recorded.
  SCRIPTS  no use of the engine fuel-override flag in tools/, python/, configs/.
  REFS     reference wasm sha256 unchanged (references/builds/manifest.json).
"""
import argparse
import datetime as dt
import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from nfs import engine  # noqa: E402
from nfs.evaluate import release as rel  # noqa: E402
from nfs.evaluate import wasm as wasm_mod  # noqa: E402


def rebuild_check(zip_path: Path, wasm_path: Path, work: Path) -> tuple[list[dict], dict]:
    if work.exists():
        shutil.rmtree(work)
    bot = work / 'bot'
    rel.safe_extract(zip_path, bot)
    out = engine.official_build(bot, work / 'rebuilt.wasm', release=True)
    a, b = engine.sha256(out), engine.sha256(wasm_path)
    sa = wasm_mod.WasmModule.load(out).section_hashes()
    sb = wasm_mod.WasmModule.load(wasm_path).section_hashes()
    info = dict(rebuilt_sha256=a, release_sha256=b, identical_sha256=a == b, identical_non_custom_sections=sa == sb,
                rebuild_dir=str(work))
    return [rel._chk('independent_rebuild_matches', a == b or sa == sb,
                     'identical sha256' if a == b else ('identical non-custom sections' if sa == sb else 'DIFFERENT'))], info


def reference_checks(builds_dir: Path | None = None) -> tuple[list[dict], dict]:
    """Verify immutable local reference artifacts by name and hashes, independent of historical absolute paths."""
    builds_dir = Path(builds_dir) if builds_dir is not None else engine.ROOT / 'references/builds'
    manifest = json.loads((builds_dir / 'manifest.json').read_text(encoding='utf-8'))['opponents']
    changed, info = [], {}
    for name, expected in manifest.items():
        if not name or name in ('.', '..') or '/' in name or '\\' in name or ':' in name:
            changed.append(name)
            info[name] = dict(error='invalid reference name')
            continue
        path = builds_dir / f'{name}.wasm'
        try:
            actual = dict(path=str(path.resolve()), wasm_sha256=engine.sha256(path),
                          code_section_sha256=dict(wasm_mod.WasmModule.load(path).section_hashes()).get(10, ''))
            matches = all(actual[key] == expected[key] for key in ('wasm_sha256', 'code_section_sha256'))
        except (OSError, ValueError) as error:
            actual, matches = dict(path=str(path.resolve()), error=str(error)), False
        info[name] = actual
        if not matches:
            changed.append(name)
    return [rel._chk('reference_binaries_unchanged', not changed, changed)], info


def verify(zip_path, wasm_path, src_dir=None, models=None, rebuild=True, scan_paths=None, work=None) -> dict:
    zip_path, wasm_path = Path(zip_path).resolve(), Path(wasm_path).resolve()
    src_dir = Path(src_dir).resolve() if src_dir else engine.ROOT / 'bot' / 'src'
    checks, info = [], {}
    checks += rel.check_zip(zip_path, src_dir)
    with zipfile.ZipFile(zip_path) as z:
        cfg_text = z.read('src/nn_config.h').decode('utf-8', 'replace') if 'src/nn_config.h' in z.namelist() else ''
        policy=z.read('src/nn_policy_config.h').decode('utf-8','replace') if 'src/nn_policy_config.h' in z.namelist() else ''
    checks += rel.check_direct_config(policy)
    if cfg_text:
        cfg = rel.parse_nn_config(cfg_text)
        info['config'] = cfg
        checks += rel.check_config(cfg)
        strip = bool(cfg['macros'].get('NN_STRIP_LAB') == 1 or cfg['flags'].get('kStripLab'))
    else:
        cfg = dict(head_modes={})
        checks.append(rel._chk('config_nn_config_h_present', False, 'src/nn_config.h missing from the ZIP'))
        strip = False
    wc, wi = rel.check_wasm(wasm_path, strip)
    checks += wc
    info['wasm'] = wi
    rc, ri = rel.check_registry(Path(models) if models else engine.ROOT / 'models', cfg['head_modes'],
                                cfg.get('head_models'))
    checks += rc
    info['models'] = ri
    checks += rel.scan_for_fuel_flag(scan_paths if scan_paths is not None else
                                     [engine.ROOT / 'tools', engine.ROOT / 'python', engine.ROOT / 'configs'])
    reference_status, reference_info = reference_checks()
    checks += reference_status
    info['references'] = reference_info
    if rebuild:
        stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
        rc2, ri2 = rebuild_check(zip_path, wasm_path, Path(work) if work else engine.ROOT / 'artifacts/tmp/H' / f'rebuild-{stamp}')
        checks += rc2
        info['rebuild'] = ri2
    else:
        checks.append(rel._chk('independent_rebuild_matches', False, 'skipped (--no-rebuild)'))
    return dict(passed=all(c['passed'] for c in checks), zip=str(zip_path), zip_sha256=engine.sha256(zip_path),
                wasm=str(wasm_path), wasm_sha256=engine.sha256(wasm_path), source=str(src_dir),
                source_tree_sha256=engine.tree_sha256(src_dir), cli_version=engine.cli_version(),
                checks=checks, info=info, submitted=False,
                verified_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--zip', required=True)
    ap.add_argument('--wasm', required=True)
    ap.add_argument('--src')
    ap.add_argument('--models')
    ap.add_argument('--out')
    ap.add_argument('--no-rebuild', action='store_true')
    a = ap.parse_args()
    doc = verify(a.zip, a.wasm, a.src, a.models, not a.no_rebuild)
    out = Path(a.out) if a.out else Path(a.zip).with_suffix('.verification.json')
    engine.write_json(out, doc)
    for c in doc['checks']:
        print(('PASS ' if c['passed'] else 'FAIL ') + c['name'] + ('' if c['passed'] else f"  {c['detail']}"))
    print('RELEASE VERIFY:', 'PASS' if doc['passed'] else 'FAIL', '->', out)
    sys.exit(0 if doc['passed'] else 1)


if __name__ == '__main__':
    main()
