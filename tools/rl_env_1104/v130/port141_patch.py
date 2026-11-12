"""Port Om's v141 gameplay fixes (on top of v220) to the v139 line. usage: port141_patch.py SRC
1. walking: with enemies in sight, diagonal steps first; the equal-path centring only on quiet routes;
2. twin guard: Cassi or Issac under close pressure (2+ extra enemies, nearest within 5) backs off: a linked body's
   death can cost the partner's bag too;
3. home siege: a carrier ready to bank does not restart the home farming cycle;
4. channel guard: enemies just outside reach (range + 2) count only for a fringe horizon on long deposits."""
import os, sys

src = sys.argv[1]


def patch(name, old, new):
    p = os.path.join(src, name)
    t = open(p, encoding="utf-8", newline="").read()
    assert t.count(old) == 1, (name, old[:80], t.count(old))
    open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))


B = "bot.cpp"
patch(B, "    if (allow_dash) try_dash(field, blocked);\n",
      "    if (allow_dash) try_dash(field, blocked);\n    const bool quiet_route = w.enemies.empty(); // v141: path centring only with no enemy in sight\n")
patch(B, "        cands[n++] = {q, dq * 512};\n",
      "        const int bias = !quiet_route && (dir.x == 0 || dir.y == 0) ? 1 : 0; // v141: diagonals first under threat\n"
      "        cands[n++] = {q, dq * 512 + bias};\n")
patch(B, "    if (n > 1) {\n        // Equal-length paths often fan out.", "    if (quiet_route && n > 1) {\n        // Equal-length paths often fan out.")
patch(B, "            winning = false;\n            if (threat_on_me <= 0) threat_on_me = 1.0f;\n        }\n    }\n    // A2_LANCH2 (E81)",
      "            winning = false;\n            if (threat_on_me <= 0) threat_on_me = 1.0f;\n        }\n"
      "        // v141 twin guard: a linked body (Cassi or Issac) under close pressure can lose its partner's bag too.\n"
      "        if ((type == bc::champion_type::cassi || type == bc::champion_type::issac) && !sure_kill && foes >= friends + 2 &&\n"
      "            nearest_d <= 5 && !bit(w.ally_spawn, pos)) {\n"
      "            winning = false;\n            in_danger = true;\n            if (threat_on_me <= 0) threat_on_me = 1.0f;\n        }\n"
      "    }\n    // A2_LANCH2 (E81)")
patch(B, "bool Bot::home_siege() {\n    if (!HS_ON || round < HS_FROM || slot >= HS_CREW) return false;\n",
      "bool Bot::home_siege() {\n    if (!HS_ON || round < HS_FROM || slot >= HS_CREW) return false;\n"
      "    if (!w.no_bank && gems > 0 && gems >= tune::kTributeCarry) return false; // v141: a carrier banks first\n")
patch(B, "bool Bot::retry_channel(ChannelRetry::Kind kind, vec2 altar) {\n",
      "// v141: the channel guard. A distant contact is uncertain over a large deposit: keep the full guard for enemies that\n"
      "// can attack after one step and count the fringe (range + 2) only over a short horizon.\n"
      "bool Bot::channel_danger(ChannelRetry::Kind kind, int duration) const {\n"
      "    if (tune::kChannelGuard <= 0.0f) return false;\n"
      "    const int projection = duration + 1;\n"
      "    const int fringe_horizon = 6;\n"
      "    const bool long_deposit = kind == ChannelRetry::submit && gems >= 150 && projection > fringe_horizon;\n"
      "    float incoming = 0.0f, fringe = 0.0f;\n"
      "    for (const auto& e : w.enemies) {\n"
      "        const int dist = cheb(e.pos, pos);\n"
      "        if (dist > e.range + 2) continue;\n"
      "        const float estimate = e.strength + e.focus * 0.5f;\n"
      "        if (long_deposit && dist == e.range + 2) fringe += estimate;\n"
      "        else incoming += estimate;\n"
      "    }\n"
      "    const float damage = incoming * static_cast<float>(projection) + fringe * static_cast<float>(fringe_horizon);\n"
      "    return damage * tune::kChannelGuard >= hp;\n"
      "}\n\n"
      "bool Bot::retry_channel(ChannelRetry::Kind kind, vec2 altar) {\n")
patch(B, "    float incoming = 0.0f;\n    for (const auto& e : w.enemies)\n"
         "        if (cheb(e.pos, pos) <= e.range + 2) incoming += e.strength + e.focus * 0.5f;\n    int duration = bc::constants::recall_time;\n",
      "    int duration = bc::constants::recall_time;\n")
patch(B, "    bool unsafe = tune::kChannelGuard > 0.0f && incoming * static_cast<float>(duration + 1) * tune::kChannelGuard >= hp;\n",
      "    bool unsafe = channel_danger(kind, duration);\n")
patch(B, "        float incoming = 0.0f;\n        for (const auto& e : w.enemies)\n"
         "            if (cheb(e.pos, pos) <= e.range + 2) incoming += e.strength + e.focus * 0.5f;\n"
         "        if (incoming * static_cast<float>(left + 1) * tune::kChannelGuard < hp) return;\n",
      "        const auto channel = state.contains(bc::champion_state::submitting_gems) ? ChannelRetry::submit : ChannelRetry::recall;\n"
      "        if (!channel_danger(channel, left)) return;\n")
patch("bot.h", "    bool retry_channel(ChannelRetry::Kind kind, vec2 altar = {-1, -1});\n",
      "    bool channel_danger(ChannelRetry::Kind kind, int duration) const;\n    bool retry_channel(ChannelRetry::Kind kind, vec2 altar = {-1, -1});\n")
print("applied v141 port")
