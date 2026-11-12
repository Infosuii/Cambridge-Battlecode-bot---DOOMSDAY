"""Create isolated EXP-007 source and reproducibility builds; never overwrite a snapshot."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'artifacts/codex-p0'
candidate = ROOT / 'bots/codex-bruiser'
if not candidate.exists():
    shutil.copytree(ROOT / 'bots/v92/src', candidate / 'src')

def replace(path, old, new):
    text = path.read_bytes()
    if b'\r\n' in text:
        old = old.replace('\n', '\r\n')
        new = new.replace('\n', '\r\n')
    if new.encode() in text:
        return
    assert text.count(old.encode()) == 1, old
    path.write_bytes(text.replace(old.encode(), new.encode(), 1))

header = candidate / 'src/common.h'
if b'#ifndef CODEX_BRUISER' not in header.read_bytes():
    header.write_bytes(b'#ifndef CODEX_BRUISER\n#define CODEX_BRUISER 1\n#endif\n' + header.read_bytes())
replace(candidate / 'src/bot.h', '    int last_enemy_dist = 99;', '''    int last_enemy_dist = 99;
#if CODEX_BRUISER
    bool codex_early_contact = false;
    bool codex_bruiser_selected = false;
#endif''')
source = candidate / 'src/bot.cpp'
replace(source, '    if (NOVA_ALTAR_INFER && prev_enemy_score >= 0 && enemy_score > prev_enemy_score) {', '''#if CODEX_BRUISER
    if (round <= 300 && last_enemy_dist <= 8) codex_early_contact = true;
#endif
    if (NOVA_ALTAR_INFER && prev_enemy_score >= 0 && enemy_score > prev_enemy_score) {''')
replace(source, '''#if A2_LAB
    const auto plan = build_for(type);
#else
    static const auto plan = build_for(type);
#endif''', '''#if CODEX_BRUISER
    auto plan = build_for(type);
    using it = bc::item_type;
    const bool monster = counts[it::monster_emblem_of_strength] > 0 ||
        counts[it::monster_emblem_of_focus] > 0 || counts[it::monster_emblem_of_health] > 0;
    if (codex_bruiser_selected || (range > 1 && codex_early_contact && monster && gold >= 30)) {
        for (auto& step : plan) {
            if (step.item != it::capture_shard_of_strength && step.item != it::capture_shard_of_focus &&
                step.item != it::capture_shard_of_health) continue;
            bool started = counts[step.item] > 0;
            if (const auto emblem = step.item.result()) started |= counts[*emblem] > 0;
            if (codex_bruiser_selected || !started) {
                codex_bruiser_selected = true;
                step = {it::bruiser_shard_of_health, 5};
            }
            break;
        }
    }
#elif A2_LAB
    const auto plan = build_for(type);
#else
    static const auto plan = build_for(type);
#endif''')
for name in ('bruiser-rebuild', 'bruiser-off'):
    dst = CACHE / name / 'src'
    shutil.copytree(candidate / 'src', dst)
    if name.endswith('-off'):
        replace(dst / 'common.h', '#define CODEX_BRUISER 1', '#define CODEX_BRUISER 0')
print('Prepared candidate, independent rebuild and switches-off control.')
