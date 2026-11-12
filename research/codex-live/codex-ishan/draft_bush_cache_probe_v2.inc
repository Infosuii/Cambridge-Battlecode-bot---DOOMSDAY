static void cache_draft_proof(){
    const int w=bc::map::width(),h=bc::map::height();const auto groups=bc::map::camp_groups().size();
    std::array<std::uint8_t,codex_field_cache::end> memory{};
    bc::detail::check(bc::detail::sdk_read_draft_memory(0,memory.data(),memory.size()));
    const auto terrain=bc::map::bushes().export_linear_buffer();
    const auto read_cache=[&](const auto& m){return codex_draft_bush::decode(reinterpret_cast<const std::byte*>(m.data()),m.size(),w,h,groups,terrain);};
    auto decoded=read_cache(memory);int bad=0,rejected=0,tests=0,compared=0;
    if(codex_draft_bush::store_state==1){
        if(!decoded.valid||!codex_draft_bush::store_preserved)++bad;
        codex_draft_bush::Parts parts;
        if(!codex_draft_bush::parts(reinterpret_cast<const std::byte*>(memory.data()),memory.size(),w,h,groups,parts))++bad;
        const auto reject=[&](const auto& m){++tests;if(!read_cache(m).valid)++rejected;};
        for(const unsigned offset:{0u,4u,8u,10u,12u,14u,16u}){
            auto broken=memory;const auto value=codex_draft_bush::read_byte(reinterpret_cast<const std::byte*>(broken.data()),parts,offset);
            codex_draft_bush::put_byte(broken.data(),parts,offset,static_cast<std::uint8_t>(value^127));reject(broken);
        }
        auto broken=memory;broken[codex_field_cache::offset+10]^=127;reject(broken);
        broken=memory;broken[codex_field_cache::offset+4]^=127;reject(broken);
        broken=memory;for(std::size_t i=0;i<parts.size();++i)codex_draft_bush::put_byte(broken.data(),parts,i,0);reject(broken);
        auto huge=codex_bush_codec::Payload{};huge.valid=true;huge.bytes.resize(parts.size(),0);
        broken=memory;++tests;if(!codex_draft_bush::write_payload(broken.data(),broken.size(),w,h,groups,huge)&&broken==memory)++rejected;
        ++tests;if(!codex_draft_bush::decode(reinterpret_cast<const std::byte*>(memory.data()),memory.size()-1,w,h,groups,terrain).valid)++rejected;
        // Start with one complete original component already labelled, then load the cached description.
        World reference;reference.init();reference.codex_bush_checked=true;
        const std::size_t n=static_cast<std::size_t>(w)*h;
        std::vector<std::uint16_t> labels(n,codex_bush_codec::absent);
        for(std::size_t i=n;i>0;){--i;if(!codex_bush_codec::bit(terrain,i))continue;reference.bush_cluster({static_cast<int>(i%w),static_cast<int>(i/w)});break;}
        auto prior=reference.bush_labeled.export_linear_buffer();
        for(std::size_t i=0;i<n;++i)if(codex_bush_codec::bit(prior,i))labels[i]=reference.bush_label[i];
        decoded.published=prior;bc::bitboard labelled=reference.bush_labeled;int next=reference.bush_clusters;
        for(std::size_t i=n;i>0;){
            --i;if(!codex_bush_codec::bit(terrain,i))continue;
            const vec2 p{static_cast<int>(i%w),static_cast<int>(i/w)};
            const int expected=reference.bush_cluster(p);
            if(!labelled.is_set(p)){
                if(!codex_bush_codec::publish(decoded,i,labels.data(),next,labelled))++bad;
                if(!(labelled^reference.bush_labeled).is_empty())++bad;
            }
            ++compared;if(labels[i]!=expected||next!=reference.bush_clusters)++bad;
        }
        if(rejected!=tests)++bad;
    }else if(decoded.valid)++bad;
    std::printf("DRAFT_BUSH_PROOF %d %d %zu %d %d %d %d %d %d %llu\n",w,h,groups,codex_draft_bush::store_state,decoded.valid,bad,rejected,tests,compared,
        static_cast<unsigned long long>(codex_draft_bush::store_before-codex_draft_bush::store_after));
}
static void cache_play_proof(){
    World actual;actual.width=bc::map::width();actual.height=bc::map::height();actual.bushes=bc::map::bushes();actual.groups.resize(bc::map::camp_groups().size());
    const std::size_t n=static_cast<std::size_t>(actual.width)*actual.height;
    actual.bush_label.reset(new std::uint16_t[n]);
    codex_draft_bush::Parts parts;
    const auto* memory=bc::draft_memory.data();const auto size=bc::draft_memory.size();
    bool present=codex_draft_bush::parts(memory,size,actual.width,actual.height,actual.groups.size(),parts);
    if(present){std::array<std::uint8_t,sizeof(codex_draft_bush::Header)> raw{};for(std::size_t i=0;i<raw.size();++i)raw[i]=codex_draft_bush::read_byte(memory,parts,i);codex_draft_bush::Header h{};std::memcpy(&h,raw.data(),sizeof(h));present=h.magic==codex_draft_bush::magic;}
    int loaded=0,id=-1;std::uint64_t cost=0;const auto r0=bc::round_number();
    if(present){
        const auto terrain=actual.bushes.export_linear_buffer();std::size_t root=0;while(root<n&&!codex_bush_codec::bit(terrain,root))++root;
        if(root<n){const auto f=bc::fuel_remaining();const auto call_round=bc::round_number();id=actual.bush_cluster({static_cast<int>(root%actual.width),static_cast<int>(root/actual.width)});cost=100000ull*(bc::round_number()-call_round)+f-bc::fuel_remaining();loaded=actual.codex_bush_cache.valid&&id==0&&actual.bush_clusters==1;}
        else loaded=codex_draft_bush::decode(memory,size,actual.width,actual.height,actual.groups.size(),terrain).valid;
    }
    std::printf("PLAY_BUSH_PROOF %d %d %d %llu %u\n",present,loaded,id,static_cast<unsigned long long>(cost),bc::round_number()-r0);
}
