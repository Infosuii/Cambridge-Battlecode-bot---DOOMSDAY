"""v118 candidate source transforms on frozen v117 (hp01). Each is isolated and combinable.

H  home siege (Homonoliths): crew of 3 attacks a >=25%-gem group reachable from our spawn tiles, on spawn (heal 1.0).
D  bridge dash: when the walk field has no walking step at a hole bridge, accept a dash that improves it by >= 1
   (chained diagonal bridges make the true landing only 1 better; try_dash required 2 and the champion idled).
R  route veto: approach-stall / unreachable cooldowns also veto the neural target override (sw08 rv10 route repair).
N  A3_NUMBERS 1: never commit to a champion fight while local foes outnumber local friends (existing, compiled off).
O  APEX_OUTNUMBERED 2: leave when enemies within 8 exceed healthy friends within 5 by 2 (existing, compiled off).
"""
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from sw08_followup import build_from, replace
import home_siege
from sw08_v113_minimal import repair


def edit_H(files, crew=3):
    home_siege.apply(files, crew=crew, trace=False)


def edit_D(files):
    h = files['bot.h'].decode()
    files['bot.h'] = replace(h, '    int bridge_hold = 0;', '    bool dash_relax = false; // v118 D: accept a 1-step field gain at a stuck bridge\n    int bridge_hold = 0;').encode()
    c = files['bot.cpp'].decode()
    c = replace(c, 'if (dq + 1 < best_d) {', 'if (dq + (dash_relax ? 0 : 1) < best_d) {')
    c = replace(c, '    if (n == 0 && w.bridges_on && !walked && bridge_hold < 12)',
                '''    if (n == 0 && w.bridges_on && allow_dash && !walked) {
        // v118 D: no walking step forward at a hole bridge. Chained diagonal bridge tiles let the field run along
        // the holes, so the real landing is only one step better than here and the strict dash never fired
        // (Islands: Vesper, Heart and Issac idled 125-500 rounds beside a crossing with the dash ready).
        dash_relax = true;
        const bool jumped = try_dash(field, blocked);
        dash_relax = false;
        if (jumped) {
            bridge_hold = 0;
            return true;
        }
    }
    if (n == 0 && w.bridges_on && !walked && bridge_hold < 12)''')
    files['bot.cpp'] = c.encode()


def edit_R(files):
    repair(files, True, False)


def edit_N(files):
    files['common.h'] = replace(files['common.h'].decode(), '#define A3_NUMBERS 0', '#define A3_NUMBERS 1').encode()


def edit_O(files):
    files['common.h'] = (b'#define APEX_OUTNUMBERED 2\n' + files['common.h'])


EDITS = {'H': edit_H, 'D': edit_D, 'R': edit_R, 'N': edit_N, 'O': edit_O}


def compose(letters):
    def edit(files):
        for ch in letters:
            EDITS[ch](files)
    return edit


def build(name, letters, debug=False, parent='hp01'):
    build_from(name, parent, compose(letters), debug=debug)
    return name


ARMS = {'v18H': 'H', 'v18D': 'D', 'v18R': 'R', 'v18DR': 'DR', 'v18N': 'N', 'v18O': 'O', 'v18HDR': 'HDR'}

if __name__ == '__main__':
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        print(list(pool.map(lambda kv: build(*kv), ARMS.items())))


LONE = '''    {
        // v118 L: a lone champion (no healthy ally within 6) facing three or more live enemies within 7 does not commit
        // unless the kill is certain. Swirl ladder loss: Varg advanced on four enemies with no ally near and died; local
        // trace: outnumbered fight-champ advances died within 15 rounds 26% of the time (approach/join 4-9%).
        int lone_friends = 1, lone_foes = 0;
        for (const auto& a : w.allies) lone_friends += cheb(a.pos, pos) <= 6 && a.hp >= 0.4f * a.max_hp;
        for (const auto& e : w.enemies) {
            if (e.hp <= 0) continue;
            const int d = cheb(e.pos, pos);
            if (d > 7 || (bit(w.enemy_spawn, e.pos) && d > e.range + 2)) continue;
            ++lone_foes;
        }
        if (lone_friends == 1 && lone_foes >= LONE_FOES && !(target && target_ttk <= 1.0f) && winning) {
            winning = false;
            if (nearest_d <= 6) {
                in_danger = true;
                if (threat_on_me <= 0) threat_on_me = 1.0f;
            }
        }
    }
#if A3_NUMBERS || A3_BACKOFF
'''


def edit_L(files, foes=3):
    files['common.h'] = (f'#define LONE_FOES {foes}\n'.encode() + files['common.h'])
    files['bot.cpp'] = replace(files['bot.cpp'].decode(), '#if A3_NUMBERS || A3_BACKOFF\n', LONE).encode()


EDITS['L'] = edit_L


CS_DEFAULTS = '''
#ifndef CS_FLEE
#define CS_FLEE 1
#endif
#ifndef CS_ESCAPE
#define CS_ESCAPE 1
#endif
#ifndef CS_FLEE_W
#define CS_FLEE_W 600.0f
#endif
#ifndef CS_SDK_AWAKE
#define CS_SDK_AWAKE 0
#endif
'''


CRLF, LF = chr(13) + chr(10), chr(10)


def edit_C(files):
    """Camp safety: camp damage in the flee step and a damage-minimising home-escape step (with dash)."""
    files['common.h'] = (files['common.h'].decode() + CS_DEFAULTS).encode()
    h = files['bot.h'].decode().replace(CRLF, LF)
    h = replace(h, '    bool retreat_from(vec2 threat);\n', '    bool retreat_from(vec2 threat);\n'
                '    void cs_build();\n    float camp_hit(vec2 q);\n    int camp_penalty(vec2 q);\n    bool cs_escape();\n'
                '    struct CsCamp { vec2 p; float s; int r; };\n    std::array<CsCamp, 24> csc{};\n    int n_csc = 0, cs_round = -1;\n')
    files['bot.h'] = h.encode()
    wh = files['world.h'].decode().replace(CRLF, LF)
    wh = replace(wh, '    bc::bitboard hot_zone;', '    std::vector<char> camp_hot; // v118 CS: camps counted in hot_zone\n    bc::bitboard awake_tiles;   // v118 CS: SDK awake camp tiles (CS_SDK_AWAKE)\n    bc::bitboard hot_zone;')
    files['world.h'] = wh.encode()
    wc = files['world.cpp'].decode().replace(CRLF, LF)
    wc = replace(wc, '    hot_zone.clear();\n    for (const auto& g : groups) {',
                 '    hot_zone.clear();\n    camp_hot.assign(camps.size(), 0);\n    awake_tiles.clear();\n'
                 '    if (CS_SDK_AWAKE) {\n        try {\n            bc::vision::awake_camp_tiles_into(awake_tiles);\n        } catch (...) {\n            awake_tiles.clear();\n        }\n    }\n'
                 '    for (const auto& g : groups) {')
    wc = replace(wc, '            if (!c.dead && c.strength > 0 && (c.hp < c.max_hp || awake)) hot_zone.draw_chebyshev(c.pos, static_cast<float>(c.range));',
                 '            if (!c.dead && c.strength > 0 && (c.hp < c.max_hp || awake || (CS_SDK_AWAKE && bit(awake_tiles, c.pos)))) {\n'
                 '                hot_zone.draw_chebyshev(c.pos, static_cast<float>(c.range));\n                camp_hot[static_cast<std::size_t>(i)] = 1;\n            }')
    files['world.cpp'] = wc.encode()
    c = files['bot.cpp'].decode()
    c = replace(c, 'bool Bot::retreat_from(vec2 threat) {', (HERE / 'cs_funcs.inc').read_text() + 'bool Bot::retreat_from(vec2 threat) {')
    c = replace(c, '    int here = away(pos) - home_w * fdist(w.spawn_field, pos) - ally_pull(pos);',
                '    int here = away(pos) - home_w * fdist(w.spawn_field, pos) - ally_pull(pos) - (CS_FLEE ? camp_penalty(pos) : 0);')
    c = replace(c, '        int sc = away(q) - home_w * static_cast<int>(fdist(w.spawn_field, q)) - ally_pull(q);',
                '        int sc = away(q) - home_w * static_cast<int>(fdist(w.spawn_field, q)) - ally_pull(q) - (CS_FLEE ? camp_penalty(q) : 0);')
    c = replace(c, '        mode = "home-escape";\n        walk_toward(~w.hot_zone & ~w.static_blocked);',
                '        mode = "home-escape";\n        if (!(CS_ESCAPE && cs_escape())) walk_toward(~w.hot_zone & ~w.static_blocked);')
    files['bot.cpp'] = c.encode()


def edit_A(files):
    files['common.h'] = b'#define CS_SDK_AWAKE 1\n' + files['common.h']


EDITS['C'] = edit_C
EDITS['A'] = edit_A


WB_FUNC = '''
// WB (v118): a bag that wins the game on submission. Local trace of 78 winning-bag episodes: the A2_ALTARFIX stuck
// lockout (80 rounds) also shelved winning bags (a Varg carried 651-777 gems with win_now() for 345 rounds while
// farming), and the tribute-win branch waited for full danger health even two tiles from an altar with no enemy near.
bool Bot::wb_safe_close() {
    if (!w.altar_ready || fdist(w.altar_field, pos) > WB_CLOSE) return false;
    for (const auto& e : w.enemies)
        if (cheb(e.pos, pos) <= 8) return false;
    return true;
}

'''


def edit_W(files):
    """Winning-bag banking: no stuck lockout for game-winning bags; bank them at any health when close and unthreatened."""
    files['common.h'] = (files['common.h'].decode() + '\n#ifndef WB_CLOSE\n#define WB_CLOSE 10\n#endif\n').encode()
    h = files['bot.h'].decode().replace(CRLF, LF)
    files['bot.h'] = replace(h, '    bool go_home_if_needed();\n', '    bool go_home_if_needed();\n    bool wb_safe_close();\n').encode()
    c = files['bot.cpp'].decode()
    c = replace(c, 'bool Bot::tribute_if_needed() {', WB_FUNC + 'bool Bot::tribute_if_needed() {')
    c = replace(c, '    if (round < tribute_off_until) {', '    if (round < tribute_off_until && !win_now()) {')
    c = replace(c, '            tribute_off_until = round + 80;\n            return false;',
                '            if (!win_now()) {\n                tribute_off_until = round + 80;\n                return false;\n            }\n'
                '            // Never shelve a winning bag: try the unit-aware walk to any altar tile instead.\n'
                '            if (walk_toward(w.altar_ring)) return true;')
    c = replace(c, '    } else if (win_now() && hp >= max_hp * tune::kDangerHp && tribute_if_needed()) {',
                '    } else if (win_now() && (hp >= max_hp * tune::kDangerHp || wb_safe_close()) && tribute_if_needed()) {')
    files['bot.cpp'] = c.encode()


EDITS['W'] = edit_W
