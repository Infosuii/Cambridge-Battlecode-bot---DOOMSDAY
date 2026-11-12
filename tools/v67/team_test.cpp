#include "../../bots/v67/src/policies/p15/team_memory.h"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <initializer_list>
int main() {
 auto m=team67::put_plan(0,-1,126,7);
 for(int s=0;s<6;++s) {
  m=team67::put_position(m,s,s*17,s*17,true);
  int x=0,y=0; assert(team67::position(m,s,x,y));
  assert(std::abs(x-s*17)<=5&&std::abs(y-s*17)<=5);
  assert(!team67::job_message(m,s));
 }
 assert(team67::rally(m)==126);
 const auto slots=m&team67::kSlotsMask;
 m=team67::put_battle(m,5,99,99,7); int target=0,x=0,y=0;
 assert((m&team67::kSlotsMask)==slots);
 assert(team67::battle(m,0,target,x,y)&&target==5&&x==98&&y==98);
 assert(team67::battle(m,2,target,x,y));
 assert(!team67::battle(m,3,target,x,y));
 for(int s=0;s<6;++s) for(int g=-1;g<126;++g) {
  auto n=team67::put_job(m,s,g);
  assert(team67::job_message(n,s)&&team67::job(n,s)==g);
  assert((n&~(std::uint64_t{255}<<(8*s)))==(m&~(std::uint64_t{255}<<(8*s))));
 }
 for(int s=0;s<6;++s) for(int g=0;g<62;++g) for(bool arrived:{false,true}) {
  auto n=team67::put_job(m,s,g,arrived,true);
  assert(team67::job(n,s,true)==g);
  assert(team67::onsite(n,s,true)==arrived);
  assert((n&team67::kSlotsMask)!=(m&team67::kSlotsMask) || team67::byte(n,s)==team67::byte(m,s));
  assert(!team67::position(n,s,x,y));
  assert((n&~team67::kSlotsMask)==(m&~team67::kSlotsMask));
 }
 for(int x0=0;x0<100;++x0) for(int y0=0;y0<100;++y0) {
  auto n=team67::put_position(m,5,x0,y0,true);
  assert(team67::position(n,5,x,y)&&std::abs(x-x0)<=5&&std::abs(y-y0)<=5);
  n=team67::put_battle(n,0,x0,y0,6);
  assert(team67::battle(n,7,target,x,y)&&target==0&&std::abs(x-x0)<=2&&std::abs(y-y0)<=2);
 }
 std::puts("v67 tagged position/job and timed battle protocol passed");
}
