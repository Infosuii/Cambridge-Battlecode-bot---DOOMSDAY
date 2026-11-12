"""Patch a bot folder in place with V70_DRAFT_TABLE: a per-map lineup table (from tools/v67/c_draft_select.py) keyed by
what the draft turn can read (width, height, team size, camp-group count; unique across the 70 pool maps). A listed
map skips the learned draft and drafts that lineup exactly as the forced-lineup test bots did; other maps are unchanged.

Usage: c_v70_draft.py bots/v70 research/v70/draft_table.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    src = ROOT / sys.argv[1] / 'src'
    table = json.loads((ROOT / sys.argv[2]).read_text())['table']
    p = src / 'draft.cpp'
    c = p.read_bytes().decode()
    nl = '\r\n' if '\r\n' in c else '\n'
    assert 'v70_lineup' not in c
    rows = ''.join(f"        {{{t['key'][0]}, {t['key'][1]}, {t['key'][2]}, {t['key'][3]}, {t['lineup']}}}, // {m}{nl}"
                   for m, t in sorted(table.items()))
    func = (f'// V70_DRAFT_TABLE: lineup per pool map (research/v70/draft_table.json; key = width, height, team size, camp groups).{nl}'
            f'int v70_lineup(int w, int h, unsigned size, int groups) {{{nl}'
            f'#if V70_DRAFT_TABLE{nl}'
            f'    struct Row {{ int w, h; unsigned size; int groups, lineup; }};{nl}'
            f'    constexpr Row kRows[] = {{{nl}{rows}    }};{nl}'
            f'    for (const auto& r : kRows){nl}'
            f'        if (r.w == w && r.h == h && r.size == size && r.groups == groups) return r.lineup;{nl}'
            f'#else{nl}'
            f'    (void)w, (void)h, (void)size, (void)groups;{nl}'
            f'#endif{nl}'
            f'    return -1;{nl}'
            f'}}{nl}{nl}')
    anchor = 'void play_draft() {'
    assert c.count(anchor) == 1
    c = c.replace(anchor, func + anchor)
    # Compute the key once at the top of play_draft.
    top = anchor + nl + '    const auto chosen = bc::draft::current_draft(team::ally);' + nl
    assert c.count(top) == 1
    # size is read just below; compute the table lineup after it.
    size_read = ('    try {' + nl + '        size = bc::draft::team_size();' + nl + '    } catch (...) {' + nl + '    }' + nl)
    i = c.index(size_read, c.index(anchor))
    key = ('    int v70 = -1;' + nl + '    try {' + nl + '        std::uint32_t v70_ng = 0;' + nl +
           '        bc::detail::sdk_map_num_camp_groups(&v70_ng);' + nl +
           '        v70 = v70_lineup(bc::map::width(), bc::map::height(), size, static_cast<int>(v70_ng));' + nl +
           '    } catch (...) {' + nl + '        v70 = -1;' + nl + '    }' + nl)
    c = c[:i + len(size_read)] + key + c[i + len(size_read):]
    old_ml = '        ml_done = !known && ml_draft_pick(size);'
    assert c.count(old_ml) == 1
    c = c.replace(old_ml, '        ml_done = !known && v70 < 0 && ml_draft_pick(size);')
    old_mob = '            if (NOVA_ALL_LINEUP < 0 && needs_gap_crossings()) {'
    if c.count(old_mob) == 1:
        c = c.replace(old_mob, '            if (NOVA_ALL_LINEUP < 0 && v70 < 0 && needs_gap_crossings()) {')
    old_pick = '        if (li >= 0 && li < kNumLineups && pick_from(kLineups[li], chosen, skip)) return;'
    assert c.count(old_pick) == 1
    c = c.replace(old_pick, '        if (v70 >= 0) li = v70, skip = false;' + nl + old_pick)
    p.write_bytes(c.encode())
    cm = (src / 'common.h').read_bytes().decode()
    nl2 = '\r\n' if '\r\n' in cm else '\n'
    cm = ('#ifndef V70_DRAFT_TABLE // 1: per-map draft lineups for the pool maps (tools/v67/c_v70_draft.py).' + nl2 +
          '#define V70_DRAFT_TABLE 1' + nl2 + '#endif' + nl2) + cm
    (src / 'common.h').write_bytes(cm.encode())
    print('patched', src, len(table), 'maps')


if __name__ == '__main__':
    main()
