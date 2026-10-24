"""Agent A: build the lab-strip scratch tree (patch 02) from ROOT/bot/src.

NN_STRIP_LAB (nn_config.h) = 0 keeps the original exactly. = 1 removes the inherited engine-lab host plumbing and keeps
the baked gameplay knobs (lab::knobs from A2_KNOBS) as compile-time constants:
  kept   (a) lab::knobs (A2_KNOBS values; becomes `inline constexpr`), every LABK(i) use, the knob blocks in
             play_turn / handle_enemies / tsearch, the A2_MID_W||A2_LAB middle-group table, the LABK(41) team-fight
             block (inert at knob 41 = 0).
  removed (b) the 12 lab_* Wasm exports (main.cpp), learner::w_lab and the learner residual (learner.h: identity at
             zero weights, but gather() costs fuel), lab::builds override in build_for, lab::ctl interventions and
             records (play_turn macro what-ifs + macro_feat, kinds 6/7, handle_enemies kinds 4/5, tribute kinds 2/3).
  untouched: A2_POLICY (pol_*) and A2_CAMPNET (cn_*, cn_log, cn_force) code, already compiled out (both macros 0).

    python tools/audit_strip_lab.py <dest_src_dir>
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = '#if A2_LAB && !NN_STRIP_LAB // engine-lab host control (NN_STRIP_LAB removes it; knobs stay)\n'


def edit(path: Path, fn) -> None:
    t = path.read_text(encoding='utf-8')
    t2 = fn(t)
    assert t2 != t, path
    path.write_text(t2, encoding='utf-8', newline='\n')


def strip(src: Path) -> None:
    # bot.cpp: gate the host-control blocks (line numbers of the original), include nn_config.h
    p = src / 'bot.cpp'
    lines = p.read_text(encoding='utf-8').splitlines(keepends=True)
    for ln in (56, 3525, 4036, 5994, 6149):
        assert lines[ln - 1] == '#if A2_LAB\n', (ln, lines[ln - 1])
        lines[ln - 1] = GATE
    for ln in (10, 2807, 5947):  # lab.h include, knob blocks: kept
        assert lines[ln - 1] == '#if A2_LAB\n', (ln, lines[ln - 1])
    assert lines[2] == '#include "bot.h"\n'
    lines.insert(3, '#include "nn_config.h"\n')
    p.write_text(''.join(lines), encoding='utf-8', newline='\n')

    # main.cpp: no lab_* exports
    edit(src / 'main.cpp', lambda t: t.replace('#include "draft.h"\n\n#if A2_LAB\n#include "learner.h"',
                                               '#include "draft.h"\n#include "nn_config.h"\n\n'
                                               '#if A2_LAB && !NN_STRIP_LAB // lab host exports (NN_STRIP_LAB removes them)\n'
                                               '#include "learner.h"', 1))

    # learner.h: the lab branch (host-written weights, gather/fix in score_groups) only without NN_STRIP_LAB
    edit(src / 'learner.h', lambda t: t.replace('#pragma once\n', '#pragma once\n#include "nn_config.h"\n', 1)
         .replace('namespace learner {\n#if A2_LAB\n', 'namespace learner {\n#if A2_LAB && !NN_STRIP_LAB // lab learner (NN_STRIP_LAB: the shipped identity)\n', 1))

    # lab.h: knobs become compile-time constants under NN_STRIP_LAB (same values)
    def lab(t: str) -> str:
        t = t.replace('#pragma once\n#include <cstdint>\n', '#pragma once\n#include <cstdint>\n\n#include "nn_config.h"\n', 1)
        old = ('#ifdef A2_KNOBS\ninline float knobs[kKnobs] = {A2_KNOBS}; // a search result baked into a build (comma-separated, missing = 0)\n'
               '#else\ninline float knobs[kKnobs] = {};\n#endif\n')
        assert old in t
        new = ('#if NN_STRIP_LAB // baked knobs as compile-time constants: gameplay values unchanged, no host can write them\n'
               '#ifdef A2_KNOBS\ninline constexpr float knobs[kKnobs] = {A2_KNOBS};\n#else\ninline constexpr float knobs[kKnobs] = {};\n#endif\n'
               '#else\n' + old + '#endif\n')
        return t.replace(old, new, 1)
    edit(src / 'lab.h', lab)


if __name__ == '__main__':
    dest = Path(sys.argv[1]).resolve()
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ROOT / 'bot' / 'src', dest, ignore=shutil.ignore_patterns('.cambc'))
    strip(dest)
    print('ok', dest)
