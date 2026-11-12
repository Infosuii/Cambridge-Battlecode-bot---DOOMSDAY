"""Z: camp-aware time-to-die in handle_enemies (requires Q's lazy camp helpers).

Ladder v117 losses: camps killed us 116 times, 72% with an enemy within 6 tiles in the last four rounds (fights inside
awake camp range). handle_enemies' ttd = hp / threat_on_me counts only enemy damage, so a fight inside camp fire looked
as safe as one outside it. Z adds the damage of awake camps that reach our tile and have no enemy closer to them (we are
the likely camp target) whenever an enemy can already hit us.
"""
from candidates import replace, EDITS

OLD = '    const float ttd = threat_on_me > 0 ? hp / threat_on_me : 1e9f;\n'
NEW = '''    float camp_on_me = 0.0f;
    if (CZ_ON && threat_on_me > 0) {
        // v118 Z: awake camps hitting our tile count toward time-to-die (no enemy nearer to the camp: we are its target).
        cs_build();
        for (int i = 0; i < n_csc; ++i) {
            const auto& c = csc[static_cast<std::size_t>(i)];
            const int dme = cheb(c.p, pos);
            if (dme > c.r) continue;
            bool closer = false;
            for (const auto& e : w.enemies)
                if (cheb(e.pos, c.p) < dme) {
                    closer = true;
                    break;
                }
            if (!closer) camp_on_me += c.s;
        }
        camp_on_me *= camp_taken_mult;
    }
    const float ttd = threat_on_me + camp_on_me > 0 ? hp / (threat_on_me + camp_on_me) : 1e9f;
'''


def edit_Z(files):
    files['common.h'] = (files['common.h'].decode() + '\n#ifndef CZ_ON\n#define CZ_ON 1\n#endif\n').encode()
    c = files['bot.cpp'].decode()
    assert 'void Bot::cs_build()' in c, 'Z requires Q (lazy camp helpers)'
    files['bot.cpp'] = replace(c, OLD, NEW).encode()


EDITS['Z'] = edit_Z
