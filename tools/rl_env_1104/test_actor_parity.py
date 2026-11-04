"""Parity of our float32 C++ actor (bots/claude-rlenv-1104/src/clrl_actor.h) against JOHNDOE's parity fixtures.

Exports actor.json -> clrl_actor_weights.h (exact float32 literals), the fixtures -> a header, compiles
actor_parity_main.cpp with the host g++ and compares preprocessing, logits (null = illegal), hidden output and argmax
with the fixture tolerance (absolute 2e-6 + relative 1e-5). Standard library only.

With --wasm it also builds a release bot (v92 + the actor) whose draft VM (10M fuel) runs every fixture once and prints
logits and hidden state, plays one round on the real engine and compares those (target runtime parity).

usage: python tools/rl_env_1104/test_actor_parity.py ACTOR.json PARITY.json [--cxx g++] [--wasm]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "bots", "claude-rlenv-1104", "src")
WORK = os.path.join(ROOT, "artifacts", "tmp", "rl_env_1104", "actor_parity")
NL, BS, NUL = chr(10), chr(92), bytes(1)

# C++ lines added to the parity bot's main(): run every fixture once in the draft VM and print logits + hidden.
WASM_LOOP = NL.join([
    "    if (bc::is_draft()) for (int f = 0; f < clrl_fx::kN; ++f) {",
    "        clrl_actor::Out o;",
    "        clrl_actor::forward(clrl_fx::raw[f], clrl_fx::hidden_in + f * clrl_actor::kH, clrl_fx::reset[f], o);",
    '        std::printf("PAR {' + BS + '"i' + BS + '":%d,' + BS + '"logits' + BS + '":[", f);',
    "        for (int i = 0; i < clrl_actor::kNA; ++i)",
    '            std::isinf(o.logits[i]) ? std::printf("%snull", i ? "," : "")'
    ' : std::printf("%s%.9g", i ? "," : "", (double)o.logits[i]);',
    '        std::printf("],' + BS + '"hidden' + BS + '":[");',
    '        for (int i = 0; i < clrl_actor::kH; ++i) std::printf("%s%.9g", i ? "," : "", (double)o.h[i]);',
    '        std::printf("]}' + BS + 'n");',
    "    }",
    "",
])


def close(a, b, tol) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= tol["absolute"] + tol["relative"] * abs(b)


def cmp(name, got, want, tol, errs, worst):
    if isinstance(want, list):
        if not isinstance(got, list) or len(got) != len(want):
            errs.append(f"{name}: shape {len(got) if isinstance(got, list) else '?'} != {len(want)}")
            return
        for i, (g, w) in enumerate(zip(got, want)):
            cmp(f"{name}[{i}]", g, w, tol, errs, worst)
        return
    if not close(got, want, tol):
        errs.append(f"{name}: {got} != {want}")
    elif got is not None:
        worst[0] = max(worst[0], abs(got - want))


def argmax_legal(logits: list) -> int:
    return max((v, j) for j, v in enumerate(logits) if v is not None)[1]


def wasm_parity(p: dict, fx_h: str) -> bool:
    """Run the fixtures in the draft VM of a release build (printing is costly in WASM, so only logits/hidden)."""
    cli = os.path.join(ROOT, "tools", "vendor", "cambc.exe" if os.name == "nt" else "cambc")
    bot = os.path.join(WORK, "bot")
    shutil.rmtree(bot, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, "bots", "v92", "src"), os.path.join(bot, "src"),
                    ignore=shutil.ignore_patterns(".cambc", "compile_commands.json"))
    for f in ("clrl_actor.h", "clrl_actor_weights.h"):
        shutil.copy(os.path.join(SRC, f), os.path.join(bot, "src", f))
    shutil.copy(fx_h, os.path.join(bot, "src", "clrl_parity_fixtures.h"))
    m = os.path.join(bot, "src", "main.cpp")
    with open(m, encoding="utf-8") as f:
        s = f.read()
    s = s.replace('#include "draft.h"' + NL, '#include "draft.h"' + NL + "#include <cmath>" + NL +
                  '#include "clrl_actor.h"' + NL + '#include "clrl_parity_fixtures.h"' + NL, 1)
    s = s.replace("int main() {" + NL, "int main() {" + NL + WASM_LOOP, 1)
    with open(m, "w", encoding="utf-8", newline="") as f:
        f.write(s)
    rel = os.path.relpath(bot, ROOT).replace(BS, "/")
    run = os.path.join(WORK, "run")
    shutil.rmtree(run, ignore_errors=True)
    r = subprocess.run([cli, "run", rel, "bots/v92", "--map", "maps/ladder-pool/00corners.map26a", "--rounds", "1",
                        "--release", "-o", run], cwd=ROOT, capture_output=True, text=True, timeout=900)
    bundles = [os.path.join(run, n) for n in os.listdir(run)] if os.path.isdir(run) else []
    if not bundles:
        print("wasm: run failed", r.stdout[-1500:], r.stderr[-1500:])
        return False
    with zipfile.ZipFile(bundles[0]) as z:  # the engine can insert NUL bytes into team stdout
        out = z.read("team-a.stdout").replace(NUL, b"").decode("utf-8", "replace")
    tol, errs, worst, ok, seen = p["tolerance"], [], [0.0], 0, set()
    for line in out.splitlines():
        if not line.startswith("PAR "):
            continue
        q = json.loads(line[4:])
        i = q["i"]
        if i in seen:
            continue
        seen.add(i)
        cmp(f"wasm fx{i}.logits", q["logits"], p["logits"][i], tol, errs, worst)
        cmp(f"wasm fx{i}.hidden", q["hidden"], p["hidden_out"][i], tol, errs, worst)
        ok += argmax_legal(q["logits"]) == p["argmax"][i]
    print(f"wasm (release, in engine): fixtures {len(seen)}/{len(p['raw'])}, argmax agree {ok}, "
          f"max abs error {worst[0]:.3g}, mismatches {len(errs)}")
    for e in errs[:10]:
        print("  ", e)
    return not errs and len(seen) == len(p["raw"]) == ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("actor")
    ap.add_argument("parity")
    ap.add_argument("--cxx", default=shutil.which("g++") or "g++")
    ap.add_argument("--wasm", action="store_true", help="also check parity inside the engine (release WASM)")
    a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)
    fx_h = os.path.join(WORK, "clrl_parity_fixtures.h")
    subprocess.run([sys.executable, os.path.join(HERE, "export_actor.py"), a.actor,
                    os.path.join(SRC, "clrl_actor_weights.h"), "--parity", a.parity, "--parity-out", fx_h], check=True)
    exe = os.path.join(WORK, "actor_parity.exe")
    subprocess.run([a.cxx, "-std=c++20", "-O2", "-ffp-contract=off", "-I", SRC, "-I", WORK,
                    os.path.join(HERE, "actor_parity_main.cpp"), "-o", exe], check=True)
    out = subprocess.run([exe], capture_output=True, text=True, check=True).stdout.splitlines()
    with open(a.parity, encoding="utf-8") as f:
        p = json.load(f)
    tol = p["tolerance"]
    errs, worst, argmax_ok = [], [0.0], 0
    for line in out:
        r = json.loads(line)
        i = r["i"]
        cmp(f"fx{i}.globals", r["globals"], p["globals"][i], tol, errs, worst)
        for k in ("ally", "enemy", "camp", "altar"):
            cmp(f"fx{i}.{k}", r[k], p["entities"][k][i], tol, errs, worst)
        cmp(f"fx{i}.logits", r["logits"], p["logits"][i], tol, errs, worst)
        cmp(f"fx{i}.hidden", r["hidden"], p["hidden_out"][i], tol, errs, worst)
        argmax_ok += argmax_legal(r["logits"]) == p["argmax"][i]
    print(f"host: fixtures {len(out)}, argmax agree {argmax_ok}/{len(out)}, max abs error {worst[0]:.3g}, "
          f"mismatches {len(errs)}")
    for e in errs[:10]:
        print("  ", e)
    ok = not errs and argmax_ok == len(out) == len(p["raw"])
    if a.wasm:
        ok = wasm_parity(p, fx_h) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
