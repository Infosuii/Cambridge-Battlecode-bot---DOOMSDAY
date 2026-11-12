"""Islands stall, second pass: inside walk_toward / follow_field / try_dash for champions already stationary >= 30
rounds, log the field distance, candidate steps, bridge hold, dash candidate and use() result. Debug-only."""
from pathlib import Path
import sys, json, collections
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run
from project import ROOT, save
from sw08_followup import build_from, load, replace
from policy_rows import stdout
import trace_islands

G = 'static int dx_still = 0;\n#define DXT (dx_still >= 30 && dx_still <= 34)\n'

def trace(files):
    trace_islands.trace(files)
    c = files['bot.cpp'].decode()
    c = replace(c, '#include "a2stack.h"\n', '#include "a2stack.h"\n' + G)
    c = replace(c, '        if (pos == st_pos) ++st_n; else st_n = 0, st_pos = pos;\n',
                '        if (pos == st_pos) ++st_n; else st_n = 0, st_pos = pos;\n        dx_still = st_n;\n')
    # try_dash internals
    c = replace(c, '        if (here == kUnreach || (here < 3 && !bridge_next)) return false;\n',
                '        debug_block({ if (DXT) std::printf("TDA %d %d s%d here%d bridge%d save%d\\n", round, slot, s, static_cast<int>(here), bridge_next ? 1 : 0, travel_dash_ok() ? 1 : 0); });\n'
                '        if (here == kUnreach || (here < 3 && !bridge_next)) return false;\n')
    c = replace(c, '        if (best == pos) return false;\n        try {\n            if (bc::self().abilities()[s].use(best)) {',
                '        debug_block({ if (DXT) std::printf("TDB %d %d best%d,%d bestd%d\\n", round, slot, best.x, best.y, static_cast<int>(best_d)); });\n'
                '        if (best == pos) return false;\n        try {\n            if (bc::self().abilities()[s].use(best)) {')
    c = replace(c, '    if (allow_dash) try_dash(field, blocked);\n    const std::uint16_t here = fdist(field, pos);\n',
                '    debug_block({ if (DXT) { int r0 = -1, r1 = -1; for (int s = 0; s < 2; ++s) if (spells[s].kind == bc::ability_kind::dash) (s ? r1 : r0) = spell_ready(s) ? 1 : 0; std::printf("FF %d %d allow%d here%d ready%d,%d bh%d\\n", round, slot, allow_dash ? 1 : 0, static_cast<int>(fdist(field, pos)), r0, r1, bridge_hold); } });\n'
                '    if (allow_dash) try_dash(field, blocked);\n    const std::uint16_t here = fdist(field, pos);\n')
    c = replace(c, '    return follow_field(field, blocked, true);\n',
                '    debug_block({ if (DXT) std::printf("WT %d %d here%d boxed%d\\n", round, slot, static_cast<int>(fdist(field, pos)), walk_boxed ? 1 : 0); });\n'
                '    return follow_field(field, blocked, true);\n')
    c = replace(c, '            walk_unreachable = true;\n            return false;\n        }\n        ++rb::ran[rb::kWalkTerrain];',
                '            walk_unreachable = true;\n            debug_block({ if (DXT) std::printf("WTU %d %d\\n", round, slot); });\n            return false;\n        }\n        ++rb::ran[rb::kWalkTerrain];')
    files['bot.cpp'] = c.encode()

def main():
    build_from('dx07', 'hp01', trace, debug=True)
    pool = {m['name']: Path(m['file']) for m in load(ROOT / 'published-maps.json')}
    maps = [pool['01islands']]
    sched = [('dx07', o, str(maps[0]), s) for o, s in [('teammate_john_nnfinal', 'a'), ('ref_x1', 'a'), ('teammate_max_gx', 'a'), ('ref_x3ctr', 'a'), ('b111', 'b')]]
    rows = run('v118-islands-trace2', ['dx07'], maps, ['teammate_john_nnfinal', 'ref_x1', 'teammate_max_gx', 'ref_x3ctr', 'b111'], workers=8, debug=True, schedule=sched)
    out = {}
    for r in rows:
        lines = [l for l in stdout(r['replay_bundle'], r['side']).splitlines() if l.split(' ', 1)[0] in ('TDA', 'TDB', 'FF', 'WT', 'WTU', 'STILL')]
        out[r['opponent'] + r['side']] = lines[:80]
    save(HERE / 'islands-trace2.json', out)
    for k, v in out.items():
        print('==', k); print('\n'.join(v[:40]))

if __name__ == '__main__':
    main()
