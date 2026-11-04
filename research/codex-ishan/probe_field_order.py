"""Sample only the original deterministic group-order call on round one."""
from concurrent.futures import ThreadPoolExecutor
import json
import re
from shutil import copytree
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from large_roster_stress import HERE, bench, native_fuel, read
from pg_dash_followup import stress_cases

OUT = bench.CACHE / "v92-field-order-profile"
BASE = bench.CACHE / "v92-travel-scan-stress"
CASES = {("v92", "pool_604288", "A"), ("v92", "pool_604376", "B")}


def prepare(src):
    copytree(bench.ROOT / "bots/v92/src", src)
    apply(src / "bot.cpp", (
        ("void Bot::build_fields() {", """static unsigned codex_field_round;
static unsigned long long codex_field_before, codex_field_after;

void Bot::build_fields() {"""),
        ("        if (!w.fields_ready() && quota > 0) w.prepare_field_order();",
         """        if (!w.fields_ready() && quota > 0) {
            const bool sample = round == 1 && w.field_order.empty();
            if (sample) codex_field_before = bc::fuel_remaining();
            w.prepare_field_order();
            if (sample) {
                codex_field_after = bc::fuel_remaining();
                codex_field_round = bc::round_number();
            }
        }"""),
        ("void Bot::play_turn() {", """void Bot::play_turn() {
    if (codex_field_round) {
        std::printf("CODEX_FIELD_ORDER S%d T%d R%u %llu %llu\\n", slot, static_cast<int>(type),
                    codex_field_round, codex_field_before, codex_field_after);
        codex_field_round = 0;
    }"""),
    ))


def play(job):
    row = bench.one(job, log_limit=1048576)
    key = f"0-{row['opponent']}-{row['map']}-{row['side']}"
    original = BASE / "games" / f"base-{key}"
    traced = OUT / "games" / f"profile-{key}"
    archive, = traced.glob("*.repl26a")
    with ZipFile(archive) as bundle:
        log = bundle.read(f"team-{row['side'].lower()}.stdout")
    samples = [list(map(int, t)) for t in re.findall(rb"CODEX_FIELD_ORDER S(\d+) T(\d+) R(\d+) (\d+) (\d+)", log)]
    b, c = (read(d / "native.json") for d in (original, traced))
    assert all(b["match"][k] == c["match"][k] for k in ("mapHash", "seed", "engineBuildHash"))
    old_events = [(event["owner"]["id"], entry["timestamp"]["round"]) for event in b["events"]
                  if event["kind"] == "fuelExhausted" and event["owner"]["team"] == "team" + row["side"]
                  for entry in event["entries"] if entry["timestamp"]["round"] == 1]
    new_events = [(e["owner"]["id"], e["timestamp"]["round"]) for e in native_fuel(row, OUT)
                  if e["timestamp"]["round"] == 1]
    return {"case": row, "same_draft": b["roster"]["draft"] == c["roster"]["draft"],
            "old_r1": old_events, "trace_r1": new_events, "samples": samples}


def main():
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    project = OUT / "diagnostic"
    prepare(project / "src")
    wasm = project / "bot.wasm"
    with (OUT / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    jobs = [("profile", 0, o, m, s, wasm) for o, m, s in stress_cases() if (o, m.stem, s) in CASES]
    assert len(jobs) == 2
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(play, jobs))
    result = {"engine": bench.ENGINE, "wasm": bench.digest(wasm), "rows": rows}
    with (HERE / "FIELD_ORDER_BOUNDARY.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
