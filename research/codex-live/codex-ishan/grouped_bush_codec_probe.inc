static void codec_proof(){
    const auto start=bc::fuel_remaining();const auto r0=bc::round_number();
    World reference;reference.init();
    const auto terrain=reference.bushes.export_linear_buffer();
    const auto encoded=codex_bush_codec::encode(reference.width,reference.height,terrain);
    auto decoded=codex_bush_codec::decode(reference.width,reference.height,encoded.count,encoded.bytes,terrain);
    const auto encode_decode_cost=start-bc::fuel_remaining();
    const std::size_t n=static_cast<std::size_t>(reference.width)*reference.height;
    std::vector<std::uint16_t> labels(n,codex_bush_codec::absent);
    bc::bitboard labelled;int next=0,mismatch=0,mask_checks=0;
    if(!encoded.valid||!decoded.valid)++mismatch;
    for(std::size_t i=n;i>0;){
        --i;if(!codex_bush_codec::bit(terrain,i))continue;
        const vec2 p{static_cast<int>(i%reference.width),static_cast<int>(i/reference.width)};
        const int expected=reference.bush_cluster(p);
        if(!labelled.is_set(p)){
            if(!codex_bush_codec::publish(decoded,i,labels.data(),next,labelled))++mismatch;
            ++mask_checks;if(!(labelled^reference.bush_labeled).is_empty())++mismatch;
        }
        if(expected!=labels[i]||next!=reference.bush_clusters)++mismatch;
    }
    int rejected=0,tests=0;
    const auto reject=[&](const auto& bytes,unsigned count){++tests;if(!codex_bush_codec::decode(reference.width,reference.height,count,bytes,terrain).valid)++rejected;};
    auto extra=encoded.bytes;extra.push_back(0);reject(extra,encoded.count);
    if(!encoded.bytes.empty()){
        auto short_data=encoded.bytes;short_data.pop_back();reject(short_data,encoded.count);
        auto bad=encoded.bytes;bad[0]=0;reject(bad,encoded.count);
        reject(encoded.bytes,encoded.count+1);
    }else{std::vector<std::uint8_t> bad{1,0,1};reject(bad,1);}
    const auto cost=start-bc::fuel_remaining();
    std::printf("CODEC_PROOF %d %d %zu %u %zu %d %d %d %d %llu %llu %u\n",reference.width,reference.height,reference.groups.size(),encoded.count,encoded.bytes.size(),mismatch,mask_checks,rejected,tests,
        static_cast<unsigned long long>(encode_decode_cost),static_cast<unsigned long long>(cost),bc::round_number()-r0);
    std::printf("CODEC_BYTES ");for(auto b:encoded.bytes)std::printf("%02x",static_cast<unsigned>(b));std::printf("\n");
}
