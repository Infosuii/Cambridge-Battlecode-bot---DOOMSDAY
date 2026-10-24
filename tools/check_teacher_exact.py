"""Official byte-identity checkpoint; no matches, training or submission. Fails closed on build errors."""
import json
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
sys.path.insert(0, str(ROOT / 'tools'))
from nfs import engine
from install_models import install


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--src', default='bot/src')
    ap.add_argument('--out', default='evaluation/results/teacher_exact_checkpoint.json')
    args=ap.parse_args()
    source=(ROOT/args.src).resolve(); source.relative_to(ROOT)
    out=(ROOT/args.out).resolve(); out.relative_to(ROOT)
    source_sha = engine.tree_sha256(source)
    result = dict(label='teacher_exact official byte-identity checkpoint', source_sha256=source_sha,
                  expected_sha256=engine.sha256(ROOT / 'references/builds/original.wasm'), passed=False)
    try:
        dest=ROOT/'artifacts/tmp/teacher_exact_check'/source_sha[:16]
        engine.make_bot_dir(source,dest)
        install('teacher_exact',dest/'src',quiet=True)
        wasm=engine.official_build(dest,dest/'teacher_exact.wasm')
        result.update(wasm=str(wasm), actual_sha256=engine.sha256(wasm))
        result['passed'] = result['actual_sha256'] == result['expected_sha256']
    except Exception as exc:
        result['error'] = str(exc)
    engine.write_json(out, result)
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
