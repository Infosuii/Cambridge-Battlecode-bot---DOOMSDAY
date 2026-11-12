"""Verify the downloaded official source for the newly active submission."""
from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, HERE, SDK_ROOT
from freeze_engine3_discovery import write


def main():
    archive = Path("C:/Users/ishan/Downloads/bot (11).zip")
    expected = "72e9a198135d9b42361a223be505e379b1cf286e1223ee3daf1fbb90a34f8463"
    assert bench.digest(archive) == expected and bench.digest(CLI) == CLI_HASH
    output = bench.CACHE / "exact-live111-source-20261105"
    output.mkdir()
    with (output / "v111-source.zip").open("xb") as out:
        out.write(archive.read_bytes())
    listing = json.loads(subprocess.run([CLI, "submissions", "list", "--json"], capture_output=True, check=True).stdout)
    write(output / "submissions.json", listing)
    item = next(s for s in listing["submissions"] if s["version"] == 111)
    assert item["id"] == "d8f4fa54-ad2b-4e6e-aee4-cb2f248795b5"
    files = {}
    with ZipFile(archive) as z:
        for entry in z.infolist():
            if entry.is_dir(): continue
            name = PurePosixPath(entry.filename)
            assert not name.is_absolute() and ".." not in name.parts and name.parts[0] == "src"
            relative = PurePosixPath(*name.parts[1:]).as_posix()
            assert relative and relative not in files and (entry.external_attr >> 16) & 0o170000 != 0o120000
            files[relative] = z.read(entry)
    assert len(files) == 40
    builds = []
    for project_name in ("live111", "live111-rebuild"):
        project = SDK_ROOT / "bots" / project_name
        source = project / "src"
        source.mkdir(parents=True)
        for name, data in files.items():
            target = source / name
            target.resolve().relative_to(source.resolve())
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as out: out.write(data)
        with (project / "build.log").open("wb") as log:
            subprocess.run([CLI, "build", project, "--release", "--output", project / "bot.wasm"], cwd=SDK_ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        builds.append(bench.digest(project / "bot.wasm"))
        print(project_name, builds[-1], flush=True)
    assert builds[0] == builds[1]
    result = {"verified_utc": datetime.now(timezone.utc).isoformat(), "platform_version": 111, "submission": item,
              "active_at_read": listing["active"]["version"], "selected_at_read": listing["selected"]["version"], "pinned": listing["pinned"],
              "archive_url": "https://2026a.battlecode.co.uk/api/v1/submissions/d8f4fa54-ad2b-4e6e-aee4-cb2f248795b5/archive",
              "archive_sha256": expected, "source_files": len(files), "source_file_hashes": {name: bench.digest(SDK_ROOT / "bots/live111/src" / name) for name in files},
              "cli_sha256": CLI_HASH, "wasm_sha256": builds[0], "rebuild_sha256": builds[1],
              "limits": "Official uploaded source and duplicate local SDK5 builds; server compiled WASM hash not exposed."}
    write(HERE / "LIVE111_SOURCE_VERIFIED.json", result)
    print({k: v for k, v in result.items() if k not in ("source_file_hashes", "submission")}, flush=True)


if __name__ == "__main__":
    main()
