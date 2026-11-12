"""Profile existing post-ward observation on independent dense stress maps."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import re
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from cpg_runtime_release import prepare
from large_roster_stress import DENSE_OUT, HERE, bench, native_fuel, read
from pg_dash_followup import read_turn
from qualify_local import DEV

OUT = bench.CACHE / "ward-refresh-stress-95000"
FUEL = 95000


def instrument(src):
    apply(src / "bot.cpp", (
        ('#include "bot.h"', '''#include "bot.h"

static struct CodexRefreshSample {
    const char* caller;
    int round;
    unsigned long long before;
} codex_refresh_sample;'''),
        ("    if (ward_reveal()) w.update(round); // the ward shows the bush now: look again",
         """    if (ward_reveal()) {
        const auto fuel = bc::fuel_remaining();
        w.update(round);
        if (static_cast<int>(bc::round_number()) != round)
            codex_refresh_sample = {"ahead", round, fuel};
    }"""),
        ("        if (me.place_ward(at)) ward_pos = at;\n        w.update(round);",
         """        if (me.place_ward(at)) ward_pos = at;
        const auto fuel = bc::fuel_remaining();
        w.update(round);
        if (static_cast<int>(bc::round_number()) != round)
            codex_refresh_sample = {"camp", round, fuel};"""),
        ("void Bot::play_turn() {", """void Bot::play_turn() {
    if (codex_refresh_sample.caller) {
        std::printf("CODEX_WARD_REFRESH %s R%d F%llu [%s]\\n", codex_refresh_sample.caller,
                    codex_refresh_sample.round, codex_refresh_sample.before, bc::to_string(type).c_str());
        codex_refresh_sample.caller = nullptr;
    }"""),
    ))


def folder(row):
    return OUT / "games" / f"{row['arm']}-0-{row['opponent']}-{row['map']}-{row['side']}"


def compare(pair):
    base, trace = pair
    assert all(base[k] == trace[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    bdir, tdir = folder(base), folder(trace)
    native_base, native_trace = (read(p / "native.json") for p in (bdir, tdir))
    draft_equal = native_base["roster"]["draft"] == native_trace["roster"]["draft"]
    errors = any(any(d["diagnostics"]["botFaults"].values()) or d["diagnostics"]["codes"] for d in (native_base, native_trace))
    archive, = tdir.glob("*.repl26a")
    with ZipFile(archive) as z:
        log = z.read(f"team-{trace['side'].lower()}.stdout")
    records = re.findall(rb"CODEX_WARD_REFRESH (\w+) R(\d+) F(\d+) \[([^\]]+)\]", log)
    old = {(e["timestamp"]["round"], e["owner"]["name"]): e["owner"]["id"] for e in native_fuel(base, OUT)}
    new = {(e["timestamp"]["round"], e["owner"]["name"]): e["owner"]["id"] for e in native_fuel(trace, OUT)}
    matches = []
    for caller, r, f, name in records:
        key = (int(r), name.decode("utf8"))
        if not draft_equal or key not in old or old[key] != new.get(key):
            continue
        b, t = (read_turn(p, key[0], base["side"], old[key]) for p in (bdir, tdir))
        if b and t and b["observation"] == t["observation"]:
            matches.append({"caller": caller.decode("ascii"), "round": key[0], "champion": key[1],
                            "fuel_at_entry": int(f), "observation": b["observation"]})
    return {"base": base, "trace": trace, "draft_equal": draft_equal, "errors": bool(errors),
            "markers": len(records), "matches": matches}


def main():
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    reference = bench.ROOT / "bots/codex-cpg-runtime-packed/bot.wasm"
    assert bench.digest(reference) == read(HERE / "CPG_RUNTIME_PACKED_BUILDS.json")["primary"]
    project = OUT / "diagnostic"
    src = project / "src"
    prepare(src, True, packed=True)
    instrument(src)
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    manifest = read(HERE / "DENSE_ROSTER_MAPS.json")["maps"]
    maps = sorted((DENSE_OUT / "maps").glob("*.map26a"), key=lambda p: sha256(f"exp103:{p.name}".encode()).digest())[:16]
    assert len(maps) == 16 and all(bench.digest(p) == manifest[p.name] for p in maps)
    for o in DEV:
        file, digest = bench.OPPS[o]
        assert bench.digest(bench.CACHE / file) == digest
    jobs = [(arm, 0, o, m, side, binary) for m in maps for o in DEV for side in "AB"
            for arm, binary in (("base", reference), ("trace", wasm))]
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(lambda j: bench.one(j, fuel=FUEL, log_limit=1048576), jobs))
        results = list(pool.map(compare, zip(rows[::2], rows[1::2], strict=True)))
    matched = [r for r in results if r["matches"]]
    result = {"engine": bench.ENGINE, "reference": bench.digest(reference), "diagnostic": bench.digest(wasm), "fuel": FUEL,
              "n": len(results), "markers": sum(r["markers"] for r in results), "errors": sum(r["errors"] for r in results),
              "matches": sum(len(r["matches"]) for r in matched), "maps": sorted({r["base"]["map"] for r in matched})}
    with (HERE / "WARD_REFRESH_STRESS.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "results": results}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
