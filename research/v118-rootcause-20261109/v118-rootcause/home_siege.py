"""Home siege: a gem group whose live camps can all be hit from our own spawn tiles is a sustainable crew job
(the spawn heals the crew while the camps hit it). Source edit shared by diagnostics and candidates."""
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from sw08_followup import replace

DECL = '    bool go_home_if_needed();\n'
DECL_NEW = DECL + '    bool home_siege();\n    int hs_find();\n    int hs_group = -2;\n    int hs_reach() const;\n'

DEFAULTS = '''
#ifndef HS_ON
#define HS_ON 1
#endif
#ifndef HS_SHARE
#define HS_SHARE 0.25f
#endif
#ifndef HS_CREW
#define HS_CREW 3
#endif
#ifndef HS_FROM
#define HS_FROM 0
#endif
#ifndef HS_TRACE
#define HS_TRACE 0
#endif
#ifndef HS_ENEMY
#define HS_ENEMY 8
#endif
'''

FUNCS = r'''
// HS (home siege, v118): a gem group whose every camp can be hit from one of our spawn tiles. The soak model ignores
// the spawn heal and always rated Homonoliths' 600-gem monolith groups "needs 7" (3 x 20,000 health, team of 4), so no
// job was ever opened while opponents cleared ours from their spawn by round ~320. A crew of HS_CREW slots stands on
// spawn tiles in range and attacks until the group dies; capture is left to the normal reward logic.
int Bot::hs_reach() const {
    int r = range;
    for (const auto& sp : spells)
        if (sp.present && sp.camps && (sp.kind == bc::ability_kind::damage || sp.kind == bc::ability_kind::aoe_damage))
            r = std::max(r, static_cast<int>(sp.range));
    return r;
}

int Bot::hs_find() {
    if (hs_group != -2) return hs_group;
    if (w.spawn_tiles.empty() || w.groups.empty() || w.camps.empty()) return -1;
    hs_group = -1;
    float total = 0.0f;
    for (const auto& g : w.groups) total += static_cast<float>(g.gems);
    std::uint32_t best = 0;
    for (std::size_t k = 0; k < w.groups.size(); ++k) {
        const auto& g = w.groups[k];
        if (g.gems == 0 || g.camps.empty() || g.harmless || static_cast<float>(g.gems) < HS_SHARE * total) continue;
        bool ok = true;
        for (int ci : g.camps) {
            int d = 1 << 20;
            for (vec2 s : w.spawn_tiles) d = std::min(d, cheb(s, w.camps[static_cast<std::size_t>(ci)].pos));
            ok = ok && d <= range;
        }
        if (ok && g.gems > best) best = g.gems, hs_group = static_cast<int>(k);
    }
    return hs_group;
}

bool Bot::home_siege() {
    if (!HS_ON || round < HS_FROM || slot >= HS_CREW) return false;
    const int gi = hs_find();
    if (gi < 0) return false;
    auto& g = w.groups[static_cast<std::size_t>(gi)];
    if (g.state != GroupState::alive) return false;
    for (const auto& e : w.enemies)
        if (cheb(e.pos, pos) <= HS_ENEMY) return false;
    int t = -1;
    float th = 1e30f;
    for (int ci : g.camps) {
        const auto& c = w.camps[static_cast<std::size_t>(ci)];
        if (c.dead) continue;
        if (c.hp < th) th = c.hp, t = ci;
    }
    if (t < 0) return false;
    const vec2 tp = w.camps[static_cast<std::size_t>(t)].pos;
    bc::bitboard stand;
    stand.clear();
    for (vec2 s : w.spawn_tiles)
        if (cheb(s, tp) <= range && !bit(w.static_blocked, s)) stand.set(s, true);
    if (stand.is_empty()) return false;
    mode = "home-siege";
    target_group = gi;
    write_claim(gi);
    if (!bit(stand, pos)) walk_toward(stand);
    bool hit = false;
    if (cheb(pos, tp) <= range && bit(w.visible, tp)) hit = attack_unit(w.camps[static_cast<std::size_t>(t)].camp, tp);
    if (!hit)
        for (int ci : g.camps) {
            const auto& c = w.camps[static_cast<std::size_t>(ci)];
            if (!c.dead && cheb(pos, c.pos) <= range && bit(w.visible, c.pos) && attack_unit(c.camp, c.pos)) {
                hit = true;
                break;
            }
        }
    if (!cast_done) cast_on_camp(t);
    if (HS_TRACE) debug_block({ if (round % 5 == 0 || hp < max_hp * 0.3f) std::printf("HS %d %d %s %d %d %.0f %.0f %d %d %d %.0f\n", round, slot, bc::to_string(type).c_str(), gi, t, static_cast<float>(hp), static_cast<float>(max_hp), pos.x, pos.y, hit ? 1 : 0, w.camps[static_cast<std::size_t>(t)].hp); });
    return true;
}

'''

ANCHOR_CALL = '    } else if (go_home_if_needed()) {\n'
CALL_NEW = '    } else if (home_siege()) {\n' + ANCHOR_CALL


def apply(files, crew=3, share=0.25, trace=False, extra=''):
    files['common.h'] = (f'#define HS_CREW {crew}\n#define HS_SHARE {share}f\n#define HS_TRACE {1 if trace else 0}\n{extra}'
                         + files['common.h'].decode() + DEFAULTS).encode()
    files['bot.h'] = replace(files['bot.h'].decode(), DECL, DECL_NEW).encode()
    c = files['bot.cpp'].decode()
    c = replace(c, 'bool Bot::go_home_if_needed() {\n', FUNCS + 'bool Bot::go_home_if_needed() {\n')
    c = replace(c, ANCHOR_CALL, CALL_NEW)
    if trace:
        c = replace(c, 'bool Bot::home_siege() {\n', 'bool Bot::home_siege() {\n    debug_block({ if (round <= 2) std::printf("SPAWNHEAL %.4f\\n", static_cast<float>(bc::constants::spawn_healing)); });\n')
    files['bot.cpp'] = c.encode()
