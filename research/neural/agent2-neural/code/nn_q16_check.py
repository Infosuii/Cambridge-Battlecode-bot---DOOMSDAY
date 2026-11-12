"""E124: would a 16-bit network make the same decisions? Simulates the wasm i16x8 fixed-point forward (q15mulr_sat + add_sat, input-major) on recorded blend rows, against the float student:
same target argmax, same blend decision (override or keep v92's pick). Scales: inputs Q(QX), weights Q14, each layer loses one bit (encoder Q(QX-1), trunk 0 Q(QX-2), trunk 1 Q(QX-3), q Q(QX-4), r Q(QX-5)).
usage (project root): python -P agent2/lab/nn_q16_check.py ROWS.npz STUDENT.pt [--qx 11] [--rows 100000]"""
import os, sys
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nn_model import BLK, TYPEF, NTYPE, Prep, load, split_blocks, student  # noqa: E402

A = sys.argv[1:]
ROWS, SPT = A[0], A[1]
arg = lambda k, d: type(d)(A[A.index(k) + 1]) if k in A else d
QX, NR = arg("--qx", 11), arg("--rows", 100000)
dev = "cuda"
d = np.load(ROWS)
X = torch.as_tensor(d["X"][:NR]).to(dev)
V = torch.as_tensor(d["v92g"][:NR]).to(dev)
S = load(student(Prep()), SPT, dev).to(dev).eval()
COFF, CN, CW = BLK["c"]
E = S.enc_dim
sat = lambda t: t.clamp(-32768, 32767)


def q15(w, x):
    """i16x8.q15mulr_sat_s on integer tensors."""
    return sat(torch.div(w * x + 16384, 32768, rounding_mode="floor"))


def qw(t):
    return sat(torch.round(t * 16384.0)).long()


def dense_q(Wq, bq, x):
    """y = b + sum_i W[:, i] * x_i, saturating adds, as add_col walks the columns. x: [N, in]; Wq: [out, in]."""
    y = bq.expand(x.shape[0], -1).clone()
    for i in range(x.shape[1]):
        c = x[:, i]
        if (c != 0).any():
            y = sat(y + q15(Wq[:, i].unsqueeze(0), c.unsqueeze(1)))
    return y


with torch.no_grad():
    B = split_blocks(X)
    P = S.prep(B)
    emb, pres = {}, {}
    for k in BLK:
        x = sat(torch.round(P[k] * (1 << QX))).long()
        lin = S.enc[k][0]
        W, b = qw(lin.weight), sat(torch.round(lin.bias * (1 << (QX - 1)))).long()
        sh = x.shape
        e = dense_q(W, b, x.reshape(-1, sh[-1]))
        emb[k] = e.clamp_min(0).reshape(sh[0], sh[1], E)
    Q0 = QX - 1
    parts = [emb["g"][:, 0], emb["s"][:, 0]]
    for k in ("a", "e", "c", "l"):
        m = (B[k][..., 0] != 0).unsqueeze(-1).long()
        cnt = m.sum(1).clamp_min(1)
        mean = torch.round((emb[k] * m).sum(1).float() / cnt.float()).long()
        mx = (emb[k] * m).max(1).values
        parts += [mean, mx]
    x2 = torch.cat(parts, -1)
    print(f"encoder values: max {x2.max().item() / (1 << Q0):.2f}, saturated share {(x2 >= 32767).float().mean().item():.5f}")
    lin0, lin1 = S.trunk[0], S.trunk[2]
    h0 = dense_q(qw(lin0.weight), sat(torch.round(lin0.bias * (1 << (Q0 - 1)))).long(), x2).clamp_min(0)
    h1 = dense_q(qw(lin1.weight), sat(torch.round(lin1.bias * (1 << (Q0 - 2)))).long(), h0).clamp_min(0)
    print(f"trunk: h0 max {h0.max().item() / (1 << (Q0 - 1)):.2f}, h1 max {h1.max().item() / (1 << (Q0 - 2)):.2f}, saturated h0 {(h0 >= 32767).float().mean().item():.5f}, h1 {(h1 >= 32767).float().mean().item():.5f}")
    lq, lk = S.q["target"], S.k["target"]
    q = dense_q(qw(lq.weight), sat(torch.round(lq.bias * (1 << (Q0 - 3)))).long(), h1)
    r = dense_q(qw(lk.weight.t()), torch.zeros(E, device=dev).long(), q)  # r = Wk^T q
    Qq, Qr, Qe = Q0 - 3, Q0 - 4, Q0
    c0 = (lk.bias * q.float() / (1 << Qq)).sum(-1)
    # logit_i = (<e_i, r> + c0) / sqrt(E), the dot in integers
    dots = (emb["c"].float() * r.unsqueeze(1).float()).sum(-1) / (1 << (Qe + Qr))
    s = (dots + c0.unsqueeze(1)) / E ** 0.5
    extra = S.extra["target"]
    ex_e = lk.weight @ extra[0] + lk.bias if False else None
    # the "far" slot: key from the extra embedding (no ReLU), as live_target does with kP_target_E
    far = ((lk.weight.t() @ (q.float() / (1 << Qq)).t()).t() * extra[0]).sum(-1) + c0
    far = far / E ** 0.5
    pc = B["c"][..., 0] != 0
    Lq = torch.cat([s.masked_fill(~pc, -1e9), far.unsqueeze(1)], 1)
    Lf = torch.cat([S(X[i:i + 8192])["target"] for i in range(0, len(X), 8192)])
    g = B["c"][..., 1].long()
    fl = ((g == V.unsqueeze(1)) & pc).float()
    ff = 1.0 - fl.max(1).values
    bonus = torch.cat([2.0 * fl, 2.0 * ff.unsqueeze(1)], 1)
    dl = (Lq - Lf)[Lf > -1e8]
    print(f"logits, 16-bit vs float: mean abs {dl.abs().mean().item():.4f}, p99 {dl.abs().quantile(0.99).item():.4f}, max {dl.abs().max().item():.3f}")
    a1, a2 = Lq.argmax(1), Lf.argmax(1)
    b1, b2 = (Lq + bonus).argmax(1), (Lf + bonus).argmax(1)
    print(f"same top camp {100 * (a1 == a2).float().mean().item():.2f}%; same blend decision {100 * (b1 == b2).float().mean().item():.2f}% on {len(X)} rows (all disagreements with v92 + 1 in 8 of the rest)")
