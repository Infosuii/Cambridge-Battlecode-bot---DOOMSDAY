"""Prepare the fixed EXP-025 combination from the two frozen experiment snapshots."""
from pathlib import Path
from shutil import copytree

ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/"artifacts/codex-p0"
RAYS=ROOT/"bots/codex-siege-rays/src"
LAZY=ROOT/"bots/codex-siege-lazy/src"

def prepare(src,enabled):
    copytree(LAZY,src)
    (src/"codex_siege_rays.h").write_bytes((RAYS/"codex_siege_rays.h").read_bytes())
    common=src/"common.h"
    data=common.read_bytes()
    nl=b"\r\n" if b"\r\n" in data else b"\n"
    old=b"#define CODEX_SIEGE_LAZY 1"
    assert data.count(old)==1
    data=data.replace(old,f"#define CODEX_SIEGE_LAZY {enabled}".encode(),1)
    flags=[b"#ifndef CODEX_SIEGE_RAYS", f"#define CODEX_SIEGE_RAYS {enabled}".encode(), b"#endif", b""]
    common.write_bytes(nl.join(flags)+data)
    bot=src/"bot.cpp"
    data=bot.read_bytes()
    ray=(RAYS/"bot.cpp").read_bytes()
    nl=b"\r\n" if b"\r\n" in data else b"\n"
    ray=ray.replace(b"\r\n",b"\n").replace(b"\n",nl)
    inc=b'#include "bot.h"'
    assert data.count(inc)==1
    data=data.replace(inc,inc+nl+b'#if CODEX_SIEGE_RAYS'+nl+b'#include "codex_siege_rays.h"'+nl+b'#endif',1)
    start=b"                            const int n = cheb(c.pos, q);"
    end=b"                            if (clear) v.set(q, true);"
    a=ray.index(b"#if CODEX_SIEGE_RAYS",ray.index(b"bool Bot::fight_camps("))
    b=ray.index(nl+b"#endif",a)+len(nl+b"#endif")
    block=ray[a:b]
    lo=data.index(start)
    hi=data.index(end,lo)+len(end)
    assert block.split(nl+b"#else"+nl)[1] == data[lo:hi]+nl+b"#endif"
    bot.write_bytes(data[:lo]+block+data[hi:])

if __name__=="__main__":
    prepare(ROOT/"bots/codex-siege-combined/src",1)
    prepare(CACHE/"siege-combined-rebuild/src",1)
    prepare(CACHE/"siege-combined-off/src",0)
