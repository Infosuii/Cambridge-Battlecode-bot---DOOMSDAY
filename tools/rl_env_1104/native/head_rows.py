"""CNR2 rows of the native target head (CLNA_HEAD, nnrec.cpp) -> exact head inputs, and the behaviour replay check.

parse_cnr2(tokens) rebuilds every float32 input of JOHNDOE's TargetHead from the logged integers and float bits
(clna-head-abi-v1, head_export.py), plus the decision's physical mapping, reference and chosen index. replay() runs the
deployed weights (read back from clna_head_w.h) on a batch and returns alpha and p(chosen) next to the logged values.

usage: python tools/rl_env_1104/native/head_rows.py --bundle REPLAY.repl26a --side A --header clna_head_w.h
"""
import argparse
import os
import struct
import sys
import zipfile

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import head_export as HX  # noqa: E402

N_CAMP, CTX, EMB, NF = 10, 160, 16, 4


def _h16(tok: str) -> np.ndarray:
    if len(tok) % 4:
        raise ValueError("hex16 token length")
    return np.array([int(tok[i:i + 4], 16) for i in range(0, len(tok), 4)], dtype=np.uint16).view(np.int16)


def _h8(tok: str) -> list:
    if len(tok) % 2:
        raise ValueError("hex8 token length")
    return [int(tok[i:i + 2], 16) for i in range(0, len(tok), 2)]


def _f64(h: str) -> float:
    return struct.unpack("<d", int(h, 16).to_bytes(8, "little"))[0]


def _f32s(tok: str) -> np.ndarray:
    if len(tok) % 8:
        raise ValueError("hex32 token length")
    return np.array([int(tok[i:i + 8], 16) for i in range(0, len(tok), 8)], dtype=np.uint32).view(np.float32)


def features(ft: np.ndarray) -> np.ndarray:
    """clna-head-abi-v1 camp fields -> float32, exactly as nnrec.cpp: wd, claim, closer, committed."""
    ft = ft.astype(np.int32).reshape(-1, NF)
    out = np.empty(ft.shape, dtype=np.float32)
    out[:, 0] = np.where(ft[:, 0] < 0, 256, np.minimum(ft[:, 0], 256)).astype(np.float32) * np.float32(1 / 32)
    out[:, 1] = np.clip(ft[:, 1], 0, 8).astype(np.float32) * np.float32(0.25)
    out[:, 2] = np.clip(ft[:, 2], 0, 8).astype(np.float32) * np.float32(0.25)
    out[:, 3] = (ft[:, 3] != 0).astype(np.float32)
    return out


def _le16(tok: str) -> np.ndarray:  # CNR3: raw little-endian int16 bytes as hex (jd_codec::hex_simd)
    if len(tok) % 4:
        raise ValueError("le16 token length")
    return np.frombuffer(bytes.fromhex(tok), dtype="<i2").astype(np.int16)


def parse_cnr2(q: list) -> dict:
    """CNR2 (int16 as 4 big-endian hex digits each; context = the camp snapshot's) or CNR3 (raw little-endian bytes;
    one more field after the pub round: the round of the context in use, staged double-buffered h)."""
    if q[0] not in ("CNR2", "CNR3"):
        raise ValueError("not a CNR2/3 row")
    o = 1 if q[0] == "CNR3" else 0
    n, nu = int(q[9]), int(q[11 + o])
    if not 0 <= n <= N_CAMP or not 1 <= nu <= 14 or len(q) < 20 + o:
        raise ValueError("CNR2/3 shape")
    groups, mp = _h8(q[14 + o]), _h8(q[15 + o])
    i16 = _le16 if o else _h16
    logits, x, ec, ft = _f32s(q[16 + o]), i16(q[17 + o]), i16(q[18 + o]), i16(q[19 + o])
    if len(groups) != nu or len(mp) != n + 1 or len(logits) != n + 1 or len(x) != CTX or len(ec) != EMB * n \
            or len(ft) != NF * n or max(mp) >= nu:
        raise ValueError("CNR2/3 lengths")
    ref_g, ch_g = int(q[5]), int(q[6])
    if ref_g not in groups or ch_g not in groups:
        raise ValueError("CNR2/3 reference/chosen outside the groups")
    pub = int(q[10])
    return dict(round=int(q[1]), slot=int(q[2]), body=int(q[3]), index=int(q[4]), ref=ref_g, chosen=ch_g,
                v92=int(q[7]), nn=int(q[8]), n=n, pub=pub, ctx_round=int(q[11]) if o else pub, groups=groups, map=mp,
                alpha=_f64(q[12 + o]), p=_f64(q[13 + o]), native=logits, x=x, ec=ec.reshape(n, EMB),
                ft=ft.reshape(n, NF))


def batch(rows: list) -> dict:
    """Pad to 10 camp slots + far (slot 10); invalid slots masked. Every float input is an exact scaling."""
    B = len(rows)
    ctx = np.zeros((B, CTX), np.float32)
    camp = np.zeros((B, N_CAMP, EMB), np.float32)
    feat = np.zeros((B, N_CAMP, NF), np.float32)
    nat = np.zeros((B, N_CAMP + 1), np.float32)
    valid = np.zeros((B, N_CAMP + 1), bool)
    mp = np.zeros((B, N_CAMP + 1), np.int64)
    ref = np.zeros(B, np.int64)
    act = np.zeros(B, np.int64)
    for b, r in enumerate(rows):
        n = r["n"]
        ctx[b] = r["x"].astype(np.float32) * np.float32(1 / 1024)
        camp[b, :n] = r["ec"].astype(np.float32) * np.float32(1 / 1024)
        feat[b, :n] = features(r["ft"])
        nat[b, :n], nat[b, N_CAMP] = r["native"][:n], r["native"][n]
        valid[b, :n] = True
        valid[b, N_CAMP] = True
        mp[b, :n], mp[b, N_CAMP] = r["map"][:n], r["map"][n]
        ref[b], act[b] = r["groups"].index(r["ref"]), r["groups"].index(r["chosen"])
    return dict(ctx=ctx, camp=camp, feat=feat, nat=nat, valid=valid, map=mp, ref=ref, act=act)


def replay(model, rows: list) -> tuple:
    t = {k: torch.from_numpy(v) for k, v in batch(rows).items()}
    with torch.no_grad():
        pol, alpha, _ = model(t["ctx"], t["camp"], t["feat"], t["nat"], t["valid"], t["map"], t["ref"], 14)
    pa = pol[torch.arange(len(rows)), t["act"]].double().numpy()
    return alpha.flatten().double().numpy(), pa


def read_bundle(path: str, side: str) -> list:
    with zipfile.ZipFile(path) as z:
        raw = z.read(f"team-{side.lower()}.stdout")
    out = []
    for line in raw.replace(bytes(1), b"\n").decode("utf-8", "replace").splitlines():
        q = line.split(" ")
        if q[0] in ("CNR2", "CNR3"):
            out.append(parse_cnr2(q))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--side", default="A")
    ap.add_argument("--header", required=True)
    a = ap.parse_args()
    model, ver = HX.load_header(a.header)
    rows = read_bundle(a.bundle, a.side)
    al, pa = replay(model, rows)
    la, lp = np.array([r["alpha"] for r in rows]), np.array([r["p"] for r in rows])
    print(f"{ver}: {len(rows)} CNR2 rows; max |alpha - logged| {np.abs(al - la).max():.3g}; "
          f"max |log p - logged| {np.abs(np.log(pa) - np.log(lp)).max():.3g}; explored {sum(r['chosen'] != r['ref'] for r in rows)}")


if __name__ == "__main__":
    main()
