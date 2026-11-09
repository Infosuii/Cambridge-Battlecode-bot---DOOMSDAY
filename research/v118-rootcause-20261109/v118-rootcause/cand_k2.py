"""K2: lethal-only camp safety (third focused attempt) and W2 late-bank ordering.

K  (lazy camp safety) cut camp deaths 7.6 -> 6.2/game on the five worst maps but cost enemy kills (23.2 -> 21.4) and
   12/90 incident games: fleeing through awake camps also drags chasers into camp fire, so a general camp penalty
   changes good kites as well as bad ones. K2 only intervenes when camp fire alone would kill us: such flee steps are
   excluded, and the escape step replaces the default exit walk only when two more rounds of camp fire would be lethal.
W2 a carrier that can only just reach an altar before the round cap banks before hunt() / other branches can take the
   turn (Twisty ladder loss: 122 gems unbanked at round 2000).
"""
from pathlib import Path
from candidates import HERE, CS_DEFAULTS, CRLF, LF, replace, EDITS

LETHAL = '''int Bot::camp_penalty(vec2 q) {
    const float h = camp_hit(q);
    if (h <= 0.0f) return 0;
    if (h >= hp) return 100000; // this step dies to the camps alone
    return static_cast<int>(CS_FLEE_W * h / std::max(hp, 1.0f));
}'''
LETHAL_NEW = '''int Bot::camp_penalty(vec2 q) {
    // K2: lethal-only. A kite through camp fire that we survive also damages the chasers; only refuse steps where
    // the camps alone would finish us (with a small margin for the enemies' hits).
    const float h = camp_hit(q);
    if (h <= 0.0f || h < hp * CS_LETHAL) return 0;
    return 100000;
}'''

K2_DEFAULTS = '''
#ifndef CS_LETHAL
#define CS_LETHAL 0.85f
#endif
'''


def edit_K2(files):
    files['common.h'] = (files['common.h'].decode() + CS_DEFAULTS + K2_DEFAULTS).encode()
    h = files['bot.h'].decode().replace(CRLF, LF)
    h = replace(h, '    bool retreat_from(vec2 threat);\n', '    bool retreat_from(vec2 threat);\n'
                '    void cs_build();\n    float camp_hit(vec2 q);\n    int camp_penalty(vec2 q);\n    bool cs_escape();\n'
                '    struct CsCamp { vec2 p; float s; int r; };\n    std::array<CsCamp, 24> csc{};\n    int n_csc = 0, cs_round = -1;\n')
    files['bot.h'] = h.encode()
    funcs = (HERE / 'cs_funcs_lazy.inc').read_text()
    assert funcs.count(LETHAL) == 1
    funcs = funcs.replace(LETHAL, LETHAL_NEW)
    c = files['bot.cpp'].decode()
    c = replace(c, 'bool Bot::retreat_from(vec2 threat) {', funcs + 'bool Bot::retreat_from(vec2 threat) {')
    c = replace(c, '    int here = away(pos) - home_w * fdist(w.spawn_field, pos) - ally_pull(pos);',
                '    int here = away(pos) - home_w * fdist(w.spawn_field, pos) - ally_pull(pos) - (CS_FLEE ? camp_penalty(pos) : 0);')
    c = replace(c, '        int sc = away(q) - home_w * static_cast<int>(fdist(w.spawn_field, q)) - ally_pull(q);',
                '        int sc = away(q) - home_w * static_cast<int>(fdist(w.spawn_field, q)) - ally_pull(q) - (CS_FLEE ? camp_penalty(q) : 0);')
    c = replace(c, '        mode = "home-escape";\n        walk_toward(~w.hot_zone & ~w.static_blocked);',
                '        mode = "home-escape";\n'
                '        // K2: the damage-aware exit only when two more rounds in camp fire would kill us.\n'
                '        if (!(CS_ESCAPE && camp_hit(pos) * 2.0f >= hp && cs_escape())) walk_toward(~w.hot_zone & ~w.static_blocked);')
    files['bot.cpp'] = c.encode()


W2_FUNC = '''
// W2 (v118): the bag can only just reach an altar before the round cap. Twisty ladder loss: 122 gems unbanked at
// round 2000. tribute_if_needed() already fires on `late`, but the regular tribute branch runs after hunt() and the
// other movement branches, so a late carrier could be pulled away for its last rounds.
bool Bot::wb_late() {
    if (gems < 10 || !w.altar_ready) return false;
    const int d = fdist(w.altar_field, pos);
    return d != kUnreach && round + d + gems / 10 + 25 >= static_cast<int>(bc::constants::max_rounds);
}

'''


def edit_W2(files):
    h = files['bot.h'].decode().replace(CRLF, LF)
    files['bot.h'] = replace(h, '    bool wb_safe_close();\n', '    bool wb_safe_close();\n    bool wb_late();\n').encode()
    c = files['bot.cpp'].decode()
    c = replace(c, 'bool Bot::tribute_if_needed() {', W2_FUNC + 'bool Bot::tribute_if_needed() {')
    old = ('    } else if (win_now() && (hp >= max_hp * tune::kDangerHp || wb_safe_close()) && tribute_if_needed()) {\n'
           '        // Our bag finishes the race: bank it before anything else (shopping can wait).\n'
           '        mode = "tribute-win";\n')
    assert c.count(old) == 1, 'W must be applied first'
    c = c.replace(old, old + '    } else if (wb_late() && tribute_if_needed()) {\n        mode = "tribute-late";\n')
    files['bot.cpp'] = c.encode()


EDITS['Q'] = edit_K2   # lethal-only camp safety
EDITS['T'] = edit_W2   # late-bank ordering (needs W)
