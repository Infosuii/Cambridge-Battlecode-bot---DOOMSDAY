"""Generate the opening-window source with a minimum predicted gem yield."""
import argparse
from pathlib import Path

from build_opening_window import patch, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src", type=Path)
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    prepare(args.src, not args.off)
    bot = args.src / "bot.cpp"
    data = bot.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    start = data.index(b"template<bool opening>\r\n" if nl == b"\r\n" else b"template<bool opening>\n")
    end = data.index(b"// Farming planner", start)
    body = data[start:end]
    edits = (
        ("    float window[8];", "    float window[8];\n    int window_gems[8];"),
        ("            has_second[i] = false;", """            window_gems[i] = window[i] > 0.0f ? w.groups[c.gi].gems : 0;
            has_second[i] = false;"""),
        ("                        window[i] = reward;", """                        window[i] = reward;
                        window_gems[i] = w.groups[c.gi].gems + w.groups[g2].gems;"""),
        ("            window[best_i] > 0.0f && window[window_best] >= 1.25f * window[best_i])",
         """            window[best_i] > 0.0f && window[window_best] >= 1.25f * window[best_i] &&
            window_gems[window_best] >= window_gems[best_i])"""),
    )
    for old, new in edits:
        body = patch(body, old, new, nl)
    bot.write_bytes(data[:start] + body + data[end:])


if __name__ == "__main__":
    main()
