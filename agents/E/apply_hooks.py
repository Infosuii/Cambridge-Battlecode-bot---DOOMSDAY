"""Lead-owned integration patch, explicit --src required. Never edits references or outside workspace.

Review before running. Each change stays inside a compile-time per-head gate; no new original-body work with all heads off.
The caller must rebuild teacher_exact and verify byte identity immediately afterward.
"""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[2]

def replace_once(text,old,new):
    if new in text: return text
    if text.count(old)!=1: raise ValueError(f'expected one hook anchor, got {text.count(old)}: {old[:120]}')
    return text.replace(old,new,1)

def function(text,name,edit):
    start=text.index('bool Bot::'+name+'(')
    end=text.find('\nbool Bot::',start+1)
    if end<0: end=len(text)
    return text[:start]+edit(text[start:end])+text[end:]

def tile_rank(text,anchor,context,limit):
    code=f'''    if constexpr (nncfg::mode(nncfg::H::move) != nncfg::Mode::off || nncfg::mode(nncfg::H::belief) != nncfg::Mode::off) {{
        const int nn_n = std::min(n, {limit});
        nne::Tile nn_tiles[{limit}];
        for (int nn_i = 0; nn_i < nn_n; ++nn_i) nn_tiles[nn_i] = {{cands[nn_i].p.x, cands[nn_i].p.y, static_cast<float>(cands[nn_i].score)}};
        const int nn_pick = nne::move_rank(*this, nn_tiles, nn_n, {context});
        if (nn_pick > 0 && nn_pick < nn_n) std::swap(cands[0], cands[nn_pick]);
    }}
'''
    return replace_once(text,anchor,code+anchor)

def apply(src):
    src=src.resolve()
    if not src.is_relative_to(ROOT) or 'references' in src.relative_to(ROOT).parts: raise ValueError('workspace scratch/source only')
    bot=src/'bot.cpp'; text=bot.read_text(encoding='utf-8')
    text=replace_once(text,'#include "nn_teacher.h"','#include "nn_teacher.h"\n#include "nn_tactics.h"')
    text=function(text,'follow_field',lambda s:tile_rank(s,'#if A2_BRIDGES\n    if (n == 0', 'combat_move ? 1 : 0',8))
    text=function(text,'retreat_from',lambda s:tile_rank(s,'    for (int i = 0; i < n; ++i) {\n        try {',2,8))
    text=function(text,'dash_away',lambda s:tile_rank(s,'        for (int i = 0; i < n && i < 4; ++i) {',2,4))
    text=function(text,'kite_step',lambda s:replace_once(s,'    if (best == pos) return false;\n    try {', '''    if constexpr (nncfg::mode(nncfg::H::move) != nncfg::Mode::off || nncfg::mode(nncfg::H::belief) != nncfg::Mode::off) {
        if (best != pos) {
            const auto nn_tile = nne::local_move(*this, {best.x, best.y, static_cast<float>(best_s)}, 3);
            best = {nn_tile.x, nn_tile.y};
        }
    }
    if (best == pos) return false;
    try {'''))
    text=function(text,'cast_on_enemy',lambda s:replace_once(s,
        '    if constexpr (nnt::kCast) nn_teacher_access::cap_cast(*this, e, best, best_value, dash_slot, dash_aim);',
        '''    if constexpr (nnt::kCast) nn_teacher_access::cap_cast(*this, e, best, best_value, dash_slot, dash_aim);
    if constexpr (nncfg::mode(nncfg::H::combat) != nncfg::Mode::off) {
        const auto nn_cast = nne::combat_cast(*this, e, best, dash_slot, dash_aim.x, dash_aim.y);
        if (nn_cast.dash) dash_slot = nn_cast.slot;
        else { dash_slot = -1; best = nn_cast.slot; }
    }'''))
    final='    if constexpr (nnt::kFight) nn_teacher_access::cap_fight_final(target, winning, in_danger, threat_on_me);'
    text=replace_once(text,final,final+'''
    if constexpr (nncfg::mode(nncfg::H::combat) != nncfg::Mode::off) {
        target = nne::combat_target(*this, target);
    }
    if constexpr (nncfg::mode(nncfg::H::engage) != nncfg::Mode::off) {
        const auto* nn_f = nn_teacher_access::fight(*this);
        const int nn_teacher = winning ? 1 : in_danger ? -1 : 0;
        const int nn_verdict = nne::engage(*this, nn_teacher, nn_f ? nn_f->td_fight : 0.0f,
            nn_f ? nn_f->td_run : 0.0f, nn_f ? nn_f->td_margin : 0.0f, ttd, target != nullptr);
        if (nn_verdict != nn_teacher) {
            winning = nn_verdict > 0; in_danger = nn_verdict < 0;
            if (in_danger && threat_on_me <= 0) threat_on_me = 1.0f;
        }
    }''')
    text=function(text,'ward_ahead',lambda s:replace_once(s,
        '    if constexpr (nnt::kWard) nn_teacher_access::cap_ward(*this, best, best_d);',
        '''    if constexpr (nnt::kWard) nn_teacher_access::cap_ward(*this, best, best_d);
    if constexpr (nncfg::mode(nncfg::H::ward) != nncfg::Mode::off) {
        if (best.x >= 0) {
            const nne::Tile nn_tile{best.x, best.y, static_cast<float>(best_d)};
            if (nne::ward_rank(*this, &nn_tile, 1, 0) < 0) best = {-1, -1};
        }
    }'''))
    text=function(text,'ward_reveal',lambda s:replace_once(s,
        '        if (me.ward_cooldown() > 0) return false;\n        for (int i = 0;',
        '''        if (me.ward_cooldown() > 0) return false;
        if constexpr (nncfg::mode(nncfg::H::ward) != nncfg::Mode::off) {
            const int nn_n = std::min(n, 3);
            nne::Tile nn_tiles[3];
            for (int nn_i = 0; nn_i < nn_n; ++nn_i) nn_tiles[nn_i] = {cands[nn_i].p.x, cands[nn_i].p.y, static_cast<float>(cands[nn_i].d)};
            const int nn_pick = nne::ward_rank(*this, nn_tiles, nn_n, 1);
            if (nn_pick < 0) return false;
            if (nn_pick > 0 && nn_pick < nn_n) std::swap(cands[0], cands[nn_pick]);
        }
        for (int i = 0;'''))
    text=function(text,'reveal_bush_camp',lambda s:replace_once(s,
        '        if (me.place_ward(at)) ward_pos = at;',
        '''        if constexpr (nncfg::mode(nncfg::H::ward) != nncfg::Mode::off) {
            const nne::Tile nn_tile{at.x, at.y, 0};
            if (nne::ward_rank(*this, &nn_tile, 1, 2) < 0) return false;
        }
        if (me.place_ward(at)) ward_pos = at;'''))
    bot.write_text(text,encoding='utf-8',newline='\n')
    ts=src/'tsearch.cpp'; text=ts.read_text(encoding='utf-8')
    text=replace_once(text,'#include "nn_teacher.h"','#include "nn_teacher.h"\n#include "nn_tactics.h"')
    anchor='            v[model][plan] = tune::kTsLocalNet ? plan_value(s, c, m, round, wts.alive) : ts::evaluate(c, wts);'
    text=replace_once(text,anchor,anchor+'''
            if constexpr (nncfg::mode(nncfg::H::ts_leaf) != nncfg::Mode::off) {
                v[model][plan] += nne::leaf(*this, s, c, m.home_x[0], m.home_y[0], plan);
            }''')
    ts.write_text(text,encoding='utf-8',newline='\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--src',type=Path,required=True); a=ap.parse_args()
    apply(a.src)
