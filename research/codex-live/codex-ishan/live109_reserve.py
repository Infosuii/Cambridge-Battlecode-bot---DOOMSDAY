"""Reserve the exact existing camp-feature order vector without changing its contents."""
from shutil import copytree

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import HERE, SDK_ROOT, read


def prepare(target, enabled):
    source = SDK_ROOT / "bots/live109/src"
    identity = read(HERE / "LIVE109_SOURCE_VERIFIED.json")
    assert all(bench.digest(source / name) == value for name, value in identity["source_file_hashes"].items())
    copytree(source, target)
    header = target / "common.h"
    header.write_bytes(f"#define CODEX_LIVE_GC_RESERVE {int(enabled)}\n".encode() + header.read_bytes())
    apply(target / "nnrec.cpp", (("""    static std::vector<GC> gc;
    if (gc.empty())
        for (std::size_t gi = 0; gi < w.groups.size(); ++gi)
            if (gst[gi].n) gc.push_back({static_cast<int>(gi), gst[gi].c, 0, 0, 0});""", """    static std::vector<GC> gc;
#if CODEX_LIVE_GC_RESERVE
    if (gc.empty()) {
        gc.reserve(w.groups.size());
        for (std::size_t gi = 0; gi < w.groups.size(); ++gi)
            if (gst[gi].n) gc.push_back({static_cast<int>(gi), gst[gi].c, 0, 0, 0});
    }
#else
    if (gc.empty())
        for (std::size_t gi = 0; gi < w.groups.size(); ++gi)
            if (gst[gi].n) gc.push_back({static_cast<int>(gi), gst[gi].c, 0, 0, 0});
#endif"""),))
