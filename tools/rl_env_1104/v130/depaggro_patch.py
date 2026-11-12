"""Deposit and aggression add-on (research/rl_env_1104/DEPOSIT_AGGRO_PLAN_20261111.md): steps S1-S5, S7, G1-G3.
Works on v221 / v139 (old channel guard) and v141 / upload_final (channel_danger). Knob steps S6, S8, G4 are not applied.
usage: depaggro_patch.py SRC"""
import os, sys

src = sys.argv[1]
rd = lambda n: open(os.path.join(src, n), encoding="utf-8", newline="").read()
wr = lambda n, t: open(os.path.join(src, n), "w", encoding="utf-8", newline="").write(t)


def patch(name, old, new, need=True):
    t = rd(name)
    if "\r\n" in t:  # CRLF sources (v221): match and write with the file's own line endings
        old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
    if t.count(old) != 1:
        assert not need, (name, old[:90], t.count(old))
        return False
    wr(name, t.replace(old, new))
    return True


patch("common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_DEPOSIT 1\n#define CL_DEP_MIN 10\n#define CL_DEP_SAFE 0.8f\n"
      "#define CL_DEP_PUSH 6\n#define CL_DEP_GUARD 10\n#define CL_AGGRO 1\n#define CL_AGG_HP 0.45f\n#define CL_AGG_BAG 100\n"
      "#define CL_GANG_BAG 40\n#define CL_GANG_TURNS 6\n")
patch("bot.h", "    bool tribute_if_needed();\n",
      "    bool tribute_if_needed();\n    int deposit_rounds(int bag) const;\n    float standing_damage(int rounds) const;\n"
      "    bool guard_depositor();\n    bool gang_up();\n    bool dep_push = false;\n    int gang_since = -100, gang_pause_until = 0;\n")
real = "e.real_recall()" if "real_recall" in rd("world.h") else "e.recalling()"
hidden = "#if A2_BELIEF\n        foes += a2_hidden_near(8, 0);\n#endif\n" if "int Bot::a2_hidden_near" in rd("bot.cpp") else ""
HELPERS = """// CL_DEPOSIT: rounds a deposit of this bag takes (the engine's rule; about one round per 10 gems).
int Bot::deposit_rounds(int bag) const {
    return std::max(bc::constants::submit_gem_minimum_duration,
        bc::constants::submit_gem_base_duration +
            static_cast<int>(std::ceil(static_cast<double>(bag) * bc::constants::submit_gem_duration_multiplier)));
}
// Damage the visible enemies can do to us over the next `rounds` rounds if we stay here. An enemy `gap` tiles
// outside its reach needs `gap` rounds to arrive (one tile of slack for a dash) and then hits every round.
float Bot::standing_damage(int rounds) const {
    float dmg = 0.0f;
    for (const auto& e : w.enemies) {
        if (e.hp <= 0 || e.tributing() || REAL) continue;
        const int gap = std::max(0, cheb(e.pos, pos) - e.range - 1);
        const int hits = rounds + 1 - gap;
        if (hits > 0) dmg += enemy_dps(e) * static_cast<float>(hits);
    }
    return dmg;
}
// CL_DEPOSIT S7: a teammate within CL_DEP_GUARD tiles is depositing and an enemy is within 8 tiles of it:
// close to our range of that enemy and hit it.
bool Bot::guard_depositor() {
    if (!CL_DEPOSIT || w.enemies.empty() || hp < max_hp * 0.5f || gems >= CL_GANG_BAG) return false;
    FlagScope combat{combat_move};
    for (const auto& a : w.allies) {
        if (cheb(a.pos, pos) > CL_DEP_GUARD || !a.unit.state().contains(bc::champion_state::submitting_gems)) continue;
        const EnemyRec* threat = nullptr;
        for (const auto& e : w.enemies)
            if (e.hp > 0 && cheb(e.pos, a.pos) <= 8 && (!threat || cheb(e.pos, a.pos) < cheb(threat->pos, a.pos))) threat = &e;
        if (!threat) continue;
        mode = "guard";
        if (cheb(threat->pos, pos) > range) {
            bc::bitboard goal;
            goal.clear();
            goal.draw_chebyshev(threat->pos, static_cast<float>(range));
            walk_toward(goal);
        }
        if (cheb(threat->pos, pos) <= range) {
            cast_on_enemy(*threat);
            attack_unit(threat->unit, threat->pos);
        }
        return true;
    }
    return false;
}
// CL_AGGRO G2: a visible enemy with fewer bodies around it than we have around it: walk in and hit it.
bool Bot::gang_up() {
    if (!CL_AGGRO || w.enemies.empty() || hp < max_hp * 0.55f || gems >= CL_GANG_BAG || heading_home ||
        round < gang_pause_until) return false;
    const EnemyRec* best = nullptr;
    for (const auto& t : w.enemies) {
        if (t.hp <= 0 || cheb(t.pos, pos) > 7 || bit(w.enemy_spawn_zone, t.pos) || bit(w.bushes, t.pos)) continue;
        int foes = 0, friends = 1;
        for (const auto& e : w.enemies) foes += e.hp > 0 && cheb(e.pos, t.pos) <= 6;
        for (const auto& a : w.allies) friends += cheb(a.pos, t.pos) <= 6 && a.hp >= 0.5f * a.max_hp;
        if (foes > 2 || friends < foes + 1) continue;
        if (!best || t.hp / std::max(1.0f, t.max_hp) < best->hp / std::max(1.0f, best->max_hp)) best = &t;
    }
    if (!best) return false;
    if (round - gang_since > CL_GANG_TURNS + 2) gang_since = round; // a new walk-in
    if (round - gang_since >= CL_GANG_TURNS) { // it got away
        gang_pause_until = round + 20;
        return false;
    }
    FlagScope combat{combat_move};
    mode = "gang";
    if (cheb(best->pos, pos) > range) {
        bc::bitboard goal;
        goal.clear();
        goal.draw_chebyshev(best->pos, static_cast<float>(range));
        walk_toward(goal);
    }
    if (cheb(best->pos, pos) <= range) {
        cast_on_enemy(*best);
        attack_unit(best->unit, best->pos);
    }
    return true;
}

""".replace("REAL", real)
patch("bot.cpp", "bool Bot::tribute_if_needed() {\n", HELPERS + "bool Bot::tribute_if_needed() {\n")
# S2: cancel guard and retry rule (two code generations)
if not patch("bot.cpp", "        if (incoming * static_cast<float>(left + 1) * tune::kChannelGuard < hp) return;\n",
             "        if (CL_DEPOSIT && state.contains(bc::champion_state::submitting_gems)) {\n"
             "            if (standing_damage(left) < hp) return; // CL: we finish before they kill us: keep channelling\n"
             "        } else if (incoming * static_cast<float>(left + 1) * tune::kChannelGuard < hp) return;\n", need=False):
    patch("bot.cpp", "        if (!channel_danger(channel, left)) return;\n",
          "        if (CL_DEPOSIT && channel == ChannelRetry::submit ? standing_damage(left) < hp : !channel_danger(channel, left)) return;\n")
ADD = "    if (CL_DEPOSIT && kind == ChannelRetry::submit) unsafe = standing_damage(duration) >= hp * CL_DEP_SAFE;\n"
a = "    bool unsafe = tune::kChannelGuard > 0.0f && incoming * static_cast<float>(duration + 1) * tune::kChannelGuard >= hp;\n"
if not patch("bot.cpp", a, a + ADD, need=False):
    b = "    bool unsafe = channel_danger(kind, duration);\n"
    patch("bot.cpp", b, b + ADD)
# S3 / S4
patch("bot.cpp", "    const bool fought =\n",
      "    // CL_DEPOSIT S3/S4: a carrier at an altar, or a few steps from one, deposits before the fight-or-flee logic\n"
      "    // when the deposit ends before the visible enemies can kill it. Damage does not interrupt a deposit.\n"
      "    bool dep_first = false;\n"
      "    if (CL_DEPOSIT && gems >= CL_DEP_MIN && !w.enemies.empty() && !w.no_bank) {\n"
      "        w.ensure_altar_field();\n"
      "        const int da = fdist(w.altar_field, pos);\n"
      "        if (da != kUnreach && da <= CL_DEP_PUSH && standing_damage(da + deposit_rounds(gems)) < hp * CL_DEP_SAFE) {\n"
      "            force_tribute = true;\n"
      "            dep_push = true;\n"
      "            dep_first = tribute_if_needed();\n"
      "            dep_push = false;\n"
      "            if (dep_first) mode = da == 0 ? \"tribute-first\" : \"tribute-push\";\n"
      "        }\n"
      "    }\n"
      "    const bool fought =\n")
patch("bot.cpp", "        handle_enemies();\n", "        (!dep_first && handle_enemies());\n")
patch("bot.cpp", "    if (fought) {\n", "    if (dep_first) {\n    } else if (fought) {\n")
patch("bot.cpp", "    if (gems >= 15) {\n", "    if (gems >= 15 && !dep_push) {\n")
# S5 (already present in upload_final as CL_BANKFIX)
patch("bot.cpp", "            tribute_off_until = round + 80;\n", "            tribute_off_until = round + (CL_DEPOSIT && gems >= 30 ? 15 : 80);\n", need=False)
# S7 / G2 chain
patch("bot.cpp", "    } else if (home_siege()) {\n", "    } else if (guard_depositor()) {\n    } else if (gang_up()) {\n    } else if (home_siege()) {\n")
# G1
patch("bot.cpp", "    if (tune::kTribDeny & 2) {\n",
      "    // CL_AGGRO G1: one body more than they have here (or level while a teammate deposits beside us): stand and\n"
      "    // fight, carriers too. Never on their spawn, in a camp's reach or at a target in a bush.\n"
      "    if (CL_AGGRO && target) {\n"
      "        int friends = 1, foes = 0;\n"
      "        bool guarding = false;\n"
      "        for (const auto& a : w.allies) {\n"
      "            if (cheb(a.pos, pos) > 6 || a.hp < 0.4f * a.max_hp) continue;\n"
      "            if (a.unit.state().contains(bc::champion_state::submitting_gems)) guarding = true; // cannot fight\n"
      "            else ++friends;\n"
      "        }\n"
      "        for (const auto& e : w.enemies) {\n"
      "            if (e.hp <= 0) continue;\n"
      "            const int d = cheb(e.pos, pos);\n"
      "            if (d > 7 || (bit(w.enemy_spawn, e.pos) && d > e.range + 2)) continue;\n"
      "            ++foes;\n"
      "        }\n" + hidden +
      "        if (foes > 0 && (friends >= foes + 1 || (guarding && friends >= foes)) && hp >= CL_AGG_HP * max_hp &&\n"
      "            gems < CL_AGG_BAG && ttd > 2.0f && !bit(w.enemy_spawn_zone, target->pos) && !bit(w.hot_zone, pos) &&\n"
      "            !bit(w.bushes, target->pos)) {\n"
      "            winning = true;\n"
      "            in_danger = false;\n"
      "        }\n"
      "    }\n"
      "    if (tune::kTribDeny & 2) {\n")
# G3
patch("bot.cpp", "    if (hp < max_hp * 0.6f || gems >= 20 || !bc::self().can_move()) return false;\n",
      "    if (hp < max_hp * 0.5f || gems >= CL_GANG_BAG || !bc::self().can_move()) return false;\n", need=False)
patch("bot.cpp", "gems >= 20 || heading_home ||", "gems >= CL_GANG_BAG || heading_home ||", need=False)
print("applied deposit + aggression add-on (" + real + ")")
