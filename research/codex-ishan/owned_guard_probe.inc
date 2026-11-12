        if(cxowned_active&&cx_stage==0) {
            const int guard_capture=cxowned.captured_at;
            bc::end_turn(); // diagnostic only: a fresh ordinary charged budget for checks
            const int guard_start=bc::round_number();
            auto same_bytes=[](const void* aa,const void* bb,std::size_t size) {
                const auto* a=static_cast<const unsigned char*>(aa);
                const auto* b=static_cast<const unsigned char*>(bb);
                std::size_t i=0;
                for(;i+16<=size;i+=16)
                    if(wasm_i8x16_bitmask(wasm_i8x16_eq(wasm_v128_load(a+i),wasm_v128_load(b+i)))!=65535)return false;
                for(;i<size;++i)if(a[i]!=b[i])return false;
                return true;
            };
            std::array<unsigned char,sizeof(nn_lv)> graph_before;
            std::array<unsigned char,sizeof(nn_lf)> features_before;
            std::array<unsigned char,sizeof(nn_pub)> publication_before;
            std::memcpy(graph_before.data(),&nn_lv,sizeof(nn_lv));
            std::memcpy(features_before.data(),nn_lf,sizeof(nn_lf));
            std::memcpy(publication_before.data(),&nn_pub,sizeof(nn_pub));
            const std::size_t cache_bytes=nn_lv.cache.size()*sizeof(nn::CampCache);
            std::vector<unsigned char> cache_before(cache_bytes);
            if(cache_bytes)std::memcpy(cache_before.data(),nn_lv.cache.data(),cache_bytes);
            auto unchanged=[&]() {
                return same_bytes(graph_before.data(),&nn_lv,sizeof(nn_lv))&&
                    same_bytes(features_before.data(),nn_lf,sizeof(nn_lf))&&
                    same_bytes(publication_before.data(),&nn_pub,sizeof(nn_pub))&&
                    (!cache_bytes||same_bytes(cache_before.data(),nn_lv.cache.data(),cache_bytes))&&cxowned_active;
            };
            const int old_xround=nn_xround[0];nn_xround[0]=-123456;
            nn_x_refresh(0);
            const bool guard_x=nn_xround[0]==-123456&&unchanged();
            nn_xround[0]=old_xround;
            const int old_zstage=nn_zstage;nn_zstage=1;
            nn_run_stages(0,round);
            const bool guard_stage=nn_zstage==1&&unchanged();
            nn_zstage=old_zstage;
            std::array<int,4> old_rounds;std::copy(nn_xround,nn_xround+4,old_rounds.begin());
            std::fill(nn_xround,nn_xround+4,-123456);
            const auto old_round0=nn_round0;const auto old_mark=nn_mark;
            nn_round0=0;nn_mark=0; // exercise ownership,not the unrelated prior-overrun early return
            nn_turn_end();
            const bool guard_end=std::all_of(nn_xround,nn_xround+4,[](int x){return x==-123456;})&&unchanged();
            std::copy(old_rounds.begin(),old_rounds.end(),nn_xround);nn_round0=old_round0;nn_mark=old_mark;
            for(int i=0;i<3;++i)bc::end_turn(); // normal charged turns; expiry check uses actual engine round
            const int now=bc::round_number();
            cxowned_reset(w.groups.size(),w.bridges_on,now,A2_NN_LAZY_TTL);
            const bool guard_expire=now-guard_capture>A2_NN_LAZY_TTL&&!cxowned_active&&!cxowned.admitted;
            cxowned_active=cxowned.begin(nn_lf,nn_lv,w.groups.size(),now,nn_xdone==15);
            const bool recaptured_mode=cxowned_active;
            cxowned_reset(w.groups.size(),!w.bridges_on,now,A2_NN_LAZY_TTL);
            const bool guard_mode=recaptured_mode&&!cxowned_active&&!cxowned.admitted;
            cxowned_reset(w.groups.size(),w.bridges_on,now,A2_NN_LAZY_TTL);
            cxowned_active=cxowned.begin(nn_lf,nn_lv,w.groups.size(),now,nn_xdone==15);
            const bool recaptured_shape=cxowned_active;
            cxowned_reset(w.groups.size()+1,w.bridges_on,now,A2_NN_LAZY_TTL);
            const bool guard_shape=recaptured_shape&&!cxowned_active&&!cxowned.admitted;
            const bool guard_pub=same_bytes(publication_before.data(),&nn_pub,sizeof(nn_pub));
            std::printf("OWNED_GUARDS %u %d %d %d %d %u %d %d %d %d %d %d %d\n",my_id,static_cast<int>(type),guard_capture,
                guard_start,now,static_cast<unsigned>(w.groups.size()),guard_x,guard_stage,guard_end,guard_expire,guard_mode,guard_shape,guard_pub);
            bc::resign();return;
        }
