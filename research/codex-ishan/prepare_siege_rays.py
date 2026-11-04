"""Prepare the isolated EXP-023 release and reproducibility controls."""
from pathlib import Path
from shutil import copytree

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "artifacts/codex-p0"

def prepare(src, enabled):
    copytree(ROOT/"bots/v92/src", src)
    (src/"codex_siege_rays.h").write_bytes(Path(__file__).with_name("codex_siege_rays.h").read_bytes())
    common=src/"common.h"
    data=common.read_bytes()
    nl=b"\r\n" if b"\r\n" in data else b"\n"
    flags=[b"#ifndef CODEX_SIEGE_RAYS", f"#define CODEX_SIEGE_RAYS {enabled}".encode(), b"#endif", b""]
    common.write_bytes(nl.join(flags)+data)
    bot=src/"bot.cpp"
    data=bot.read_bytes()
    nl=b"\r\n" if b"\r\n" in data else b"\n"
    inc=b'#include "bot.h"'
    assert data.count(inc)==1
    data=data.replace(inc,inc+nl+b'#if CODEX_SIEGE_RAYS'+nl+b'#include "codex_siege_rays.h"'+nl+b'#endif',1)
    start=b"                            const int n = cheb(c.pos, q);"
    end=b"                            if (clear) v.set(q, true);"
    assert data.count(start)==data.count(end)==1
    a=data.index(start)
    b=data.index(end,a)+len(end)
    old=data[a:b]
    new=nl.join([
        b"#if CODEX_SIEGE_RAYS",
        b"                            const auto& ray = codex_siege::rays[(dy + 4) * 9 + dx + 4];",
        b"                            bool clear = true;",
        b"                            for (int k = 0; k < ray.count && clear; ++k) {",
        b"                                const auto offset = ray.offsets[k];",
        b"                                clear = !opaque_at(vec2{q.x + offset.x, q.y + offset.y});",
        b"                            }",
        b"                            if (clear) set_bit(v, q);",
        b"#else",
        old,
        b"#endif",
    ])
    bot.write_bytes(data[:a]+new+data[b:])

if __name__ == "__main__":
    prepare(ROOT/"bots/codex-siege-rays/src",1)
    prepare(CACHE/"siege-rays-rebuild/src",1)
    prepare(CACHE/"siege-rays-off/src",0)
