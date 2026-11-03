"""Use native WASI SDK 33 tools with the published Windows release libraries."""
from hashlib import sha256
import argparse
from pathlib import Path
import shutil
import tarfile

ARCHIVE_SHA = "df14ca2a2127c2d6b6be07e6f5549b3af9c1b3c0112430c200a4749970c59f06"
ARCHIVE_ROOT = "wasi-sdk-33.0-x86_64-windows"
LIB_PATHS = ("share/wasi-sysroot", "lib/clang/22/lib")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("native_cache", type=Path)
    parser.add_argument("windows_archive", type=Path)
    parser.add_argument("new_cache", type=Path)
    args = parser.parse_args()
    native = args.native_cache.resolve()
    dest = args.new_cache.resolve()
    with args.windows_archive.open("rb") as f:
        digest = sha256()
        for chunk in iter(lambda: f.read(2**20), b""):
            digest.update(chunk)
    if digest.hexdigest() != ARCHIVE_SHA:
        parser.error("Unexpected WASI SDK archive digest.")
    sdk = native / "wasi-sdk-33"
    if not (sdk / "bin/clang++").is_file():
        parser.error("Build once with the native CLI to populate the WASI SDK cache.")
    dest.mkdir(parents=True, exist_ok=False)
    new_sdk = dest / sdk.name
    shutil.copytree(sdk, new_sdk, symlinks=True)
    for p in native.iterdir():
        if p.is_dir() and p.name.startswith(("cmake-", "ninja-")):
            (dest / p.name).symlink_to(p, target_is_directory=True)
    with tarfile.open(args.windows_archive, "r:gz") as archive:
        for relative in LIB_PATHS:
            shutil.rmtree(new_sdk / relative)
        for member in archive:
            root, _, tail = member.name.partition("/")
            if root != ARCHIVE_ROOT or not any(tail == p or tail.startswith(p + "/") for p in LIB_PATHS):
                continue
            member.name = tail
            archive.extract(member, new_sdk, filter="data")
    print(dest)


if __name__ == "__main__":
    main()
