"""Merge v113 repairs with retained banking work and isolated mechanism flags."""
from pathlib import Path
import shutil,json,difflib,concurrent.futures
from project import ROOT,ARENA,save,digest,build,sha,check_stop

def replace(text,old,new):
    assert text.count(old)==1,('Non-unique patch anchor',old[:150],text.count(old))
    return text.replace(old,new)

def sources(mask):
    original={p.name:p.read_text(encoding='utf-8') for p in (ARENA/'bots/b113/src').iterdir() if p.is_file()}
    out=dict(original)
    out['integration.h']=f'''#pragma once
#include <cstdint>
// Same executable sections for all mechanism arms; only initialized data differs.
inline volatile std::uint32_t integration_flags[2] = {{{mask}, 1}};
inline bool integration_enabled(std::uint32_t bit) {{
    return integration_flags[1] == 1 && (integration_flags[0] & bit) != 0;
}}
'''
    h=out['bot.h']
    h=replace(h,'#include "channel_retry.h"','#include "channel_retry.h"\n#include "integration.h"')
    h=replace(h,'    bool start_recall();','    bool start_recall(bool banking_route = false);\n    bool banking_recall_intent = false;\n    bool integration_release_spawn();')
    out['bot.h']=h
    wh=out['world.h']
    wh=replace(wh,'    bc::bitboard camp_tiles_all;','    bc::bitboard camp_tiles_all;\n    int group_at_spawn(vec2 p) const;')
    out['world.h']=wh
    wc=out['world.cpp']
    wc=replace(wc,'void World::init() {','''int World::group_at_spawn(vec2 p) const {
    if (p.x < 0 || p.y < 0 || p.x >= width || p.y >= height) return -1;
    const int ci = find_camp(static_cast<std::uint32_t>(p.y * width + p.x) + 1);
    return ci >= 0 && static_cast<std::size_t>(ci) < camp_group.size() ? camp_group[ci] : -1;
}

void World::init() {''')
    out['world.cpp']=wc
    c=out['bot.cpp']
    c=replace(c,'bool Bot::start_recall() {\n    if (!retry_channel(ChannelRetry::recall)) return false;\n    bc::self().recall();',
        'bool Bot::start_recall(bool banking_route) {\n    if (!retry_channel(ChannelRetry::recall)) return false;\n    bc::self().recall();\n    banking_recall_intent = banking_route;')
    c=replace(c,'    // A recall started before a capture landed: if the bag now finishes the race, walk to an altar instead.\n    if (state.contains(bc::champion_state::recalling) && win_now() && hp >= max_hp * tune::kDangerHp) {',
        '    if (!state.contains(bc::champion_state::recalling)) banking_recall_intent = false;\n'
        '    // Preserve recalls deliberately selected as a shorter banking route.\n'
        '    if (state.contains(bc::champion_state::recalling) && win_now() && hp >= max_hp * tune::kDangerHp &&\n'
        '        !(integration_enabled(2) && banking_recall_intent)) {')
    c=replace(c,'bool Bot::tribute_if_needed() {\n    if (gems <= 0) return false;',
        'bool Bot::tribute_if_needed() {\n    if (gems <= 0) return false;\n    const bool terminal_bank = integration_enabled(2) && win_now();')
    c=replace(c,'        if (!in_range) return false;','        if (!in_range && !terminal_bank) return false;')
    c=replace(c,'        if (tribute_stuck >= 20) {','        if (tribute_stuck >= 20 && !terminal_bank) {')
    parent=(ARENA/'bots/bterm/src/bot.cpp').read_text(encoding='utf-8')
    a=parent.index('    // Banking used only direct walking');b=parent.index('    if (!follow_field(walk_field',a)
    shortcut=parent[a:b]
    shortcut=replace(shortcut,'    static volatile int bank_shortcuts[2] = {3, 1};\n    if (bank_shortcuts[1] == 1 &&', '    if (integration_enabled(2) &&')
    shortcut=shortcut.replace('(bank_shortcuts[0] & 1) && recall_saves','recall_saves')
    shortcut=shortcut.replace('try { me.recall(); bank_recall_intent = true; mode = "bank-recall"; return true; } catch (...) {}',
        'try { if (start_recall(true)) { mode = "bank-recall"; return true; } } catch (...) {}')
    shortcut=shortcut.replace('(bank_shortcuts[0] & 2) && tp_held != 0','tp_held != 0')
    c=replace(c,'    if (!follow_field(walk_field, blocked, true) && tune::kUnstick && !walk_toward(w.altar_ring))',shortcut+'    if (!follow_field(walk_field, blocked, true) && tune::kUnstick && !walk_toward(w.altar_ring))')
    c=replace(c,'            tp_held = 0;\n            mode = "teleport";',
        '            tp_held = integration_enabled(8) ? std::max(0, tp_held - 1) : 0;\n            mode = "teleport";')
    c=replace(c,'        LOG("teleport error %s\\n", e.what());\n        tp_held = 0;',
        '        LOG("teleport error %s\\n", e.what());\n        tp_held = integration_enabled(8) ? -1 : 0;')
    release='''bool Bot::integration_release_spawn() {
    if (!integration_enabled(1) && !integration_enabled(4)) return false;
    auto& self = bc::self();
    if (!self.can_move() || walked) return false;
    // A healed snapshot after our turn does not imply full health at our next turn:
    // camps attack before the champion phase. Escape the awake reach first.
    if (integration_enabled(1) && bit(w.ally_spawn, pos) && bit(w.hot_zone, pos) && hp < max_hp) {
        bc::bitboard goal = ~w.hot_zone & ~w.static_blocked & ~w.unit_tiles;
        if (!goal.is_empty() && walk_toward(goal)) {
            mode = "fix-spawn";
            debug_block({ std::printf("FIXSPAWN %d %u\\n", round, my_id); });
            return true;
        }
    }
    if (!integration_enabled(4) || !bit(w.camp_tiles_all, pos)) return false;
    const int gi = w.group_at_spawn(pos);
    if (gi < 0 || static_cast<std::size_t>(gi) >= w.groups.size()) return false;
    const auto& g = w.groups[gi];
    if (g.state != GroupState::respawning || round < g.respawn_round) return false;
#if V54_HOLD
    // Keep the existing intentional lead-denial policy when it actually applies.
    if (gi == sole_gem_group && round >= A2_SOLE_FROM && ally_score-enemy_score >= V54_HOLD_LEAD &&
        gems < 10 && hp >= max_hp*0.5f) return false;
#endif
    bc::bitboard goal = ~g.tiles & ~w.static_blocked & ~w.unit_tiles & ~w.hot_zone;
    if (!goal.is_empty() && walk_toward(goal)) {
        mode = "fix-respawn";
        debug_block({ std::printf("FIXRESPAWN %d %u %d\\n", round, my_id, gi); });
        return true;
    }
    return false;
}

'''
    c=replace(c,'bool Bot::go_home_if_needed() {',release+'bool Bot::go_home_if_needed() {')
    c=replace(c,'        mode = "tribute-win";\n#if (A2_NN & 8) && A2_NN_MACRO',
        '        mode = "tribute-win";\n    } else if (integration_release_spawn()) {\n#if (A2_NN & 8) && A2_NN_MACRO')
    out['bot.cpp']=c
    n=out['nnrec.cpp']
    n=replace(n,'static std::int16_t nn_zf[kNF] = {}, nn_zfp[kNF] = {};',
        'static std::int16_t nn_zf[kNF] = {}, nn_zfp[kNF] = {};\nstatic float nn_published_logits[kC+1] = {};')
    marker='                nn_pub = nn_make_pub(nn_lf, nn_lo.target, kC + 1, kC, kCOffL, -1, fast_at);'
    n=replace(n,marker,'''#if defined(A2_NN_RLIVE) && A2_NN_RLIVE
                debug_block({
                    std::copy(nn_lf, nn_lf+kNF, nn_zf);
                    std::copy(nn_lo.target, nn_lo.target+kC+1, nn_published_logits);
                    ++nn_zid;
                });
#endif
'''+marker)
    start=n.index('int Bot::nn_ens_sample(int v92g) {');end=n.index('\n#endif',start)
    # The first nested #ifdef occurs later; operate on the complete function span.
    end=n.index('\n    return out;\n}',start)+len('\n    return out;\n}')
    sampler=n[start:end]
    sampler=replace(sampler,'        float v[kC + 1];','''        float v[kC + 1];
#if defined(A2_NN_NNUE) && defined(A2_NN_LAZY) && !defined(A2_NN_LAZYFULL)
        // Fast work may already be building a different observation. Sample and
        // log the last committed policy, never a mixture of its inputs and scores.
        const auto* sample_features = nn_zf;
        const auto* sample_logits = nn_published_logits;
#else
        const auto* sample_features = nn_lf;
        const auto* sample_logits = nn_lo.target;
#endif''')
    sampler=sampler.replace('std::copy(nn_lo.target, nn_lo.target + kC + 1, v);','std::copy(sample_logits, sample_logits + kC + 1, v);')
    sampler=sampler.replace('nn_lf[kCOffL +','sample_features[kCOffL +')
    sampler=sampler.replace('std::copy(nn_lf, nn_lf + kNF, xn);','std::copy(sample_features, sample_features + kNF, xn);')
    logline='            std::printf("NRL %d %d %d %.5f %d %d %d %s\\n", round, slot, a, lp, chg ? 1 : 0, nn_zid, bs, b64(xn, kNF).c_str());'
    sampler=replace(sampler,logline,'''            // Preserve the actual sampled quantized distribution for PPO checks.
            std::printf("NRQ %d %u %s\\n", round, my_id,
                b64(reinterpret_cast<const std::int16_t*>(v), 2*(kC+1)).c_str());
'''+logline)
    n=n[:start]+sampler+n[end:];out['nnrec.cpp']=n
    return original,out

def make(name,mask,rl=False):
    check_stop();original,out=sources(mask)
    if rl:out['common.h']='#define A2_NN_RLIVE 1\n#define A2_NN_RL_KEEP 1\n'+out['common.h']
    dst=ARENA/'bots'/name/'src'
    if dst.exists():
        assert {p.name:p.read_text(encoding='utf-8') for p in dst.iterdir() if p.is_file()}==out
    else:
        dst.mkdir(parents=True)
        for p,t in out.items():(dst/p).write_text(t,encoding='utf-8',newline='\n')
    changes={}
    for p,t in out.items():
        if original.get(p)==t:continue
        diff='\n'.join(difflib.unified_diff(original.get(p,'').splitlines(),t.splitlines(),fromfile='v113/'+p,tofile=name+'/'+p,lineterm=''))
        target=ROOT/'merge-diffs'/name/(p+'.diff');target.parent.mkdir(parents=True,exist_ok=True);target.write_text(diff,encoding='utf-8');changes[p]=len(diff.splitlines())
    save(dst.parent/'integration.json',{'base':'b113','mask':mask,'flags':{'1':'spawn-healing escape','2':'bank shortcuts, planned recall and terminal cooldown exception','4':'vacate expired occupied camp spawn','8':'recover crystal cache after failures / remaining inventory'},'rl_recorder_repaired':True,'rl_enabled':rl,'source_sha256':digest(dst),'changed_files':changes})
    wasm=build(name,debug=rl)
    return {'name':name,'mask':mask,'source_sha256':digest(dst),'wasm_sha256':sha(wasm),'wasm':str(wasm)}

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda pair:make(*pair),[('m00',0),('m15',15)]))
    save(ROOT/'initial-merged-builds.json',results);print(json.dumps(results,indent=2))
