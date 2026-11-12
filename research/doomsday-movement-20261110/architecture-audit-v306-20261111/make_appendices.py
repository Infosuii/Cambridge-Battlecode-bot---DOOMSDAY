"""Read-only source inventory. Writes documentation beside this script, never bot files."""
from pathlib import Path
import json
import re

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
SRC = ROOT / "arena/bots/v306AltarPressureReach/src"
data = json.loads((OUT / "inventory.json").read_text(encoding="utf-8"))

def link(name, line=None):
    suffix = f":{line}" if line else ""
    return f"[{name}{suffix}](<{(SRC / name).as_posix()}{suffix}>)"

def cell(s):
    return str(s).replace("|", "&#124;").replace("\n", " ").replace("`", "&#96;")

lines = [
    "# v306 complete source macro inventory",
    "",
    "Generated from the release-target compiler preprocessing of all 13 C++ translation units, and the 44 source files. No bot source was edited.",
    "",
    f"Source SHA-256: `{data['source_sha256']}`. Release Wasm SHA-256: `{data['release_wasm_sha256']}`.",
    "",
    "These are named source macros, not a count of independent features. They include feature switches, numeric tuning values, bit masks, weight lists and helper macros. A value of 1 does not prove that a feature executes; earlier returns, runtime settings and other gates still apply. Undefined means absent from that translation unit's final macro environment, not necessarily absent from every compiled code path: local macros can be defined and later undefined.",
    "",
    "The bot column is the main decision file. Exceptions list every distinct value in the other translation units. Values are literal preprocessor replacements; aliases and C++ expressions are not numerically evaluated here. Refer to BOT-ARCHITECTURE.md for execution status and interactions.",
    "",
    "| Macro | Main bot.cpp value | Other translation-unit differences | Source declaration(s) |",
    "|---|---|---|---|",
]
bot = data["effective_by_translation_unit"]["bot.cpp"]
for name, declarations in sorted(data["definitions"].items()):
    base = bot.get(name, "undefined")
    grouped = {}
    for unit, macros in data["effective_by_translation_unit"].items():
        value = macros.get(name, "undefined")
        if value != base:
            grouped.setdefault(value, []).append(unit)
    differences = "; ".join(f"{', '.join(units)}: {cell(value)}" for value, units in grouped.items()) or "same"
    refs = ", ".join(link(x["file"], x["line"]) for x in declarations)
    lines.append(f"| `{name}` | `{cell(base)}` | {differences} | {refs} |")
lines += ["", f"Total: {len(data['definitions'])} distinct source-defined macro names.", ""]
(OUT / "CONFIGURATION-APPENDIX.md").write_text("\n".join(lines), encoding="utf-8")

index = ["# v306 source method index", "", "Definitions in the source, including disabled branches. Duplicate method names can be alternative implementations behind compile switches. Presence here does not establish runtime reachability.", "", "| Method | Source |", "|---|---|"]
for p in sorted(SRC.iterdir()):
    if p.suffix not in (".h", ".cpp"):
        continue
    for number, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith((" ", "\t", "//", "#")):
            continue
        match = re.search(r"\b((?:Bot|World)::[A-Za-z_]\w*)\s*\(", line)
        if match:
            index.append(f"| `{match.group(1)}` | {link(p.name, number)} |")
index.append("")
(OUT / "SOURCE-METHOD-INDEX.md").write_text("\n".join(index), encoding="utf-8")

values = [x.strip() for x in bot["A2_KNOBS"].split(",")]
knobs = ["# v306 runtime knob reference", "", "The first 96 entries are the baked A2_KNOBS values; later entries are zero-initialized. These values can be replaced or adjusted by recognised-map tables, hybrid presets and fitted map corrections. They are not the final live tuning values on every map.", "", "References below are literal source lines, including disabled experiments. Within the main lab tuning block, `k` aliases `lab::knobs`. Elsewhere only explicitly named lab/RT references are collected. The complete compiler snapshots remain in this directory.", "", "| Index | Baked value | Source use(s) |", "|---|---|---|"]
uses = {}
for p in sorted(SRC.iterdir()):
    if p.suffix not in (".h", ".cpp"):
        continue
    for number, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if len(line) > 1200 or line.lstrip().startswith("#define A2_KNOBS"):
            continue
        found = re.findall(r"(?:lab::knobs\[|LABK\(|RT[GX]\(|RTV\()\s*(\d+)", line)
        if p.name == "bot.cpp" and 8300 <= number <= 8355:
            found += re.findall(r"\bk\[\s*(\d+)\s*\]", line)
        for value in set(found):
            uses.setdefault(int(value), []).append((p.name, number, line.strip()))
for i in range(max(120, len(values))):
    refs = "<br>".join(f"{link(n, at)}: `{cell(line)}`" for n, at, line in uses.get(i, []))
    if not refs:
        refs = "No literal-index use found by this index; may be accessed through a table or loop."
    knobs.append(f"| {i} | {cell(values[i] if i < len(values) else '0')} | {refs} |")
knobs.append("")
(OUT / "RUNTIME-KNOBS.md").write_text("\n".join(knobs), encoding="utf-8")
print(json.dumps({"macros": len(data["definitions"]), "source_files": len(list(SRC.iterdir())), "knob_values": len(values), "output": str(OUT)}))
