"""Neural bot: per-head imitation labels from the recorder's rows (agent2/lab/nn_record.py output; layout in nnrec.cpp).
Heads (-1 = no label / masked out of the loss):
  behaviour  0 farm, 1 bank, 2 fight champions, 3 flee, 4 home, 5 ward, 6 regroup, 7 idle      (from v92's mode)
  target     camp slot 0-9 holding v92's target_group, 10 = target farther than the 10 nearest groups
  step       0-7 direction of this turn's move (DIRS order), 8 = no move
  attack     0-7 enemy slot, 8-17 camp slot (8 + camp slot), 18 = no attack
  cast       0 none, 1 slot 0, 2 slot 1
  cast_tgt   0 self, 1-5 ally slot, 6-13 enemy slot, 14-23 camp slot, 24-31 position in direction d, 32 own tile
  cast_pre   1 the cast came before the move, 0 after (or no move)
  utility    0 none, 1 recall, 2 tribute (submit gems), 3 ward, 4 use consumable, 5 cancel channel
  shop       0 none, 1 + item id (buy_item), 1 + 84 + consumable id (buy_consumable)
usage: python -P nn_labels.py DATA_DIR OUT.npz   (all games; writes X int16, meta, labels int16 [N, 9], game index, map key)
"""
import glob, json, os, sys
import numpy as np

D, OUTF = sys.argv[1], sys.argv[2]
if int(os.environ.get("NN_LAYOUT", "2")) == 3:  # version 3: 24 camp groups, allies' claimed targets (828 features)
    NF = 828
    G, S, A, AF, E, EF, C, CF, L, LF = 0, 16, 60, 16, 140, 16, 268, 22, 796, 8
    NA, NE, NC, NL = 5, 8, 24, 4
else:
    NF = 500
    G, S, A, AF, E, EF, C, CF, L, LF = 0, 16, 60, 12, 120, 16, 248, 22, 468, 8  # offsets and per-entity widths
    NA, NE, NC, NL = 5, 8, 10, 4
T_FAR, A_NONE = NC, NE + NC                                  # target: far; attack: none
CT_A, CT_E, CT_C, CT_DIR = 1, 1 + NA, 1 + NA + NE, 1 + NA + NE + NC  # cast target offsets (self = 0); own tile = CT_DIR + 8
DIRS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
BEH = {0: "approach stage wait-respawn capture to-capture capture-stand siege fight nofarm-camp reveal snipe-camp",
       1: "tribute tribute-win plan-bank",
       2: "fight-champ kite kite-cast hold-kite cmicro tsearch hunt pairhunt snipe gap-dash stand stand2 enemy rush-lead "
          "counter-ambush bush-ambush",
       3: "flee flee-dash flee-stun disengage danger-avoid evade-ambush home-escape",
       4: "home recall-travel flee-home bush-recall teleport",
       5: "bush-ward",
       6: "join regroup fog-regroup converge escort rescue rush-join rush-follow"}
MB = {m: b for b, ms in BEH.items() for m in ms.split()}
modes = json.load(open(os.path.join(D, "modes.json")))
inv = {v: k for k, v in modes.items()}
beh_of_mode = np.array([MB.get(inv[i], 7) for i in range(len(inv))], np.int16)

Xs, Ms, Ys, gi, keys = [], [], [], [], []
files = sorted(glob.glob(os.path.join(D, "*.npz")))
for k, f in enumerate(files):
    d = np.load(f)
    X, M, ACT = d["X"], d["meta"], d["acts"]
    camps = {s: dict(tuple(int(t) for t in p.split(":")) for p in v.split()) for s, v in json.loads(str(d["camps"])).items()}
    Y = np.full((len(X), 9), -1, np.int16)
    for i in range(len(X)):
        x, m, acts = X[i], M[i], str(ACT[i]).split()
        Y[i, 0] = beh_of_mode[m[3]]
        cg = x[C + 1:C + NC * CF:CF]  # group index per camp slot
        cpresent = x[C:C + NC * CF:CF]
        tg = m[4]
        if tg >= 0:
            hit = np.where((cpresent == 1) & (cg == tg))[0]
            Y[i, 1] = hit[0] if len(hit) else T_FAR
        px, py = int(x[S + 18]), int(x[S + 19])
        ehandle = x[E + 14:E + NE * EF:EF]
        ahandle = x[A + 10:A + NA * AF:AF]
        epresent = x[E:E + NE * EF:EF]
        step, att, cast, ctgt, cpre, util, shop = 8, A_NONE, 0, -1, 0, 0, 0
        moved = False
        cmap = camps.get(str(m[1]), {})
        for a in acts:
            t, _, v = a.partition(":")
            v = [int(z) for z in v.split(",")] if v else []
            if t == "m" and v[2] == 1 and not moved:
                dx, dy = np.sign(v[0] - px), np.sign(v[1] - py)
                if (dx, dy) in DIRS:
                    step = DIRS.index((dx, dy)); moved = True
            elif t == "a" and v[2] == 0 and att == A_NONE:
                if v[0] == 1:
                    h = np.where((epresent == 1) & (ehandle == v[1]))[0]
                    if len(h): att = h[0]
                elif v[0] == 2 and v[1] in cmap:
                    h = np.where((cpresent == 1) & (cg == cmap[v[1]]))[0]
                    if len(h): att = NE + h[0]
            elif t == "c" and v[5] == 1 and cast == 0:
                cast = 1 + v[0]; cpre = 0 if moved else 1
                if v[1] == 1 and v[2] == int(x[S + 31]):
                    ctgt = 0
                elif v[1] == 1:
                    h = np.where((ahandle == v[2]) & (x[A:A + NA * AF:AF] == 1))[0]
                    if len(h): ctgt = CT_A + h[0]
                    else:
                        h = np.where((epresent == 1) & (ehandle == v[2]))[0]
                        ctgt = CT_E + h[0] if len(h) else CT_DIR + 8
                elif v[1] == 2 and v[2] in cmap:
                    h = np.where((cpresent == 1) & (cg == cmap[v[2]]))[0]
                    ctgt = CT_C + h[0] if len(h) else CT_DIR + 8
                else:
                    # position cast: the enemy within 2 of the point, else the camp group whose centre is within 4
                    gx, gy = v[3] - px, v[4] - py
                    sd = (int(np.sign(gx)), int(np.sign(gy)))
                    ctgt = CT_DIR + DIRS.index(sd) if sd in DIRS else CT_DIR + 8  # direction of a dash / far point; 32 = own tile
                    ed = [max(abs(int(x[E + j * EF + 2]) - gx), abs(int(x[E + j * EF + 3]) - gy)) if epresent[j] else 99 for j in range(NE)]
                    cd = [max(abs(int(x[C + j * CF + 2]) - gx), abs(int(x[C + j * CF + 3]) - gy)) if cpresent[j] else 99 for j in range(NC)]
                    if min(ed) <= 2:
                        ctgt = CT_E + int(np.argmin(ed))
                    elif min(cd) <= 4:
                        ctgt = CT_C + int(np.argmin(cd))
            elif t == "r": util = 1
            elif t == "s": util = 2
            elif t == "w" and v[2] == 1: util = 3
            elif t == "u" and v[3] == 1: util = 4
            elif t == "cc": util = 5
            elif t == "bi" and shop == 0: shop = 1 + v[0]
            elif t == "bc" and shop == 0: shop = 1 + 84 + v[0]
        Y[i, 2], Y[i, 3], Y[i, 4], Y[i, 5], Y[i, 6], Y[i, 7], Y[i, 8] = step, att, cast, ctgt, cpre if cast else -1, util, shop
    Xs.append(X); Ms.append(M); Ys.append(Y); gi.append(np.full(len(X), k, np.int32))
    keys.append(os.path.basename(f).split("__")[0] + "/" + os.path.basename(f).split("__")[1])
X, M, Y, GI = np.concatenate(Xs), np.concatenate(Ms), np.concatenate(Ys), np.concatenate(gi)
np.savez(OUTF, X=X, meta=M, Y=Y, game=GI, keys=np.array(keys), files=np.array([os.path.basename(f) for f in files]))
names = ["behaviour", "target", "step", "attack", "cast", "cast_tgt", "cast_pre", "utility", "shop"]
print(f"{len(files)} games, {len(X)} rows")
for j, n in enumerate(names):
    v = Y[:, j][Y[:, j] >= 0]
    u, c = np.unique(v, return_counts=True)
    top = sorted(zip(c, u), reverse=True)[:8]
    print(f"{n:9s} labelled {len(v) / len(Y):.2f}; top classes " + ", ".join(f"{int(b)}:{a / len(v):.2f}" for a, b in top))
