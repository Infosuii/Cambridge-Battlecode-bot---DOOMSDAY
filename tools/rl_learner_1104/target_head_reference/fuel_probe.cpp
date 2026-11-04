#include <cambc.h>
#include <wasm_simd128.h>
#include <cstdio>
#include <cstdint>
#include <cmath>
namespace bc=cambc;
static float W[11826], X[160], C[51][16], F[51][4];
static volatile float sink;
__attribute__((noinline)) void dense_scalar(const float* x,const float* w,int in,int out,float* y,bool relu){
    for(int j=0;j<out;++j){float s=w[in*out+j];for(int i=0;i<in;++i)s+=x[i]*w[i*out+j];y[j]=relu&&s<0?0:s;}
}
__attribute__((noinline)) void dense_simd(const float* x,const float* w,int in,int out,float* y,bool relu){
    for(int j=0;j<out;j+=4){v128_t s=wasm_v128_load(w+in*out+j);for(int i=0;i<in;++i)s=wasm_f32x4_add(s,wasm_f32x4_mul(wasm_f32x4_splat(x[i]),wasm_v128_load(w+i*out+j)));if(relu)s=wasm_f32x4_max(s,wasm_f32x4_splat(0));wasm_v128_store(y+j,s);}
}
template<int OUT>
__attribute__((noinline)) void dense_tiled(const float*x,const float*w,int in,float*y,bool relu){
    v128_t accum[OUT/4];
#pragma clang loop unroll(full)
    for(int j=0;j<OUT/4;++j)accum[j]=wasm_v128_load(w+in*OUT+4*j);
    for(int i=0;i<in;++i){
        const auto xv=wasm_f32x4_splat(x[i]);
#pragma clang loop unroll(full)
        for(int j=0;j<OUT/4;++j)accum[j]=wasm_f32x4_add(accum[j],wasm_f32x4_mul(xv,wasm_v128_load(w+i*OUT+4*j)));
    }
#pragma clang loop unroll(full)
    for(int j=0;j<OUT/4;++j)wasm_v128_store(y+4*j,relu?wasm_f32x4_max(accum[j],wasm_f32x4_splat(0)):accum[j]);
}
__attribute__((noinline)) float head(int n,int mode){
    float h[64],q[16],keys[16],features[16];
    auto dense=mode?dense_simd:dense_scalar;
    if(mode>=2)dense_tiled<64>(X,W,160,h,true);else dense(X,W,160,64,h,true);
    if(mode>=2)dense_tiled<16>(h,W+10304,64,q,false);else dense(h,W+10304,64,16,q,false);
    float sum=0;
    if(mode==3){
        float ek[16]={},ef[4]={},bias=0;
        for(int j=0;j<16;++j)bias+=(W[11344+256+j]+W[11616+64+j])*q[j];
        for(int i=0;i<16;++i)for(int j=0;j<16;++j)ek[i]+=W[11344+i*16+j]*q[j];
        for(int i=0;i<4;++i)for(int j=0;j<16;++j)ef[i]+=W[11616+i*16+j]*q[j];
        for(int k=0;k<n;++k){float score=bias;for(int j=0;j<16;++j)score+=C[k][j]*ek[j];for(int j=0;j<4;++j)score+=F[k][j]*ef[j];sum+=score/4;}
    }else{
        for(int k=0;k<n;++k){
            if(mode>=2)dense_tiled<16>(C[k],W+11344,16,keys,false);else dense(C[k],W+11344,16,16,keys,false);
            if(mode>=2)dense_tiled<16>(F[k],W+11616,4,features,false);else dense(F[k],W+11616,4,16,features,false);
            float score=0;for(int j=0;j<16;++j)score+=(keys[j]+features[j])*q[j];sum+=score/4;
        }
    }
    // Two scalar outputs; explicit column-major 64->1 with biases.
    float far=W[11760],gate=W[11825];
    for(int j=0;j<64;++j){far+=h[j]*W[11696+j];gate+=h[j]*W[11761+j];}
    return sum+far+1/(1+std::exp(-gate));
}
int main(){
    std::uint32_t state=unsigned(bc::round_number())+71;
    auto next=[&](){state=state*1664525u+1013904223u;return (float(int(state>>16)-32768)/32768)*.05f;};
    for(auto&x:W)x=next();for(auto&x:X)x=next();for(auto&r:C)for(auto&x:r)x=next();for(auto&r:F)for(auto&x:r)x=next();
    auto a=bc::fuel_remaining();auto b=bc::fuel_remaining();std::printf("READ_COST %llu\n",(unsigned long long)(a-b));
    for(int n:{10,51})for(int mode:{0,1,2,3}){
        auto before=bc::fuel_remaining();float result=head(n,mode);sink=result;auto after=bc::fuel_remaining();
        std::printf("HEAD_FUEL n=%d mode=%d fuel=%llu checksum=%.9g\n",n,mode,(unsigned long long)(before-after),double(result));
    }
    std::fflush(stdout);bc::resign();bc::end_turn();
}
