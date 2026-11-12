"""Port Agent 2's neural actor path (agent2-neural 56b60b96, rl_workspace/agent2/lab/nn_mkbot.py) into the candidate
bots/jd-g5070-1104/src, reproducibly and behind default-0 switches (JD_NN / A2_NN, JD_NN_EVENT; jd_config.h).

What it does (idempotent: an already applied patch is recognised and left alone):
  1. optional: export a checkpoint with Agent 2's nn_export.py (unchanged) into the weights header (--pt, --kind);
  2. nn_mkbot.py's source patches to bot.h / bot.cpp / main.cpp (the common.h defaults live in jd_config.h);
  3. JD hooks: jd_nn_turn / jd_nn_pipe / jd_nn_stat (jd_nn_event.cpp), farm() skips v92's own group scoring while
     a network target is held, per-decision fuel lines for the every-turn arm (JD_NN_LOG);
  4. copies nnrec.cpp and nn_infer.h from the lab (with the JD hooks) and the weights as jd_nn_weights.h;
  5. --check-zero: builds the default config and asserts the release WASM hash is v92's (5704d7ba...).

usage (worktree root):
  py tools/jd_g5070-1104/mk_nn.py [--pt agent2/student_i2.pt --kind student] [--weights H] [--check-zero]
  py tools/jd_g5070-1104/mk_nn.py --smoke   (port + default hash check + one JD_NN_EVENT build; one command)
"""
import argparse, hashlib, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.dirname(os.path.dirname(HERE))
EVAL = os.path.join(os.path.dirname(WT), "jd-eval")
A2 = os.path.join(EVAL, "a2", "research", "agent2-neural", "rl_workspace")
LAB = os.path.join(A2, "agent2", "lab")
VENV_PY = os.path.join(os.path.dirname(WT), ".venv-jd", "Scripts", "python.exe")
SRC = os.path.join(WT, "bots", "jd-g5070-1104", "src")
V92_SHA = "5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47"
# git blob ids of the lab sources at agent2-neural 56b60b96 (the port refuses other versions)
LAB_BLOBS = {"nnrec.cpp": "e7be3cdb0b99230096d4d264c5edd399318a872b", "nn_infer.h": "b6979316bfbaa256addc461e9fb3851c4676f069",
             "nn_export.py": "21bb3bd6ed049778b4bf4eb10084cd0fc380c1d1", "nn_model.py": "1b566ac40e36a14a0bfd1c863a97b28c0e9b8a3b"}


def blob(path):
    d = open(path, "rb").read()
    return hashlib.sha1(b"blob %d\0" % len(d) + d).hexdigest()


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def patch_text(s, old, new, name):
    """Apply old -> new once; if `new` is already present the patch counts as applied (idempotent)."""
    if s.count(new) == 1:
        return s, False
    assert s.count(old) == 1, (name, old[:70], s.count(old))
    return s.replace(old, new), True


def patch(fn, old, new, marker=None):
    p = os.path.join(SRC, fn)
    s = open(p, encoding="utf-8").read()
    if marker and marker in s:
        return False  # applied before and then edited by a later patch (FARMSEL + RESID): never insert a second copy
    s2, changed = patch_text(s, old, new, fn)
    if changed:
        open(p, "w", encoding="utf-8", newline="\n").write(s2)
    return changed


BOT_H_OLD = "class Bot {\npublic:\n    void play_turn();\n"
BOT_H_NEW = """class Bot {
public:
    void play_turn();
#if A2_NN
    void nn_feats(std::int16_t* f, int near); // the 500 network features of this turn (nnrec.cpp)
    template <int NC, int AF> void nn_feats_t(std::int16_t* f, int near);
    void nn_feats3(std::int16_t* f, int near); // version 3: 24 camp groups + allies' claimed targets (828)
    int nn_near() const;
    void nn_track();             // per-turn history for the network's memory features
    void nn_decide();            // after the world update: run the student network
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
    void jd_nn_stat();           // JD_NN_LOG: per-turn counters, JDN C lines (jd_nn_event.cpp)
    void jd_nn_turn();           // JD_NN_EVENT: events, held decision, fallback (after the world update)
    void jd_nn_pipe();           // JD_NN_EVENT: end of turn, pipelined inference admitted by the governor
    void jd_nn_pipe_core();      // JD_NN_EVENT: the pipeline steps (jd_nn_pipe then writes queued JD_NN_REC rows)
    bool jd_nn_resid_ok(int v92best); // JD_NN_RESID: the held network target beats v92's choice by the margin
#endif
"""

BELIEF = "        if (tune::kBelief) w.update_beliefs(round, tune::kDet ? static_cast<std::uint64_t>(tune::kDetSafety) : 40000);\n"
FARMSEL_OLD = '    PROF_CHECK("farmsel");\n'
FARMSEL_NEW = '''    PROF_CHECK("farmsel");
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
'''
BANK_OLD = "    } else if (tribute_if_needed()) {\n        mode = \"tribute\";\n"
BANK_NEW = ("    } else if (\n#if (A2_NN & 2) && A2_NN_FAST\n        (nn_beh < 0 || (nn_beh == 1 && gems > 0 && (force_tribute = true))) &&\n"
            "#elif A2_NN & 2\n        nn_beh == 1 && gems > 0 && (force_tribute = true) &&\n#endif\n        tribute_if_needed()) {\n        mode = \"tribute\";\n")
LAB_OLD = "#if A2_LAB\n    {\n        // Engine lab (lab.h kinds 4 / 5): from the first turn an enemy is within 4"
LAB_NEW = ("#if (A2_NN & 4) && A2_NN_MACRO\n    if (nn_hold_contact && nn_beh == 2) {\n        winning = true;\n        in_danger = false;\n"
           "    } else if (nn_hold_contact && nn_beh == 3) {\n        winning = false;\n        in_danger = true;\n"
           "        if (threat_on_me <= 0) threat_on_me = 1.0f;\n    }\n#endif\n" + LAB_OLD)
OPT_OLD = '        mode = "tribute-win";\n    } else if (go_home_if_needed()) {'
OPT_NEW = '        mode = "tribute-win";\n#if (A2_NN & 8) && A2_NN_MACRO\n    } else if (nn_option_out()) {\n#endif\n    } else if (go_home_if_needed()) {'
# JD: while the network's target is held, farm() takes it instead of running v92's own group scoring
SCORE_OLD = "    if (best < 0) best = score_groups(duo_leader ? 2 : 1, best_need, best_score);\n"
SCORE_NEW = ("#if JD_NN_EVENT && !JD_NN_ZERO && !JD_NN_RESID\n    if (best < 0 && nn_group >= 0 && nn_group < static_cast<int>(w.groups.size())) best = nn_group, best_need = 1;\n#endif\n"
             + SCORE_OLD)
# JD_NN_RESID: KEEP_BASELINE dominant (the network's held target must beat v92's own choice by a logit margin)
RESID_OLD = '    PROF_CHECK("farmsel");\n#if A2_NN & 1\n    nn_v92best = best;\n'
RESID_NEW = RESID_OLD + "#if JD_NN_EVENT && JD_NN_RESID\n    if (nn_group >= 0 && nn_group != best && !jd_nn_resid_ok(best)) nn_group = -1;\n#endif\n"
MAIN1_OLD = "            else\n                bot.play_turn();\n#endif"
MAIN1_NEW = ("            else {\n                bot.play_turn();\n#if A2_NN_MACRO && defined(A2_NN_RL)\n                bot.nn_rl_end();\n#endif\n"
             "#if defined(A2_NN_PIPE) && A2_NN_PIPE\n                bot.nn_pipe_step();\n#endif\n#if JD_NN_EVENT\n                bot.jd_nn_pipe();\n#endif\n"
             "            }\n#endif")
MAIN2_OLD = "                bot.play_turn();\n                ++turns;\n"
MAIN2_NEW = ("                bot.play_turn();\n#if defined(A2_NN_PIPE) && A2_NN_PIPE\n                bot.nn_pipe_step();\n#endif\n"
             "#if JD_NN_EVENT\n                bot.jd_nn_pipe();\n#endif\n                ++turns;\n")

# JD hooks inside the lab copies
REC_DECIDE_OLD = ("    nn_v92best = target_group; // v92 keeps its target unless farm() chooses again\n    if (!inited) return;\n"
                  "    nn_track();\n")
REC_DECIDE_NEW = REC_DECIDE_OLD + "#if JD_NN_LOG\n    jd_nn_stat();\n#endif\n#if JD_NN_EVENT\n    jd_nn_turn();\n    return;\n#endif\n"
REC_FUEL_OLD = "    std::int16_t f[kNFa] = {};\n#ifdef A2_NN_FUEL\n    const std::uint64_t f0 = bc::fuel_remaining();\n#endif\n"
REC_FUEL_NEW = ("    std::int16_t f[kNFa] = {};\n#if JD_NN_LOG\n    const std::uint64_t jd_f0 = bc::fuel_remaining();\n    const auto jd_r0 = bc::round_number();\n#endif\n"
                "#ifdef A2_NN_FUEL\n    const std::uint64_t f0 = bc::fuel_remaining();\n#endif\n")
REC_ARG_OLD = "    nn_beh = nn::argmax(o.behaviour);\n    int t = nn::argmax(o.target);\n"
REC_ARG_NEW = REC_ARG_OLD + ("#if JD_NN_LOG\n    {\n        // every-turn arm: one decision = features + forward on this turn (a crossed round = the turn suspended)\n"
                             "        const bool over = bc::round_number() != jd_r0;\n"
                             "        const std::uint64_t used = over ? jd_f0 : jd_f0 - bc::fuel_remaining();\n"
                             "        std::printf(\"JDN D %d %d %llu %llu 1 %d every %d %d\\n\", static_cast<int>(bc::round_number()), slot,\n"
                             "                    static_cast<unsigned long long>(used), static_cast<unsigned long long>(used), over ? 1 : 0, t, nn_beh);\n"
                             "    }\n#endif\n")
INF_INC_OLD = '#include "nn_weights.h"\n'
INF_INC_NEW = '#include "jd_nn_weights.h"\n'
INF_PIPE_OLD = "#if defined(A2_NN_PIPE) && A2_NN_PIPE\n// Pipelined forward"
INF_PIPE_NEW = "#if (defined(A2_NN_PIPE) && A2_NN_PIPE) || JD_NN_EVENT\n// Pipelined forward"


def copy_lab(name, out, pairs):
    s = open(os.path.join(LAB, name), encoding="utf-8").read()
    for old, new in pairs:
        s, _ = patch_text(s, old, new, name)
    p = os.path.join(SRC, out)
    prev = open(p, encoding="utf-8").read() if os.path.exists(p) else None
    if prev != s:
        open(p, "w", encoding="utf-8", newline="\n").write(s)
    return prev != s


def build(src_bot, out):
    exe = os.path.join(WT, "tools", "vendor", "cambc.exe")
    r = subprocess.run([exe, "build", src_bot, "--release", "--output", out], cwd=WT, capture_output=True, text=True)
    cc = os.path.join(WT, src_bot, "compile_commands.json")
    if os.path.exists(cc):
        os.remove(cc)
    if r.returncode != 0 or not os.path.exists(out):
        print((r.stdout + r.stderr)[-4000:])
        raise SystemExit("BUILD FAILED " + src_bot)
    return sha256(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pt", help="checkpoint to export with nn_export.py (path relative to the a2 rl_workspace or absolute)")
    ap.add_argument("--kind", default="student")
    ap.add_argument("--weights", help="weights header to install as jd_nn_weights.h")
    ap.add_argument("--check-zero", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    for n, want in LAB_BLOBS.items():
        got = blob(os.path.join(LAB, n))
        print(f"lab {n} blob {got} {'= 56b60b96' if got == want else 'DIFFERS from 56b60b96'}")
        if got != want:
            raise SystemExit("lab sources are not agent2-neural 56b60b96; refusing to port")
    weights = a.weights
    if a.pt:
        pt = a.pt if os.path.isabs(a.pt) else os.path.join(A2, a.pt)
        weights = weights or os.path.join(EVAL, "export", os.path.splitext(os.path.basename(pt))[0] + "_w.h")
        os.makedirs(os.path.dirname(weights), exist_ok=True)
        r = subprocess.run([VENV_PY, "-P", os.path.join(LAB, "nn_export.py"), pt, a.kind, weights], cwd=A2, capture_output=True, text=True)
        print(r.stdout.strip(), r.stderr.strip()[-500:])
        assert r.returncode == 0
        print(f"exported {pt} sha256 {sha256(pt)} -> {weights} sha256 {sha256(weights)}")
    ch = []
    ch.append(patch("bot.h", BOT_H_OLD, BOT_H_NEW))
    ch.append(patch("bot.cpp", BELIEF, BELIEF + "#if A2_NN\n        nn_decide();\n#endif\n"))
    ch.append(patch("bot.cpp", FARMSEL_OLD, FARMSEL_NEW, marker="    nn_v92best = best;\n"))
    ch.append(patch("bot.cpp", BANK_OLD, BANK_NEW))
    ch.append(patch("bot.cpp", LAB_OLD, LAB_NEW))
    ch.append(patch("bot.cpp", OPT_OLD, OPT_NEW))
    ch.append(patch("bot.cpp", SCORE_OLD, SCORE_NEW))
    ch.append(patch("bot.cpp", RESID_OLD, RESID_NEW))
    ch.append(patch("main.cpp", MAIN1_OLD, MAIN1_NEW))
    ch.append(patch("main.cpp", MAIN2_OLD, MAIN2_NEW))
    ch.append(copy_lab("nnrec.cpp", "nnrec.cpp", [(REC_DECIDE_OLD, REC_DECIDE_NEW), (REC_FUEL_OLD, REC_FUEL_NEW), (REC_ARG_OLD, REC_ARG_NEW)]))
    ch.append(copy_lab("nn_infer.h", "nn_infer.h", [(INF_INC_OLD, INF_INC_NEW), (INF_PIPE_OLD, INF_PIPE_NEW)]))
    if weights:
        dst = os.path.join(SRC, "jd_nn_weights.h")
        same = os.path.exists(dst) and open(dst, "rb").read() == open(weights, "rb").read()
        if not same:
            shutil.copyfile(weights, dst)
        ch.append(not same)
    assert os.path.exists(os.path.join(SRC, "jd_nn_weights.h")), "no weights header: pass --pt or --weights"
    print("patched/copied:", sum(ch), "of", len(ch), "(0 = port already in place)")
    print("jd_nn_weights.h sha256", sha256(os.path.join(SRC, "jd_nn_weights.h")))
    if a.check_zero or a.smoke:
        out = os.path.join(EVAL, "wasm", "jd-mknn-zero.wasm")
        h = build("bots/jd-g5070-1104", out)
        print("default build", h, "OK = v92" if h == V92_SHA else "MISMATCH")
        if h != V92_SHA:
            raise SystemExit(1)
    if a.smoke:
        # one JD_NN_EVENT build from a temporary copy (defines prepended to jd_config.h, like jdrun.py freeze)
        tmp = os.path.join(EVAL, "bots", "_mknn_smoke")
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.copytree(os.path.join(WT, "bots", "jd-g5070-1104"), tmp, ignore=shutil.ignore_patterns(".cambc", "compile_commands.json"))
        jc = os.path.join(tmp, "src", "jd_config.h")
        s = open(jc, encoding="utf-8").read()
        open(jc, "w", encoding="utf-8", newline="\n").write("#define JD_NN 3\n#define A2_NN_FAST 1\n#define JD_NN_EVENT 1\n" + s)
        exe = os.path.join(EVAL, "tools", "vendor", "cambc.exe")
        out = os.path.join(EVAL, "wasm", "jd-mknn-event.wasm")
        r = subprocess.run([exe, "build", "bots/_mknn_smoke", "--release", "--output", out], cwd=EVAL, capture_output=True, text=True)
        ok = r.returncode == 0 and os.path.exists(out)
        print("JD_NN_EVENT build", "OK " + sha256(out) if ok else "FAILED\n" + (r.stdout + r.stderr)[-3000:])
        shutil.rmtree(tmp, ignore_errors=True)
        if not ok:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
