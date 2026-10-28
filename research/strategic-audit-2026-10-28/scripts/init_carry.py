"""Experimental carry-capture prototype (strategic audit 2026-10-28). Never a release candidate as written.

Usage: init_carry.py OUT_DIR [--pull 3.0] [--dist 8] [--wait 15]
Copies frozen bots/v76 to OUT_DIR (under artifacts/tmp/v67) and adds SA_CARRY:
* a non-Vesper champion on a finished gold region steps off it when a visible Vesper is within SA_CARRY_DIST tiles,
  waiting up to SA_CARRY_WAIT rounds; once Vesper stands on the region it leaves (avoid 8 rounds), so Vesper captures
  alone and every reward passes through her +33% gold passive (+53% with Treasure);
* Vesper values finished gold regions SA_CARRY_PULL times higher;
* UB_GOLD_FUNNEL=1 (existing): Vesper keeps rewards she stands on, allies hand theirs to her.
SA_CARRY=0 leaves the v76 code path unchanged apart from the funnel define.
"""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ap = argparse.ArgumentParser()
ap.add_argument('out')
ap.add_argument('--pull', default='3.0f')
ap.add_argument('--dist', default='8')
ap.add_argument('--wait', default='15')
ap.add_argument('--carry', default='1')
ap.add_argument('--role', default='0', help='SA_ROLE: 1 = Vesper values gold x role_v, teammates x role_o')
ap.add_argument('--role-v', default='3.0f')
ap.add_argument('--role-o', default='0.5f')
a = ap.parse_args()
out = ROOT / a.out
assert out.resolve().is_relative_to(ROOT / 'artifacts/tmp/v67') and not out.exists()
shutil.copytree(ROOT / 'bots/v76/src', out / 'src', copy_function=shutil.copyfile)


def edit(name, old, new):
    p = out / 'src' / name
    s = p.read_text(encoding='utf8')
    assert s.count(old) == 1, (name, old[:60], s.count(old))
    p.write_text(s.replace(old, new), encoding='utf8')


edit('common.h', '#define A2_CAMPNET 1\n',
     f'#define A2_CAMPNET 1\n#define SA_CARRY {a.carry}\n#define SA_CARRY_DIST {a.dist}\n#define SA_CARRY_WAIT {a.wait}\n'
     f'#define SA_CARRY_PULL {a.pull}\n#define SA_ROLE {a.role}\n#define SA_ROLE_V {a.role_v}\n#define SA_ROLE_O {a.role_o}\n')
edit('common.h', '#ifndef UB_GOLD_FUNNEL\n#define UB_GOLD_FUNNEL 0\n#endif',
     '#ifndef UB_GOLD_FUNNEL\n#define UB_GOLD_FUNNEL SA_CARRY\n#endif')
edit('bot.h', '    std::vector<int> avoid_until;',
     '    int sa_yield_group = -1, sa_yield_since = -1; // SA_CARRY: region this champion is leaving to the carry\n'
     '    bool sa_team_vesper = false; // SA_ROLE: a Vesper has been seen on our team (all start together on spawn)\n'
     '    std::vector<int> avoid_until;')
edit('bot.cpp', '''    shared = read_shared();
    decode_claims();
#if V54_ONSITE
''', '''    shared = read_shared();
    decode_claims();
#if SA_ROLE
    sa_team_vesper |= type == bc::champion_type::vesper_vale;
    for (const auto& a : w.allies) sa_team_vesper |= a.type == bc::champion_type::vesper_vale;
#endif
#if V54_ONSITE
''')
edit('bot.cpp', '''        mode = "capture";
        if (bit(g.tiles, pos)) {
#if V69_CAPTURE_STALL''', '''        mode = "capture";
#if SA_CARRY
        // Carry capture: rewards are split among allies on the region when it pays out, and Vesper earns 33% more
        // gold (53% with Treasure). With Vesper close, step off the region and let her take the whole reward.
        if (type != bc::champion_type::vesper_vale && w.enemies.empty() && g.gold > 0) {
            const AllyRec* carry = nullptr;
            for (const auto& a : w.allies)
                if (a.type == bc::champion_type::vesper_vale && a.hp > 0) carry = &a;
            const int gi_y = static_cast<int>(&g - &w.groups[0]);
            if (carry) {
                bc::bitboard off;
                off.clear();
                for (int ci : g.camps) off.draw_chebyshev(w.camps[ci].pos, 2.0f);
                off &= ~g.tiles;
                off &= ~w.static_blocked;
                if (bit(g.tiles, carry->pos)) {
                    if (bit(g.tiles, pos)) {
                        mode = "carry-leave";
                        walk_toward(off);
                    }
                    if (static_cast<std::size_t>(gi_y) < avoid_until.size()) avoid_until[gi_y] = round + 8;
                    sa_yield_group = -1;
                    return bit(g.tiles, pos);
                }
                int cd = 99;
                for (int ci : g.camps) cd = std::min(cd, cheb(w.camps[ci].pos, carry->pos));
                if (cd <= SA_CARRY_DIST) {
                    if (sa_yield_group != gi_y) sa_yield_group = gi_y, sa_yield_since = round;
                    if (round - sa_yield_since <= SA_CARRY_WAIT) {
                        mode = "carry-yield";
                        if (bit(g.tiles, pos)) walk_toward(off);
                        return true;
                    }
                }
            }
        }
#endif
        if (bit(g.tiles, pos)) {
#if V69_CAPTURE_STALL''')
edit('bot.cpp', '''        float value = static_cast<float>(g.gems) + gold_weight() * static_cast<float>(g.gold);
#if A2_DPLAN
''', '''        float value = static_cast<float>(g.gems) + gold_weight() * static_cast<float>(g.gold);
#if SA_CARRY
        if (type == bc::champion_type::vesper_vale && g.gold > 0 && g.state == GroupState::reward) value *= SA_CARRY_PULL;
#endif
#if SA_ROLE
        // Role split: with a Vesper on the team, she farms the gold (her passive multiplies it) and teammates the gems.
        if (sa_team_vesper)
            value += ((type == bc::champion_type::vesper_vale ? SA_ROLE_V : SA_ROLE_O) - 1.0f) * gold_weight() * static_cast<float>(g.gold);
#endif
#if A2_DPLAN
''')
(out / 'VARIANT.txt').write_text(f'init_carry.py from bots/v76: {vars(a)}\n', encoding='utf8')
print('prepared', out)
