"""Prepare the isolated EXP-014 build and two identity controls."""
from pathlib import Path
from shutil import copytree

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "bots/v92/src"
CACHE = ROOT / "artifacts/codex-p0"

for source, enabled in (
    (ROOT / "bots/codex-marcella-bruiser/src", 1),
    (CACHE / "marcella-bruiser-rebuild/src", 1),
    (CACHE / "marcella-bruiser-off/src", 0),
):
    copytree(BASE, source)
    header = source / "common.h"
    data = header.read_bytes()
    newline = b"\r\n" if b"\r\n" in data else b"\n"
    flags = [b"#ifndef CODEX_MARCELLA_BRUISER",
             f"#define CODEX_MARCELLA_BRUISER {enabled}".encode(), b"#endif", b""]
    header.write_bytes(newline.join(flags) + data)

    bot = source / "bot.cpp"
    data = bot.read_bytes()
    newline = b"\r\n" if b"\r\n" in data else b"\n"
    old = b"        plan = {{it::jungle_shard_of_strength,5}, {it::prospector_shard_of_focus,5},"
    assert data.count(old) == 1
    change = newline.join([
        b"#if CODEX_MARCELLA_BRUISER",
        b"        plan = {{it::jungle_shard_of_strength,5}, {it::bruiser_shard_of_focus,5},",
        b"#else",
        old,
        b"#endif",
    ])
    bot.write_bytes(data.replace(old, change, 1))
