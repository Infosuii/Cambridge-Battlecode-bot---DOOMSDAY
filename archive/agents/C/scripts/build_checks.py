"""Agent C build checks (scratch only, under artifacts/tmp/C): with NN_ANY_HEAD == 0 the Wasm code section must equal
references/builds/original.wasm.

  A  lead-owned sources of bot/src + nn_config.h + agent C's files only (isolates C's contribution)
  B  a snapshot of the whole current bot/src (whatever the other agents have landed so far)

Writes archive/agents/C/evidence/build_checks.json.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine  # noqa: E402

C_FILES = ['nn_schema.h', 'nn_obs.h', 'nn_obs.cpp', 'nn_obs_glue.cpp']
TMP = ROOT / 'artifacts' / 'tmp' / 'C'


def tree(name: str, files: list[Path]) -> Path:
    dest = TMP / name / 'bot'
    if (dest / 'src').exists():
        shutil.rmtree(dest / 'src')
    (dest / 'src').mkdir(parents=True)
    for p in files:
        shutil.copy2(p, dest / 'src' / p.name)
    return dest


def main() -> int:
    src = ROOT / 'bot' / 'src'
    lead = [p for p in src.iterdir() if p.is_file() and not p.name.startswith('nn_')]
    mine = [src / n for n in C_FILES] + [src / 'nn_config.h']
    every = [p for p in src.iterdir() if p.is_file()]
    ref = engine.code_section_sha(ROOT / 'references' / 'builds' / 'original.wasm')
    out = {'reference': 'references/builds/original.wasm', 'reference_code_sha': ref, 'builds': []}
    for name, files in (('build_c_only', lead + mine), ('build_snapshot', every)):
        bot = tree(name, files)
        wasm = engine.official_build(bot, TMP / name / 'bot.wasm')
        sha = engine.code_section_sha(wasm)
        out['builds'].append({'name': name, 'files': sorted(p.name for p in files), 'code_sha': sha,
                              'identical_code_section': sha == ref, 'wasm_sha256': engine.sha256(wasm)})
        print(name, 'identical' if sha == ref else 'DIFFERENT', sha)
    engine.write_json(ROOT / 'agents' / 'C' / 'evidence' / 'build_checks.json', out)
    return 0 if all(b['identical_code_section'] for b in out['builds']) else 1


if __name__ == '__main__':
    sys.exit(main())
