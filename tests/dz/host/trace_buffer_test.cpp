#include "trace_buffer.h"
#include <cassert>
#include <cstdint>
#include <deque>
#include <iostream>
#include <random>

int main() {
    dz::TraceBuffer ring;std::deque<char> reference;std::mt19937 random(2049);
    unsigned wrapped=0,partial=0;
    for(unsigned turn=0;turn<10000;++turn) {
        const unsigned append=random()%2048;
        for(unsigned i=0;i<append;++i) {
            const char c=static_cast<char>(random()%127);const bool room=reference.size()<ring.capacity;
            assert(ring.put(c)==room);if(room)reference.push_back(c);
        }
        assert(ring.size==reference.size()&&(!ring.size||ring.last()==reference.back()));
        const std::uint64_t fuel=random()%100001,spare=30000;
        const auto segment=ring.contiguous();const auto chunk=dz::trace_chunk(segment.size(),fuel,spare);
        assert(chunk<=4096&&chunk<=segment.size());
        if(chunk) {
            assert(8*chunk+4096+spare<=fuel);
            for(unsigned i=0;i<chunk;++i)assert(segment[i]==reference[i]);
            const auto written=1+random()%chunk;partial+=written<chunk;
            wrapped+=ring.head+written>=ring.capacity;
            assert(ring.consume(written));for(unsigned i=0;i<written;++i)reference.pop_front();
        }
        const auto before=ring.size;assert(!ring.consume(before+1)&&ring.size==before);
    }
    assert(wrapped&&partial);
    while(!reference.empty()) {
        const auto segment=ring.contiguous();for(auto c:segment){assert(c==reference.front());reference.pop_front();}
        assert(ring.consume(segment.size()));
    }
    assert(ring.size==0&&ring.contiguous().empty()&&ring.last()==0);
    assert(dz::trace_chunk(ring.capacity,34096,30000)==0);
    assert(dz::trace_chunk(ring.capacity,100000,30000)==4096);
    std::cout<<"10000 independent trace-queue schedules; wrapped/partial writes and physical fuel bounds passed\n";
}
