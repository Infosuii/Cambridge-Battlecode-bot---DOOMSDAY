"""CL_JOIN for v220 (A2_TEAM bit 2): a2_join_fight walked a healthy champion into any ally's fight within 8 tiles
unless our side was already winning, also when the ally was badly outnumbered: champions arrived one by one into a
lost fight (mid-game wipes of 3 champions). Now a champion joins only if, with it, our side at that fight would at
least match the enemies there. usage: join_patch.py SRC"""
import os, sys

src = sys.argv[1]


def patch(name, old, new):
    p = os.path.join(src, name)
    t = open(p, encoding="utf-8", newline="").read()
    assert t.count(old) == 1, (name, old[:80], t.count(old))
    open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))


patch("common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_JOIN 1\n")
patch("bot.cpp", "        if (friends > foes + 1) continue; // already winning there without us\n",
      "        if (friends > foes + 1) continue; // already winning there without us\n"
      "        if (CL_JOIN && friends + 1 < foes) continue; // CL_JOIN: still outnumbered with us: do not walk in one by one\n")
print("applied CL_JOIN")
