"""Trajectory contract for DOOMSDAY RL (task rl-env-adapter-1104).

One shard = one directory holding a manifest (shard.json) and one little-endian binary file per column (<name>.bin).
Writing needs only the standard library, so collectors run on machines without numpy. Learners load columns with
numpy (np.fromfile / np.memmap) through load_shard(); validate() works with or without numpy.

Rules the format enforces (validate()):
  - one observation layout per shard (2 = 500 features, 4 = 556); loaders refuse to mix layouts or contract versions;
  - actor inputs are only the legal per-body features (x_fresh, x_stale and the ages); privileged data (match summary,
    replay, events) may feed reward/critic columns only and is never stored as actor features;
  - a row is one logged decision of one body; rows of a body are in round order within an episode;
  - logp is NaN exactly when has_logp == 0 (deterministic teachers such as v92 get no invented probabilities);
  - the sampled action is legal under its mask; inclusion weights are > 0 (Agent 2 logs unchanged decisions 1/KEEP);
  - death is not an episode end: terminated/truncated mark only a body's last decision of an episode, and never both;
  - a truncated body may bootstrap only from a real final observation: a boundary row (boundary=1, action=-1, weight 0)
    carrying the body's observation at the cut, with bootstrap_valid=1; log cuts and timeouts get bootstrap_valid=0;
  - PPO uses only shards whose manifest says sampling == "complete" (every policy decision logged, A2_NN_RL_KEEP=1)
    and episodes with ppo_eligible == true; subsampled shards are imitation/diagnostic data.
"""
from __future__ import annotations

import array
import hashlib
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from typing import Iterator

CONTRACT_VERSION = "rlenv-2"


@dataclass(frozen=True)
class ObsLayout:
    """Feature layout of one int16 observation vector (Agent 2 nnrec.cpp kG/kS/kA·kAF/kE·kEF/kC·kCF/kL·kLF)."""
    layout: int
    blocks: tuple  # (name, count, width) in vector order
    self_id_index: int  # index of the engine champion id (self block + 31)

    @property
    def nf(self) -> int:
        return sum(n * w for _, n, w in self.blocks)

    def offset(self, name: str) -> int:
        off = 0
        for b, n, w in self.blocks:
            if b == name:
                return off
            off += n * w
        raise KeyError(name)

    def width(self, name: str) -> int:
        return next(w for b, _, w in self.blocks if b == name)

    def count(self, name: str) -> int:
        return next(n for b, n, _ in self.blocks if b == name)


def _layout(layout: int, g: int, c: int) -> ObsLayout:
    blocks = (("g", 1, g), ("s", 1, 44), ("a", 5, 12), ("e", 8, 16), ("c", 10, c), ("l", 4, 8))
    return ObsLayout(layout, blocks, self_id_index=g + 31)


# Layout 10 = cl1: our own SDK-based encoder (bots/claude-rlenv-1104/src/clrl_rec.h, research/rl_env_1104/CL1_SCHEMA.md).
# Layouts 2 and 4 are external (Agent 2 recorder): readable here, never produced by our collector.
LAYOUTS = {
    10: ObsLayout(10, (("g", 1, 16), ("s", 1, 32), ("a", 5, 16), ("e", 6, 16), ("c", 12, 16), ("l", 4, 8)),
                  self_id_index=16 + 31),
    2: _layout(2, 16, 22),
    4: _layout(4, 22, 27),
}
EXTERNAL_LAYOUTS = (2, 4)
assert LAYOUTS[10].nf == 448 and LAYOUTS[2].nf == 500 and LAYOUTS[4].nf == 556


@dataclass(frozen=True)
class ActionSchema:
    name: str
    n: int
    control: str  # "hybrid": the network picks only this head, the rest is v92 code; "full": all primitive controls
    doc: str


ACTION_SCHEMAS = {
    # Agent 2 target head: index i < 10 = i-th nearest camp group in the c block, 10 = "far" (outside the 10 nearest).
    # cl1 macro head: c-row 0..11 (12 nearest camp groups) or 12 = none / outside the 12 nearest. Legal iff c-row present.
    "target13-cl1": ActionSchema("target13-cl1", 13, "hybrid",
                                 "v92's camp-group target mapped to a cl1 c-row; 12 = none or outside the 12 nearest"),
    "target11-v1": ActionSchema("target11-v1", 11, "hybrid",
                                "camp-group pointer over the c block; 10 = far; legal iff c-row valid"),
    # Full primitive control gets a new versioned schema (conditional heads: move/attack/cast/bank/buy/ward) when the
    # SDK action-phase audit (E0 test_action_phases) is done; it is not defined here yet.
}

# Column name -> (dtype code, trailing shape key). Shape keys: "" = [N], "nf" = [N, NF], "a" = [N, A], "h" = [N, H].
# dtype codes are numpy names; ARRAY_CODES maps them to the stdlib array typecodes used for writing.
COLUMNS = {
    "x_fresh": ("int16", "nf"),      # this decision's fresh features (NRL X)
    "x_stale": ("int16", "nf"),      # slow-part summary in force (NRZ X); zeros when has_stale == 0
    "has_stale": ("uint8", ""),
    "feat_round": ("int32", ""),     # round the fresh features were captured
    "stale_round": ("int32", ""),    # round the summary was computed; -1 unknown
    "act_round": ("int32", ""),      # round the action was applied
    "episode": ("uint32", ""),       # index into manifest["episodes"]
    "body_id": ("int32", ""),        # engine champion id (equals x_fresh[self_id_index])
    "slot": ("int8", ""),            # team slot 0..5
    "mask": ("uint8", "a"),          # legal actions (derived from the c block when the recorder logs none)
    "action": ("int16", ""),         # sampled / chosen action index
    "teacher_action": ("int16", ""), # v92's own choice in the same schema (Agent 2 'bs'); -1 none
    "executed": ("int16", ""),       # action the SDK actually applied; -1 unknown
    "logp": ("float32", ""),         # behaviour log-probability of `action`; NaN when has_logp == 0
    "has_logp": ("uint8", ""),
    "weight": ("float32", ""),       # inclusion weight (KEEP for subsampled unchanged rows, 1 otherwise)
    "changed": ("uint8", ""),        # action changed the body's target
    "reset": ("uint8", ""),          # first decision after episode start or a respawn (recurrent state reset)
    "reward": ("float32", ""),       # reward from this decision to the body's next logged decision (reward_spec)
    "dt_rounds": ("int32", ""),      # rounds from this decision to the next logged one (or episode end)
    "terminated": ("uint8", ""),     # body's last row and the game ended (engine outcome)
    "truncated": ("uint8", ""),      # body's last decision and the game did not end (round cap, timeout, log cut)
    "boundary": ("uint8", ""),       # observation-only row at a truncation cut: action -1, weight 0, excluded from losses
    "bootstrap_valid": ("uint8", ""),  # on a truncated decision: 1 iff the next row is this body's boundary row
    "h0": ("float32", "h"),          # recurrent state before this decision; absent when hidden_size == 0
    # Primitive outcome of the turn (manifest prim_labels: true), measured by diffing the body's state at capture and
    # at the end of its turn: bits 1 moved, 2 attacked, 4 cast, 8 recall started, 16 submit started, 32 bought,
    # 64 ward placed. Labels for full-control curricula; never actor inputs.
    "prim": ("uint16", ""),
    "move_dx": ("int8", ""),
    "move_dy": ("int8", ""),
}
PRIM_COLUMNS = ("prim", "move_dx", "move_dy")
ARRAY_CODES = {"int8": "b", "uint8": "B", "int16": "h", "uint16": "H", "int32": "i", "uint32": "I", "float32": "f"}
ITEMSIZE = {"int8": 1, "uint8": 1, "int16": 2, "uint16": 2, "int32": 4, "uint32": 4, "float32": 4}
EPISODE_STATUS = ("terminated", "truncated", "truncated_log", "failed")
SAMPLING = ("complete", "subsampled", "teacher")  # complete = every policy decision logged (A2_NN_RL_KEEP=1)


def episode_split(map_hash: str, salt: str = "rlenv-1104", dev_fraction: float = 0.2) -> str:
    """Deterministic train/dev split by map, so both sides and all opponents of a map land on the same side."""
    h = int(hashlib.sha256(f"{salt}|{map_hash}".encode()).hexdigest()[:8], 16)
    return "dev" if h / 0xFFFFFFFF < dev_fraction else "train"


def column_shape(name: str, rows: int, manifest: dict) -> tuple:
    key = COLUMNS[name][1]
    if key == "":
        return (rows,)
    if key == "nf":
        return (rows, LAYOUTS[manifest["layout"]].nf)
    if key == "a":
        return (rows, ACTION_SCHEMAS[manifest["action_schema"]].n)
    return (rows, manifest["hidden_size"])


def required_columns(manifest: dict) -> list:
    skip = set()
    if manifest.get("hidden_size", 0) == 0:
        skip.add("h0")
    if not manifest.get("stale_block", True):  # layouts without a slow summary (cl1) omit x_stale; has_stale stays 0
        skip.add("x_stale")
    if not manifest.get("prim_labels", False):
        skip.update(PRIM_COLUMNS)
    return [c for c in COLUMNS if c not in skip]


class ShardWriter:
    """Append episodes; flush to a new shard every `max_rows` rows. Shards are immutable once written.

    Resume: episode keys already present in any shard of `run_dir` are reported by done_keys(), so a restarted
    collector skips finished games. Each shard is written to a temp dir and renamed, so a crash leaves no half shard.
    """

    def __init__(self, run_dir: str, base_manifest: dict, max_rows: int = 50_000):
        for k in ("layout", "action_schema", "reward_spec", "policy", "engine", "run_ns", "sampling"):
            if k not in base_manifest:
                raise ValueError(f"base manifest needs {k}")
        if base_manifest["layout"] not in LAYOUTS:
            raise ValueError(f"unknown layout {base_manifest['layout']}")
        if base_manifest["sampling"] not in SAMPLING:
            raise ValueError(f"sampling must be one of {SAMPLING}")
        self.run_dir, self.base, self.max_rows = run_dir, dict(base_manifest), max_rows
        self.base.setdefault("hidden_size", 0)
        os.makedirs(run_dir, exist_ok=True)
        self._cols = {c: array.array(ARRAY_CODES[COLUMNS[c][0]]) for c in required_columns(self.base)}
        self._episodes, self._rows = [], 0
        self._next = 1 + max([int(d.split("_")[1]) for d in os.listdir(run_dir) if d.startswith("shard_")] or [-1])

    def done_keys(self) -> set:
        keys = set()
        for d in sorted(os.listdir(self.run_dir)):
            p = os.path.join(self.run_dir, d, "shard.json")
            if d.startswith("shard_") and not d.endswith(".tmp") and os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    keys |= {e["key"] for e in json.load(f)["episodes"]}
        return keys | {e["key"] for e in self._episodes}

    def add_episode(self, meta: dict, rows: dict) -> None:
        """meta: key, map_file, map_hash, opponent{name, wasm_sha256}, side, seed, status, our_team, outcome,
        rounds_completed. rows: column -> flat list (row-major for 2-D columns); `episode` is filled in here."""
        if meta.get("status") not in EPISODE_STATUS:
            raise ValueError(f"episode status must be one of {EPISODE_STATUS}")
        n = len(rows["action"])
        rows = dict(rows, episode=[len(self._episodes)] * n)
        eligible = (self.base["sampling"] == "complete" and meta["status"] in ("terminated", "truncated")
                    and meta.get("reward_complete", False))
        meta = dict(meta, split=meta.get("split") or episode_split(meta["map_hash"]), rows=n,
                    ppo_eligible=bool(meta.get("ppo_eligible", eligible)) and eligible)
        for c, buf in self._cols.items():
            want = math.prod(column_shape(c, n, self.base))
            vals = rows[c]
            if len(vals) != want:
                raise ValueError(f"{c}: {len(vals)} values, expected {want}")
            buf.extend(vals)
        self._episodes.append(meta)
        self._rows += n
        if self._rows >= self.max_rows:
            self.flush()

    def flush(self) -> str | None:
        if not self._episodes:
            return None
        name = f"shard_{self._next:05d}"
        tmp, final = os.path.join(self.run_dir, name + ".tmp"), os.path.join(self.run_dir, name)
        os.makedirs(tmp, exist_ok=False)
        cols = {}
        for c, buf in self._cols.items():
            if sys.byteorder != "little":
                buf = array.array(buf.typecode, buf)
                buf.byteswap()
            with open(os.path.join(tmp, c + ".bin"), "wb") as f:
                buf.tofile(f)
            cols[c] = {"dtype": COLUMNS[c][0], "shape": list(column_shape(c, self._rows, self.base))}
        man = dict(self.base, contract_version=CONTRACT_VERSION, rows=self._rows, episodes=self._episodes,
                   columns=cols, created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        with open(os.path.join(tmp, "shard.json"), "w", encoding="utf-8") as f:
            json.dump(man, f, indent=1)
        os.replace(tmp, final)
        self._cols = {c: array.array(b.typecode) for c, b in self._cols.items()}
        self._episodes, self._rows, self._next = [], 0, self._next + 1
        return final


def _read_column(path: str, dtype: str, shape: list, use_numpy: bool):
    if use_numpy:
        import numpy as np
        return np.fromfile(path, dtype=np.dtype(dtype).newbyteorder("<")).reshape(shape)
    buf = array.array(ARRAY_CODES[dtype])
    with open(path, "rb") as f:
        buf.frombytes(f.read())
    if sys.byteorder != "little":
        buf.byteswap()
    return buf


def load_shard(shard_dir: str, use_numpy: bool | None = None) -> tuple:
    """Return (manifest, {column: array}). With numpy: arrays shaped per manifest. Without: flat stdlib arrays."""
    if use_numpy is None:
        try:
            import numpy  # noqa: F401
            use_numpy = True
        except ImportError:
            use_numpy = False
    with open(os.path.join(shard_dir, "shard.json"), encoding="utf-8") as f:
        man = json.load(f)
    if man.get("contract_version") != CONTRACT_VERSION:
        raise ValueError(f"{shard_dir}: contract {man.get('contract_version')} != {CONTRACT_VERSION}")
    cols = {c: _read_column(os.path.join(shard_dir, c + ".bin"), spec["dtype"], spec["shape"], use_numpy)
            for c, spec in man["columns"].items()}
    return man, cols


def iter_shards(root: str, layout: int, split: str | None = None, action_schema: str = "target13-cl1",
                validate_each: bool = True) -> Iterator[tuple]:
    """Yield (manifest, columns) for every shard under root (recursively) with this layout/schema.
    Raises on a shard of another layout or contract instead of skipping it silently: mixing is a data error."""
    for dirpath, dirs, files in os.walk(root):
        dirs.sort()
        if "shard.json" not in files or dirpath.endswith(".tmp"):
            continue
        man, cols = load_shard(dirpath)
        if man["layout"] != layout or man["action_schema"] != action_schema:
            raise ValueError(f"{dirpath}: layout {man['layout']}/{man['action_schema']} in a {layout}/{action_schema} "
                             f"stream; keep layouts in separate roots")
        if validate_each:
            errs = validate(man, cols)
            if errs:
                raise ValueError(f"{dirpath}: " + "; ".join(errs[:5]))
        if split is not None:
            keep = [i for i, e in enumerate(man["episodes"]) if e["split"] == split]
            if not keep:
                continue
            man = dict(man, selected_episodes=keep)
        yield man, cols


def validate(man: dict, cols: dict) -> list:
    """Check one shard against the contract. Returns a list of error strings (empty = valid)."""
    errs = []
    lay = LAYOUTS.get(man.get("layout"))
    sch = ACTION_SCHEMAS.get(man.get("action_schema"))
    if lay is None or sch is None:
        return [f"unknown layout/schema {man.get('layout')}/{man.get('action_schema')}"]
    n = man["rows"]
    for c in required_columns(man):
        if c not in cols:
            errs.append(f"missing column {c}")
            continue
        want = math.prod(column_shape(c, n, man))
        got = cols[c].size if hasattr(cols[c], "size") else len(cols[c])
        if got != want:
            errs.append(f"{c}: {got} values, expected {want}")
    if errs:
        return errs

    def flat(c):
        v = cols[c]
        return v.reshape(-1).tolist() if hasattr(v, "reshape") else list(v)

    nf, na = lay.nf, sch.n
    xf, mask = flat("x_fresh"), flat("mask")
    act, logp, hasl, w = flat("action"), flat("logp"), flat("has_logp"), flat("weight")
    ep, body, fr, ar, sr = flat("episode"), flat("body_id"), flat("feat_round"), flat("act_round"), flat("stale_round")
    term, trunc, dt = flat("terminated"), flat("truncated"), flat("dt_rounds")
    bnd, bval = flat("boundary"), flat("bootstrap_valid")
    if man.get("sampling") not in SAMPLING:
        errs.append(f"manifest sampling {man.get('sampling')!r} not in {SAMPLING}")
    last_row, last_dec = {}, {}
    for i in range(n):
        if bnd[i]:
            if act[i] != -1 or w[i] != 0 or hasl[i] != 0 or term[i] or trunc[i] or bval[i]:
                errs.append(f"row {i}: boundary row must have action -1, weight 0, no logp and no flags")
            prev = last_dec.get((ep[i], body[i]))
            if prev is None or not trunc[prev] or not bval[prev]:
                errs.append(f"row {i}: boundary row without a preceding truncated, bootstrap_valid decision")
        else:
            if not 0 <= act[i] < na:
                errs.append(f"row {i}: action {act[i]} outside 0..{na - 1}")
            elif mask[i * na + act[i]] != 1:
                errs.append(f"row {i}: action {act[i]} not legal under its mask")
            if not w[i] > 0:
                errs.append(f"row {i}: weight {w[i]} <= 0")
            if bval[i] and not trunc[i]:
                errs.append(f"row {i}: bootstrap_valid on a row that is not a truncated final decision")
        if hasl[i] not in (0, 1) or (hasl[i] == 1) == math.isnan(logp[i]):
            errs.append(f"row {i}: logp/has_logp mismatch")
        elif hasl[i] == 1 and logp[i] > 1e-6:
            errs.append(f"row {i}: logp {logp[i]} > 0")
        if xf[i * nf + lay.self_id_index] != body[i]:
            errs.append(f"row {i}: body_id {body[i]} != self-id feature {xf[i * nf + lay.self_id_index]}")
        if ar[i] < fr[i] or (sr[i] >= 0 and sr[i] > fr[i]):
            errs.append(f"row {i}: round order stale {sr[i]} <= feat {fr[i]} <= act {ar[i]} violated")
        if dt[i] < 0:
            errs.append(f"row {i}: dt_rounds {dt[i]} < 0")
        if term[i] and trunc[i]:
            errs.append(f"row {i}: both terminated and truncated")
        if not 0 <= ep[i] < len(man["episodes"]):
            errs.append(f"row {i}: episode {ep[i]} out of range")
        key = (ep[i], body[i])
        if key in last_row and fr[i] < fr[last_row[key]]:
            errs.append(f"row {i}: body {body[i]} rows out of round order")
        last_row[key] = i
        if not bnd[i]:
            last_dec[key] = i
        if len(errs) > 50:
            errs.append("... (truncated)")
            return errs
    ends = set(last_dec.values())
    for i in range(n):
        if (term[i] or trunc[i]) and i not in ends:
            errs.append(f"row {i}: terminal flag on a non-final row of body {body[i]} (death is not an episode end)")
    for key, i in last_dec.items():
        if bval[i] and last_row[key] == i:
            errs.append(f"row {i}: bootstrap_valid but no boundary row follows")
    for e, meta in enumerate(man["episodes"]):
        if meta.get("ppo_eligible") and man.get("sampling") != "complete":
            errs.append(f"episode {e}: ppo_eligible in a {man.get('sampling')} shard")
        if meta.get("ppo_eligible") and meta["status"] not in ("terminated", "truncated"):
            errs.append(f"episode {e}: ppo_eligible with status {meta['status']}")
        for i in (r for (ee, _), r in last_dec.items() if ee == e):
            if meta["status"] in ("truncated_log", "failed") and bval[i]:
                errs.append(f"episode {e}: {meta['status']} episode may not bootstrap (row {i})")
            if meta["status"] == "terminated" and not term[i]:
                errs.append(f"episode {e}: terminated game but body's last row {i} not marked terminated")
            if meta["status"] != "terminated" and term[i]:
                errs.append(f"episode {e}: status {meta['status']} but row {i} marked terminated")
    return errs
