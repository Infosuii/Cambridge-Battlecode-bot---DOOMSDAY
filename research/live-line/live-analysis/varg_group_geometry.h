#pragma once
#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
namespace codex_varg {
struct Point{int x,y;};
struct Shape{
 bool built=false,valid=false,cliques=false;
 unsigned char n=0,components=0;
 std::array<std::uint16_t,12> adjacent{},component{};
};
inline Shape build(const Point* points,unsigned n){
 Shape s;s.built=true;if(n==0||n>12)return s;s.n=static_cast<unsigned char>(n);s.valid=true;s.cliques=true;
 for(unsigned i=0;i<n;++i)for(unsigned j=0;j<n;++j)if(std::max(std::abs(points[i].x-points[j].x),std::abs(points[i].y-points[j].y))<=1)s.adjacent[i]|=static_cast<std::uint16_t>(1u<<j);
 unsigned remaining=(1u<<n)-1;
 while(remaining){unsigned reach=remaining&(~remaining+1u),prior=0;
  while(reach!=prior){prior=reach;for(unsigned i=0;i<n;++i)if(reach>>i&1u)reach|=s.adjacent[i];}
  s.component[s.components++]=static_cast<std::uint16_t>(reach);remaining&=~reach;
  for(unsigned i=0;i<n;++i)if((reach>>i&1u)&&s.adjacent[i]!=reach)s.cliques=false;
 }
 return s;
}
inline unsigned neighbours(const Shape& s,unsigned i,unsigned alive){return std::popcount(static_cast<unsigned>(s.adjacent[i])&alive&~(1u<<i));}
struct Capability{bool valid=false;std::uint32_t attacks=0;float factor=1.6f;};
inline Capability capability(const Shape& s,const float* hp,float damage){
 Capability result;if(!s.valid||!s.cliques||!std::isfinite(damage)||damage<1.0f||damage>16777216.0f)return result;
 double total=0;for(unsigned i=0;i<s.n;++i){if(!std::isfinite(hp[i])||hp[i]<0||hp[i]>16777216.0f)return result;total+=hp[i];}
 std::uint32_t attacks=0;
 for(unsigned k=0;k<s.components;++k){float highest=0;for(unsigned i=0;i<s.n;++i)if(s.component[k]>>i&1u)highest=std::max(highest,hp[i]);
  attacks+=static_cast<std::uint32_t>(std::ceil(static_cast<double>(highest)/static_cast<double>(damage)));
 }
 result.valid=true;result.attacks=attacks;
 if(attacks)result.factor=static_cast<float>(total/(static_cast<double>(damage)*attacks));
 return result;
}
}
