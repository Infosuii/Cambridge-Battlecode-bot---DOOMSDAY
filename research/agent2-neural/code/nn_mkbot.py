"""Neural bot: v4/bots/NAME = v92 + A2_NN (the student network from nn_train.py / nn_export.py decides; v92's code
executes). A2_NN bits: 1 farming target group (farm() takes the network's group), 2 banking (v92's ordinary tribute
call runs only when the network's behaviour head says bank; then the trip is forced). With A2_NN_MACRO=1 (macro
policy: behaviour options held until done, nnrec.cpp): 4 the fight / flee verdict in contact, 8 the out-of-contact
options (farm / bank / hunt / home / regroup; nn_option_out), and RL rows per turn (NRB, main.cpp -> nn_rl_end).
Features: nnrec.cpp nn_feats, the same code the recorder used for the training data.
usage (project root): python -P agent2/lab/nn_mkbot.py NAME WEIGHTS.h [A2_NN=3] [KEY=VALUE ...]"""
import os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
B = os.path.join(ROOT, "v4", "bots")
LAB = os.path.join(ROOT, "agent2", "lab")
NAME, WEIGHTS = sys.argv[1], sys.argv[2]
defs = dict(a.split("=", 1) for a in sys.argv[3:])
BASE = defs.pop("BASE", "v92")  # BASE=nnrec: DAgger recorder (the network acts, the log keeps v92's choice as the label)
nnbits = defs.pop("A2_NN", "3")
# TOP_NAME=VALUE: define NAME at the very top of common.h (switches such as LADDER_TABLES / A2_LADFIT are set there)
top = {k[4:]: defs.pop(k) for k in list(defs) if k.startswith("TOP_")}
shutil.rmtree(os.path.join(B, NAME), ignore_errors=True)
shutil.copytree(os.path.join(B, BASE), os.path.join(B, NAME), ignore=shutil.ignore_patterns(".cambc"))
S = os.path.join(B, NAME, "src") + os.sep


def patch(fn, old, new, count=1):
    s = open(S + fn, encoding="utf-8").read()
    assert s.count(old) == count, (fn, old[:60], s.count(old))
    open(S + fn, "w", encoding="utf-8", newline="\n").write(s.replace(old, new))


# A2_NN_DPLAN=1 (E122): the draft turn's 10M fuel computes the map analysis and a team opening schedule (mappre.h, sched.h, E62) passed
# through draft memory; the plan's current step overrides the network's target in the opening (nn_decide).
# A2_NN_XF=1 (E123): the same analysis as network inputs instead of an override: A2_DP_UNTIL -1 turns off every direct effect of the plan.
xf = defs.get("A2_NN_XF", "0") != "0"
if xf:
    top.setdefault("A2_DP_UNTIL", "-1")
dplan = defs.get("A2_NN_DPLAN", "0") != "0" or xf
if dplan:  # (at the top of common.h: its own defaults come before the define block below)
    for k, v in (("A2_DPLAN", "1"), ("A2_MAPPRE", "1"), ("A2_SCHED", "1"), ("A2_SCHED_ROLLOUTS", "48"), ("A2_SCHED_MOVES", "1500")):
        top.setdefault(k, v)
extra = "".join(f"#ifndef {k}\n#define {k} {v}\n#endif\n" for k, v in defs.items())
ANCHOR = "#ifndef A2_NNREC\n" if BASE == "nnrec" else "#include <cambc.h>\n"  # the recorder's own block comes first
patch("common.h", ANCHOR, f"""{extra}#ifndef A2_NN
#define A2_NN {nnbits} // neural bot: 1 target group, 2 banking; with A2_NN_MACRO: 4 contact verdict, 8 options
#endif
#ifndef A2_NN_MACRO
#define A2_NN_MACRO 0
#endif
#ifndef A2_NN_LAYOUT
#define A2_NN_LAYOUT 2 // the acting network's feature layout (2 = 500, 3 = 828)
#endif
#ifndef A2_NNREC_LAYOUT
#define A2_NNREC_LAYOUT 2 // layout the recorder logs
#endif
#ifndef A2_NNREC
#define A2_NNREC 0
#endif
#if defined(A2_NN_LIVE) && A2_NN_LIVE
inline unsigned long long nn_field_fuel = 0; // fuel of v92's optional distance-field building this turn (build_fields)
inline unsigned long long nn_spent = 0;      // fuel the network spent so far this turn (v92's fuel checks add it back)
inline unsigned long long nn_sg_need = 0;    // A2_NN_SGAUTO: what the scoring will need after v92's target search
#endif
{ANCHOR}
""")
# A2_NN_SGCACHE=n (E123): v92's target search runs every n rounds while its pick stays open (22k fuel on average; the blend only needs it as an anchor).
patch("bot.h", "    int score_groups(int participants_hint, int& best_need, float& best_score);\n",
      "    int score_groups(int participants_hint, int& best_need, float& best_score);\n#if defined(A2_NN_SGCACHE) || defined(A2_NN_SGAUTO)\n    int score_groups_full(int participants_hint, int& best_need, float& best_score);\n#endif\n")
patch("bot.cpp", "int Bot::score_groups(int participants_hint, int& best_need, float& best_score) {\n", """#ifdef A2_NN_SGCACHE
int Bot::score_groups(int participants_hint, int& best_need, float& best_score) {
    static int last = -1000, hint = -1, pick = -1, need = 1;
    static float sc = 0.0f;
    if (round - last < A2_NN_SGCACHE && hint == participants_hint && pick >= 0 && pick == target_group && pick < static_cast<int>(w.groups.size()) &&
        w.groups[static_cast<std::size_t>(pick)].state != GroupState::respawning && avoid_until[static_cast<std::size_t>(pick)] <= round) {
        best_need = need, best_score = sc;
        return pick;
    }
    pick = score_groups_full(participants_hint, best_need, best_score);
    last = round, hint = participants_hint, need = best_need, sc = best_score;
    return pick;
}
int Bot::score_groups_full(int participants_hint, int& best_need, float& best_score) {
#elif defined(A2_NN_SGAUTO)
// E124: on a turn the fuel cannot cover both v92's search and the network's scoring, the search is the one skipped: its last pick stands, if still open
int Bot::score_groups(int participants_hint, int& best_need, float& best_score) {
    static int hint = -1, pick = -1, need = 1;
    static float sc = 0.0f;
    static std::uint64_t est = 25000;
    const std::uint64_t left = bc::fuel_remaining();
    if (nn_sg_need && left < nn_sg_need + est && hint == participants_hint && pick >= 0 && pick < static_cast<int>(w.groups.size()) &&
        w.groups[static_cast<std::size_t>(pick)].state != GroupState::respawning && avoid_until[static_cast<std::size_t>(pick)] <= round) {
        best_need = need, best_score = sc;
        return pick;
    }
    pick = score_groups_full(participants_hint, best_need, best_score);
    const std::uint64_t now = bc::fuel_remaining();
    if (left > now) est = std::max(left - now, est - est / 32);
    hint = participants_hint, need = best_need, sc = best_score;
    return pick;
}
int Bot::score_groups_full(int participants_hint, int& best_need, float& best_score) {
#else
int Bot::score_groups(int participants_hint, int& best_need, float& best_score) {
#endif
""")
# A2_NN_LIVE: the first turn's doubled budget goes to the distance fields, all but a small reserve (v92 stopped after 4 fields and
# left about 60k unused), and field building is measured so it does not count as fuel v92 needs (it only takes what is left).
patch("bot.cpp", "void Bot::build_fields() {\n", """void Bot::build_fields() {
#if defined(A2_NN_LIVE) && A2_NN_LIVE
    struct NNFieldFuel {
        std::uint64_t f0 = bc::fuel_remaining();
        ~NNFieldFuel() {
            const std::uint64_t now = bc::fuel_remaining();
            if (now < f0) nn_field_fuel += f0 - now;
        }
    } nn_ff;
#endif
""")
patch("bot.cpp", "        int quota = field_calls++ == 0 ? (NOVA_FUEL_FIRST ? 1000 : 2 * tune::kDetFields)\n", """#if defined(A2_NN_LIVE) && A2_NN_LIVE
        int quota = field_calls++ == 0 ? 1000
#else
        int quota = field_calls++ == 0 ? (NOVA_FUEL_FIRST ? 1000 : 2 * tune::kDetFields)
#endif
""")
patch("bot.cpp", "                full + static_cast<std::uint64_t>(NOVA_FUEL_OPEN ? 30000 : tune::kDetSafety);\n", """#if defined(A2_NN_LIVE) && A2_NN_LIVE
                full + static_cast<std::uint64_t>(field_calls <= 1 ? 20000 : NOVA_FUEL_OPEN ? 30000 : tune::kDetSafety);
#else
                full + static_cast<std::uint64_t>(NOVA_FUEL_OPEN ? 30000 : tune::kDetSafety);
#endif
""")
patch("bot.h", "class Bot {\npublic:\n    void play_turn();\n", """class Bot {
public:
    void play_turn();
#if A2_NN
""" + ("" if BASE == "nnrec" else """    void nn_feats(std::int16_t* f, int near); // the 500 network features of this turn (nnrec.cpp)
    template <int NC, int AF> void nn_feats_t(std::int16_t* f, int near, int parts = 3); // parts: 1 all but camps, 2 camps, 4 self, 8 global, 16 allies, 32 enemies, 64 altars
    void nn_feats3(std::int16_t* f, int near); // version 3: 24 camp groups + allies' claimed targets (828)
    int nn_near() const;
    void nn_track();             // per-turn history for the network's memory features
""") + """    void nn_decide();            // after the world update: run the student network
#ifdef A2_NN_LAZY
    void nn_lazy_score();        // in farm(): score the camps on the fuel v92 leaves (nnrec.cpp)
#endif
    bool nn_stay = false;        // no fresh scores this turn: the current target stays (A2_NN_HOLDKEEP)
#ifdef A2_NN_NNUE
    void nn_x_refresh(int x);    // refresh one slow block of the network's input (nnrec.cpp)
#endif
#ifdef A2_NN_ENSLOG
    void nn_ens_log(int v92g, int ng);
#endif
#ifdef A2_NN_FCMP
    void nn_fcmp(int v92g);
#endif
#ifdef A2_NN_ENS
    bool nn_ens_keep(int v92g, int ng) const; // blend with v92's choice (nnrec.cpp)
    int nn_ens_sample(int v92g);              // the same in RL rollouts (A2_NN_RLIVE)
#endif
    int nn_group = -1, nn_beh = -1;
    int nn_v92best = -1;         // v92's own target choice this turn (the DAgger label)
    int nn_rl_a = -1, nn_rl_val = 0; // A2_NN_RL: sampled target slot, own value (banked by this champion + carried)
    float nn_rl_lp = 0.0f;           // A2_NN_RL: log-probability of the sampled slot
    std::string nn_rl_feat;          // A2_NN_RL: base64 features of this turn ("" once logged)
    // A2_NN_MACRO: the held option and this turn's RL row
    int nn_hold_beh = -1, nn_hold_until = -1;
    bool nn_hold_contact = false;
    int nn_rl_beh_a = -1;
    float nn_rl_beh_lp = 0.0f;
    bool nn_rl_contact = false, nn_rl_tgt_applied = false, nn_rl_chg = false;
    int nn_rl_gold = 0, nn_rl_kills = 0, nn_rl_deaths = 0;
    bool nn_option_out();        // out-of-contact options (dispatch, bit 8)
    void nn_rl_end();            // end of turn: the NRB row
    void nn_pipe_step();         // A2_NN_PIPE, end of turn: advance the pipelined network with the fuel left
    void nn_turn_end();          // A2_NN_LIVE, end of turn: measure what v92 spent after the decision
#endif
""")
patch("bot.cpp", "        if (tune::kBelief) w.update_beliefs(round, tune::kDet ? static_cast<std::uint64_t>(tune::kDetSafety) : 40000);\n",
      "        if (tune::kBelief) w.update_beliefs(round, tune::kDet ? static_cast<std::uint64_t>(tune::kDetSafety) : 40000);\n"
      "#if A2_NN\n        nn_decide();\n#endif\n")
# 1: the network's target group replaces v92's choice (v92's crew size kept when they agree)
# A2_NN_SKIPSEL (E121, fuel): with a network target in force v92's own selection is wasted work (score_groups 22.5k a farm
# turn, its route search included), so it is not run. best_need 1, as when the network overrides v92's choice.
patch("bot.cpp", "    // Escort (APEX_ESCORT): a caster farms where the nearest healthy melee ally farms, so a protector is\n",
      "#if (A2_NN & 1) && defined(A2_NN_SKIPSEL) && A2_NN_SKIPSEL\n    if (best < 0 && nn_group >= 0 && nn_group < static_cast<int>(w.groups.size())) best = nn_group, best_need = 1;\n#endif\n"
      "    // Escort (APEX_ESCORT): a caster farms where the nearest healthy melee ally farms, so a protector is\n")
patch("bot.cpp", '    PROF_CHECK("farmsel");\n', '''    PROF_CHECK("farmsel");
#if A2_NN & 1
    nn_v92best = best;
#ifdef A2_NN_TDBG
    {
        static int agree = 0, total = 0, none = 0;
        ++total, agree += nn_group == best, none += nn_group < 0;
        if (total % 100 == 0) std::printf("NNT r%d slot %d agree %d/%d none %d (v92 %d nn %d mode %s)\\n", round, slot, agree, total, none, best, nn_group, mode);
    }
#endif
#ifdef A2_NN_LAZY
    nn_lazy_score();
#endif
#ifdef A2_NN_ENSLOG
    if (best >= 0 && nn_group >= 0) nn_ens_log(best, nn_group);
#endif
#ifdef A2_NN_FCMP
    if (best >= 0 && nn_group >= 0) nn_fcmp(best);
#endif
#ifdef A2_NN_ENS
#if defined(A2_NN_RLIVE) && A2_NN_RLIVE
    if (best >= 0 && nn_group >= 0 && !nn_stay) nn_group = nn_ens_sample(best);
#else
    if (best >= 0 && nn_group >= 0 && !nn_stay && nn_ens_keep(best, nn_group)) nn_group = best;
#endif
#endif
    if (nn_group >= 0 && nn_group < static_cast<int>(w.groups.size()) && nn_group != best) best = nn_group, best_need = 1;
#ifdef A2_NN_RL
#if A2_NN_MACRO
    nn_rl_tgt_applied = true; // the NRB row at the end of the turn carries this choice
    nn_rl_chg = best != target_group;
#else
    // RL: log the applied choice (state, sampled action, log-prob, target changed, own value) - farm turns only
    if (!nn_rl_feat.empty()) {
        std::printf("NRL %d %d %d %.5f %d %d %s\\n", round, slot, nn_rl_a, nn_rl_lp, best != target_group ? 1 : 0, nn_rl_val,
                    nn_rl_feat.c_str());
        nn_rl_feat.clear();
    }
#endif
#endif
#endif
''')
# 2: v92's ordinary banking call only when the network says bank, and then the trip is forced (the macro policy's bank
# option acts here too: forcing it earlier in v92's order lost ~8 points, E117)
# (A2_NN_FAST deployment: with no network decision in force, nn_beh < 0, v92 banks as usual - E120: without this the
# pipelined bot never banked between decisions and lost 10/10)
patch("bot.cpp", "    } else if (tribute_if_needed()) {\n        mode = \"tribute\";\n",
      "    } else if (\n#if (A2_NN & 2) && A2_NN_FAST\n        (nn_beh < 0 || (nn_beh == 1 && gems > 0 && (force_tribute = true))) &&\n"
      "#elif A2_NN & 2\n        nn_beh == 1 && gems > 0 && (force_tribute = true) &&\n#endif\n        tribute_if_needed()) {\n        mode = \"tribute\";\n")
# A2_NN_MACRO 4: in contact, the held option fight / flee sets v92's verdict (where the engine lab forces it)
patch("bot.cpp", "#if A2_LAB\n    {\n        // Engine lab (lab.h kinds 4 / 5): from the first turn an enemy is within 4",
      "#if (A2_NN & 4) && A2_NN_MACRO\n    if (nn_hold_contact && nn_beh == 2) {\n        winning = true;\n        in_danger = false;\n"
      "    } else if (nn_hold_contact && nn_beh == 3) {\n        winning = false;\n        in_danger = true;\n"
      "        if (threat_on_me <= 0) threat_on_me = 1.0f;\n    }\n#endif\n"
      "#if A2_LAB\n    {\n        // Engine lab (lab.h kinds 4 / 5): from the first turn an enemy is within 4")
# A2_NN_MACRO 8: out-of-contact options right after the win-now bank
patch("bot.cpp", '        mode = "tribute-win";\n    } else if (go_home_if_needed()) {',
      '        mode = "tribute-win";\n#if (A2_NN & 8) && A2_NN_MACRO\n    } else if (nn_option_out()) {\n#endif\n    } else if (go_home_if_needed()) {')
if BASE != "nnrec":
    # macro RL rows are printed at the end of every turn; A2_NN_PIPE advances the pipelined network there (also in the
    # A2_FUELLOG branch, which counts turns that overran into the next round)
    patch("main.cpp", "            else\n                bot.play_turn();\n#endif",
          "            else {\n                bot.play_turn();\n#if A2_NN_MACRO && defined(A2_NN_RL)\n                bot.nn_rl_end();\n#endif\n"
          "#if defined(A2_NN_PIPE) && A2_NN_PIPE\n                bot.nn_pipe_step();\n#endif\n"
          "#if defined(A2_NN_LIVE) && A2_NN_LIVE\n                bot.nn_turn_end();\n#endif\n            }\n#endif")
    patch("main.cpp", "                bot.play_turn();\n                ++turns;\n",
          "                bot.play_turn();\n#if defined(A2_NN_PIPE) && A2_NN_PIPE\n                bot.nn_pipe_step();\n#endif\n"
          "#if defined(A2_NN_LIVE) && A2_NN_LIVE\n                bot.nn_turn_end();\n#endif\n                ++turns;\n")
if top:
    c = open(S + "common.h", encoding="utf-8").read()
    open(S + "common.h", "w", encoding="utf-8", newline="\n").write("".join(f"#define {k} {v}\n" for k, v in top.items()) + c)
if defs.get("A2_NN_LIVE", "0") != "0":
    # E122: v92's fuel checks (many sit well above what the step needs: 38-58k) must see the fuel they would see without the network, or
    # the network's spending quietly switches parts of v92 off, and then v92 looks cheap and the network takes more. So they add
    # back what the network spent this turn; nn_decide leaves what v92 really spends. Field building takes what is left: it keeps the true number.
    for fn in os.listdir(S):
        if fn.endswith((".cpp", ".h")) and fn != "draft.cpp":
            txt = open(S + fn, encoding="utf-8").read()
            if "bc::fuel_remaining()" in txt:
                if fn == "bot.cpp":
                    i = txt.index("void Bot::build_fields() {")
                    j = txt.index("void Bot::play_turn() {", i)
                    add = lambda t: t.replace("bc::fuel_remaining()", "(bc::fuel_remaining() + nn_spent)")
                    txt = add(txt[:i]) + txt[i:j] + add(txt[j:])
                else:
                    txt = txt.replace("bc::fuel_remaining()", "(bc::fuel_remaining() + nn_spent)")
                open(S + fn, "w", encoding="utf-8", newline="\n").write(txt)
if dplan:
    shutil.copy(os.path.join(LAB, "mappre.h"), S + "mappre.h")
    shutil.copy(os.path.join(LAB, "sched.h"), S + "sched.h")
    patch("draft.cpp", '#include "strategy.h"\n', '#include "strategy.h"\n#include "mappre.h"\n#include "sched.h"\n')
    patch("draft.cpp", "    done = true;\n    try {\n        constexpr float kHp[6] = {1350, 2400, 120, 120, 20000, 5000};\n",
          "    done = true;\n#if A2_SCHED\n    try {\n        bytes = sched::build(size);\n    } catch (...) {\n        bytes.clear();\n    }\n    return bytes;\n#endif\n"
          "    try {\n        constexpr float kHp[6] = {1350, 2400, 120, 120, 20000, 5000};\n")
if xf:
    # after the plan in draft memory: per group the value per round of a round trip from our spawn (mappre) and the gems around the group
    # (walking distance, weight e^(-d/16)). Built once, on the first draft turn's 10M fuel: the later draft turns have 100k.
    patch("draft.cpp", """            std::vector<std::uint8_t> all(8, 0);
            all.insert(all.end(), plan.begin(), plan.end());
            bc::draft_memory = all;
""", """            static std::vector<std::uint8_t> all;
            if (all.empty()) {
                all.assign(8, 0);
                all.insert(all.end(), plan.begin(), plan.end());
                if (all.size() <= 200) {
                    all.resize(200, 0);
                    const auto& A = mappre::analysis();
                    const int N = static_cast<int>(A.G.size()), n = std::min(N, 96);
                    std::uint8_t vpt[96] = {}, nbr[96] = {};
                    for (int i = 0; A.ok && i < n; ++i) {
                        vpt[i] = static_cast<std::uint8_t>(std::min(255.0f, 10.0f * A.vpt[static_cast<std::size_t>(i)]));
                        if (!A.have_mat) continue;
                        float s = 0.0f;
                        for (int j = 0; j < N; ++j) {
                            const int dij = A.mat[static_cast<std::size_t>((1 + i) * N + j)];
                            if (j != i && dij != mappre::kUnreach) s += A.G[static_cast<std::size_t>(j)].gems * std::exp(-static_cast<float>(dij) / 16.0f);
                        }
                        nbr[i] = static_cast<std::uint8_t>(std::min(255.0f, s));
                    }
                    all.push_back('X');
                    all.push_back(static_cast<std::uint8_t>(n));
                    all.insert(all.end(), vpt, vpt + 96);
                    all.insert(all.end(), nbr, nbr + 96);
                }
            }
            bc::draft_memory = all;
""")
shutil.copy(os.path.join(LAB, "nnrec.cpp"), S + "nnrec.cpp")
shutil.copy(os.path.join(LAB, "nn_infer.h"), S + "nn_infer.h")
shutil.copy(WEIGHTS, S + "nn_weights.h")
r = subprocess.run([os.path.join(ROOT, "v4", "cambc.exe"), "build", f"bots/{NAME}", "--release"], cwd=os.path.join(ROOT, "v4"),
                   capture_output=True, text=True)
ok = os.path.exists(os.path.join(B, NAME, ".cambc", "build-release", "bot.wasm")) and r.returncode == 0
print(NAME, "built" if ok else "BUILD FAILED")
if not ok:
    print("\n".join(l for l in (r.stdout + r.stderr).splitlines() if "error" in l)[:3000])
