"""Preserve and rebuild the exact source downloaded from the active submissions."""
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, SDK_ROOT

HERE = Path(__file__).resolve().parent
ARCHIVES = {
    108: Path("C:/Users/ishan/Downloads/bot (10).zip"),
    109: Path("C:/Users/ishan/Downloads/bot__1_.zip"),
}
EXPECTED = "c013c216393de628334c1d38d4c24d6abdd1b8bf159d8ffb262711040febd5e8"


def extract(archive, project):
    project.mkdir()
    with ZipFile(archive) as bundle:
        assert len(bundle.infolist()) < 100 and sum(i.file_size for i in bundle.infolist()) < 5242880
        for entry in bundle.infolist():
            name = PurePosixPath(entry.filename)
            assert not name.is_absolute() and ".." not in name.parts and all(":" not in p and "\\" not in p for p in name.parts)
            target = project.joinpath(*name.parts)
            assert target.resolve().is_relative_to(project.resolve())
            if not entry.is_dir():
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as out:
                    out.write(bundle.read(entry))


def main():
    assert bench.digest(CLI) == CLI_HASH
    cache = bench.CACHE / "exact-live-source-20261105"
    cache.mkdir()
    for version, archive in ARCHIVES.items():
        assert bench.digest(archive) == EXPECTED
        shutil.copyfile(archive, cache / f"v{version}-source.zip")
    projects = [SDK_ROOT / "bots" / name for name in ("live109", "live109-rebuild")]
    builds = []
    for project in projects:
        extract(ARCHIVES[109], project)
        with (project / "build.log").open("wb") as log:
            subprocess.run([CLI, "build", project, "--release", "--output", project / "bot.wasm"],
                           cwd=SDK_ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        builds.append(bench.digest(project / "bot.wasm"))
        print(project.name, builds[-1], flush=True)
    assert builds[0] == builds[1]
    source = projects[0] / "src"
    files = {p.relative_to(source).as_posix(): bench.digest(p) for p in sorted(source.rglob("*")) if p.is_file()}
    result = {"archive_sha256": EXPECTED, "archive_versions": [108, 109], "identical_archives": True,
              "source_file_hashes": files, "wasm_sha256": builds[0], "rebuild_sha256": builds[1],
              "header_sha256": files["nn_weights.h"], "sdk_header_sha256": bench.digest(SDK_ROOT / "sdk/cpp/cambc.h"),
              "cli_sha256": CLI_HASH, "active_observed": 109, "selected_observed": 109, "pinned_observed": False,
              "source_url": "https://2026a.battlecode.co.uk/api/v1/submissions/8dcc60cb-3d34-480b-ba3c-043d12437a40/archive"}
    with (HERE / "LIVE109_SOURCE_VERIFIED.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k: v for k, v in result.items() if k != "source_file_hashes"}, flush=True)


if __name__ == "__main__":
    main()
