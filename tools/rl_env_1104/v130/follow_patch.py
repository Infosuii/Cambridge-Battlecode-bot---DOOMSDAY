"""CL_FOLLOW for v139: the route planner's follow-up table zeroed every group a champion cannot clear alone (and every
group a teammate claims), so a champion waiting at a big respawning camp never planned "small camp now, big camp when
it respawns". A respawning group whose crew is already forming (teammates claim it, and with us they meet its need at
full health) is now a follow-up at this champion's share: value / crew and kill time / crew.
usage: follow_patch.py SRC"""
import os, sys

src = sys.argv[1]


def patch(name, old, new):
    p = os.path.join(src, name)
    t = open(p, encoding="utf-8", newline="").read()
    assert t.count(old) == 1, (name, old[:80], t.count(old))
    open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))


patch("common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_FOLLOW 1\n")
patch("bot.cpp",
      "    const float base_dps = my_dps(nullptr);\n    for (std::size_t gi = 0; gi < n; ++gi) {\n        const auto& g = w.groups[gi];\n"
      "        const float dps = (type == bc::champion_type::varg",
      "    const float base_dps = my_dps(nullptr);\n"
      "    static std::vector<char> crew_follow; // CL_FOLLOW: crew follow-ups survive the claim filter below\n"
      "    crew_follow.assign(n, 0);\n    for (std::size_t gi = 0; gi < n; ++gi) {\n        const auto& g = w.groups[gi];\n"
      "        const float dps = (type == bc::champion_type::varg")
patch("bot.cpp",
      "        const bool solo = g.harmless || g.strength * kill < hp * 0.8f;\n"
      "        if (!solo || avoid_until[gi] > round) value = 0.0f;\n"
      "        follow_value[gi] = value;\n"
      "        follow_fixed[gi] = kill + static_cast<float>(capture_time) + 4.0f;\n",
      "        bool solo = g.harmless || g.strength * kill < hp * 0.8f;\n"
      "        float crew = 1.0f;\n"
      "        if (!solo && CL_FOLLOW && g.state == GroupState::respawning && avoid_until[gi] <= round) {\n"
      "            // CL_FOLLOW: a crew already forms at this respawning group; we join for our share after a small job.\n"
      "            const int others = claim_count(static_cast<int>(gi));\n"
      "            if (others > 0) {\n"
      "                const int need = champions_needed(g, g.max_hp);\n"
      "                if (need <= team_size && others + 1 >= need) {\n"
      "                    solo = true;\n"
      "                    crew = static_cast<float>(others + 1);\n"
      "                    crew_follow[gi] = 1;\n"
      "                }\n"
      "            }\n"
      "        }\n"
      "        if (!solo || avoid_until[gi] > round) value = 0.0f;\n"
      "        follow_value[gi] = value / crew;\n"
      "        follow_fixed[gi] = kill / crew + static_cast<float>(capture_time) + 4.0f;\n")
patch("bot.cpp",
      "        if (s != slot && c >= 0 && c < static_cast<int>(n)) follow_value[static_cast<std::size_t>(c)] = 0.0f;\n",
      "        if (s != slot && c >= 0 && c < static_cast<int>(n) && !crew_follow[static_cast<std::size_t>(c)])\n"
      "            follow_value[static_cast<std::size_t>(c)] = 0.0f;\n")
print("applied CL_FOLLOW")
