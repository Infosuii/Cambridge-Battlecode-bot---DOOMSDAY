"""Transfer the previously verified exact packing implementation to unchanged111."""
from shutil import copytree

import ablate_dev as bench
from engine3_pool import HERE, SDK_ROOT, read
from live111_exact_component import run
from v92_field_pack import apply_pack


def prepare(target, enabled):
    identity = read(HERE / "LIVE111_SOURCE_VERIFIED.json")
    source = SDK_ROOT / "bots/live111/src"
    assert all(bench.digest(source / n) == h for n,h in identity["source_file_hashes"].items())
    copytree(source,target)
    apply_pack(target,enabled)


if __name__ == "__main__": run("field-pack",prepare)
