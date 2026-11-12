"""Neural bot: merge label sets (nn_labels.py outputs) for DAgger; optional row subsample per set.
usage: python -P nn_merge.py OUT.npz A.npz[:fraction] B.npz[:fraction] ..."""
import sys
import numpy as np

out, parts = sys.argv[1], sys.argv[2:]
X, M, Y, G, K = [], [], [], [], []
off = 0
rng = np.random.default_rng(0)
for p in parts:
    f, _, frac = p.partition(":")
    d = np.load(f)
    n = len(d["Y"])
    idx = np.sort(rng.choice(n, int(n * float(frac)), replace=False)) if frac else np.arange(n)
    X.append(d["X"][idx]); M.append(d["meta"][idx]); Y.append(d["Y"][idx]); G.append(d["game"][idx] + off)
    K.append(d["keys"]); off += len(d["keys"])
    print(f, len(idx), "rows")
np.savez(out, X=np.concatenate(X), meta=np.concatenate(M), Y=np.concatenate(Y), game=np.concatenate(G), keys=np.concatenate(K))
print("merged", sum(len(y) for y in Y))
