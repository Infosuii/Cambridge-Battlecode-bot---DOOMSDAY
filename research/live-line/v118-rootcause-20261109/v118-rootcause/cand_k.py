"""Lazy camp safety (K): flee camp penalty + damage-minimising escape step; no world-update changes; dash only near-lethal."""
from candidates import HERE, CS_DEFAULTS, CRLF, LF, replace, EDITS


def edit_K(files):
    files['common.h'] = (files['common.h'].decode() + CS_DEFAULTS).encode()
    h = files['bot.h'].decode().replace(CRLF, LF)
    h = replace(h, '    bool retreat_from(vec2 threat);\n', '    bool retreat_from(vec2 threat);\n'
                '    void cs_build();\n    float camp_hit(vec2 q);\n    int camp_penalty(vec2 q);\n    bool cs_escape();\n'
                '    struct CsCamp { vec2 p; float s; int r; };\n    std::array<CsCamp, 24> csc{};\n    int n_csc = 0, cs_round = -1;\n')
    files['bot.h'] = h.encode()
    c = files['bot.cpp'].decode()
    c = replace(c, 'bool Bot::retreat_from(vec2 threat) {', (HERE / 'cs_funcs_lazy.inc').read_text() + 'bool Bot::retreat_from(vec2 threat) {')
    c = replace(c, '    int here = away(pos) - home_w * fdist(w.spawn_field, pos) - ally_pull(pos);',
                '    int here = away(pos) - home_w * fdist(w.spawn_field, pos) - ally_pull(pos) - (CS_FLEE ? camp_penalty(pos) : 0);')
    c = replace(c, '        int sc = away(q) - home_w * static_cast<int>(fdist(w.spawn_field, q)) - ally_pull(q);',
                '        int sc = away(q) - home_w * static_cast<int>(fdist(w.spawn_field, q)) - ally_pull(q) - (CS_FLEE ? camp_penalty(q) : 0);')
    c = replace(c, '        mode = "home-escape";\n        walk_toward(~w.hot_zone & ~w.static_blocked);',
                '        mode = "home-escape";\n        if (!(CS_ESCAPE && cs_escape())) walk_toward(~w.hot_zone & ~w.static_blocked);')
    files['bot.cpp'] = c.encode()


EDITS['K'] = edit_K
