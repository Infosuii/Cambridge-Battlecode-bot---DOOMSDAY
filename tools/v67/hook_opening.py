"""Install opening hooks while preserving the fork's CRLF source text."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def edit(name,old,new):
    p=ROOT/'bots/v67/src'/name
    s=p.read_bytes().decode()
    end='\r\n' if '\r\n' in s else '\n'
    old=old.replace('\n',end); new=new.replace('\n',end)
    if old not in s: raise RuntimeError('missing hook: '+name)
    p.write_bytes(s.replace(old,new,1).encode())
edit('draft.cpp','#if V67_META >= 0\n    if (v67meta::draft(size))', '#if V67_OPENING || V67_META >= 0\n    if (v67meta::draft(size))')
edit('bot.cpp','    using it = bc::item_type;\n#include "v67_meta_build.inc"','''    using it = bc::item_type;
#if V67_OPENING & 2
    if (const auto* opening = v67meta::opening()) {
        for (unsigned i = 0; i < opening->ni; ++i) {
            const auto& items = opening->items[i];
            if (items.hero != t) continue;
            std::vector<BuildStep> plan;
            for (unsigned j = 0; j < items.n; ++j) plan.push_back({items.items[j], items.totals[j]});
            const bool caster = t == bc::champion_type::heart_of_ruin || t == bc::champion_type::cassi ||
                t == bc::champion_type::stellar || t == bc::champion_type::prism || t == bc::champion_type::marcella;
            const it main = caster ? it::bruiser_shard_of_focus : it::bruiser_shard_of_strength;
            int main_count = 0, health_count = 0;
            for (auto step : plan) {
                if (step.item == main) main_count = std::max(main_count,step.total);
                if (step.item == it::bruiser_shard_of_health) health_count = std::max(health_count,step.total);
            }
            for (int n = 1; n <= 25; ++n) {
                plan.push_back({main,main_count+5*n});
                if (n%2 == 0) plan.push_back({it::bruiser_shard_of_health,health_count+5*(n/2)});
            }
            return plan;
        }
    }
#endif
#include "v67_meta_build.inc"''')
edit('bot.cpp','int Bot::score_groups(int participants_hint, int& best_need, float& best_score) {','''int Bot::score_groups(int participants_hint, int& best_need, float& best_score) {
#if V67_OPENING & 4
    if (const int gi = v67_opening_job(); gi >= 0) {
        best_need = 1; best_score = 1e9f; return gi;
    }
#endif''')
