// Vendored unchanged from JOHNDOE's johndoe/rl-learner-e3-1104 @ e6807c95 tools/rl_learner_1104/target_head_reference/optimized_head.h
// (target head 11826 float32: input-major SIMD dense layers, folded pointer, physical mixture). Used by CLNA_HEAD.
#pragma once
#include <wasm_simd128.h>
#include <cmath>
namespace jd_head {
// Packed layers in input-major order, each followed by biases. 11826 float32 values.
template<int OUT>
inline void dense(const float*x,const float*w,int in,float*y,bool relu){
    v128_t accum[OUT/4];
#pragma clang loop unroll(full)
    for(int j=0;j<OUT/4;++j)accum[j]=wasm_v128_load(w+in*OUT+4*j);
    for(int i=0;i<in;++i){const auto xv=wasm_f32x4_splat(x[i]);
#pragma clang loop unroll(full)
        for(int j=0;j<OUT/4;++j)accum[j]=wasm_f32x4_add(accum[j],wasm_f32x4_mul(xv,wasm_v128_load(w+i*OUT+4*j)));
    }
#pragma clang loop unroll(full)
    for(int j=0;j<OUT/4;++j)wasm_v128_store(y+4*j,relu?wasm_f32x4_max(accum[j],wasm_f32x4_splat(0)):accum[j]);
}
inline float scores(const float*w,const float*x,const float*camps,const float*features,const float*native,int n,float*out){
    float h[64],q[16],ek[16]={},ef[4]={};
    dense<64>(x,w,160,h,true);dense<16>(h,w+10304,64,q,false);
    float bias=0;
    for(int j=0;j<16;++j)bias+=(w[11600+j]+w[11680+j])*q[j];
    for(int i=0;i<16;++i)for(int j=0;j<16;++j)ek[i]+=w[11344+i*16+j]*q[j];
    for(int i=0;i<4;++i)for(int j=0;j<16;++j)ef[i]+=w[11616+i*16+j]*q[j];
    for(int k=0;k<n;++k){float z=bias;for(int j=0;j<16;++j)z+=camps[k*16+j]*ek[j];for(int j=0;j<4;++j)z+=features[k*4+j]*ef[j];out[k]=native[k]+z/4;}
    float far=w[11760],gate=w[11825];
    for(int j=0;j<64;++j){far+=h[j]*w[11696+j];gate+=h[j]*w[11761+j];}
    out[n]=native[n]+far;return gate;
}
// n+1 slots map to physical indices 0..p-1. At least one valid slot; valid reference supported.
// Caller must validate support, bounds and finite inputs once per admitted decision.
inline void probabilities(const float*w,const float*x,const float*c,const float*f,const float*native,int n,const bool*valid,const int*map,int reference,int p,double*out,double&alpha){
    float logits[64]; // caller contract: n <= 63
    const float gate=scores(w,x,c,f,native,n,logits);
    alpha=1/(1+std::exp(-double(gate)));
    float mx=-INFINITY;for(int j=0;j<=n;++j)if(valid[j]&&logits[j]>mx)mx=logits[j];
    double total=0,expv[64];for(int j=0;j<=n;++j){expv[j]=valid[j]?std::exp(double(logits[j]-mx)):0;total+=expv[j];}
    for(int j=0;j<p;++j)out[j]=0;
    for(int j=0;j<=n;++j)if(valid[j])out[map[j]]+=alpha*(expv[j]/total);
    out[reference]+=1-alpha;
}
} // namespace jd_head
