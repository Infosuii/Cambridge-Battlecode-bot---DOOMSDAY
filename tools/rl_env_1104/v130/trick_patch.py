"""Test opponent only (never uploaded): the fake-recall trick used by 57 of 58 ladder opponents (v221 notes). The
champion starts a recall as the last action of its turn (when not already channelling) and cancels it first thing
next turn, so opponents that read 'recalling' as 'passive' misjudge every fight. usage: trick_patch.py SRC"""
import os, sys

src = sys.argv[1]


def patch(name, old, new):
    p = os.path.join(src, name)
    t = open(p, encoding="utf-8", newline="").read()
    assert t.count(old) == 1, (name, old[:80], t.count(old))
    open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))


patch("common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_TRICK 1\n")
patch("bot.h", "    float soak_coefficient(int group, float hp_left);\n",
      "    float soak_coefficient(int group, float hp_left);\n    bool trick_recall = false; // CL_TRICK test opponent: our fake recall is running\n")
patch("bot.cpp", "    round = static_cast<int>(bc::round_number());\n    if (!inited) {\n",
      "    round = static_cast<int>(bc::round_number());\n"
      "    if (CL_TRICK && trick_recall) {\n"
      "        trick_recall = false;\n"
      "        try {\n"
      "            if (me.state().contains(bc::champion_state::recalling)) me.cancel_recall();\n"
      "        } catch (...) {\n"
      "        }\n"
      "    }\n"
      "    if (!inited) {\n")
patch("bot.cpp", "    build_fields();\n    PROF_CHECK(\"fields\");\n",
      "    build_fields();\n    PROF_CHECK(\"fields\");\n"
      "    if (CL_TRICK && !trick_recall) {\n"
      "        try {\n"
      "            const auto s = me.state();\n"
      "            if (!s.contains(bc::champion_state::recalling) && !s.contains(bc::champion_state::submitting_gems) &&\n"
      "                !s.contains(bc::champion_state::teleporting) && !s.is_dead()) {\n"
      "                me.recall();\n"
      "                trick_recall = true;\n"
      "            }\n"
      "        } catch (...) {\n"
      "        }\n"
      "    }\n")
print("applied CL_TRICK (test opponent)")
