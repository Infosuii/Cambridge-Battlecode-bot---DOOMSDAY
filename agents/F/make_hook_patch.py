"""Generate lead-reviewed integration patch without modifying original gameplay files."""
from pathlib import Path
import difflib

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "bot/src/bot.cpp"
original = path.read_text(encoding="utf-8")
updated = original


def replace_once(before, after):
    global updated
    if updated.count(before) != 1:
        raise RuntimeError(f"expected exactly one hook anchor: {before[:100]!r}")
    updated = updated.replace(before, after, 1)


replace_once('#include "nn_budget.h"\n', '#include "nn_budget.h"\n#include "nn_economy.h"\n')
# The Wave1 capture pre-pass duplicates build_for (which allocates), SDK shop checks and inventory queries.
# Candidate0 now denotes the opaque unchanged executor, so remove the entire duplicate pre-pass rather than
# moving it inside a gate. The original executor starts at this exact try/lock-buy anchor and remains untouched.
shop_start = updated.index('void Bot::shop() {')
preview_start = updated.index('    if constexpr (nnt::kShop) {', shop_start)
executor_start = updated.index('    try {\n        if (tune::kAltarLocks', preview_start)
replace_once(updated[preview_start:executor_start],
             '    if constexpr (nncfg::mode(nncfg::H::shop) != nncfg::Mode::off) {\n'
             '        if (nne::shop(*this)) return;\n'
             '    }\n')
replace_once('    const bool go = force_tribute || wins || late || end_bank || rhythm || edge || gems >= tune::kTributeCarry ||',
             '    bool go = force_tribute || wins || late || end_bank || rhythm || edge || gems >= tune::kTributeCarry ||')
anchor = '    if constexpr (nnt::kBank) nn_teacher_access::cap_bank(*this, go, dist, wins, late, end_bank, rhythm, edge, threatened, use_safe);\n'
replace_once(anchor, anchor +
             '    if constexpr (nncfg::mode(nncfg::H::bank) != nncfg::Mode::off) {\n'
             '        const nne::BankTerms terms{go, use_safe, force_tribute, wins, late, end_bank, rhythm, edge, threatened, dist, -1};\n'
             '        const auto choice = nne::bank(*this, terms);\n'
             '        go = choice.go; use_safe = choice.safe; dist = choice.dist;\n'
             '    }\n')
patch = ''.join(difflib.unified_diff(original.splitlines(keepends=True), updated.splitlines(keepends=True),
                                     fromfile="a/bot/src/bot.cpp", tofile="b/bot/src/bot.cpp"))
(ROOT / "agents/F/HOOKS.diff").write_text(patch, encoding="utf-8", newline="\n")
print("Wrote agents/F/HOOKS.diff; original gameplay files unchanged")
