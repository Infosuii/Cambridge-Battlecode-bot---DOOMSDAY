"""CL_PLAN for v139: install mapplan.h (the draft's 10M-turn map analysis) and use the plan in game.
usage: clplan_patch.py REPO SRC BITS
BITS (CL_PLAN): 1 sweepers (gem and gold cluster regions get 1-2 dedicated champions), 2 effort terms in the group
score (heal trip for the health a group drains, scaled by the walk home; the share of a bank trip for its gems),
4 carried-gem risk on enemy-side groups, 8 sweepers bank small bags (CL_SW_CARRY), 16 sweepers buy Capture then
Prospector first."""
import os, shutil, sys

repo, src, bits = sys.argv[1], sys.argv[2], int(sys.argv[3])


def patch(name, old, new, count=1):
    p = os.path.join(src, name)
    t = open(p, encoding="utf-8", newline="").read()
    assert t.count(old) == count, (name, old[:80], t.count(old))
    open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))


shutil.copy(os.path.join(repo, "tools", "rl_env_1104", "v130", "mapplan.h"), os.path.join(src, "mapplan.h"))
patch("mapplan.h", "#define CL_PLAN 1 //", f"#define CL_PLAN {bits} //")
# Draft: the analysis runs on the first draft turn (the only one with the fuel), before the header is written.
patch("draft.cpp", '#include "strategy.h"\n', '#include "strategy.h"\n#include "mapplan.h"\n')
patch("draft.cpp",
      "void play_draft() {\n    const auto chosen = bc::draft::current_draft(team::ally);\n"
      "    [[maybe_unused]] std::uint32_t size = 0;\n    try {\n        size = bc::draft::team_size();\n    } catch (...) {\n    }\n",
      "void play_draft() {\n    const auto chosen = bc::draft::current_draft(team::ally);\n"
      "    [[maybe_unused]] std::uint32_t size = 0;\n    try {\n        size = bc::draft::team_size();\n    } catch (...) {\n    }\n"
      "    try {\n        static bool cl_plan_done = false; // CL_PLAN: map analysis on the turn with the fuel\n"
      "        if (!cl_plan_done && (CL_PLAN & 1)) cl_plan_done = mapplan::draft_write(size);\n    } catch (...) {\n    }\n")
patch("bot.h", '#include "world.h"\n', '#include "world.h"\n#include "mapplan.h"\n')
patch("bot.h", "    float soak_coefficient(int group, float hp_left);\n",
      "    float soak_coefficient(int group, float hp_left);\n"
      "    // CL_PLAN: the draft's map plan (mapplan.h).\n"
      "    mapplan::Plan cl_plan;\n"
      "    int my_sweep_region = 0;                  // 1-based sweep region we hold, 0 = not a sweeper\n"
      "    int sweep_slot[2] = {-1, -1};             // the sweepers' slots\n"
      "    std::vector<std::int8_t> sweep_region_of; // per group: 1-based sweep region, 0 = none\n"
      "    void cl_plan_init();\n"
      "    float sweep_mult(int gi);\n"
      "    bool sweep_idle();\n"
      "    float cl_effort(const GroupRec& g, int gi, float hp_left, float team_dps);\n")
patch("bot.cpp",
      "    my_id = static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(me));\n    type = me.champion_name();\n",
      "    my_id = static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(me));\n    type = me.champion_name();\n"
      "    cl_plan_init();\n")
FUNCS = r'''
// CL_PLAN: decode the draft's plan; sweepers are the weakest fighters by base health x strength (never Cassi or Issac,
// whose duo logic pairs them), the same choice on every body.
void Bot::cl_plan_init() {
    sweep_region_of.assign(w.groups.size(), 0);
    my_sweep_region = 0;
    if (!(CL_PLAN & 1)) return;
    cl_plan = mapplan::read();
    if (!cl_plan.ok || cl_plan.sweepers <= 0 || team_size < 4) return; // three bodies cannot spare one
    for (const auto& e : cl_plan.entries) {
        vec2 p = pos;
        p.x = e[0];
        p.y = e[1];
        const int gi = w.group_of_camp_tile(p);
        if (gi >= 0 && gi < static_cast<int>(sweep_region_of.size())) sweep_region_of[static_cast<std::size_t>(gi)] = static_cast<std::int8_t>(e[2]);
    }
    struct C {
        float fight;
        int s;
    };
    std::vector<C> c;
    for (int s = 0; s < team_size && s < static_cast<int>(slot_type.size()); ++s) {
        const auto t = slot_type[static_cast<std::size_t>(s)];
        if (t == bc::champion_type::cassi || t == bc::champion_type::issac) continue;
        const auto& b = kBase[static_cast<std::size_t>(t)];
        c.push_back({b.hp * b.str, s});
    }
    std::sort(c.begin(), c.end(), [](const C& a, const C& b) { return a.fight < b.fight || (a.fight == b.fight && a.s > b.s); });
    for (int k = 0; k < cl_plan.sweepers && k < static_cast<int>(c.size()); ++k) {
        sweep_slot[k] = c[static_cast<std::size_t>(k)].s;
        if (c[static_cast<std::size_t>(k)].s == slot) my_sweep_region = cl_plan.region_of_sweeper[k];
    }
    debug_block({ if (slot == 0 || my_sweep_region > 0) std::printf("CLPLAN_GAME slot %d sweeper_region %d sweepers %d/%d entries %zu\n", slot, my_sweep_region, sweep_slot[0], sweep_slot[1], cl_plan.entries.size()); });
}

// CL_PLAN bit 32 (dynamic sweepers): every group of our region is down for more than CL_SW_IDLE rounds, so we play
// as a normal champion meanwhile (crews, golems beside the clusters, fights, banking) instead of waiting there.
bool Bot::sweep_idle() {
    static int cached_round = -1;
    static bool idle = false;
    if (cached_round == round) return idle;
    cached_round = round;
    int n = 0;
    for (std::size_t g = 0; g < sweep_region_of.size(); ++g) {
        if (sweep_region_of[g] != my_sweep_region) continue;
        ++n;
        const auto& gr = w.groups[g];
        if (gr.state != GroupState::respawning || gr.respawn_round - round <= CL_SW_IDLE) return idle = false;
    }
    idle = n > 0;
    return idle;
}

// CL_PLAN bit 1: a sweeper farms its region; the others leave a living sweeper's region to it.
float Bot::sweep_mult(int gi) {
    if (!(CL_PLAN & 1) || gi < 0 || gi >= static_cast<int>(sweep_region_of.size())) return 1.0f;
    const int rg = sweep_region_of[static_cast<std::size_t>(gi)];
    if (my_sweep_region > 0) {
        if ((CL_PLAN & 32) && sweep_idle()) return 1.0f; // region down: a normal champion
        if (rg == my_sweep_region) return CL_SW_IN;
        return w.groups[static_cast<std::size_t>(gi)].state == GroupState::reward ? 1.0f : CL_SW_OUT;
    }
    if (rg > 0)
        for (int k = 0; k < 2; ++k)
            if (sweep_slot[k] >= 0 && sweep_slot[k] != slot && cl_plan.region_of_sweeper[k] == rg &&
                claim_of(sweep_slot[k]) != static_cast<int>(kClaimCodeDead))
                return CL_SW_OTHER;
    return 1.0f;
}

// CL_PLAN bit 2: champion-turns a job costs beyond walking, killing and capturing: the heal trip for the health the
// camps drain (bars of health x the walk home and back), and this group's share of a bank trip for its gems.
float Bot::cl_effort(const GroupRec& g, int gi, float hp_left, float team_dps) {
    if (g.camps.empty()) return 0.0f;
    const vec2 c = w.camps[static_cast<std::size_t>(g.camps[0])].pos;
    float extra = 0.0f;
    if (!g.harmless && g.state != GroupState::reward) {
        int home = fdist(w.spawn_field, c);
        if (home >= kUnreach) home = 40;
        const float bars = soak_coefficient(gi, hp_left) * camp_taken_mult / std::max(team_dps, 1.0f) / std::max(max_hp, 1.0f);
        extra += bars * (CL_HEAL0 + static_cast<float>(std::min(home, 60)));
    }
    if (g.gems > 0 && w.altar_ready) {
        int alt = fdist(w.altar_field, c);
        if (alt >= kUnreach) alt = 40;
        extra += 2.0f * static_cast<float>(std::min(alt, 60)) * static_cast<float>(g.gems) / CL_BANK_C;
    }
    return extra;
}

'''
patch("bot.cpp", "// Follow-up table for one champion alone, rebuilt once per turn in a single pass over the groups.\n",
      FUNCS + "// Follow-up table for one champion alone, rebuilt once per turn in a single pass over the groups.\n")
patch("bot.cpp",
      "            wait = static_cast<int>(wait * (NOVA_BIGCAMP * 0.01f)); // big strips respawn on a cycle: cheap waiting\n",
      "            wait = static_cast<int>(wait * (NOVA_BIGCAMP * 0.01f)); // big strips respawn on a cycle: cheap waiting\n"
      "        if ((CL_PLAN & 1) && my_sweep_region > 0 && gi < sweep_region_of.size() && sweep_region_of[gi] == my_sweep_region &&\n"
      "            !((CL_PLAN & 32) && sweep_idle()))\n"
      "            wait = static_cast<int>(static_cast<float>(wait) * CL_SW_WAITW); // CL_PLAN: a sweeper waits on its loop\n")
patch("bot.cpp",
      "        const float mid_mult = gi < mid_group.size() && mid_group[gi] ? A2_MID_W * std::exp(0.3f * LABK(40)) : 1.0f;\n",
      "        const float mid_mult = gi < mid_group.size() && mid_group[gi] ? A2_MID_W * std::exp(0.3f * LABK(40)) : 1.0f;\n"
      "        const float sw_mult = sweep_mult(static_cast<int>(gi));\n")
patch("bot.cpp", " * mid_mult *\n                tune::kStickiness /", " * mid_mult * sw_mult *\n                tune::kStickiness /")
patch("bot.cpp", "        value *= mid_mult;\n",
      "        value *= mid_mult;\n        value *= sw_mult;\n"
      "        // CL_PLAN bit 4: a carried bag makes enemy-side groups dearer (killers take bags).\n"
      "        if ((CL_PLAN & 4) && gems >= 20 && w.enemy_ready && gi < w.group_margin.size() && w.group_margin[gi] < 0)\n"
      "            value /= 1.0f + CL_RISK * static_cast<float>(gems) * static_cast<float>(-w.group_margin[gi]);\n")
patch("bot.cpp", "            capture_time + 4.0f + drain;\n",
      "            capture_time + 4.0f + drain +\n"
      "            ((CL_PLAN & 2) ? cl_effort(g, static_cast<int>(gi), hp_left, my_dps(&g) + static_cast<float>(participants - 1) * dps) : 0.0f);\n")
patch("bot.cpp",
      "    if (tune::kEarlyCarry > 0 && round < tune::kEarlyUntil) tune::kTributeCarry = std::min(tune::kTributeCarry, tune::kEarlyCarry);\n",
      "    if (tune::kEarlyCarry > 0 && round < tune::kEarlyUntil) tune::kTributeCarry = std::min(tune::kTributeCarry, tune::kEarlyCarry);\n"
      "    if ((CL_PLAN & 8) && my_sweep_region > 0) tune::kTributeCarry = std::min(tune::kTributeCarry, CL_SW_CARRY); // CL_PLAN sweeper banks small bags\n")
patch("bot.cpp", "    const auto plan = build_for(type);\n",
      "    auto plan = build_for(type);\n"
      "    if ((CL_PLAN & 16) && my_sweep_region > 0) {\n"
      "        // CL_PLAN: a sweeper captures all game: Capture (5 -> 3 turns), then Prospector (+25% cluster gems and gold).\n"
      "        using it = bc::item_type;\n"
      "        const bool fu = type == bc::champion_type::stellar || type == bc::champion_type::prism || type == bc::champion_type::willow ||\n"
      "            type == bc::champion_type::marcella || type == bc::champion_type::cassi;\n"
      "        plan.insert(plan.begin(), BuildStep{fu ? it::prospector_shard_of_focus : it::prospector_shard_of_strength, 5});\n"
      "        plan.insert(plan.begin(), BuildStep{fu ? it::capture_shard_of_focus : it::capture_shard_of_strength, 5});\n"
      "    }\n")
print("applied CL_PLAN", bits)
