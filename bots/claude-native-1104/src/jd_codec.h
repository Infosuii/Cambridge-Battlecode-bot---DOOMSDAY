// Vendored unchanged from JOHNDOE's johndoe/rl-learner-e3-1104 @ ef5117b5 tools/rl_learner_1104/target_head_reference/exact_codec.h
// (exact byte transport: SIMD hex of raw little-endian bytes). Used by the CNR3 logger (CLNA_HEAD).
#pragma once
#include <cstddef>
#include <cstdint>
#include <wasm_simd128.h>
namespace jd_codec {
// Exact byte transport only; payload schema, little-endian packing and completeness
// validation belong to the caller. No heap allocation, floating formatting or I/O.
inline std::size_t base64(const std::uint8_t*data,std::size_t n,char*out,std::size_t capacity){
    static constexpr char table[]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    const std::size_t length=4*((n+2)/3);
    if(capacity<length+1)return 0;
    std::size_t i=0,j=0;
    for(;i+3<=n;i+=3){
        const std::uint32_t v=(std::uint32_t(data[i])<<16)|(std::uint32_t(data[i+1])<<8)|data[i+2];
        out[j++]=table[(v>>18)&63];out[j++]=table[(v>>12)&63];out[j++]=table[(v>>6)&63];out[j++]=table[v&63];
    }
    if(i<n){const std::uint32_t v=(std::uint32_t(data[i])<<16)|(i+1<n?std::uint32_t(data[i+1])<<8:0);
        out[j++]=table[(v>>18)&63];out[j++]=table[(v>>12)&63];out[j++]=i+1<n?table[(v>>6)&63]:'=';out[j++]='=';
    }
    out[j]=0;return j;
}
inline std::size_t hex(const std::uint8_t*data,std::size_t n,char*out,std::size_t capacity){
    static constexpr char table[]="0123456789abcdef";
    if(capacity<2*n+1)return 0;
    for(std::size_t i=0;i<n;++i){out[2*i]=table[data[i]>>4];out[2*i+1]=table[data[i]&15];}
    out[2*n]=0;return 2*n;
}
inline std::size_t hex_simd(const std::uint8_t*data,std::size_t n,char*out,std::size_t capacity){
    if(capacity<2*n+1)return 0;
    const auto table=wasm_v128_load("0123456789abcdef");const auto mask=wasm_i8x16_splat(15);
    std::size_t i=0;
    for(;i+16<=n;i+=16){
        const auto bytes=wasm_v128_load(data+i);
        const auto hi=wasm_i8x16_swizzle(table,wasm_u8x16_shr(bytes,4));
        const auto lo=wasm_i8x16_swizzle(table,wasm_v128_and(bytes,mask));
        wasm_v128_store(out+2*i,wasm_i8x16_shuffle(hi,lo,0,16,1,17,2,18,3,19,4,20,5,21,6,22,7,23));
        wasm_v128_store(out+2*i+16,wasm_i8x16_shuffle(hi,lo,8,24,9,25,10,26,11,27,12,28,13,29,14,30,15,31));
    }
    static constexpr char t[]="0123456789abcdef";
    for(;i<n;++i){out[2*i]=t[data[i]>>4];out[2*i+1]=t[data[i]&15];}
    out[2*n]=0;return 2*n;
}
}
