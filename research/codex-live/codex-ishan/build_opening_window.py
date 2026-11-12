"""Generate the exact EXP-030 source, including its switches-off build."""
import argparse
from pathlib import Path
from shutil import copytree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def write(file, data):
    file.write_bytes(data)


def patch(data, before, after, nl):
    before = before.encode().replace(b"\n", nl)
    after = after.encode().replace(b"\n", nl)
    assert data.count(before) == 1, before
    return data.replace(before, after, 1)


def prepare(src, enabled):
    copytree(ROOT / "bots/v92/src", src)
    common = src / "common.h"
    data = common.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    write(common, f"#define CODEX_OPENING_WINDOW {int(enabled)}".encode() + nl + data)
    header = src / "bot.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    declaration = "    int route_search(const RouteCand* top, int n_top);"
    write(header, patch(data, declaration, declaration + """
#if CODEX_OPENING_WINDOW
    template<bool opening>
    int route_search_impl(const RouteCand* top, int n_top);
#endif""", nl))
    bot = src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start = data.index(b"int Bot::route_search(")
    end = data.index(b"// Farming planner", start)
    body = data[start:end]
    edits = (
        ("int Bot::route_search(const RouteCand* top, int n_top) {", """#if CODEX_OPENING_WINDOW
int Bot::route_search(const RouteCand* top, int n_top) {
    if (round <= 150) return route_search_impl<true>(top, n_top);
    return route_search_impl<false>(top, n_top);
}

template<bool opening>
int Bot::route_search_impl(const RouteCand* top, int n_top) {
#else
int Bot::route_search(const RouteCand* top, int n_top) {
#endif"""),
        ("    int best_i = -1;", """#if CODEX_OPENING_WINDOW
    float window[8];
    bool has_second[8];
    int window_best = -1;
#endif
    int best_i = -1;"""),
        ("        const float sticky =", """#if CODEX_OPENING_WINDOW
        if constexpr (opening) {
            window[i] = c.need == 1 && c.finish <= 49 && w.has_field(c.gi) ? c.value : 0.0f;
            has_second[i] = false;
        }
#endif
        const float sticky ="""),
        ("\n                if (rate > route) route = rate;", """
#if CODEX_OPENING_WINDOW
                if constexpr (opening) {
                    const float reward = c.value + fv[g2];
                    if (window[i] > 0.0f && done2 <= 49 && reward > window[i]) {
                        window[i] = reward;
                        has_second[i] = true;
                    }
                }
#endif
                if (rate > route) route = rate;"""),
        ("        if (route > best_rate)", """#if CODEX_OPENING_WINDOW
        if constexpr (opening) {
            if (window[i] > 0.0f && (window_best < 0 || window[i] > window[window_best]))
                window_best = i;
        }
#endif
        if (route > best_rate)"""),
        ("    return best_i;", """#if CODEX_OPENING_WINDOW
    if constexpr (opening) {
        if (best_i >= 0 && window_best >= 0 && window_best != best_i && has_second[window_best] &&
            window[best_i] > 0.0f && window[window_best] >= 1.25f * window[best_i])
            return window_best;
    }
#endif
    return best_i;"""),
    )
    for before, after in edits:
        body = patch(body, before, after, nl)
    write(bot, data[:start] + body + data[end:])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("src", type=Path)
    p.add_argument("--off", action="store_true")
    args = p.parse_args()
    prepare(args.src, not args.off)


if __name__ == "__main__":
    main()
