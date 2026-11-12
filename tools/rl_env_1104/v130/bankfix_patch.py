"""CL_BANKFIX for the v139 line. Ladder match 01a1c6ca (enemy holding the middle altars, 3+ champions there for 76
rounds): we deposited 0 times in 615 rounds and carried up to ~200 gems while they deposited 30 times. The route to the
altar treats recent enemy sightings as blocked, the carrier approaches and backs off, and after 20 turns without
progress banking was shelved for 80 rounds. Now (1) a carrier of 30+ gems retries after 15 rounds, and (2) any bag of
15+ is banked when an altar is within 12 steps and no enemy is in sight (short deposits in quiet moments).
usage: bankfix_patch.py SRC"""
import os, sys

src = sys.argv[1]


def patch(name, old, new):
    p = os.path.join(src, name)
    t = open(p, encoding="utf-8", newline="").read()
    assert t.count(old) == 1, (name, old[:80], t.count(old))
    open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))


patch("common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_BANKFIX 1\n")
patch("bot.cpp", "                tribute_off_until = round + 80;\n",
      "                tribute_off_until = round + (CL_BANKFIX && gems >= 30 ? 15 : 80); // CL_BANKFIX: a big bag retries soon\n")
patch("bot.cpp", "        dist <= tune::kTributeNearDist + static_cast<int>(std::lround(2.0f * LABK(36))) || (threatened && gems >= 20 && dist <= 8);\n",
      "        dist <= tune::kTributeNearDist + static_cast<int>(std::lround(2.0f * LABK(36))) || (threatened && gems >= 20 && dist <= 8) ||\n"
      "        (CL_BANKFIX && gems >= 15 && dist <= 12 && w.enemies.empty()); // CL_BANKFIX: bank in quiet moments\n")
print("applied CL_BANKFIX")
