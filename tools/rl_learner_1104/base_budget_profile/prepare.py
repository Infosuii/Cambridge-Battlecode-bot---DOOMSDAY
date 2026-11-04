from pathlib import Path
import shutil,json,hashlib
r=Path(__file__).resolve().parent; p=r/'base-budget-profile'
assert not p.exists()
p.mkdir();(p/'bots/submission').mkdir(parents=True)
src=p/'bots/submission/src';shutil.copytree(r/'head-cached-review/bots/submission/src',src)
for name in ('sdk','cmake'):(p/name).symlink_to(r/'mac-project'/name,target_is_directory=True)
f=src/'common.h';s=f.read_text()
for line in ['#define CLNA_HEAD 1\n','#define CLNA_HEAD_MIN 35000\n','#define CLNA_RLOG 1\n','#define CLNA_EPS 0.02\n']:
 assert s.count(line)==1;s=s.replace(line,'',1)
f.write_text(s)
# Real raw fuel, not existing profiler's fuel+nn_spent virtual accounting.
(src/'jd_budget_profile.h').write_text('''#pragma once
#include <cstdint>
#include <cstdio>
namespace jdbp {
enum Section { turn, heuristic_score, neural_lazy, neural_decide, neural_background, farm, count };
inline std::uint64_t used[count] = {}, calls[count] = {}, interrupted[count] = {}, maxima[count] = {};
struct Scope {
 int id; std::uint64_t f; std::uint32_t r;
 explicit Scope(int i):id(i),f(bc::fuel_remaining()),r(bc::round_number()) {}
 ~Scope(){const auto now=bc::fuel_remaining();++calls[id];
  if (bc::round_number()!=r || now>f) {++interrupted[id];return;}
  const auto n=f-now;used[id]+=n;if(n>maxima[id])maxima[id]=n;
 }
};
inline void report(){
 static std::uint32_t last=0; const auto r=bc::round_number();
 if (r<last+250 || bc::fuel_remaining()<10000u) return;
 last=r;
 for(int i=0;i<count;++i) std::printf("JDBP %u %u %d %llu %llu %llu %llu\\n",r,static_cast<unsigned>(static_cast<bc::handle_champion_t>(bc::self())),i,
  static_cast<unsigned long long>(calls[i]),static_cast<unsigned long long>(used[i]),
  static_cast<unsigned long long>(interrupted[i]),static_cast<unsigned long long>(maxima[i]));
}
}
''')
for name,changes in {
 'bot.cpp':[('int Bot::score_groups_full(int participants_hint, int& best_need, float& best_score) {','heuristic_score'),('bool Bot::farm() {','farm'),('void Bot::play_turn() {','turn')],
 'nnrec.cpp':[('void Bot::nn_lazy_score() {','neural_lazy'),('void Bot::nn_decide() {','neural_decide'),('void Bot::nn_turn_end() {','neural_background')]
}.items():
 f=src/name;s=f.read_text();assert '#include "bot.h"' in s;s=s.replace('#include "bot.h"','#include "bot.h"\n#include "jd_budget_profile.h"',1)
 for sig,section in changes:
  assert sig in s,(name,sig);s=s.replace(sig,sig+'\n    jdbp::Scope jd_budget_scope(jdbp::'+section+');')
 f.write_text(s)
f=src/'main.cpp';s=f.read_text().replace('#include "bot.h"','#include "bot.h"\n#include "jd_budget_profile.h"',1)
# after the turn's background work and before handing control back to engine
needle='        bc::end_turn();';assert needle in s;s=s.replace(needle,'        jdbp::report();\n'+needle)
f.write_text(s)
report=dict(source='isolated copy of 8cccf446 cached review, CLNA defines removed; native NN flags retained',
 sections=['play_turn','score_groups_full','nn_lazy_score','nn_decide','nn_turn_end','farm'],
 limitations=['Instrumentation changes fuel timing; not a strength evaluation.',
 'Nested inclusive scopes cannot be added as disjoint costs.',
 'Interrupted calls counted separately and omitted from fuel totals, so completed-call estimates have survivor bias.',
 'Periodic reports have fuel guard and may omit late counts; no total-game coverage claim.',
 'Raw engine fuel used, not virtual fuel+nn_spent accounting.'])
(p/'profile_plan.json').write_text(json.dumps(report,indent=2)+'\n')
print(p)
