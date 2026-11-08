"""Read-only source audit and duplicate local builds of three existing submissions."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, HERE, SDK_ROOT

OUT = bench.CACHE / "uploaded-112-114-audit-20261108"
SOURCE = {
    111: ("bot (11).zip", "d8f4fa54-ad2b-4e6e-aee4-cb2f248795b5", 720806, "72e9a198135d9b42361a223be505e379b1cf286e1223ee3daf1fbb90a34f8463"),
    112: ("bot (13).zip", "a3b4bcb6-5c9b-44ee-b0ad-6351247d8867", 723302, "9397a56e4d19e998489578debaff58be3c90892514b97bda6d4e6be57cffe001"),
    113: ("v206.zip", "ff2f3acc-c4af-48fd-b2a2-85121a367e64", 726116, "93332ea2a4d972852bbfdf3341493897245381042984d6e845fe8fa4e1d407e5"),
    114: ("bot (12).zip", "2d96e758-d567-4642-b33c-1e963cba2924", 724570, "44afb7e990608178573514838c2243a4cdd977feacdc35d23da5e3fe0c181f2e"),
}


def write(path, doc):
    with path.open("x", encoding="utf8", newline="\n") as out:
        json.dump(doc, out, indent=2)
        out.write("\n")


def files(archive):
    result = {}
    with ZipFile(archive) as zipped:
        for info in zipped.infolist():
            if info.is_dir():
                continue
            name = PurePosixPath(info.filename)
            assert len(name.parts) >= 2 and name.parts[0] == "src"
            assert ".." not in name.parts and "\\" not in info.filename and ":" not in info.filename
            assert (info.external_attr >> 16) & 0o170000 != 0o120000
            relative = PurePosixPath(*name.parts[1:]).as_posix()
            assert relative.casefold() not in {key.casefold() for key in result}
            result[relative] = zipped.read(info)
    return result


def build(job):
    version, suffix, source = job
    project = SDK_ROOT / "bots" / f"codex-upload-audit-v{version}-{suffix}-20261108"
    project.mkdir()
    for name, data in source.items():
        path = project / "src" / name
        path.resolve().relative_to(project.resolve())
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as out:
            out.write(data)
    wasm = project / "bot.wasm"
    with (project / "build.log").open("xb") as log:
        subprocess.run([CLI, "build", project, "--release", "--output", wasm], cwd=SDK_ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    result = {"path": str(wasm), "sha256": bench.digest(wasm)}
    print(version, suffix, result["sha256"], flush=True)
    return version, suffix, result


def main():
    assert bench.digest(CLI) == CLI_HASH
    OUT.mkdir()
    versions = {}
    docs = {}
    downloads = Path("C:/Users/ishan/Downloads")
    for version, (filename, submission, size, digest) in SOURCE.items():
        archive = downloads / filename
        assert archive.stat().st_size == size and bench.digest(archive) == digest
        with (OUT / f"v{version}.zip").open("xb") as out:
            out.write(archive.read_bytes())
        versions[version] = files(archive)
        docs[version] = {"id": submission, "archive_bytes": size, "archive_sha256": digest,
                         "source_sha256": {k: sha256(v).hexdigest() for k, v in sorted(versions[version].items())}}
    diffs = {}
    for a, b in ((111, 112), (112, 113), (112, 114), (113, 114)):
        first, second = versions[a], versions[b]
        diffs[f"{a}->{b}"] = {"added": sorted(second.keys() - first.keys()),
                             "removed": sorted(first.keys() - second.keys()),
                             "changed": sorted(k for k in first.keys() & second.keys() if first[k] != second[k])}
    assert diffs["112->114"] == {"added": ["cl_newmap_table.h"], "removed": [], "changed": ["bot.cpp", "common.h"]}
    write(HERE / "UPLOADED_112_114_SOURCES.json",
          {"cli_sha256": CLI_HASH, "submissions": docs, "diffs": diffs,
           "scope": "Authenticated team source downloads, with submission ID from each rendered download link. Server WASM not exposed."})
    jobs = [(v, s, versions[v]) for v in (112, 113, 114) for s in ("release", "repeat")]
    builds = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for version, suffix, result in pool.map(build, jobs):
            builds.setdefault(version, {})[suffix] = result
    for variants in builds.values():
        assert variants["release"]["sha256"] == variants["repeat"]["sha256"]
    write(HERE / "UPLOADED_112_114_BUILDS.json",
          {"source_manifest_sha256": bench.digest(HERE / "UPLOADED_112_114_SOURCES.json"),
           "cli_sha256": CLI_HASH, "local_builds": builds, "all_duplicate_hashes_match": True})


if __name__ == "__main__":
    main()
