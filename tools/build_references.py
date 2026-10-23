"""Build the frozen reference opponents from their unchanged sources with the official CLI and record identities.

Sources are copies of: original (baseline/src of mld_fuel35_engine103.zip), v47 (opponents/v47-supplied/src),
first-hour release (release/bot_neural/src), version 50 (phase2-two-hours/release/bot_neural/src).
Copies are verified byte-identical to the previous experiment's files before building.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from nfs import engine  # noqa: E402

PREV = Path(engine.PATHS['previous_experiment'])
REFS = {
    'original': (engine.ROOT / 'references/original-src', PREV / 'baseline/src'),
    'v47': (engine.ROOT / 'references/v47-src', PREV / 'opponents/v47-supplied/src'),
    'first-hour': (engine.ROOT / 'references/first-hour-src', PREV / 'release/bot_neural/src'),
    'v50': (engine.ROOT / 'references/v50-src', PREV / 'phase2-two-hours/release/bot_neural/src'),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(engine.ROOT / 'references/builds'))
    args = ap.parse_args()
    out = Path(args.out)
    manifest = {'cli': engine.cli_version(), 'opponents': {}}
    for name, (copy, origin) in REFS.items():
        if engine.tree_sha256(copy) != engine.tree_sha256(origin):
            raise SystemExit(f'{name}: reference copy differs from its origin {origin}')
        bot_dir = out / name
        engine.make_bot_dir(copy, bot_dir)
        wasm = engine.official_build(bot_dir, out / f'{name}.wasm')
        manifest['opponents'][name] = dict(source=str(origin), source_tree_sha256=engine.tree_sha256(copy),
                                           wasm=str(wasm), wasm_sha256=engine.sha256(wasm),
                                           code_section_sha256=engine.code_section_sha(wasm))
        print(name, manifest['opponents'][name]['wasm_sha256'], flush=True)
    engine.write_json(out / 'manifest.json', manifest)


if __name__ == '__main__':
    main()
