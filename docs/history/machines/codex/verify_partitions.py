"""Verify JD map partition digests from the pinned source inputs; no matches run."""
from hashlib import sha256
from pathlib import Path, PurePosixPath
import json
import shutil
import subprocess
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "artifacts/codex-p0"
SETS = CACHE / "jd-sets"
REF = "12c1804bbd475d99bfb8a70643c954e91b84ebd3"
manifest = json.loads(subprocess.check_output(["git", "show", f"{REF}:research/jd-g5070-1104/RUN_MANIFEST.json"], cwd=ROOT))

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def files(path):
    return sorted(path.glob("*.map26a"))

with ZipFile(CACHE / "jd-poolfresh.zip") as z:
    entries = sorted(p for p in z.namelist() if p.endswith(".map26a"))[:120]
    assert len(entries) == 120
    for i, entry in enumerate(entries):
        (SETS / ("dev" if i < 60 else "select") / ("pf_" + PurePosixPath(entry).name)).write_bytes(z.read(entry))
conf = SETS / "conf"
conf.mkdir(exist_ok=True)
for src in sorted(files(SETS / "dev"), key=lambda p:(-p.stat().st_size, p.name))[:16]:
    shutil.copyfile(src, conf / src.name)
paths = {n:SETS / n for n in ("dev", "select", "conf", "fresh51104")}
paths["pool"] = ROOT / "maps/ladder-pool"
results = {}
digests = {}
for name, path in paths.items():
    rows = [(digest(p), p.name) for p in files(path)]
    actual = sha256("\n".join(f"{d} {p}" for d,p in rows).encode()).hexdigest()
    expected = manifest["map_sets"][name]
    digests[name] = {d for d,_ in rows}
    results[name] = {"actual": actual, "expected": expected["sha256"], "count":len(rows),
                     "verified": len(rows)==expected["count"] and actual==expected["sha256"]}
sealed = {line.split()[0] for line in (Path(__file__).resolve().parent/"FRESH_HOLDOUT.sha256").read_text().splitlines()}
assert len(sealed)==100
results["sealed_sha256_overlaps"] = {n:len(ds & sealed) for n,ds in digests.items()}
(Path(__file__).resolve().parent/"PARTITIONS.json").write_text(json.dumps(results,indent=2)+"\n", encoding="utf8", newline="\n")
print(json.dumps(results,indent=2))
