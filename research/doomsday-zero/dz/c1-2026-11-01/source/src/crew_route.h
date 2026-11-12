#pragma once
#include "camp_threat.h"
#include <array>
#include <cstdint>
#include <vector>

namespace dz::crew {
// Resumable shortest walking path. Only visited cells are read; the large queue
// and parent arrays deliberately have no initialisation/copy on each new job.
class RouteSearch {
    static constexpr unsigned capacity=16384;
    std::array<std::uint16_t,capacity> queue_;
    std::array<std::uint8_t,capacity> parent_;
    std::array<std::uint64_t,capacity/64> seen_{};
    unsigned head_=0,tail_=0,next_=0,from_=0,to_=0,back_=0;
    int width_=0,height_=0;
    bool tracing_=false;
    unsigned index(Tile p) const {return p.y*width_+p.x;}
    Tile tile(unsigned i) const {return {static_cast<int>(i%width_),static_cast<int>(i/width_)};}
    bool inside(Tile p) const {return p.x>=0&&p.y>=0&&p.x<width_&&p.y<height_;}
    static constexpr std::array<Tile,8> directions{{{-1,-1},{-1,0},{-1,1},{0,-1},{0,1},{1,-1},{1,0},{1,1}}};
public:
    enum class Status { Idle, Pending, Complete, Unreachable, Unsupported };
    Status status=Status::Idle;
    std::vector<Tile> path;
    RouteSearch() {} // Do not value-initialise the unvisited queue/parent storage.
    RouteSearch(const RouteSearch&)=delete;
    RouteSearch& operator=(const RouteSearch&)=delete;
    void begin(Tile from,Tile to,int width,int height) {
        status=Status::Unsupported;path.clear();width_=width;height_=height;
        if(width<=0||height<=0||static_cast<long long>(width)*height>capacity||!inside(from)||!inside(to))return;
        seen_.fill(0);head_=tail_=next_=0;tracing_=false;from_=index(from);to_=index(to);
        queue_[tail_++]=from_;seen_[from_/64]|=std::uint64_t{1}<<(from_%64);status=Status::Pending;
        if(from_==to_)status=Status::Complete;
    }
    template<class Open,class Budget>
    Status resume(Open open,Budget budget) {
        while(status==Status::Pending) {
            if(!budget())return status;
            if(tracing_) {
                if(back_==from_) {std::reverse(path.begin(),path.end());status=Status::Complete;break;}
                if(path.size()>=128){status=Status::Unsupported;break;}
                const auto p=tile(back_),d=directions[parent_[back_]];
                path.push_back(p);back_=index({p.x-d.x,p.y-d.y});continue;
            }
            if(head_==tail_){status=Status::Unreachable;break;}
            if(next_==directions.size()){++head_;next_=0;continue;}
            const auto p=tile(queue_[head_]),d=directions[next_];const unsigned direction=next_++;
            const Tile q{p.x+d.x,p.y+d.y};if(!inside(q))continue;
            const unsigned i=index(q);
            if((seen_[i/64]&(std::uint64_t{1}<<(i%64)))||!open(q))continue;
            seen_[i/64]|=std::uint64_t{1}<<(i%64);parent_[i]=direction;queue_[tail_++]=i;
            if(i==to_){back_=i;tracing_=true;}
        }
        return status;
    }
};
}
