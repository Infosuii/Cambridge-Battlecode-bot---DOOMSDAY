"""Swirl-style contact trace: a champion with >=3 enemies within 7 and no visible ally within 6 that ends its turn
closer to the nearest enemy. Logs the final mode (the branch that ran) and whether combat (handle_enemies) claimed
the turn. Debug-only printf; no behavior change."""
from pathlib import Path
import sys, json, collections
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from local_panel import run
from project import ROOT, save
from sw08_followup import build_from, load, replace
from policy_rows import stdout

PRE = '    const vec2 ox_pos0 = pos;\n    const float ox_hp0 = hp;\n    const bool fought ='
POST = r'''    PROF_CHECK("decide");
    debug_block({
        int n7 = 0, d0 = 99, d1 = 99, a6 = 0;
        float ehp = 0.0f;
        for (const auto& e : w.enemies) {
            const int a = cheb(e.pos, ox_pos0);
            if (a <= 7) ++n7, ehp += e.hp;
            d0 = std::min(d0, a);
            d1 = std::min(d1, cheb(e.pos, pos));
        }
        for (const auto& al : w.allies) a6 += cheb(al.pos, ox_pos0) <= 6;
        if (n7 >= 2 && n7 >= a6 + 2 && d1 < d0)
            std::printf("OUTN %d %d %s %s %d %d %d %d %d %.0f %.0f %.0f %d %d\n", round, slot, bc::to_string(type).c_str(), mode, fought ? 1 : 0,
                n7, a6, d0, d1, static_cast<float>(ox_hp0), static_cast<float>(max_hp), ehp, gems, target_group);
    });
'''

def trace(files):
    c = files['bot.cpp'].decode()
    c = replace(c, '    const bool fought =', PRE)
    c = replace(c, '    PROF_CHECK("decide");\n', POST)
    files['bot.cpp'] = c.encode()

def main():
    build_from('dx05', 'hp01', trace, debug=True)
    pool = {m['name']: Path(m['file']) for m in load(ROOT / 'published-maps.json')}
    maps = [pool[n] for n in ('00swirl', '01elk_arena', '03ambush_field', '03membrane', '04dunes')]
    rows = run('v118-outnumbered-trace', ['dx05'], maps, ['ref_x1', 'teammate_john_nnfinal', 'nnm4', 'teammate_max_gx'], workers=14, debug=True)
    modes = collections.Counter(); modes3 = collections.Counter(); by_map = collections.Counter(); examples = []
    for r in rows:
        for l in stdout(r['replay_bundle'], r['side']).splitlines():
            if not l.startswith('OUTN'): continue
            p = l.split(); n7 = int(p[6])
            key = (p[4], p[5]); modes[key] += 1
            if n7 >= 3: modes3[key] += 1
            by_map[r['map']] += 1
            if n7 >= 3 and len(examples) < 40: examples.append([r['map'], r['opponent'], r['side']] + p[1:])
    res = {'games': len(rows), 'score': sum(r['score'] for r in rows), 'modes_n2': [[*k, v] for k, v in modes.most_common(25)],
           'modes_n3': [[*k, v] for k, v in modes3.most_common(25)], 'by_map': dict(by_map), 'examples': examples}
    save(HERE / 'outnumbered-trace.json', res)
    print(json.dumps({k: res[k] for k in ('games', 'score', 'modes_n2', 'modes_n3', 'by_map')}))

if __name__ == '__main__':
    main()
