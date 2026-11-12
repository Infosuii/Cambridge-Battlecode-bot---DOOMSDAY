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
{ANCHOR}
""")
patch("bot.h", "class Bot {\npublic:\n    void play_turn();\n", """class Bot {
public:
    void play_turn();
#if A2_NN
""" + ("" if BASE == "nnrec" else """    void nn_feats(std::int16_t* f, int near); // the 500 network features of this turn (nnrec.cpp)
    template <int NC, int AF> void nn_feats_t(std::int16_t* f, int near);
    void nn_feats3(std::int16_t* f, int near); // version 3: 24 camp groups + allies' claimed targets (828)
    int nn_near() const;
    void nn_track();             // per-turn history for the network's memory features
""") + """    void nn_decide();            // after the world update: run the student network
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
#endif
""")
patch("bot.cpp", "        if (tune::kBelief) w.update_beliefs(round, tune::kDet ? static_cast<std::uint64_t>(tune::kDetSafety) : 40000);\n",
      "        if (tune::kBelief) w.update_beliefs(round, tune::kDet ? static_cast<std::uint64_t>(tune::kDetSafety) : 40000);\n"
      "#if A2_NN\n        nn_decide();\n#endif\n")
# 1: the network's target group replaces v92's choice (v92's crew size kept when they agree)
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
          "#if defined(A2_NN_PIPE) && A2_NN_PIPE\n                bot.nn_pipe_step();\n#endif\n            }\n#endif")
    patch("main.cpp", "                bot.play_turn();\n                ++turns;\n",
          "                bot.play_turn();\n#if defined(A2_NN_PIPE) && A2_NN_PIPE\n                bot.nn_pipe_step();\n#endif\n                ++turns;\n")
if top:
    c = open(S + "common.h", encoding="utf-8").read()
    open(S + "common.h", "w", encoding="utf-8", newline="\n").write("".join(f"#define {k} {v}\n" for k, v in top.items()) + c)
shutil.copy(os.path.join(LAB, "nnrec.cpp"), S + "nnrec.cpp")
shutil.copy(os.path.join(LAB, "nn_infer.h"), S + "nn_infer.h")
shutil.copy(WEIGHTS, S + "nn_weights.h")
r = subprocess.run([os.path.join(ROOT, "v4", "cambc.exe"), "build", f"bots/{NAME}", "--release"], cwd=os.path.join(ROOT, "v4"),
                   capture_output=True, text=True)
ok = os.path.exists(os.path.join(B, NAME, ".cambc", "build-release", "bot.wasm")) and r.returncode == 0
print(NAME, "built" if ok else "BUILD FAILED")
if not ok:
    print("\n".join(l for l in (r.stdout + r.stderr).splitlines() if "error" in l)[:3000])
