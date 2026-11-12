inline Cache decode(int w,int h,unsigned count,const std::vector<std::uint8_t>& bytes,const std::vector<std::uint8_t>& terrain){
    Cache out;
    if(w<=0||h<=0||static_cast<std::uint64_t>(w)*h>65535)return out;
    const auto n=static_cast<std::size_t>(w)*h;
    if(terrain.size()!=(n+7)/8||count>n||count>=absent)return out;
    out.tile_count=static_cast<std::uint32_t>(n);out.published.assign(terrain.size(),0);out.starts.resize(count+1);
    out.runs.reserve(std::min(n,bytes.size()/2));std::size_t p=0;
    for(unsigned cid=0;cid<count;++cid){
        out.starts[cid]=static_cast<std::uint16_t>(out.runs.size());
        std::uint32_t runs=0;if(!get(bytes,p,runs)||!runs||runs>n)return Cache{};
        std::uint64_t last=0;
        for(std::uint32_t r=0;r<runs;++r){
            std::uint32_t gap=0,length=0;if(!get(bytes,p,gap)||!get(bytes,p,length)||!length)return Cache{};
            const std::uint64_t start=last+gap,end=start+length;
            if(end>n||out.runs.size()>=n)return Cache{};
            for(std::size_t b=start>>3;b<=((end-1)>>3);++b){
                const unsigned lo=static_cast<unsigned>(std::max<std::uint64_t>(start,8*b)-8*b);
                const unsigned hi=static_cast<unsigned>(std::min<std::uint64_t>(end,8*b+8)-8*b);
                const auto mask=static_cast<std::uint8_t>(((1u<<hi)-1)&~((1u<<lo)-1));
                if(out.published[b]&mask)return Cache{};out.published[b]|=mask;
            }
            out.runs.push_back({static_cast<std::uint16_t>(start),static_cast<std::uint16_t>(length),static_cast<std::uint16_t>(cid)});last=end;
        }
    }
    out.starts[count]=static_cast<std::uint16_t>(out.runs.size());
    if(p!=bytes.size()||out.published!=terrain)return Cache{};
    out.lookup.resize(out.runs.size());for(std::size_t i=0;i<out.lookup.size();++i)out.lookup[i]=static_cast<std::uint16_t>(i);
    std::sort(out.lookup.begin(),out.lookup.end(),[&](auto a,auto b){return out.runs[a].start<out.runs[b].start;});
    std::fill(out.published.begin(),out.published.end(),0);out.valid=true;return out;
}
template<class Board> inline bool publish(Cache& cache,std::size_t at,std::uint16_t* labels,int& next_id,Board& labelled){
    if(!cache.valid||at>=cache.tile_count)return false;
    const auto pos=std::upper_bound(cache.lookup.begin(),cache.lookup.end(),at,[&](auto value,auto i){return value<cache.runs[i].start;});
    if(pos==cache.lookup.begin())return false;
    const auto& found=cache.runs[*(pos-1)];
    if(at>=static_cast<std::size_t>(found.start)+found.length)return false;
    const unsigned cid=found.cid;if(cid+1>=cache.starts.size())return false;
    const auto id=static_cast<std::uint16_t>(next_id++);
    for(unsigned i=cache.starts[cid];i<cache.starts[cid+1];++i){
        const auto& r=cache.runs[i];const std::size_t start=r.start,end=start+r.length;
        std::fill(labels+start,labels+end,id);
        for(std::size_t b=start>>3;b<=((end-1)>>3);++b){
            const unsigned lo=static_cast<unsigned>(std::max(start,8*b)-8*b),hi=static_cast<unsigned>(std::min(end,8*b+8)-8*b);
            cache.published[b]|=static_cast<std::uint8_t>(((1u<<hi)-1)&~((1u<<lo)-1));
        }
    }
    labelled.import_linear_buffer(cache.published);return true;
}
