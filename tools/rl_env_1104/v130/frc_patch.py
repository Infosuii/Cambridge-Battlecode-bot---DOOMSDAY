"""CL_FRC (fake-recall check) for the v139 line, after the v221 finding: 57 of 58 ladder opponents start a recall at
the end of every turn and cancel it at the start of the next, so every enemy looked passive to us (the fight search
marks a recalling enemy as unable to hit back, kiting and escape ignore it as a chaser) and we took fights we lost.
A recall now counts as real only once its remaining channel time went down since our previous look (1-2 rounds ago);
a fresh or restarted recall is a normal, dangerous enemy. Applied where the enemy list is built, so every reader of
EnemyRec::recalling() sees it. usage: frc_patch.py SRC"""
import os, sys

src = sys.argv[1]


def patch(name, old, new):
    p = os.path.join(src, name)
    t = open(p, encoding="utf-8", newline="").read()
    assert t.count(old) == 1, (name, old[:80], t.count(old))
    open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))


patch("common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_FRC 1\n")
t = open(os.path.join(src, "world.cpp"), encoding="utf-8", newline="").read()
if "#include <unordered_map>" not in t:
    i = t.index("#include")
    open(os.path.join(src, "world.cpp"), "w", encoding="utf-8", newline="").write(t[:i] + "#include <unordered_map>\n" + t[i:])
patch("world.cpp",
      "            std::uint32_t gems = 0;\n            d::sdk_champion_gems(handle, &gems);\n"
      "            enemies.push_back(EnemyRec{unit, p, info.health, info.max_health, info.strength, info.focus,\n"
      "                info.attack_range, static_cast<bc::champion_type>(info.type), static_cast<int>(gems), handle,\n"
      "                static_cast<std::uint32_t>(info.state)});\n",
      "            std::uint32_t gems = 0;\n            d::sdk_champion_gems(handle, &gems);\n"
      "            std::uint32_t st = static_cast<std::uint32_t>(info.state);\n"
      "            if (CL_FRC && (st & (1u << 1))) {\n"
      "                // CL_FRC: a recall is real only once its remaining time went down since our previous look.\n"
      "                static std::unordered_map<std::uint32_t, std::pair<int, int>> seen; // handle -> (left, round)\n"
      "                std::int32_t left = -1;\n"
      "                const int rnd = static_cast<int>(bc::round_number());\n"
      "                bool real = false;\n"
      "                if (d::sdk_champion_channel_time(handle, &left) == 0) {\n"
      "                    const auto it = seen.find(handle);\n"
      "                    real = it != seen.end() && rnd - it->second.second <= 2 && left < it->second.first;\n"
      "                    seen[handle] = {static_cast<int>(left), rnd};\n"
      "                }\n"
      "                if (!real) st &= ~(1u << 1);\n"
      "            }\n"
      "            enemies.push_back(EnemyRec{unit, p, info.health, info.max_health, info.strength, info.focus,\n"
      "                info.attack_range, static_cast<bc::champion_type>(info.type), static_cast<int>(gems), handle, st});\n")
print("applied CL_FRC")
