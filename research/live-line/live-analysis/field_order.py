"""Test the exact v92 guard for field-order work that cannot feed a field yet."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
from pathlib import Path
import re
from shutil import copytree
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from bounded_verdict import apply

HERE = Path(__file__).resolve().parent
OUT = bench.CACHE / "field-order-probe"
LIMIT = 1048576


def prepare(src, enabled, diagnostic):
    copytree(bench.ROOT / "bots/v92/src", src)
    common = src / "common.h"
    data = common.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    common.write_bytes(nl.join([
        f"#define CODEX_FIELD_ORDER_ROOM {int(enabled)}".encode(),
        f"#define CODEX_FIELD_ORDER_DIAG {int(diagnostic)}".encode(),
        data,
    ]))
    apply(src / "bot.cpp", (
        ("        if (!w.fields_ready() && quota > 0) w.prepare_field_order();",
         """#if CODEX_FIELD_ORDER_ROOM
        if (!w.fields_ready() && quota > 0 && w.field_order.empty()) {
            if (room()) {
#if CODEX_FIELD_ORDER_DIAG
                const std::uint64_t before = bc::fuel_remaining();
#endif
                w.prepare_field_order();
#if CODEX_FIELD_ORDER_DIAG
                std::printf("CODEX_ORDER_BUILT R%d S%d G%zu F%llu\\\\n", round, slot, w.field_order.size(),
                    static_cast<unsigned long long>(before - bc::fuel_remaining()));
#endif
            }
#if CODEX_FIELD_ORDER_DIAG
            else {
                static int recorded_round = -1;
                if (recorded_round != round) {
                    recorded_round = round;
                    std::printf("CODEX_ORDER_DEFER R%d S%d G%zu\\\\n", round, slot, w.groups.size());
                }
            }
#endif
        }
#else
        if (!w.fields_ready() && quota > 0) w.prepare_field_order();
#endif"""),
    ))
    if diagnostic:
        apply(src / "main.cpp", (
            ("                play_draft();",
             """                static bool capture_announced = false;
                if (!capture_announced) { std::puts("CODEX_ORDER_CAPTURE"); capture_announced = true; }
                play_draft();"""),
        ))


def run(job):
    row = bench.one(job, log_limit=LIMIT)
    _, _, opp, mp, side, _ = job
    case = OUT / "games" / f"order-0-{opp}-{mp.stem}-{side}"
    with ZipFile(next(case.glob("*.repl26a"))) as z:
        log = z.read(f"team-{side.lower()}.stdout").replace(b"\0", b"")
    assert len(log) < LIMIT and b"CODEX_ORDER_CAPTURE" in log
    defer = [[int(x) for x in m] for m in re.findall(rb"CODEX_ORDER_DEFER R(\d+) S(\d+) G(\d+)", log)]
    built = [[int(x) for x in m] for m in re.findall(rb"CODEX_ORDER_BUILT R(\d+) S(\d+) G(\d+) F(\d+)", log)]
    return {**row, "defer": defer, "build": built}


def probe():
    project = OUT / "diagnostic"
    prepare(project / "src", True, True)
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm],
                       cwd=bench.ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    name = "x3inv"
    file, expected = bench.OPPS[name]
    assert bench.digest(bench.CACHE / file) == expected
    maps = sorted((bench.CACHE / "jd-sets/dev").glob("*.map26a"))
    md = bench.sha256("\n".join(f"{bench.digest(p)} {p.name}" for p in maps).encode()).hexdigest()
    assert len(maps) == 90 and md == "4268c4752502f768848d11ac1bd460a2cc6fc12e32756f240dbc9d71d9114b06"
    bench.OUT = OUT
    (OUT / "games").mkdir()
    jobs = [("order", 0, name, mp, side, wasm) for mp in maps for side in "AB"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(run, jobs))
    delayed = sorted({r["map"] for r in rows if r["defer"]})
    resumed = sum(sum(any(b[0] > a[0] and b[1] == a[1] and b[2] == a[2] for b in row["build"])
                      for a in row["defer"]) for row in rows)
    result = {"engine": bench.ENGINE, "map_digest": md, "wasm": bench.digest(wasm), "n": len(rows),
              "maps_with_deferral": delayed, "confirmed_resumptions": resumed,
              "deferrals": sum(len(r["defer"]) for r in rows),
              "max_order_fuel": max((b[3] for row in rows for b in row["build"]), default=None),
              "fuel": sum(r["fuel_outs"] for r in rows), "faults": sum(r["faults"] for r in rows), "rows": rows}
    with (HERE / "FIELD_ORDER_PROBE.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print({k: v for k, v in result.items() if k != "rows"}, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src", type=Path)
    p.add_argument("--off", action="store_true")
    a = p.parse_args()
    if a.src:
        prepare(a.src, not a.off, False)
    else:
        probe()


if __name__ == "__main__":
    main()
