#include <cambc.h>
#include <cstdio>
#include <cmath>
#include "fixtures.h"
#include "optimized_head.h"
static volatile double sink;
static unsigned state=71;
static double uniform(){state=1664525u*state+1013904223u;return double(state)/4294967296.;}
__attribute__((noinline)) static double expensive(int b){
 float logits[11];jd_head::scores(weights,contexts+b*160,camps+b*160,features+b*40,native+b*11,10,logits);
 double sum=0;for(int j=0;j<11;++j)sum+=std::exp(double(logits[j])*.01);return sum;
}
int main(){
 for(int mode=0;mode<2;++mode){state=71;int calls=0,invokes=0;double total=0;
  auto before=cambc::fuel_remaining();
  for(int i=0;i<64;++i){
   const int b=i%32;double g=-3.8918202981106265;
   for(int j=0;j<8;++j)g+=contexts[b*160+j]*.003;
   const double alpha=1/(1+std::exp(-g));const bool invoke=uniform()<alpha;
   if(invoke)++invokes;
   if(!mode||invoke){total+=expensive(b);++calls;}
   total+=invoke?std::log(alpha):std::log1p(-alpha);
  }
  sink=total;auto after=cambc::fuel_remaining();
  std::printf("CONDITIONAL mode=%d decisions=64 head_calls=%d invokes=%d fuel=%llu\n",mode,calls,invokes,(unsigned long long)(before-after));
 }
 std::fflush(stdout);cambc::resign();cambc::end_turn();
}
