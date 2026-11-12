"""CL_CREW for v220 / v139: crew size by efficiency, not by survival alone.
Ladder games: we sent one champion to camp groups where the top teams sent two or three. champions_needed() returns the
smallest crew that survives the camps' damage. Every crew member walks (approach + gathering), while the damage the
crew takes, and with it the heal trips, falls with the crew size (spread over more bodies and a faster kill):
champion-turns ~ n x walk + heal x bars1 / n, least at n = sqrt(heal x bars1 / walk), where bars1 = health bars one
champion would lose and heal = turns of a heal trip (CL_CREW_HEAL0 + the walk home). Elk groups come out at about 3,
golems 4 (cap), wolf groups 1.
BITS: 1 crew size max(survival need, sweet spot), 2 the heal trip for the crew's share of the damage enters the score.
usage: crew_patch.py SRC BITS"""
import os, sys

src, bits = sys.argv[1], int(sys.argv[2])


def patch(name, old, new):
    p = os.path.join(src, name)
    t = open(p, encoding="utf-8", newline="").read()
    assert t.count(old) == 1, (name, old[:80], t.count(old))
    open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))


patch("common.h", "#define A2_KITFIX 31\n",
      f"#define A2_KITFIX 31\n#define CL_CREW {bits}\n#define CL_CREW_GATHER 4.0f\n#define CL_CREW_CAP 4\n#define CL_CREW_HEAL0 6.0f\n")
patch("bot.cpp", "            need = champions_needed(g, hp_left);\n        }\n",
      "            need = champions_needed(g, hp_left);\n        }\n"
      "        // CL_CREW: the crew with the most gems per champion-turn, not the smallest that survives.\n"
      "        float cl_heal = 0.0f, cl_bars1 = 0.0f;\n"
      "        if ((CL_CREW & 3) && !g.harmless && g.state == GroupState::alive && hp_left > 0.0f && !g.camps.empty()) {\n"
      "            int home = fdist(w.spawn_field, w.camps[static_cast<std::size_t>(g.camps[0])].pos);\n"
      "            if (home >= kUnreach) home = 40;\n"
      "            cl_heal = CL_CREW_HEAL0 + static_cast<float>(std::min(home, 60));\n"
      "            cl_bars1 = soak_coefficient(static_cast<int>(gi), hp_left) * camp_taken_mult / std::max(my_dps(&g), 1.0f) / std::max(max_hp, 1.0f);\n"
      "            if (CL_CREW & 1) {\n"
      "                const float walk = std::max(2.0f, static_cast<float>(approach) + CL_CREW_GATHER);\n"
      "                const int sweet = static_cast<int>(std::lround(std::sqrt(cl_heal * cl_bars1 / walk)));\n"
      "                need = std::max(need, std::min(sweet, std::min(team_size, CL_CREW_CAP)));\n"
      "            }\n"
      "        }\n")
patch("bot.cpp", "        const float cost = static_cast<float>(participants) * (static_cast<float>(approach + wait) + kill) +\n",
      "        if ((CL_CREW & 2) && cl_bars1 > 0.0f) drain = std::max(drain, cl_heal * cl_bars1 / static_cast<float>(std::max(participants, 1)));\n"
      "        const float cost = static_cast<float>(participants) * (static_cast<float>(approach + wait) + kill) +\n")
print("applied CL_CREW", bits)
