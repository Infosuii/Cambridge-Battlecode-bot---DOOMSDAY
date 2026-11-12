"""Neural bot: export a trained net (nn_train.py student.pt / teacher.pt) to a C++ header for nn_infer.h.
usage: python -P nn_export.py NET.pt student|teacher OUT.h"""
import math, os, sys
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nn_model import BLK, NCLS, NT, NTYPE, TYPEF, Prep, load, student, teacher  # noqa: E402

PT, KIND, OUTF = sys.argv[1:4]
prep = Prep()
net = (student if KIND == "student" else teacher)(prep)
load(net, PT)  # checkpoints from before the option head get a fresh "none" option head
net.eval()
L = []
TR = []  # weight matrices dense() reads: also written input-major ([in][out]) for the A2_NN_FAST loop (E120)
f = lambda t: ", ".join(f"{x:.7e}f" for x in t.detach().flatten().tolist())
fi = lambda t: ", ".join(str(int(x)) for x in t)
L.append("// Neural bot weights (agent2/lab/nn_export.py). Generated; do not edit.\n#pragma once\n#define NNW_HAS_OPTION 1\n#define NNW_HAS_NTYPE 1\nnamespace nnw {")
L.append(f"inline constexpr int kNT = {NT}, kEnc = {net.enc_dim};")
for k, (o, n, w) in BLK.items():
    keep = prep.keep[k]
    L.append(f"inline constexpr int k{k}_off = {o}, k{k}_n = {n}, k{k}_w = {w}, k{k}_nkeep = {len(keep)}, k{k}_type = {TYPEF.get(k, -1)}, k{k}_ntype = {NTYPE.get(k, NT)};")
    L.append(f"inline constexpr int k{k}_keep[] = {{{fi(keep)}}};")
    L.append(f"inline constexpr float k{k}_mu[] = {{{f(getattr(net.prep, 'mu_' + k))}}};")
    L.append(f"inline constexpr float k{k}_sd[] = {{{f(getattr(net.prep, 'sd_' + k))}}};")
    lin = [m for m in net.enc[k] if isinstance(m, torch.nn.Linear)]
    L.append(f"inline constexpr int k{k}_layers = {len(lin)};")
    for i, m in enumerate(lin):
        L.append(f"inline constexpr int k{k}_in{i} = {m.in_features};")
        L.append(f"inline constexpr float k{k}_W{i}[] = {{{f(m.weight)}}};  // [out][in]")
        TR.append((f"k{k}_W{i}", m.weight))
        L.append(f"inline constexpr float k{k}_b{i}[] = {{{f(m.bias)}}};")
    if len(lin) > 1:
        L.append(f"inline constexpr const float* k{k}_W1v = k{k}_W1; inline constexpr const float* k{k}_b1v = k{k}_b1;")
    else:
        L.append(f"inline constexpr const float* k{k}_W1v = nullptr; inline constexpr const float* k{k}_b1v = nullptr;")
lin = [m for m in net.trunk if isinstance(m, torch.nn.Linear)]
L.append(f"inline constexpr int kTrunk = {lin[0].out_features}, kTrunkLayers = {len(lin)}, kTrunkIn = {lin[0].in_features};")
for i, m in enumerate(lin):
    L.append(f"inline constexpr float kT_W{i}[] = {{{f(m.weight)}}};")
    TR.append((f"kT_W{i}", m.weight))
    L.append(f"inline constexpr float kT_b{i}[] = {{{f(m.bias)}}};")
for h, n in NCLS.items():
    m = net.lin[h]
    L.append(f"inline constexpr int kH_{h}_n = {n};")
    L.append(f"inline constexpr float kH_{h}_W[] = {{{f(m.weight)}}};")
    TR.append((f"kH_{h}_W", m.weight))
    L.append(f"inline constexpr float kH_{h}_b[] = {{{f(m.bias)}}};")
for h in ("target", "attack", "cast_tgt"):
    L.append(f"inline constexpr float kP_{h}_qW[] = {{{f(net.q[h].weight)}}};")
    TR.append((f"kP_{h}_qW", net.q[h].weight))
    L.append(f"inline constexpr float kP_{h}_qb[] = {{{f(net.q[h].bias)}}};")
    L.append(f"inline constexpr float kP_{h}_kW[] = {{{f(net.k[h].weight)}}};")
    L.append(f"inline constexpr float kP_{h}_kb[] = {{{f(net.k[h].bias)}}};")
    L.append(f"inline constexpr int kP_{h}_extra = {net.extra[h].shape[0]};")
    L.append(f"inline constexpr float kP_{h}_E[] = {{{f(net.extra[h])}}};")
for name, wt in TR:
    L.append(f"inline constexpr float {name}_T[] = {{{f(wt.t())}}};")
L.append("inline const float* transposed_of(const float* W) {")
for name, _ in TR:
    L.append(f"    if (W == {name}) return {name}_T;")
L.append("    return nullptr;")
L.append("}")
# signed-log tables for the A2_NN_FAST input prep (E121: first-use log1p calls cost about 200 fuel each and dominated first decisions):
# exact below 4096, then every 16th value, interpolated by slogi (E123)
L.append("inline constexpr float kSlog[4096] = {" + ", ".join(f"{math.log1p(i):.7e}f" for i in range(4096)) + "};")
L.append("inline constexpr float kSlog16[2050] = {" + ", ".join(f"{math.log1p(i * 16):.7e}f" for i in range(2050)) + "};")
# E124: 16-bit copies for A2_NN_Q16 (one-layer encoders): weights Q14, input-major; biases at the scale of what they add to (encoder Q10, trunk layer 0 Q9, layer 1 Q8, q Q7)
if all(len([m for m in net.enc[k] if isinstance(m, torch.nn.Linear)]) == 1 for k in BLK):
    def q14(t):
        return ", ".join(str(int(v)) for v in (t * 16384.0).round().clamp(-32768, 32767).long().flatten().tolist())

    def qs(t, bits):
        return ", ".join(str(int(v)) for v in (t * float(1 << bits)).round().clamp(-32768, 32767).long().flatten().tolist())

    for k in BLK:
        m = net.enc[k][0]
        L.append(f"inline constexpr short k{k}_W0_TQ[] = {{{q14(m.weight.t())}}};")
        L.append(f"inline constexpr short k{k}_b0Q[] = {{{qs(m.bias, 10)}}};")
    lin = [m for m in net.trunk if isinstance(m, torch.nn.Linear)]
    L.append(f"inline constexpr short kT_W0_TQ[] = {{{q14(lin[0].weight.t())}}};")
    L.append(f"inline constexpr short kT_b0Q[] = {{{qs(lin[0].bias, 9)}}};")
    L.append(f"inline constexpr short kT_W1_TQ[] = {{{q14(lin[1].weight.t())}}};")
    L.append(f"inline constexpr short kT_b1Q[] = {{{qs(lin[1].bias, 8)}}};")
    L.append(f"inline constexpr short kP_target_qW_TQ[] = {{{q14(net.q['target'].weight.t())}}};")
    L.append(f"inline constexpr short kP_target_qbQ[] = {{{qs(net.q['target'].bias, 7)}}};")
    L.append(f"inline constexpr short kP_target_kWQ[] = {{{q14(net.k['target'].weight)}}};")
    L.append(f"inline constexpr short kP_target_kbQ[] = {{{qs(net.k['target'].bias, 9)}}};")
    L.append(f"inline constexpr short kP_target_EQ[] = {{{qs(net.extra['target'], 10)}}};")
L.append("} // namespace nnw")
L.append("#define NNW_HAS_SLOG 1")
L.append("#define NNW_HAS_T 1")
open(OUTF, "w", newline="\n").write("\n".join(L) + "\n")
print("wrote", OUTF, os.path.getsize(OUTF) // 1024, "KB")
