"""Agent A: build the fuel-routing scratch tree (patch 01) from ROOT/bot/src.

Every bc::fuel_remaining() (and rb::left()) that gates a teacher decision is routed through nnb::teacher_left()
(nn_budget.h). Instrumentation-only reads (APEX_PROFILE / A2_TEL / APEX_ESC* / APEX_TSLOG / LOG prints) are left on
the raw engine value on purpose: they measure real fuel and are compiled out of this build.

    python tools/audit_fuel_routing.py <dest_src_dir>
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = 'bc::fuel_remaining()'
NEW = 'nnb::teacher_left()'

# file -> list of (1-based line, number of occurrences to replace on that line: 'all' or int)
SITES: dict[str, list[tuple[int, object]]] = {
    'bot.cpp': [(702, 'all'), (1003, 'all'), (1064, 'all'), (2323, 1), (3258, 'all'), (4868, 'all'), (4869, 'all'),
                (5142, 'all'), (5186, 'all'), (5265, 'all'), (5369, 'all'), (5455, 'all'), (5456, 'all'), (5639, 'all'),
                (5640, 'all'), (5814, 'all'), (5829, 'all'), (5832, 'all'), (5834, 'all'), (5836, 'all'), (6349, 'all'),
                (6352, 'all')],
    'tsearch.cpp': [(124, 'all'), (447, 'all'), (532, 'all'), (560, 'all'), (571, 'all'), (797, 'all'), (805, 'all'),
                    (906, 'all'), (939, 'all'), (952, 'all'), (994, 'all'), (1033, 'all'), (1044, 'all')],
    'world.cpp': [(643, 'all')],
    'draft.cpp': [(542, 'all')],
}
# Instrumentation reads deliberately left raw (documented in AUDIT.md / REPORT.md).
LEFT_RAW = {
    'bot.cpp': [1917, 1980, 2325, 2330, 2333, 2334, 5460, 6518],
    'tsearch.cpp': [609, 778, 931, 963, 1127],
    'world.cpp': [43, 47, 48, 189],
    'common.h': [658, 667, 960, 961, 978, 986, 1016, 1017, 1030],
}
INCLUDE_AFTER = {  # file -> (anchor line text, include line inserted after it)
    'bot.cpp': ('#include "runtime_budget.h"\n', '#include "nn_budget.h"\n'),
    'tsearch.cpp': None,  # resolved below: after its first #include line
    'world.cpp': None,
    'draft.cpp': None,
}


def route(src: Path) -> dict:
    report = {}
    for name, sites in SITES.items():
        p = src / name
        lines = p.read_text(encoding='utf-8').splitlines(keepends=True)
        count = 0
        for ln, how in sites:
            text = lines[ln - 1]
            if RAW not in text:
                raise SystemExit(f'{name}:{ln}: expected {RAW!r}, got {text!r}')
            n = text.count(RAW) if how == 'all' else int(how)
            lines[ln - 1] = text.replace(RAW, NEW, n)
            count += n
        for ln in LEFT_RAW.get(name, []):
            if RAW not in lines[ln - 1]:
                raise SystemExit(f'{name}:{ln}: expected a raw instrumentation read')
        # include nn_budget.h (line numbers above are pre-insertion, so insert last)
        anchor = INCLUDE_AFTER.get(name)
        if anchor:
            idx = lines.index(anchor[0])
        else:
            idx = next(i for i, t in enumerate(lines) if t.startswith('#include "'))
        lines.insert(idx + 1, '#include "nn_budget.h"\n')
        p.write_text(''.join(lines), encoding='utf-8', newline='\n')
        remaining = sum(t.count(RAW) for t in lines)
        report[name] = {'routed': count, 'raw_left': remaining}
    # runtime_budget.h: rb::left() is the governor's only fuel read
    p = src / 'runtime_budget.h'
    t = p.read_text(encoding='utf-8')
    old = 'inline std::uint64_t left() { return bc::fuel_remaining(); }'
    assert t.count(old) == 1
    t = t.replace(old, 'inline std::uint64_t left() { return nnb::teacher_left(); } // teacher fuel view (nn_budget.h)')
    t = t.replace('#include "common.h"\n', '#include "common.h"\n#include "nn_budget.h"\n', 1)
    p.write_text(t, encoding='utf-8', newline='\n')
    report['runtime_budget.h'] = {'routed': 1, 'raw_left': t.count(RAW)}
    return report


if __name__ == '__main__':
    dest = Path(sys.argv[1]).resolve()
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ROOT / 'bot' / 'src', dest, ignore=shutil.ignore_patterns('.cambc'))
    import json
    print(json.dumps(route(dest), indent=1))
