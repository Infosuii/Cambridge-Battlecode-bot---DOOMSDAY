#pragma once
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include "jd_codec.h"
namespace jd_contact {
inline int calls=0, hooks=0, opportunities=0, low_fuel=0, records=0;
// NONTRAINED diagnostic coefficients. Padded8-output int16 SIMD,3 real logits.
inline constexpr auto W=[] {std::array<std::int16_t,48*8> x{};for(int i=0;i<48;++i)for(int j=0;j<3;++j)x[i*8+j]=static_cast<std::int16_t>(((i*71+j*97)%1025)-512);return x;}();
inline constexpr std::int16_t bias[8]={13,-9,7,0,0,0,0,0};
inline void score(const std::int16_t* x,std::int16_t* z){
    auto acc=wasm_v128_load(bias);
    for(int i=0;i<48;++i)if(x[i])acc=wasm_i16x8_add_sat(acc,wasm_i16x8_q15mulr_sat(wasm_v128_load(W.data()+8*i),wasm_i16x8_splat(x[i])));
    wasm_v128_store(z,acc);
}
inline void record(int logical,int body,int seq,int ref_win,int ref_danger,const bool* valid,const std::int16_t* x,const std::int16_t* z,std::uint64_t f0,std::uint64_t f1,std::uint64_t f2){
    char row[1024];int n=std::snprintf(row,sizeof row,"JDC1 %d %u %d %d %d %d %d %d %d %d %llu %llu %llu ",logical,bc::round_number(),body,seq,ref_win,ref_danger,calls,hooks,opportunities,low_fuel,static_cast<unsigned long long>(f0),static_cast<unsigned long long>(f1),static_cast<unsigned long long>(f2));
    for(int i=0;i<3;++i)row[n++]=valid[i]?'1':'0';row[n++]=' ';
    n+=jd_codec::hex_simd(reinterpret_cast<const std::uint8_t*>(x),96,row+n,sizeof row-n);row[n++]=' ';
    n+=jd_codec::hex_simd(reinterpret_cast<const std::uint8_t*>(z),16,row+n,sizeof row-n);row[n++]='\n';std::fwrite(row,1,n,stdout);
    std::printf("JDE1 %d %d %u %llu\n",body,seq,bc::round_number(),static_cast<unsigned long long>(bc::fuel_remaining()));std::fflush(stdout);
}
}
