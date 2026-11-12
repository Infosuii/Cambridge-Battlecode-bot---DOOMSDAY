    cxowned_reset(w.groups.size(),w.bridges_on,round,A2_NN_LAZY_TTL);
    bool cx_published=false;
    const bool cx_ready=nn_warm==2&&nn_xdone==15&&w.fields_ready();
    if(!cx_ready)cxowned_drop();
    if(cx_ready&&!cxowned_active&&cxowned_fits(cxowned_capture_cost,floor_f)) {
        const auto cx_start=bc::fuel_remaining();const auto cx_round=bc::round_number();
#if CODEX_FINE
        CODEX_FINE_MARK("owner_capture_begin",static_cast<int>(type),round,cxowned_capture_cost,floor_f);
#endif
        std::fill(nn_lf+kCOffL,nn_lf+kCOffL+kC*kCF,static_cast<std::int16_t>(0));
        std::fill(nn_lf+kG,nn_lf+kG+kS,static_cast<std::int16_t>(0));
        nn_feats_t<kC,kAF>(nn_lf,near_e,2|4);
        if(bc::round_number()==cx_round&&cxowned_fits(2000+sizeof(cxowned.features),floor_f)) {
            cxowned_active=cxowned.begin(nn_lf,nn_lv,w.groups.size(),round,nn_xdone==15);
#if CODEX_FINE
            cxowned_hash=cxowned.input_hash();
            CODEX_FINE_MARK("owner_captured",static_cast<int>(type),round,cxowned.captured_at,cxowned_active);
#endif
        }
        const auto cx_used=100000ull*(bc::round_number()-cx_round)+cx_start-bc::fuel_remaining();
        cxowned_learn(cxowned_capture_cost,cx_used);
        if(bc::round_number()!=cx_round)cxowned_drop();
    }
    while(cxowned_active&&cxowned.stage<5&&cxowned_fits(cxowned_cost[cxowned.stage],floor_f)) {
        const int cx_stage=cxowned.stage;
        const auto cx_start=bc::fuel_remaining();const auto cx_round=bc::round_number();
#if CODEX_FINE
        CODEX_FINE_MARK("owner_step_begin",static_cast<int>(type),round,cx_stage,cxowned_cost[cx_stage]);
#endif
        cxowned.advance();
        const auto cx_used=100000ull*(bc::round_number()-cx_round)+cx_start-bc::fuel_remaining();
        cxowned_learn(cxowned_cost[cx_stage],cx_used);
#if CODEX_FINE
        CODEX_FINE_MARK("owner_step_end",static_cast<int>(type),round,cx_stage,cx_used);
#endif
        if(bc::round_number()!=cx_round)cxowned_drop();
    }
    if(cxowned_active&&cxowned.ready()&&cxowned_fits(cxowned_publish_cost,floor_f)) {
        const auto cx_start=bc::fuel_remaining();const auto cx_round=bc::round_number();
        if(cxowned.fresh(round,A2_NN_LAZY_TTL)) {
            std::copy(cxowned.output.target,cxowned.output.target+kC+1,nn_lo.target);
            nn_pub=nn_make_pub(cxowned.features.data(),nn_lo.target,kC+1,kC,kCOffL,-1,cxowned.captured_at);
            ++nn_c_camps;cx_published=true;
#if CODEX_FINE
            CODEX_FINE_MARK("owner_published",static_cast<int>(type),round,cxowned.captured_at,cxowned.input_hash()==cxowned_hash);
            if(codex_trace::active&&cxowned.captured_at==CODEX_TARGET_ROUND)codex_trace::frame_published=true;
#endif
        }
        const auto cx_used=100000ull*(bc::round_number()-cx_round)+cx_start-bc::fuel_remaining();
        cxowned_learn(cxowned_publish_cost,cx_used);cxowned_drop();
    }
    if(cx_published)nn_path=1;else ++nn_c_hold,nn_path=0;
