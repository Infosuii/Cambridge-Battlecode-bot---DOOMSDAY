"""CL_FLEECAP for v137 (v135 lineage): break perpetual flight from the outnumbered rule. handle_enemies counts every
enemy within 8 tiles (foes >= friends + k forces in_danger, threat_on_me = 1) even when none can hit us; on 04lines
(45x31, 211 camps) every champion fled every turn from round ~750 to 2000 and banked 0 gems (ladder: idle 800-1,059
rounds each, 0 gems from round 1,100 while the opponent banked 640). After CL_FLEECAP consecutive "flee" turns with no
health lost, the count-only rule is ignored for CL_FLEECAP_OFF rounds; damage-based danger (ttd) is unchanged.
usage: fleecap_patch.py SRC"""
import sys


def patch(path, old, new):
    t = open(path, encoding="utf-8", newline="").read()
    assert t.count(old) == 1, (path, old[:70], t.count(old))
    open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new))


src = sys.argv[1]
patch(src + "/common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_FLEECAP 20\n#define CL_FLEECAP_OFF 40\n")
patch(src + "/bot.h", "    bool walked = false;\n",
      "    int flee_streak = 0;              // CL_FLEECAP: consecutive turns ending in a flee mode\n"
      "    float flee_hp0 = 0.0f;            // health when the streak began\n"
      "    int outnumbered_off_until = -1;   // the count-only outnumbered rule is off until this round\n"
      "    bool walked = false;\n")
patch(src + "/bot.cpp", "        if (foes >= friends + outnumbered_k && !sure_kill) {",
      "        if (foes >= friends + outnumbered_k && !sure_kill && (!CL_FLEECAP || round >= outnumbered_off_until)) {")
anchor = '    debug_block({ std::printf("M %d %u %s %d\\n", round, my_id, mode, target_group); });\n'
patch(src + "/bot.cpp", anchor,
      "    if (CL_FLEECAP) {\n"
      "        // CL_FLEECAP: a flight that costs no health for this long is from enemies that are not attacking us\n"
      "        // (04lines: everyone fled every turn for 1,250 rounds and banked nothing). Farm again for a while.\n"
      "        if (std::string_view(mode).starts_with(\"flee\")) {\n"
      "            if (flee_streak++ == 0) flee_hp0 = hp;\n"
      "            if (flee_streak >= CL_FLEECAP && hp >= flee_hp0 - 1.0f) {\n"
      "                outnumbered_off_until = round + CL_FLEECAP_OFF;\n"
      "                flee_streak = 0;\n"
      "            }\n"
      "        } else {\n"
      "            flee_streak = 0;\n"
      "        }\n"
      "    }\n" + anchor)
print("applied fleecap")
