"""Islands stall trace: champions stationary for >= 25 rounds (alive, movable). Logs mode, target, walking distance to
the target group, distance to spawn, dash cooldowns, enemy count. Debug-only printf; no behavior change."""
from pathlib import Path
import sys, json, collections
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from local_panel import run
from project import ROOT, save
from sw08_followup import build_from, load, replace
from policy_rows import stdout

POST = r'''    PROF_CHECK("decide");
    debug_block({
        static vec2 st_pos{-9, -9};
        static int st_n = 0;
        if (pos == st_pos) ++st_n; else st_n = 0, st_pos = pos;
        if (st_n >= 25 && st_n % 25 == 0) {
            const int tg = target_group;
            const int gd = tg >= 0 && tg < static_cast<int>(w.groups.size()) && w.has_field(tg) ? w.group_distance(tg, pos) : -1;
            const int sd = static_cast<int>(fdist(w.spawn_field, pos));
            int bestd = 1 << 20, bestg = -1, alive_reach = 0;
            for (std::size_t k = 0; k < w.groups.size(); ++k) {
                if (!w.has_field(static_cast<int>(k))) continue;
                const int d = w.group_distance(static_cast<int>(k), pos);
                if (d < 100000) ++alive_reach;
                if (d < bestd) bestd = d, bestg = static_cast<int>(k);
            }
            std::printf("STILL %d %d %s %s %d %d %d %d %d %d %d %d %d %.0f %d %d %d %d %d\n", round, slot, bc::to_string(type).c_str(), mode, st_n, tg, gd,
                sd, bestg, bestd, alive_reach, static_cast<int>(w.groups.size()), static_cast<int>(w.fields_ready()), static_cast<float>(hp), gems,
                cooldown[0], cooldown[1], static_cast<int>(spells[0].kind), static_cast<int>(spells[1].kind));
        }
    });
'''

def trace(files):
    c = files['bot.cpp'].decode()
    c = replace(c, '    PROF_CHECK("decide");\n', POST)
    files['bot.cpp'] = c.encode()

def main():
    build_from('dx06', 'hp01', trace, debug=True)
    pool = {m['name']: Path(m['file']) for m in load(ROOT / 'published-maps.json')}
    maps = [pool[n] for n in pool if 'island' in n]
    print([m.stem for m in maps])
    opps = ['b111', 'nnm4', 'v92', 'ref_x1', 'ref_x3ctr', 'ref_p65pack', 'ref_hold_rush100', 'teammate_max_gx', 'teammate_john_nnfinal']
    rows = run('v118-islands-trace', ['dx06'], maps, opps, workers=16, debug=True)
    eps = []
    for r in rows:
        best = {}
        for l in stdout(r['replay_bundle'], r['side']).splitlines():
            if not l.startswith('STILL'): continue
            p = l.split()
            best[(p[2], p[3])] = p  # last line per champion = longest so far (approximate)
        for k, p in best.items():
            eps.append([r['map'], r['opponent'], r['side'], r['score']] + p[1:])
    eps.sort(key=lambda e: -int(e[8]))
    save(HERE / 'islands-trace.json', {'games': len(rows), 'score': sum(r['score'] for r in rows), 'episodes': eps})
    print(len(rows), sum(r['score'] for r in rows))
    for e in eps[:25]: print(' '.join(map(str, e)))

if __name__ == '__main__':
    main()
