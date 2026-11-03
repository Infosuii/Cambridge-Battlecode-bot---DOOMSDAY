"""Neural bot: export a trained net (nn_train.py student.pt / teacher.pt) to a C++ header for nn_infer.h.
usage: python -P nn_export.py NET.pt student|teacher OUT.h"""
import os, sys
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nn_model import BLK, NCLS, NT, TYPEF, Prep, student, teacher  # noqa: E402

PT, KIND, OUTF = sys.argv[1:4]
prep = Prep()
net = (student if KIND == "student" else teacher)(prep)
net.load_state_dict(torch.load(PT, map_location="cpu"))
net.eval()
L = []
f = lambda t: ", ".join(f"{x:.7e}f" for x in t.detach().flatten().tolist())
fi = lambda t: ", ".join(str(int(x)) for x in t)
L.append("// Neural bot weights (agent2/lab/nn_export.py). Generated; do not edit.\n#pragma once\nnamespace nnw {")
L.append(f"inline constexpr int kNT = {NT}, kEnc = {net.enc_dim};")
for k, (o, n, w) in BLK.items():
    keep = prep.keep[k]
    L.append(f"inline constexpr int k{k}_off = {o}, k{k}_n = {n}, k{k}_w = {w}, k{k}_nkeep = {len(keep)}, k{k}_type = {TYPEF.get(k, -1)};")
    L.append(f"inline constexpr int k{k}_keep[] = {{{fi(keep)}}};")
    L.append(f"inline constexpr float k{k}_mu[] = {{{f(getattr(net.prep, 'mu_' + k))}}};")
    L.append(f"inline constexpr float k{k}_sd[] = {{{f(getattr(net.prep, 'sd_' + k))}}};")
    lin = [m for m in net.enc[k] if isinstance(m, torch.nn.Linear)]
    L.append(f"inline constexpr int k{k}_layers = {len(lin)};")
    for i, m in enumerate(lin):
        L.append(f"inline constexpr int k{k}_in{i} = {m.in_features};")
        L.append(f"inline constexpr float k{k}_W{i}[] = {{{f(m.weight)}}};  // [out][in]")
        L.append(f"inline constexpr float k{k}_b{i}[] = {{{f(m.bias)}}};")
    if len(lin) > 1:
        L.append(f"inline constexpr const float* k{k}_W1v = k{k}_W1; inline constexpr const float* k{k}_b1v = k{k}_b1;")
    else:
        L.append(f"inline constexpr const float* k{k}_W1v = nullptr; inline constexpr const float* k{k}_b1v = nullptr;")
lin = [m for m in net.trunk if isinstance(m, torch.nn.Linear)]
L.append(f"inline constexpr int kTrunk = {lin[0].out_features}, kTrunkLayers = {len(lin)}, kTrunkIn = {lin[0].in_features};")
for i, m in enumerate(lin):
    L.append(f"inline constexpr float kT_W{i}[] = {{{f(m.weight)}}};")
    L.append(f"inline constexpr float kT_b{i}[] = {{{f(m.bias)}}};")
for h, n in NCLS.items():
    m = net.lin[h]
    L.append(f"inline constexpr int kH_{h}_n = {n};")
    L.append(f"inline constexpr float kH_{h}_W[] = {{{f(m.weight)}}};")
    L.append(f"inline constexpr float kH_{h}_b[] = {{{f(m.bias)}}};")
for h in ("target", "attack", "cast_tgt"):
    L.append(f"inline constexpr float kP_{h}_qW[] = {{{f(net.q[h].weight)}}};")
    L.append(f"inline constexpr float kP_{h}_qb[] = {{{f(net.q[h].bias)}}};")
    L.append(f"inline constexpr float kP_{h}_kW[] = {{{f(net.k[h].weight)}}};")
    L.append(f"inline constexpr float kP_{h}_kb[] = {{{f(net.k[h].bias)}}};")
    L.append(f"inline constexpr int kP_{h}_extra = {net.extra[h].shape[0]};")
    L.append(f"inline constexpr float kP_{h}_E[] = {{{f(net.extra[h])}}};")
L.append("} // namespace nnw")
open(OUTF, "w", newline="\n").write("\n".join(L) + "\n")
print("wrote", OUTF, os.path.getsize(OUTF) // 1024, "KB")
