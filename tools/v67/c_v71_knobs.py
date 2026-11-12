"""Patch a bot folder in place with V71_MAP_KNOBS: a per-map strategy profile (lab knob values) applied at runtime.

The map is recognised on the first initialised turn by width, height, camp-group count and total camp-group gems (unique
across the 70 pool maps); its profile's knob values overwrite lab::knobs before the turn's knob block reads them.
Maps without an entry keep the build's own knobs.

Usage: c_v71_knobs.py bots/v71 research/v71/knob_table.json [--replace]   (--replace swaps an existing table)
The table JSON: {"table": {map: {"profile": name, "key": [w, h, size, groups, gems]}}}; profiles from c_profiles.py.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/v67'))
from c_profiles import deltas, vector  # noqa: E402


def main():
    bot = sys.argv[1]
    src = ROOT / bot / 'src'
    table = json.loads((ROOT / sys.argv[2]).read_text())['table']
    sets, rows, first = [], [], {}
    for name in sorted({t['profile'] for t in table.values()}):
        v = vector(bot, name)
        first[name] = (len(sets), len(deltas(name)))
        for i in sorted(deltas(name)):
            sets.append((i, v[i]))
    for m, t in sorted(table.items()):
        w, h, _size, groups, gems = t['key']
        f, n = first[t['profile']]
        rows.append(f'            {{{w}, {h}, {groups}, {gems}u, {f}, {n}}}, // {m}: {t["profile"]}')
    nl_probe = (src / 'bot.cpp').read_bytes().decode()
    nl = '\r\n' if '\r\n' in nl_probe else '\n'
    block = [
        '#if V71_MAP_KNOBS',
        '    // Per-map strategy profile (research/v71): the pool map is recognised once, on the first initialised turn.',
        '    if (!v71_done_ && inited) {',
        '        v71_done_ = true;',
        '        std::uint32_t total_gems = 0;',
        '        for (const auto& gr : w.groups) total_gems += gr.gems;',
        '        const int n_groups = static_cast<int>(w.groups.size());',
        '        struct KnobSet { int index; float value; };',
        '        struct MapRow { int w, h, groups; std::uint32_t gems; int first, count; };',
        '        static constexpr KnobSet kSets[] = {',
        *[f'            {{{i}, {v}f}},' for i, v in sets],
        '        };',
        '        static constexpr MapRow kRows[] = {',
        *rows,
        '        };',
        '        for (const auto& r : kRows)',
        '            if (r.w == w.width && r.h == w.height && r.groups == n_groups && r.gems == total_gems) {',
        '                for (int k = 0; k < r.count; ++k) lab::knobs[kSets[r.first + k].index] = kSets[r.first + k].value;',
        '                break;',
        '            }',
        '    }',
        '#endif',
    ]
    c = nl_probe
    anchor = '#if A2_LAB' + nl + '    {' + nl + '        // Engine-lab joint search (lab.h knobs'
    assert c.count(anchor) == 1
    if '--replace' in sys.argv:
        # Swap the table of a bot that already has one (bot.h / common.h already carry their parts).
        start = c.index('#if V71_MAP_KNOBS' + nl)
        end = c.index(anchor)
        assert start < end and c.count('#if V71_MAP_KNOBS' + nl) == 1
        c = c[:start] + nl.join(block) + nl + c[end:]
        (src / 'bot.cpp').write_bytes(c.encode())
        print('replaced table in', src, len(rows), 'maps,', len(sets), 'knob settings')
        return
    assert 'V71_MAP_KNOBS' not in c
    c = c.replace(anchor, nl.join(block) + nl + anchor)
    (src / 'bot.cpp').write_bytes(c.encode())
    h = (src / 'bot.h').read_bytes().decode()
    hn = '\r\n' if '\r\n' in h else '\n'
    marker = 'class Bot {' + hn + 'public:' + hn
    at = h.index('private:', h.index(marker))
    h = h[:at] + 'private:' + hn + '    bool v71_done_ = false; // V71_MAP_KNOBS applied' + hn + h[at + len('private:'):]
    (src / 'bot.h').write_bytes(h.encode())
    cm = (src / 'common.h').read_bytes().decode()
    cn = '\r\n' if '\r\n' in cm else '\n'
    cm = ('#ifndef V71_MAP_KNOBS // 1: per-map strategy profiles over the runtime lab knobs (tools/v67/c_v71_knobs.py).' + cn +
          '#define V71_MAP_KNOBS 1' + cn + '#endif' + cn) + cm
    (src / 'common.h').write_bytes(cm.encode())
    print('patched', src, len(rows), 'maps,', len(sets), 'knob settings')


if __name__ == '__main__':
    main()
