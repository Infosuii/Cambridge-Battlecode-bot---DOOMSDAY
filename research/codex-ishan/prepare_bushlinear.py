"""Prepare EXP-009 and separate native equivalence/reproducibility builds."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'artifacts/codex-p0'
candidate = ROOT / 'bots/codex-bushlinear'
shutil.copytree(ROOT / 'bots/v92/src', candidate / 'src')

def edit(name, old, new):
    p = candidate / 'src' / name
    b = p.read_bytes()
    if b'\r\n' in b:
        old, new = (v.replace('\n', '\r\n') for v in (old, new))
    assert b.count(old.encode()) == 1, old
    p.write_bytes(b.replace(old.encode(), new.encode(), 1))

header = candidate / 'src/common.h'
header.write_bytes(b'#ifndef CODEX_BUSH_LINEAR\n#define CODEX_BUSH_LINEAR 1\n#endif\n' + header.read_bytes())
(candidate / 'src/codex_bush.h').write_text('''#pragma once
#include <cstdint>
#include <vector>

namespace codex_bush {
// SDK packed row-major bits, verified against is_set on the native engine.
inline bool bit(const std::vector<std::uint8_t>& mask, int i) {
    return (mask[static_cast<std::size_t>(i) >> 3] & (1u << (i & 7))) != 0;
}
inline void mark(std::vector<std::uint8_t>& mask, int i) {
    mask[static_cast<std::size_t>(i) >> 3] |= static_cast<std::uint8_t>(1u << (i & 7));
}
inline void fill(int width, int height, const std::vector<std::uint8_t>& bush,
                 std::vector<std::uint8_t>& seen, std::uint16_t* labels,
                 std::uint16_t id, int root, std::vector<int>& stack) {
    stack.clear();
    mark(seen, root);
    stack.push_back(root);
    while (!stack.empty()) {
        const int at = stack.back();
        stack.pop_back();
        labels[at] = id;
        const int x = at % width, y = at / width;
        const int x0 = x > 0 ? x - 1 : 0, x1 = x + 1 < width ? x + 1 : x;
        const int y0 = y > 0 ? y - 1 : 0, y1 = y + 1 < height ? y + 1 : y;
        for (int yy = y0; yy <= y1; ++yy) for (int xx = x0; xx <= x1; ++xx) {
            const int next = yy * width + xx;
            if (!bit(bush, next) || bit(seen, next)) continue;
            mark(seen, next);
            stack.push_back(next);
        }
    }
}
} // namespace codex_bush
''', encoding='utf8', newline='\n')
edit('world.h', '    int bush_clusters = 0;', '''    int bush_clusters = 0;
#if CODEX_BUSH_LINEAR
    std::vector<std::uint8_t> codex_bush_bits, codex_bush_seen;
    std::vector<int> codex_bush_stack;
#endif''')
edit('world.cpp', '#include "world.h"', '''#include "world.h"
#if CODEX_BUSH_LINEAR
#include "codex_bush.h"
#endif''')
edit('world.cpp', '        const auto id = static_cast<std::uint16_t>(bush_clusters++);', '''        const auto id = static_cast<std::uint16_t>(bush_clusters++);
#if CODEX_BUSH_LINEAR
        if (codex_bush_bits.empty()) {
            codex_bush_bits = bushes.export_linear_buffer();
            codex_bush_seen.assign(codex_bush_bits.size(), 0);
            codex_bush_stack.reserve(static_cast<std::size_t>(width * height));
        }
        codex_bush::fill(width, height, codex_bush_bits, codex_bush_seen,
                         bush_label.get(), id, p.y * width + p.x, codex_bush_stack);
        bush_labeled.import_linear_buffer(codex_bush_seen);
#else''')
# Close the alternate implementation before the outer lazy-label condition ends.
edit('world.cpp', '''        }
    }
    return bush_label[static_cast<std::size_t>(p.y * width + p.x)];''', '''        }
#endif
    }
    return bush_label[static_cast<std::size_t>(p.y * width + p.x)];''')
for name in ('bushlinear-rebuild', 'bushlinear-off', 'bushlinear-check'):
    dst = CACHE / name / 'src'
    shutil.copytree(candidate / 'src', dst)
    if name.endswith('-off'):
        p = dst / 'common.h'
        p.write_bytes(p.read_bytes().replace(b'#define CODEX_BUSH_LINEAR 1', b'#define CODEX_BUSH_LINEAR 0', 1))
print('Prepared candidate, independent rebuild, off control and fixture copy.')
