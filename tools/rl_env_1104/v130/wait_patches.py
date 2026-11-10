"""Camping optimisations for v130's wait-respawn (03twisty: champions stand beside 120-hp home camps 15-22% of the
game; the waits earn the team's average rate, but 18% of them are a second champion waiting on the same camp).
  A  waitshop30: while waiting, go home to shop from 30 gold (one shard) instead of 90
  B  waitbank5:  while waiting, bank from 5 gems instead of 10 when the altar round trip fits before the respawn
  C  nodupwait:  a respawning solo group an earlier claimant already holds is skipped, not valued at 15%
usage: wait_patches.py SRC A|B|C ..."""
import sys


def patch(path, old, new):
    t = open(path, encoding="utf-8", newline="").read()
    assert t.count(old) == 1, (old[:60], t.count(old))
    open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new))


def a(src):
    patch(src + "/bot.cpp",
          "            if (gold >= 90 && !shop_done && wait > home_trip + 4 && type != bc::champion_type::tavi) {",
          "            if (gold >= 30 && !shop_done && wait > home_trip + 4 && type != bc::champion_type::tavi) { // CL waitshop30")


def b(src):
    patch(src + "/bot.cpp", "            const int altar_trip = gems >= 10 && w.ensure_altar_field()",
          "            const int altar_trip = gems >= 5 && w.ensure_altar_field()")
    patch(src + "/bot.cpp", "            if (gems >= 10 && wait > altar_trip + 2) {",
          "            if (gems >= 5 && wait > altar_trip + 2) { // CL waitbank5")


def c(src):
    anchor = "        const bool solo_job = need == 1 && (g.state == GroupState::reward || hp_left < 1500.0f);\n"
    patch(src + "/bot.cpp", anchor, anchor +
          "        // CL nodupwait: one champion takes a small respawning group's reward, so a second waiter beside it adds\n"
          "        // nothing (03twisty: 18% of the camping time was a second champion waiting on the same 120-hp camp).\n"
          "        if (g.state == GroupState::respawning && solo_job && senior_claims(static_cast<int>(gi)) > 0) continue;\n")


src = sys.argv[1]
for name in sys.argv[2:]:
    {"A": a, "B": b, "C": c}[name](src)
    print("applied", name)
