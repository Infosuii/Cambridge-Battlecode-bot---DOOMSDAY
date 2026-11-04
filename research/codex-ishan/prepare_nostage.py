"""Create EXP-011 and independent build controls from frozen v92."""
from pathlib import Path
from shutil import copytree

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "bots/v92/src"
CANDIDATE = ROOT / "bots/codex-nostage/src"
CACHE = ROOT / "artifacts/codex-p0"
SWITCH = "CODEX_NO_STAGE"

for source, enabled in (
    (CANDIDATE, 1),
    (CACHE / "nostage-rebuild/src", 1),
    (CACHE / "nostage-off/src", 0),
):
    copytree(BASE, source)
    config = source / "common.h"
    data = config.read_bytes()
    newline = b"\r\n" if b"\r\n" in data else b"\n"
    guard = [f"#ifndef {SWITCH}", f"#define {SWITCH} {enabled}", "#endif", ""]
    config.write_bytes(newline.join(line.encode() for line in guard) + data)

    bot = source / "bot.cpp"
    data = bot.read_bytes()
    newline = b"\r\n" if b"\r\n" in data else b"\n"
    old = b"    case GroupState::alive: return fight_camps(g, best_need);"
    assert data.count(old) == 1
    change = newline.join([
        f"#if {SWITCH}".encode(),
        b"    case GroupState::alive: return fight_camps(g, 1);",
        b"#else",
        old,
        b"#endif",
    ])
    bot.write_bytes(data.replace(old, change, 1))
