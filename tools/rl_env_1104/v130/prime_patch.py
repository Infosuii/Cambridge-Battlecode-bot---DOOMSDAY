"""CL_PRIME for v130: FürFortnite's primed recall. Every turn ends with a recall already started (only stuns break
channels, not damage), so a recall v130 decides on at the next turn start is one turn into its 5-turn channel. At the
turn start the primed recall is kept only when v130 itself would go home now and is past walking distance (low health,
a trip home already under way, or gold to spend with nothing on a capture); otherwise it is cancelled before acting.
v130's channel guard still cancels a kept recall when the enemies in reach would kill us before it completes.
usage: prime_patch.py SRC"""
import sys


def patch(path, old, new):
    t = open(path, encoding="utf-8", newline="").read()
    assert t.count(old) == 1, (path, old[:70], t.count(old))
    open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new))


src = sys.argv[1]
patch(src + "/common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_PRIME 1\n")
patch(src + "/bot.h", "    bool shop_done = false;", "    bool cl_primed = false; // CL_PRIME: this champion ended its last turn with a primed recall\n    bool shop_done = false;")

start_old = ("    // A recall started before a capture landed: if the bag now finishes the race, walk to an altar instead.\n"
             "    if (state.contains(bc::champion_state::recalling) && win_now() && hp >= max_hp * tune::kDangerHp) {")
start_new = ("#if CL_PRIME\n"
             "    // CL_PRIME: keep last turn's primed recall only when we would go home now, past walking distance.\n"
             "    bool cl_prime_cancelled = false;\n"
             "    if (cl_primed) {\n"
             "        cl_primed = false;\n"
             "        if (state.contains(bc::champion_state::recalling)) {\n"
             "            const bool far = inited && fdist(w.spawn_field, pos) > tune::kShopWalkDist;\n"
             "            const bool low = hp < max_hp * tune::kRetreatHp;\n"
             "            const bool rich = gold >= tune::kShopGold && !shop_done;\n"
             "            const bool capturing = target_group >= 0 && target_group < static_cast<int>(w.groups.size()) &&\n"
             "                w.groups[target_group].state == GroupState::reward && bit(w.groups[target_group].tiles, pos);\n"
             "            const bool keep = far && !win_now() && (low || (heading_home && !capturing) || (rich && !capturing && w.enemies.empty()));\n"
             "            if (keep) {\n"
             "                heading_home = true;\n"
             "            } else {\n"
             "                try {\n"
             "                    me.cancel_recall();\n"
             "                    cl_prime_cancelled = true;\n"
             "                } catch (const std::exception& e) {\n"
             "                    LOG(\"prime cancel error %s\\n\", e.what());\n"
             "                }\n"
             "            }\n"
             "        }\n"
             "    }\n"
             "#else\n"
             "    constexpr bool cl_prime_cancelled = false;\n"
             "#endif\n"
             "    // A recall started before a capture landed: if the bag now finishes the race, walk to an altar instead.\n"
             "    if (!cl_prime_cancelled && state.contains(bc::champion_state::recalling) && win_now() && hp >= max_hp * tune::kDangerHp) {")
patch(src + "/bot.cpp", start_old, start_new)
patch(src + "/bot.cpp",
      "    } else if (state.contains(bc::champion_state::recalling) || state.contains(bc::champion_state::submitting_gems) ||",
      "    } else if ((!cl_prime_cancelled && state.contains(bc::champion_state::recalling)) || state.contains(bc::champion_state::submitting_gems) ||")

tail_old = '    debug_block({ std::printf("M %d %u %s %d\\n", round, my_id, mode, target_group); });\n'
tail_new = ("#if CL_PRIME\n"
            "    // CL_PRIME: end the turn with a recall already started (the next turn start keeps or cancels it).\n"
            "    try {\n"
            "        auto& me2 = bc::self();\n"
            "        const auto st2 = me2.state();\n"
            "        if (!st2.is_dead() && !st2.contains(bc::champion_state::recalling) && !st2.contains(bc::champion_state::submitting_gems) &&\n"
            "            !st2.contains(bc::champion_state::teleporting) && !bit(w.ally_spawn, me2.position())) {\n"
            "            me2.recall();\n"
            "            cl_primed = true;\n"
            "        }\n"
            "    } catch (const std::exception& e) {\n"
            "        LOG(\"prime error %s\\n\", e.what());\n"
            "    }\n"
            "#endif\n") + tail_old
patch(src + "/bot.cpp", tail_old, tail_new)
print("applied prime")
