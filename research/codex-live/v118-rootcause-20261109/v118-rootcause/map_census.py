"""Static census: which maps have a gem group that our spawn tiles can hit (home-siege geometry). Debug probe only."""
from pathlib import Path
import sys, json
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from local_panel import run
from project import ROOT, save
from sw08_followup import build_from, load, replace
from policy_rows import stdout
import home_siege

PROBE = r'''    if (round <= 2 && slot == 0) debug_block({
        float total = 0.0f;
        for (const auto& g : w.groups) total += static_cast<float>(g.gems);
        for (std::size_t k = 0; k < w.groups.size(); ++k) {
            const auto& g = w.groups[k];
            if (g.gems == 0 || g.camps.empty()) continue;
            int worst = 0;
            for (int ci : g.camps) {
                int d = 1 << 20;
                for (vec2 s : w.spawn_tiles) d = std::min(d, cheb(s, w.camps[static_cast<std::size_t>(ci)].pos));
                worst = std::max(worst, d);
            }
            std::printf("HSMAP %d %zu %u %.3f %d %d %d %.0f %d\n", round, k, g.gems, g.gems / std::max(1.0f, total), worst, g.harmless ? 1 : 0, range, g.max_hp, static_cast<int>(g.camps.size()));
        }
    });
'''

def probe(files):
    home_siege.apply(files, crew=0, trace=False)
    c = files['bot.cpp'].decode()
    files['bot.cpp'] = replace(c, 'bool Bot::home_siege() {\n', 'bool Bot::home_siege() {\n' + PROBE).encode()

def main():
    build_from('dx04', 'hp01', probe, debug=True)
    maps = [Path(m['file']) for m in load(ROOT / 'published-maps.json')]
    cells = [('dx04', 'b111', str(m), 'a') for m in maps]
    rows = run('v118-hs-census', ['dx04'], maps, ['b111'], workers=14, debug=True, schedule=cells)
    out = {}
    for r in rows:
        lines = [l.split() for l in stdout(r['replay_bundle'], 'a').splitlines() if l.startswith('HSMAP')]
        seen = {}
        for p in lines:
            if len(p) != 10: continue
            seen[int(p[2])] = dict(gems=int(p[3]), share=float(p[4]), spawn_dist=int(p[5]), harmless=int(p[6]), range=int(p[7]), hp=float(p[8]), camps=int(p[9]))
        out[r['map']] = {'groups': seen, 'score': r['score']}
    save(HERE / 'hs-census.json', out)
    hits = {m: {k: g for k, g in v['groups'].items() if g['spawn_dist'] <= 4 and g['share'] >= 0.1} for m, v in out.items()}
    for m, h in sorted(hits.items()):
        if h: print(m, h)

if __name__ == '__main__':
    main()
