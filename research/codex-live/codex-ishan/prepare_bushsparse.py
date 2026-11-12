"""Prepare EXP-010 independently from frozen EXP-009."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'artifacts/codex-p0'
candidate = ROOT / 'bots/codex-bushsparse'
shutil.copytree(ROOT / 'bots/codex-bushlinear/src', candidate / 'src')
p = candidate / 'src/codex_bush.h'
b = p.read_bytes()
b = b.replace(b'#include <vector>', b'#include <vector>\n#include "cambc.h"', 1)
old = b'std::uint16_t id, int root, std::vector<int>& stack) {'
new = b'std::uint16_t id, int root, std::vector<int>& stack, cambc::bitboard* publish = nullptr) {'
assert b.count(old) == 1
b = b.replace(old, new, 1)
old = b'        const int x = at % width, y = at / width;'
assert b.count(old) == 1
b = b.replace(old, old + b'\n        if (publish) publish->set({x, y}, true);', 1)
p.write_bytes(b)
p = candidate / 'src/world.cpp'
b = p.read_bytes()
old = b'bush_label.get(), id, p.y * width + p.x, codex_bush_stack);'
assert b.count(old) == 1
b = b.replace(old, b'bush_label.get(), id, p.y * width + p.x, codex_bush_stack, &bush_labeled);', 1)
b = b.replace(b'        bush_labeled.import_linear_buffer(codex_bush_seen);', b'        // The fill publishes only this component, avoiding a full-map copy.', 1)
p.write_bytes(b)
for name in ('bushsparse-rebuild', 'bushsparse-off', 'bushsparse-check'):
    dst = CACHE / name / 'src'
    shutil.copytree(candidate / 'src', dst)
    if name.endswith('-off'):
        p = dst / 'common.h'
        p.write_bytes(p.read_bytes().replace(b'#define CODEX_BUSH_LINEAR 1', b'#define CODEX_BUSH_LINEAR 0', 1))

# Exact sparse publication in the equivalence fixture; frozen original stays intact.
fixture = (ROOT / 'research/codex-ishan/bush_equivalence.cpp').read_text()
fixture = fixture.replace('    int components = 0;', '    bc::bitboard restored;\n    restored.clear();\n    int components = 0;')
fixture = fixture.replace('i, stack);', 'i, stack, &restored);')
fixture = fixture.replace('    bc::bitboard restored;\n    restored.import_linear_buffer(seen);\n', '')
dst = CACHE / 'bushsparse-check/src'
(dst / 'codex_equivalence.h').write_text(fixture, encoding='utf8', newline='\n')
p = dst / 'main.cpp'
b = p.read_bytes().replace(b'#include "draft.h"', b'#include "draft.h"\n#include "codex_equivalence.h"', 1)
old = b'                play_draft();'
assert b.count(old) == 1
p.write_bytes(b.replace(old, b'                static bool checked = false;\n                if (!checked) { checked = true; codex_check_components(); }\n' + old, 1))
print('Prepared sparse candidate, two controls and exact-publication fixture.')
