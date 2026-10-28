"""Patch a bot folder in place with the v69 idle fixes (each behind its own switch in common.h).

V69_ISLAND 1: walk_toward finds no walking route and we stand where walking cannot reach our spawn (a hole island we
  dashed onto: 01big-world Vesper stood at (28,19) from round 70 to 1300 with the shore two tiles away). Dash to the
  reachable tile that is closest to spawn, or recall when no dash is ready.
V69_CAPTURE_STALL N: a capture has not paid out after N rounds on the reward region. With a visible enemy on or beside
  the region and at least as many of us there, attack it; otherwise give the group up for 80 rounds (2.5N rounds when
  no enemy is visible). 00vault: both teams held the 49-camp reward region from round 600 to 2000 without fighting.

Usage: c_v69_fixes.py bots/v69
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ISLAND = r'''
#if V69_ISLAND
// Stranded on a hole island (walking cannot reach our spawn from here): dash to the reachable tile closest to spawn,
// or recall. Returns true when it acted.
bool Bot::escape_island() {
    if (bit(w.ally_spawn, pos) || fdist(w.spawn_field, pos) != kUnreach) return false;
    auto& me = bc::self();
    for (int s = 0; s < 2; ++s) {
        if (!spell_ready(s) || spells[s].kind != bc::ability_kind::dash) continue;
        const int reach = std::max(1, static_cast<int>(spells[s].range));
        const bc::bitboard blocked = w.static_blocked | w.unit_tiles;
        vec2 best = pos;
        int best_d = kUnreach;
        for (int dy = -reach; dy <= reach; ++dy)
            for (int dx = -reach; dx <= reach; ++dx) {
                const vec2 q{pos.x + dx, pos.y + dy};
                if (!in_bounds(q, w.width, w.height) || bit(blocked, q)) continue;
                const int d = fdist(w.spawn_field, q);
                if (d < best_d) best_d = d, best = q;
            }
        if (best == pos) break;
        try {
            if (me.abilities()[s].use(best)) {
                pos = best;
                cast_done = true;
                mode = "island-dash";
                return true;
            }
        } catch (const std::exception& e) {
            LOG("island dash error %s\n", e.what());
        }
    }
    try {
        if (!me.state().contains(bc::champion_state::recalling)) me.recall();
        mode = "island-recall";
        return true;
    } catch (const std::exception& e) {
        LOG("island recall error %s\n", e.what());
    }
    return false;
}
#endif
'''

STALL = r'''        if (bit(g.tiles, pos)) {
#if V69_CAPTURE_STALL
            // A capture pays out five rounds after the region is ours alone. Still holding long after that means an enemy
            // contests it (00vault: both teams stood on the reward region for 1,400 rounds): fight for it with the
            // numbers, or leave it.
            const int cap_gi = static_cast<int>(&g - &w.groups[0]);
            if (cap_group_ != cap_gi) cap_group_ = cap_gi, cap_since_ = round;
            if (round - cap_since_ > V69_CAPTURE_STALL) {
                bc::bitboard near;
                near.clear();
                for (int ci : g.camps) near.draw_chebyshev(w.camps[ci].pos, 1.0f);
                const EnemyRec* foe = nullptr;
                int theirs = 0;
                for (const auto& e : w.enemies)
                    if (bit(near, e.pos)) {
                        ++theirs;
                        if (!foe || cheb(e.pos, pos) < cheb(foe->pos, pos)) foe = &e;
                    }
                int ours = 1;
                for (const auto& a : w.allies) ours += a.id != my_id && bit(near, a.pos);
                if (foe && ours >= theirs) {
                    mode = "capture-contest";
                    cast_on_enemy(*foe);
                    if (cheb(foe->pos, pos) <= range) {
                        if (attack_unit(foe->unit, foe->pos)) use_reset_and_attack(foe->unit, foe->pos);
                    } else {
                        bc::bitboard goal;
                        goal.clear();
                        goal.draw_chebyshev(foe->pos, static_cast<float>(range));
                        walk_toward(goal);
                        if (cheb(foe->pos, pos) <= range) attack_unit(foe->unit, foe->pos);
                    }
                    return true;
                }
                if (foe || round - cap_since_ > (5 * V69_CAPTURE_STALL) / 2) {
                    if (static_cast<std::size_t>(cap_gi) < avoid_until.size()) avoid_until[cap_gi] = round + 80;
                    cap_group_ = -1;
                    mode = "capture-leave";
                    return false;
                }
            }
#endif
            return true; // capturing: hold position
        }
#if V69_CAPTURE_STALL
        cap_group_ = -1;
#endif
'''


def main():
    src = ROOT / sys.argv[1] / 'src'
    h = (src / 'bot.h').read_bytes().decode()
    nl = '\r\n' if '\r\n' in h else '\n'
    assert 'escape_island' not in h
    marker = 'class Bot {' + nl + 'public:' + nl
    at = h.index('private:', h.index(marker))
    fields = ('private:' + nl + '    // v69 idle fixes (V69_ISLAND, V69_CAPTURE_STALL).' + nl +
              '    bool escape_island();' + nl +
              '    int cap_group_ = -1, cap_since_ = 0;' + nl)
    h = h[:at] + fields + h[at + len('private:'):]
    (src / 'bot.h').write_bytes(h.encode())

    c = (src / 'bot.cpp').read_bytes().decode()
    nl = '\r\n' if '\r\n' in c else '\n'
    # 1. Island escape inside walk_toward, wherever the terrain-only search also fails.
    start = c.index('bool Bot::walk_toward(const bc::bitboard& goals_in) {')
    end = c.index('\n}', start)
    body = c[start:end]
    hits = body.count('walk_unreachable = true;')
    assert hits >= 1
    body = body.replace('walk_unreachable = true;', '#if V69_ISLAND' + nl +
                        '            if (escape_island()) return true;' + nl + '#endif' + nl +
                        '            walk_unreachable = true;')
    c = c[:start] + body + c[end:]
    c = c.replace('bool Bot::walk_toward(const bc::bitboard& goals_in) {',
                  ISLAND.replace('\n', nl) + nl + 'bool Bot::walk_toward(const bc::bitboard& goals_in) {', 1)
    # 2. Capture stall breaker in farm()'s reward case.
    old = ('        mode = "capture";' + nl + '        if (bit(g.tiles, pos)) return true; // capturing: hold position' + nl)
    assert c.count(old) == 1
    c = c.replace(old, '        mode = "capture";' + nl + STALL.replace('\n', nl))
    (src / 'bot.cpp').write_bytes(c.encode())

    cm = (src / 'common.h').read_bytes().decode()
    nl = '\r\n' if '\r\n' in cm else '\n'
    assert 'V69_ISLAND' not in cm
    cm = ('#ifndef V69_ISLAND // 1: stranded on a hole island, dash back to walkable ground or recall.' + nl +
          '#define V69_ISLAND 1' + nl + '#endif' + nl +
          '#ifndef V69_CAPTURE_STALL // rounds on a reward region before a stalled capture is fought for or left (0 off).' + nl +
          '#define V69_CAPTURE_STALL 15' + nl + '#endif' + nl) + cm
    (src / 'common.h').write_bytes(cm.encode())
    print('patched', src, 'island hooks', hits)


if __name__ == '__main__':
    main()
