"""CL_SPAWNSAFE for v137: on our own spawn the heal restores us fully every round (spawn_healing 1.0), so standing
there is only dangerous when the enemies in reach kill us within about two rounds. 04lines (local, vs v112opp): the
enemy team waited 3-4 tiles outside our spawn and every champion fled in place for 1,250 rounds without losing health.
usage: spawnsafe_patch.py SRC"""
import sys


def patch(path, old, new):
    t = open(path, encoding="utf-8", newline="").read()
    assert t.count(old) == 1, (path, old[:70], t.count(old))
    open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new))


src = sys.argv[1]
patch(src + "/common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_SPAWNSAFE 1\n")
anchor = ("    // A2_LANCH2 (E81): fitted Lanchester engagement (Game AI Pro 3 ch. 25; lanch_model.h from forced arena fights).\n")
patch(src + "/bot.cpp", anchor,
      "    if (CL_SPAWNSAFE && in_danger && bit(w.ally_spawn, pos) && bc::constants::spawn_healing >= 0.99f && ttd >= 2.0f)\n"
      "        in_danger = false; // CL_SPAWNSAFE: the spawn heals us fully each round; only a two-round kill is a danger here\n"
      + anchor)
print("applied spawnsafe")
