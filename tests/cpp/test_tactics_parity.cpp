// Synthetic typed candidate fixture driver. Native C++/Python feature and mask parity only.
#include "nn_tactics.h"
#include <cstdio>
int main() {
    int head,n,ctx;
    while (std::scanf("%d %d %d",&head,&n,&ctx)==3) {
        if(head==10) { float x; if(std::scanf("%f",&x)!=1) return 7; std::printf("%d %.9g\n",nne::belief_sector(n,ctx),nne::bounded_belief(x)); continue; }
        if (head==12) {
            float raw[8],feat[8]; for(float& f:raw) if(std::scanf("%f",&f)!=1) return 2;
            nne::build_leaf(raw,feat); std::printf("12 1 8 0\n");
            for(float f:feat) std::printf("%.9g ",f); std::printf("\n"); continue;
        }
        nne::Option a[32];
        if (n<0 || n>32) return 3;
        for(int i=0;i<n;++i) {
            unsigned id,legal; if(std::scanf("%u %u",&id,&legal)!=2) return 4;
            a[i].id=id; a[i].legal=static_cast<std::uint8_t>(legal);
            for(float& f:a[i].raw) if(std::scanf("%f",&f)!=1) return 5;
        }
        nnh::Decision d;
        if(head==6) nne::build_move(a,n,ctx,d);
        else if(head==7) nne::build_combat(a,n,ctx,d);
        else if(head==8) nne::build_engage(a,n,ctx,d);
        else if(head==9) nne::build_ward(a,n,ctx,d);
        else return 6;
        std::printf("%d %d %d %u\n",static_cast<int>(d.head),d.K,d.F,d.context);
        for(int i=0;i<d.K;++i) {
            std::printf("%u %u %.9g ",d.id[i],d.legal[i],d.prior[i]);
            for(int f=0;f<d.F;++f) std::printf("%.9g ",d.feat[i*d.F+f]);
            std::printf("\n");
        }
    }
}
