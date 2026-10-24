"""Prepare/review the full Wave2 hook integration in scratch only. Never mutates bot/src or references.

Official fuel measurement and teacher_exact byte identity are still mandatory before promoting this source.
--native-check performs SDK syntax checks, not a Wasm build or engine verification.
"""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f'expected one integration anchor: {old[:100]!r}; got {text.count(old)}')
    return text.replace(old, new, 1)


def strategy_hooks(src):
    p = src/'bot.cpp'; text = p.read_text(encoding='utf-8')
    text = once(text, '#include "nn_teacher.h"', '#include "nn_teacher.h"\n#include "nn_strategy.h"')
    anchor = '    if constexpr (nnt::kObjective) nn_teacher_access::cap_objective(*this, top, n_top, best, best_need, best_score, participants_hint);'
    text = once(text, anchor, anchor + '''
    if constexpr (nncfg::mode(nncfg::H::objective) != nncfg::Mode::off)
        best = nns::objective(*this, best, best_need, best_score);''')
    anchor = '        if constexpr (nnt::kChain) nn_teacher_access::cap_chain(*this, nnt::Chain::home);'
    text = once(text, anchor, anchor + '''
    } else if ([&]() {
        if constexpr (nncfg::mode(nncfg::H::strategy) != nncfg::Mode::off ||
                      nncfg::mode(nncfg::H::role) != nncfg::Mode::off ||
                      nncfg::mode(nncfg::H::value) != nncfg::Mode::off) return nns::act(*this);
        return false;
    }()) {
        // A guarded neural priority acted. Option0 falls through to the remaining teacher chain.''')
    anchor = '        if constexpr (nnt::kChain) nn_teacher_access::cap_chain(*this, nnt::Chain::dead);'
    text = once(text, anchor, anchor + '''
        if constexpr (nncfg::mode(nncfg::H::role) != nncfg::Mode::off ||
                      nncfg::mode(nncfg::H::value) != nncfg::Mode::off) nns::reset_role();''')
    p.write_text(text, encoding='utf-8', newline='\n')
    p=src/'draft.h'; text=p.read_text(encoding='utf-8')
    text=once(text,'void play_draft();','''#include "nn_config.h"
class Bot;
void play_draft(
#if NN_ANY_HEAD
    const Bot& bot
#endif
);''')
    p.write_text(text, encoding='utf-8', newline='\n')
    p=src/'draft.cpp'; text=p.read_text(encoding='utf-8')
    text=once(text,'#include "nn_teacher.h"','#include "nn_teacher.h"\n#include "nn_strategy.h"')
    text=once(text,'bool ml_draft_pick(std::uint32_t size) {','''bool ml_draft_pick(std::uint32_t size
#if NN_ANY_HEAD
    , const Bot& bot
#endif
) {''')
    text=once(text,'void play_draft() {','''void play_draft(
#if NN_ANY_HEAD
    const Bot& bot
#endif
) {''')
    text=once(text,'ml_done = !known && ml_draft_pick(size);','''ml_done = !known && ml_draft_pick(size
#if NN_ANY_HEAD
            , bot
#endif
        );''')
    anchor = '    if constexpr (nnt::kDraft) nn_teacher_access::cap_draft_pick(best); // draft_pick head hook: substitute `best` here'
    text=once(text,anchor,anchor+'''
#if NN_ANY_HEAD
    if constexpr (nncfg::mode(nncfg::H::draft_pick) != nncfg::Mode::off) {
        unsigned ours_mask=0, theirs_mask=0, taken_mask=0;
        for(int c=0;c<12;++c) if(taken[c]) taken_mask |= 1u<<c;
        for(auto c:ours) if(static_cast<unsigned>(c)<12) ours_mask |= 1u<<static_cast<unsigned>(c);
        for(auto c:theirs) if(static_cast<unsigned>(c)<12) theirs_mask |= 1u<<static_cast<unsigned>(c);
        best=nns::draft_pick(bot,best,feat,taken_mask,ours_mask,theirs_mask,
                            static_cast<float>(j)/static_cast<float>(sz),first);
    }
#endif''')
    p.write_text(text, encoding='utf-8', newline='\n')
    p=src/'main.cpp'; text=p.read_text(encoding='utf-8')
    text=once(text,'                play_draft();','''                play_draft(
#if NN_ANY_HEAD
                    bot
#endif
                );''')
    p.write_text(text, encoding='utf-8', newline='\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dest', default='artifacts/tmp/wave2_integrated')
    ap.add_argument('--profile', default='dev_untrained')
    ap.add_argument('--native-check', action='store_true')
    a=ap.parse_args()
    dest=(ROOT/a.dest).resolve()
    dest.relative_to((ROOT/'artifacts/tmp').resolve())
    src=engine.make_bot_dir(ROOT/'bot/src',dest/'bot')/'src'
    strategy_hooks(src)
    subprocess.run([sys.executable,str(ROOT/'agents/E/apply_hooks.py'),'--src',str(src)],check=True,cwd=ROOT)
    subprocess.run(['git','apply','--directory='+dest.relative_to(ROOT).as_posix(),
                    str(ROOT/'agents/F/HOOKS.diff')],check=True,cwd=ROOT)
    subprocess.run([sys.executable,str(ROOT/'tools/install_models.py'),'--profile',a.profile,'--src',str(src),
                    '--receipt',str(dest/'install.json')],check=True,cwd=ROOT)
    receipt=dict(label='staged integration; NOT official verification', profile=a.profile,
                 source_sha256=engine.tree_sha256(src), source=str(src), official_build='NOT RUN',
                 fuel='NOT MEASURED', native_checks=[])
    if a.native_check:
        for name in ('bot.cpp','draft.cpp','main.cpp','tsearch.cpp','nn_strategy.cpp','nn_tactics.cpp',
                     'nn_economy.cpp','nn_head.cpp','nn_obs_glue.cpp'):
            cmd=[engine.PATHS['native_cxx'],'-std=c++20','-fsyntax-only','-Wno-attributes',
                 '-I'+str(src),'-I'+str(ROOT/'sdk/cpp'),str(src/name)]
            r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
            receipt['native_checks'].append(dict(file=name,passed=r.returncode==0,output=r.stdout+r.stderr))
            if r.returncode:
                engine.write_json(dest/'stage_receipt.json',receipt)
                raise SystemExit(r.stdout+r.stderr)
    engine.write_json(dest/'stage_receipt.json',receipt)
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
