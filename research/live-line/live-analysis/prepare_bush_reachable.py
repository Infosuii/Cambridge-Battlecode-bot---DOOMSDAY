"""Prepare the isolated EXP-019 implementation."""
from pathlib import Path
from shutil import copytree

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "artifacts/codex-p0"
CODE = r'''#if CODEX_BUSH_REACHABLE
        const auto tile_count = static_cast<std::uint64_t>(width) * height;
        if (tile_count <= std::numeric_limits<std::uint16_t>::max()) {
            if (!non_bush_walls) non_bush_walls.emplace(~bushes);
            const auto component = non_bush_walls->reachable_tiles(p, static_cast<std::uint16_t>(tile_count - 1));
            for (vec2 tile : component.positions()) {
                bush_label[static_cast<std::size_t>(tile.y * width + tile.x)] = id;
#if A2_TEL
                ++a2_size;
#endif
            }
            bush_labeled |= component;
        } else
#endif
'''

def prepare(src, enabled):
    copytree(ROOT/"bots/v92/src", src)
    header = src/"common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    flag = [b"#ifndef CODEX_BUSH_REACHABLE", f"#define CODEX_BUSH_REACHABLE {enabled}".encode(), b"#endif", b""]
    header.write_bytes(nl.join(flag)+data)
    path = src/"world.h"
    data = path.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    anchor=b"    bc::bitboard bushes;"
    assert data.count(anchor)==1
    addition=nl.join([b"",b"#if CODEX_BUSH_REACHABLE",b"    std::optional<bc::bitboard> non_bush_walls;",b"#endif"])
    path.write_bytes(data.replace(anchor,anchor+addition,1))
    path = src/"world.cpp"
    data = path.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start = data.index(b"int World::bush_cluster(vec2 p) {")
    end = data.index(b"void World::cluster_board(",start)
    body = data[start:end]
    head=b"#if A2_BUSH_FAST"
    assert body.count(head)==1
    body=body.replace(head,CODE.encode().replace(b"\n",nl)+head,1)
    path.write_bytes(data[:start]+body+data[end:])

if __name__ == "__main__":
    prepare(ROOT/"bots/codex-bush-reachable/src",1)
