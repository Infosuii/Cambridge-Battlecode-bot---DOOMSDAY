"""Neural bot step 1: v4/bots/nnrec = v92 + A2_NNREC, a recorder for imitation data (agent2/plans/neural_bot_2026-11-03.md).
Every sampled turn each champion prints one line to stdout (kept in the real engine's replay bundle, team-?.stdout):
    NR <round> <slot> <fight> <features: base64 int16 x kNF> <mode> <target_group> <heading_home> | <actions>
features = global 16, self 32, 5 allies x 12, 8 enemies x 16, 10 camp groups x 16, 4 altars x 8 (layout in nnrec.cpp);
actions = every SDK action call of the whole turn with its result (wrapped imports, recorder build only):
    m:x,y,ok  a:kind,handle,rc  c:slot,kind,handle,x,y,ok  bi:item,count  bc:id  u:id,x,y,ok  r  s:x,y  w:x,y,ok  sl:item  cc
Once per champion: NRC <slot> camp handle:group index pairs (maps camp attack targets to groups offline).
usage (project root): python -P agent2/lab/nn_mkrec.py [STRIDE=4]"""
import os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
B = os.path.join(ROOT, "v4", "bots")
STRIDE = int(sys.argv[1]) if len(sys.argv) > 1 else 4
shutil.rmtree(B + "/nnrec", ignore_errors=True)
shutil.copytree(B + "/v92", B + "/nnrec", ignore=shutil.ignore_patterns(".cambc"))
S = B + "/nnrec/src/"


def patch(fn, old, new, count=1):
    s = open(S + fn, encoding="utf-8").read()
    assert s.count(old) == count, (fn, old[:60], s.count(old))
    open(S + fn, "w", encoding="utf-8", newline="\n").write(s.replace(old, new))


# SDK action imports wrapped (recorder build only; the shared SDK is untouched): a bot-local copy of cambc.h
# (cambc_rec.h) gets wrappers that call the real imports right after its include of imports.h, then macros, so its
# own calls go through the wrappers.
WRAP = """#include <string>
namespace nnrec {{
inline std::string acts; // this turn's SDK actions
inline void add(const char* fmt, long a = 0, long b = 0, long c = 0, long d = 0, long e = 0, long f = 0) {{
    char buf[96];
    std::snprintf(buf, sizeof buf, fmt, a, b, c, d, e, f);
    if (!acts.empty()) acts += ' ';
    acts += buf;
}}
}} // namespace nnrec
namespace cambc::detail {{
inline std::int32_t nnrec_move_to(std::int32_t x, std::int32_t y, std::int32_t* ok) {{
    const std::int32_t rc = sdk_move_to(x, y, ok); nnrec::add("m:%ld,%ld,%ld", x, y, rc == 0 && ok && *ok); return rc; }}
inline std::int32_t nnrec_attack(std::uint32_t k, std::uint32_t h) {{
    const std::int32_t rc = sdk_attack(k, h); nnrec::add("a:%ld,%ld,%ld", k, h, rc); return rc; }}
inline std::int32_t nnrec_cast(std::uint32_t s, std::uint32_t k, std::uint32_t h, std::int32_t x, std::int32_t y, std::int32_t* ok) {{
    const std::int32_t rc = sdk_cast(s, k, h, x, y, ok); nnrec::add("c:%ld,%ld,%ld,%ld,%ld,%ld", s, k, h, x, y, rc == 0 && ok && *ok); return rc; }}
inline std::int32_t nnrec_buy_item(std::uint32_t t, std::uint32_t n) {{
    const std::int32_t rc = sdk_buy_item(t, n); if (rc == 0) nnrec::add("bi:%ld,%ld", t, n); return rc; }}
inline std::int32_t nnrec_buy_consumable(std::uint32_t t) {{
    const std::int32_t rc = sdk_buy_consumable(t); if (rc == 0) nnrec::add("bc:%ld", t); return rc; }}
inline std::int32_t nnrec_use_consumable(std::uint32_t t, std::int32_t x, std::int32_t y, std::int32_t* ok) {{
    const std::int32_t rc = sdk_use_consumable(t, x, y, ok); nnrec::add("u:%ld,%ld,%ld,%ld", t, x, y, rc == 0 && ok && *ok); return rc; }}
inline std::int32_t nnrec_recall() {{ const std::int32_t rc = sdk_recall(); if (rc == 0) nnrec::add("r"); return rc; }}
inline std::int32_t nnrec_submit_gems(std::int32_t x, std::int32_t y) {{
    const std::int32_t rc = sdk_submit_gems(x, y); if (rc == 0) nnrec::add("s:%ld,%ld", x, y); return rc; }}
inline std::int32_t nnrec_place_ward(std::int32_t x, std::int32_t y, std::int32_t* ok) {{
    const std::int32_t rc = sdk_place_ward(x, y, ok); nnrec::add("w:%ld,%ld,%ld", x, y, rc == 0 && ok && *ok); return rc; }}
inline std::int32_t nnrec_sell(std::uint32_t t) {{ const std::int32_t rc = sdk_sell(t); if (rc == 0) nnrec::add("sl:%ld", t); return rc; }}
inline std::int32_t nnrec_cancel_channel() {{ const std::int32_t rc = sdk_cancel_channel(); if (rc == 0) nnrec::add("cc"); return rc; }}
}} // namespace cambc::detail
#define sdk_move_to nnrec_move_to
#define sdk_attack nnrec_attack
#define sdk_cast nnrec_cast
#define sdk_buy_item nnrec_buy_item
#define sdk_buy_consumable nnrec_buy_consumable
#define sdk_use_consumable nnrec_use_consumable
#define sdk_recall nnrec_recall
#define sdk_submit_gems nnrec_submit_gems
#define sdk_place_ward nnrec_place_ward
#define sdk_sell nnrec_sell
#define sdk_cancel_channel nnrec_cancel_channel
""".replace("{{", "{").replace("}}", "}")
sdk = open(os.path.join(ROOT, "v4", "sdk", "cpp", "cambc.h"), encoding="utf-8").read()
assert sdk.count('#include "imports.h"\n') == 1
sdk = sdk.replace('#include "imports.h"\n', '#include "imports.h"\n' + WRAP)
open(S + "cambc_rec.h", "w", encoding="utf-8", newline="\n").write("// Recorder copy of the SDK's cambc.h (agent2/lab/nn_mkrec.py)\n" + sdk)
patch("common.h", "#include <cambc.h>\n", f"""#ifndef A2_NNREC
#define A2_NNREC {STRIDE} // neural bot recorder: sample stride in rounds (0 = off)
#endif
#if A2_NNREC
#include "cambc_rec.h"
#else
#include <cambc.h>
#endif
""")
patch("bot.h", "class Bot {\npublic:\n    void play_turn();\n", """class Bot {
public:
    void play_turn();
#if A2_NNREC
    void nn_feats(std::int16_t* f, int near); // the 500 network features of this turn (nnrec.cpp)
    template <int NC, int AF> void nn_feats_t(std::int16_t* f, int near, int parts = 3); // parts: 1 all but camps, 2 camps
    void nn_feats3(std::int16_t* f, int near); // version 3: 24 camp groups + allies' claimed targets (828)
    int nn_near() const;
    void nn_track();             // per-turn history for the network's memory features
    void nnrec_begin();          // after the world update: features of this turn (if sampled)
    void nnrec_end();            // after the turn: print features + v92's decisions + every action
    std::string nnrec_line;      // features of the sampled turn ("" = not sampled)
    bool nnrec_camps_done = false;
#endif
""")
patch("bot.cpp", "        if (tune::kBelief) w.update_beliefs(round, tune::kDet ? static_cast<std::uint64_t>(tune::kDetSafety) : 40000);\n",
      "        if (tune::kBelief) w.update_beliefs(round, tune::kDet ? static_cast<std::uint64_t>(tune::kDetSafety) : 40000);\n"
      "#if A2_NNREC\n        nnrec_begin();\n#endif\n")
patch("main.cpp", "            else\n                bot.play_turn();\n#endif", """            else {
#if A2_NNREC
                nnrec::acts.clear();
                bot.nnrec_line.clear();
#endif
                bot.play_turn();
#if A2_NNREC
                bot.nnrec_end();
#endif
            }
#endif""")
shutil.copy(os.path.join(ROOT, "agent2", "lab", "nnrec.cpp"), S + "nnrec.cpp")
print("nnrec written, stride", STRIDE)
