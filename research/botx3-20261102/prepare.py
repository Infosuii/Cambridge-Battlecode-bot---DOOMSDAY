"""Prepare only the isolated botx3 copy; preserve production x1 unchanged."""
from pathlib import Path
import hashlib, json, zipfile
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SRC = ROOT/'bots/botx3/src'
def change(name, old, new):
    p=SRC/name; text=p.read_text(encoding='utf-8')
    assert text.count(old)==1, (name, old[:80])
    p.write_text(text.replace(old,new), encoding='utf-8', newline='\n')
original=ROOT/'bots/x1/src'
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in original.iterdir() if p.is_file()}
(OUT/'original-x1-source.json').write_text(json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(OUT/'original-x1-source.zip','x',zipfile.ZIP_DEFLATED) as z:
    for p in original.iterdir():
        if p.is_file(): z.write(p,'src/'+p.name)
with (SRC/'x1_config.h').open('a') as f:
    f.write('''
#ifndef X3_PLAN_END
#define X3_PLAN_END 0
#endif
#ifndef X3_BANKCYCLE
#define X3_BANKCYCLE 0
#endif
#ifndef X3_COVER_SAFE
#define X3_COVER_SAFE 0
#endif
#ifndef X3_TRACE
#define X3_TRACE 0
#endif
''')
change('bot.cpp','#include "neural_policy.h"','#include "neural_policy.h"\n#include "economic_cycle.h"')
change('bot.cpp','const int plan = pr >= 0 && round >= pr ? plan_id : 0;', '''#if X3_PLAN_END
        static volatile int plan_end = X3_PLAN_END;
        const int plan = economic_cycle::plan_active(round, pr, plan_end) ? plan_id : 0;
#else
        const int plan = pr >= 0 && round >= pr ? plan_id : 0;
#endif
#if X3_TRACE
        static int previous_plan = -1;
        if (previous_plan != plan) {
            std::printf("X3_PLAN R%d slot%d plan%d\\n", round, slot, plan);
            previous_plan = plan;
        }
#endif''')
# Plan 6 and 8 change a persistent hunt knob. Expiry must undo that too.
change('bot.cpp','if (hunt) tune::kHuntRange = std::max(0, base_hunt + hunt);', '''#if X3_PLAN_END
        tune::kHuntRange = std::max(0, base_hunt + hunt);
#else
        if (hunt) tune::kHuntRange = std::max(0, base_hunt + hunt);
#endif''')
change('bot.cpp','float score = value / cost;', '''float cycle_cost = cost;
#if X3_BANKCYCLE
        if (w.altar_ready && !w.no_bank && g.gems > 0) {
            int bank_distance = kUnreach;
            for (int ci : g.camps)
                bank_distance = std::min(bank_distance, static_cast<int>(fdist(w.altar_field, w.camps[ci].pos)));
            if (bank_distance != kUnreach)
                cycle_cost = economic_cycle::delivery_cost(cost, static_cast<float>(g.gems),
                    gold_weight() * static_cast<float>(g.gold), bank_distance);
#if X3_TRACE
            if (round % 100 == 0 && cycle_cost > cost)
                std::printf("X3_CYCLE R%d slot%d G%zu collect%.2f cycle%.2f bank%d\\n", round, slot, gi, cost, cycle_cost, bank_distance);
#endif
        }
#endif
        float score = value / cycle_cost;''')
# Do not expose provisional component IDs. Cover also checks live ward tiles,
# because a component may complete after the per-turn ward cache was made.
change('world.cpp','return bush_label[static_cast<std::size_t>(p.y * width + p.x)];', '''#if X3_COVER_SAFE && X1_BUSHPRE
    if (pre_id >= 0 && bush_label[static_cast<std::size_t>(p.y * width + p.x)] == pre_id) return -1;
#endif
    return bush_label[static_cast<std::size_t>(p.y * width + p.x)];''')
change('bot.cpp','if (c < 0 || w.warded(c)) return false;', '''if (c < 0 || w.warded(c)) return false;
#if X3_COVER_SAFE
    for (vec2 p : bc::vision::ward_tiles(team::enemy).positions()) {
        const int ward_cluster = w.bush_cluster(p);
        if (ward_cluster < 0 || ward_cluster == c) return false;
    }
#endif''')
print('Prepared isolated botx3; original x1 source frozen.')
