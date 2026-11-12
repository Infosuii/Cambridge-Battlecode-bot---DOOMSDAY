"""Prepare the isolated EXP-018 implementation."""
from pathlib import Path
from shutil import copytree

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "artifacts/codex-p0"
CODE = r'''#if CODEX_BUSH_SPANS
        struct Span { int left, right, y; };
        static std::vector<Span> pending;
        pending.clear();
        auto unlabelled = [&](int x, int y) {
            const vec2 tile{x, y};
            return bit(bushes, tile) && !bit(bush_labeled, tile);
        };
        auto claim = [&](int x, int y) {
            int left = x, right = x;
            while (left > 0 && unlabelled(left - 1, y)) --left;
            while (right + 1 < width && unlabelled(right + 1, y)) ++right;
            for (int i = left; i <= right; ++i) {
                set_bit(bush_labeled, {i, y});
                bush_label[static_cast<std::size_t>(y * width + i)] = id;
            }
#if A2_TEL
            a2_size += right - left + 1;
#endif
            pending.push_back({left, right, y});
            return right;
        };
        claim(p.x, p.y);
        while (!pending.empty()) {
            const Span run = pending.back();
            pending.pop_back();
            const int left = std::max(0, run.left - 1);
            const int right = std::min(width - 1, run.right + 1);
            for (int y : {run.y - 1, run.y + 1}) {
                if (y < 0 || y >= height) continue;
                for (int x = left; x <= right; ++x)
                    if (unlabelled(x, y)) x = claim(x, y);
            }
        }
#else
'''

def prepare(src, enabled):
    copytree(ROOT/"bots/v92/src", src)
    header = src/"common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    flag = [b"#ifndef CODEX_BUSH_SPANS", f"#define CODEX_BUSH_SPANS {enabled}".encode(), b"#endif", b""]
    header.write_bytes(nl.join(flag)+data)
    path=src/"world.cpp"
    data=path.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start=data.index(b"int World::bush_cluster(vec2 p) {")
    end=data.index(b"void World::cluster_board(", start)
    body=data[start:end]
    head=b"#if A2_BUSH_FAST"
    tail=b"    }"+nl+b"    return bush_label"
    assert body.count(head)==body.count(tail)==1
    body=body.replace(head,CODE.encode().replace(b"\n",nl)+head,1)
    body=body.replace(tail,b"#endif"+nl+tail,1)
    path.write_bytes(data[:start]+body+data[end:])

if __name__=="__main__":
    prepare(ROOT/"bots/codex-bush-spans/src",1)
