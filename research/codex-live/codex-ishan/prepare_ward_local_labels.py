"""Copy the frozen v92 source into the isolated EXP-017 build projects."""
from pathlib import Path
from shutil import copytree

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "artifacts/codex-p0"
BASE = ROOT / "bots/v92/src"

def prepare(src, enabled):
    copytree(BASE, src)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    flag = [b"#ifndef CODEX_WARD_LOCAL_LABELS", f"#define CODEX_WARD_LOCAL_LABELS {enabled}".encode(), b"#endif", b""]
    header.write_bytes(nl.join(flag) + data)
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start = data.index(b"bool Bot::ward_ahead() {")
    end = data.index(b"\nbool ", start)
    region = data[start:end]
    def replace(before, after):
        nonlocal region
        a = before.encode().replace(b"\n", nl)
        b = after.encode().replace(b"\n", nl)
        assert region.count(a) == 1, before
        region = region.replace(a, b, 1)
    replace("    int n_cov = 0;", """    int n_cov = 0;
#if CODEX_WARD_LOCAL_LABELS
    std::array<int, 25> local_labels;
    bool local_labels_ready = false;
#endif""")
    replace("""        if (!wt.is_empty())
            for (vec2 p : wt.positions()) {
                const int c = w.bush_cluster(p);
                if (c >= 0 && n_cov < 16) covered[n_cov++] = c;
            }""", """#if CODEX_WARD_LOCAL_LABELS
        if (!wt.is_empty()) {
            local_labels.fill(-1);
            for (int dy = -2; dy <= 2; ++dy)
                for (int dx = -2; dx <= 2; ++dx) {
                    const vec2 q{pos.x + dx, pos.y + dy};
                    if (!in_bounds(q, w.width, w.height) || bit(w.static_blocked, q)) continue;
                    local_labels[(dy + 2) * 5 + dx + 2] = w.bush_cluster(q);
                }
            local_labels_ready = true;
            for (vec2 p : wt.positions()) {
                if (!bit(w.bushes, p)) continue;
                // Every local candidate component has a label. An unlabelled
                // ward still occupies a slot in the original first-16 sample.
                covered[n_cov++] = bit(w.bush_labeled, p) ? w.bush_label[p.y * w.width + p.x] : -1;
                if (n_cov == static_cast<int>(covered.size())) break;
            }
        }
#else
        if (!wt.is_empty())
            for (vec2 p : wt.positions()) {
                const int c = w.bush_cluster(p);
                if (c >= 0 && n_cov < 16) covered[n_cov++] = c;
            }
#endif""")
    replace("            const int c = w.bush_cluster(q);", """#if CODEX_WARD_LOCAL_LABELS
            const int c = local_labels_ready ? local_labels[(dy + 2) * 5 + dx + 2] : w.bush_cluster(q);
#else
            const int c = w.bush_cluster(q);
#endif""")
    bot.write_bytes(data[:start] + region + data[end:])

if __name__ == "__main__":
    prepare(ROOT / "bots/codex-ward-local-labels/src", 1)
    prepare(CACHE / "ward-local-labels-rebuild/src", 1)
    prepare(CACHE / "ward-local-labels-off/src", 0)
