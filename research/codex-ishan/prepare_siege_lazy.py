"""Prepare the isolated EXP-024 implementation."""
from pathlib import Path
from shutil import copytree

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT/"artifacts/codex-p0"

def prepare(src, enabled):
    copytree(ROOT/"bots/v92/src",src)
    common=src/"common.h"
    data=common.read_bytes()
    nl=b"\r\n" if b"\r\n" in data else b"\n"
    flags=[b"#ifndef CODEX_SIEGE_LAZY",f"#define CODEX_SIEGE_LAZY {enabled}".encode(),b"#endif",b""]
    common.write_bytes(nl.join(flags)+data)
    bot=src/"bot.cpp"
    data=bot.read_bytes()
    nl=b"\r\n" if b"\r\n" in data else b"\n"
    first=data.index(b"bool Bot::fight_camps(")
    last=data.index(b"bool Bot::farm()",first)
    region=data[first:last]
    pairs=[
        ("""                static std::vector<bc::bitboard> los;
                static std::vector<std::uint8_t> los_ready;""",
         """#if CODEX_SIEGE_LAZY
                static std::vector<std::optional<bc::bitboard>> los;
#else
                static std::vector<bc::bitboard> los;
                static std::vector<std::uint8_t> los_ready;
#endif"""),
        ("""                if (los.size() < w.camps.size()) { los.resize(w.camps.size()); los_ready.resize(w.camps.size(), 0); }""",
         """#if CODEX_SIEGE_LAZY
                if (los.size() < w.camps.size()) los.resize(w.camps.size());
#else
                if (los.size() < w.camps.size()) { los.resize(w.camps.size()); los_ready.resize(w.camps.size(), 0); }
#endif"""),
        ("""                    if (!los_ready[static_cast<std::size_t>(ci)]) {""",
         """#if CODEX_SIEGE_LAZY
                    auto& cached = los[static_cast<std::size_t>(ci)];
                    if (!cached) {
#else
                    if (!los_ready[static_cast<std::size_t>(ci)]) {
#endif"""),
        ("""                        los[static_cast<std::size_t>(ci)] = v;
                        los_ready[static_cast<std::size_t>(ci)] = 1;
                    }
                    any |= los[static_cast<std::size_t>(ci)];""",
         """#if CODEX_SIEGE_LAZY
                        cached.emplace(std::move(v));
#else
                        los[static_cast<std::size_t>(ci)] = v;
                        los_ready[static_cast<std::size_t>(ci)] = 1;
#endif
                    }
#if CODEX_SIEGE_LAZY
                    any |= *cached;
#else
                    any |= los[static_cast<std::size_t>(ci)];
#endif"""),
    ]
    for old,new in pairs:
        old,new=(s.encode().replace(b"\n",nl) for s in (old,new))
        assert region.count(old)==1,old
        region=region.replace(old,new,1)
    bot.write_bytes(data[:first]+region+data[last:])

if __name__=="__main__":
    prepare(ROOT/"bots/codex-siege-lazy/src",1)
