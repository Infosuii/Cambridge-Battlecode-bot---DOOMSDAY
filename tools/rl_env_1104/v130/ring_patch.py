"""CL_RING (standstill fix) for the v139 line: the crew staging ring was a fixed 5 tiles around the camps minus the
danger zone; around camps whose reach covers it nothing was left, walk_toward got an empty goal and the champion stood
still until the 60-round walk timeout. The ring now sits outside the live camps' actual reach (widened a tile at a
time until a tile exists), and an empty ring or 3 failed walks in a row release the job. usage: ring_patch.py SRC"""
import os, sys

src = sys.argv[1]


def patch(name, old, new):
    p = os.path.join(src, name)
    t = open(p, encoding="utf-8", newline="").read()
    assert t.count(old) == 1, (name, old[:80], t.count(old))
    open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))


patch("common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_RING 1\n")
patch("bot.cpp",
      "        bc::bitboard stage;\n        stage.clear();\n        for (int ci : g.camps)\n"
      "            if (!w.camps[ci].dead) stage.draw_chebyshev(w.camps[ci].pos, 5.0f);\n        stage &= ~danger_zone;\n",
      "        bc::bitboard stage;\n        stage.clear();\n"
      "        static int ring_fails = 0; // CL_RING: failed walks to the ring release the job\n"
      "        if (CL_RING) {\n"
      "            // CL_RING: the ring sits outside the live camps' actual reach, widened until a tile exists.\n"
      "            int reach = 3;\n"
      "            for (int ci : g.camps)\n"
      "                if (!w.camps[ci].dead) reach = std::max(reach, w.camps[ci].range);\n"
      "            for (int r = std::max(5, reach + 1); r <= reach + 3; ++r) {\n"
      "                stage.clear();\n"
      "                for (int ci : g.camps)\n"
      "                    if (!w.camps[ci].dead) stage.draw_chebyshev(w.camps[ci].pos, static_cast<float>(r));\n"
      "                stage &= ~danger_zone & ~w.static_blocked;\n"
      "                if (!stage.is_empty()) break;\n"
      "            }\n"
      "        } else {\n"
      "            for (int ci : g.camps)\n"
      "                if (!w.camps[ci].dead) stage.draw_chebyshev(w.camps[ci].pos, 5.0f);\n"
      "            stage &= ~danger_zone;\n"
      "        }\n")
patch("bot.cpp",
      "        if (!bit(stage, pos)) walk_toward(stage);\n        // Spells reach 4 tiles, one more than camps: chip damage for free while we wait.\n",
      "        if (!CL_RING) {\n            if (!bit(stage, pos)) walk_toward(stage);\n"
      "        } else if (!bit(stage, pos)) {\n"
      "            if (!stage.is_empty() && walk_toward(stage)) ring_fails = 0;\n"
      "            else if (++ring_fails >= 3 || stage.is_empty()) {\n"
      "                ring_fails = 0;\n"
      "                avoid_until[target_group] = round + 30;\n"
      "                staging_since = -1;\n"
      "                staging_walk_since = -1;\n"
      "                return false;\n"
      "            }\n"
      "        } else {\n            ring_fails = 0;\n        }\n"
      "        // Spells reach 4 tiles, one more than camps: chip damage for free while we wait.\n")
print("applied CL_RING")
