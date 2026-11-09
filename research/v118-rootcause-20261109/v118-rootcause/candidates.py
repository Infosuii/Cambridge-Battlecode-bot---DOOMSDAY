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
