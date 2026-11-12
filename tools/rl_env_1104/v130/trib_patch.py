"""CL_TRIBALERT for v137: use the dormant distress bit (APEX_DISTRESS is 0) of the shared sighting for an enemy banking
a big bag. A tributer cannot move and only a kill (or a stun, which frees it) ends the channel, so the champion that
sees it publishes it with bit 62 (share_sighting already keeps such a sighting for 2 rounds against overwrites), and
healthy allies within CL_TRIB_RANGE that cannot see it walk over (hunt(): "deny-trib"); handle_enemies' tribute denial
takes over on arrival. usage: trib_patch.py SRC"""
import sys


def patch(path, old, new):
    t = open(path, encoding="utf-8", newline="").read()
    assert t.count(old) == 1, (path, old[:70], t.count(old))
    open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new))


src = sys.argv[1]
patch(src + "/common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_TRIBALERT 30\n#define CL_TRIB_RANGE 10\n")
B = src + "/bot.cpp"
patch(B, "    for (const auto& e : w.enemies)\n        if (!best || cheb(e.pos, pos) < cheb(best->pos, pos)) best = &e;\n    if (!best) return;\n",
      "    for (const auto& e : w.enemies)\n        if (!best || cheb(e.pos, pos) < cheb(best->pos, pos)) best = &e;\n    if (!best) return;\n"
      "    if (CL_TRIBALERT > 0)\n"
      "        for (const auto& e : w.enemies)\n"
      "            if (e.tributing() && e.gems >= CL_TRIBALERT) {\n"
      "                // CL_TRIBALERT: an enemy banking a big bag cannot move; flag it for allies out of sight of it.\n"
      "                best = &e;\n"
      "                call_for_help = true;\n"
      "                break;\n"
      "            }\n")
patch(B, "    // Answer a teammate's distress call: the enemy chasing them is out of position.\n",
      "    if (CL_TRIBALERT > 0 && round - distress.round <= 2 && hp >= max_hp * 0.5f && gems < 60) {\n"
      "        // CL_TRIBALERT: a teammate sees an enemy banking a big bag nearby; go and take it before the channel ends.\n"
      "        const int d = cheb(distress.pos, pos);\n"
      "        if (d > 0 && d <= CL_TRIB_RANGE) {\n"
      "            mode = \"deny-trib\";\n"
      "            bc::bitboard goal;\n"
      "            goal.clear();\n"
      "            goal.draw_chebyshev(distress.pos, static_cast<float>(range));\n"
      "            walk_toward(goal);\n"
      "            return true;\n"
      "        }\n"
      "    }\n"
      "    // Answer a teammate's distress call: the enemy chasing them is out of position.\n")
print("applied trib alert")
