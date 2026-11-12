"""Prepare the isolated EXP-016 build and two identity controls."""
from pathlib import Path
from shutil import copytree

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "bots/v92/src"
CACHE = ROOT / "artifacts/codex-p0"

for source, enabled in (
    (ROOT / "bots/codex-ward-preflight/src", 1),
    (CACHE / "ward-preflight-rebuild/src", 1),
    (CACHE / "ward-preflight-off/src", 0),
):
    copytree(BASE, source)
    header = source / "common.h"
    data = header.read_bytes()
    newline = b"\r\n" if b"\r\n" in data else b"\n"
    flags = [b"#ifndef CODEX_WARD_PREFLIGHT", f"#define CODEX_WARD_PREFLIGHT {enabled}".encode(),
             b"#endif", b""]
    header.write_bytes(newline.join(flags) + data)

    bot = source / "bot.cpp"
    data = bot.read_bytes()
    newline = b"\r\n" if b"\r\n" in data else b"\n"
    start = data.index(b"bool Bot::ward_reveal() {")
    end = data.index(b"bool Bot::hidden_here()", start)
    fragment = data[start:end]
    anchor = b"    const int mine = w.bush_cluster(pos);"
    early = newline.join([
        b"#if CODEX_WARD_PREFLIGHT",
        b"    auto& me = bc::self();",
        b"    try {",
        b"        if (me.ward_cooldown() > 0) return false;",
        b"    } catch (const std::exception& e) {",
        b'        LOG("ward cooldown error %s\\n", e.what());',
        b"        return false;",
        b"    }",
        b"#endif",
        anchor,
    ])
    late = newline.join([
        b"    auto& me = bc::self();",
        b"    try {",
        b"        if (me.ward_cooldown() > 0) return false;",
    ])
    guarded = newline.join([
        b"#if !CODEX_WARD_PREFLIGHT",
        b"    auto& me = bc::self();",
        b"#endif",
        b"    try {",
        b"#if !CODEX_WARD_PREFLIGHT",
        b"        if (me.ward_cooldown() > 0) return false;",
        b"#endif",
    ])
    assert fragment.count(anchor) == fragment.count(late) == 1
    fragment = fragment.replace(late, guarded).replace(anchor, early)
    bot.write_bytes(data[:start] + fragment + data[end:])
