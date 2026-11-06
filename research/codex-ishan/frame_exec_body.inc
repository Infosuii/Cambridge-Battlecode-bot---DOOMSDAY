    cxframe_reset(w.groups.size(),w.bridges_on);
    bool cx_published=false;
    if(cxframe_pending&&(round-cxframe.captured_at>A2_NN_LAZY_TTL||cxframe.captured_at>round))cxframe_pending=false;
    const bool cx_ready=nn_warm==2&&nn_xdone==15&&w.fields_ready();
    if(!cx_ready)cxframe_pending=false;
    if(cx_ready&&!cxframe_pending&&cxframe_fits(cxframe_capture_cost,floor_f)) {
        const auto cx_start=bc::fuel_remaining();const auto cx_round=bc::round_number();
#if CODEX_FINE
        CODEX_FINE_MARK("frame_capture_begin",static_cast<int>(type),round,cxframe_capture_cost,floor_f);
#endif
        std::fill(nn_lf+kCOffL,nn_lf+kCOffL+kC*kCF,static_cast<std::int16_t>(0));
        std::fill(nn_lf+kG,nn_lf+kG+kS,static_cast<std::int16_t>(0));
        nn_feats_t<kC,kAF>(nn_lf,near_e,2|4);
        if(bc::round_number()==cx_round&&cxframe_fits(cxframe_copy_bound(w.groups.size()),floor_f)) {
            cxframe_pending=cxframe.begin(nn_lf,nn_lv,w.groups.size(),round,nn_xdone==15);
#if CODEX_FINE
            cxframe_hash=cxframe.input_hash();
            CODEX_FINE_MARK("frame_captured",static_cast<int>(type),round,cxframe.captured_at,cxframe_pending);
#endif
        }
        const auto cx_now=bc::fuel_remaining();
        const auto cx_used=100000ull*(bc::round_number()-cx_round)+cx_start-cx_now;
        cxframe_learn(cxframe_capture_cost,cx_used);
        if(bc::round_number()!=cx_round)cxframe_pending=false;
    }
    while(cxframe_pending&&cxframe.stage<5&&cxframe_fits(cxframe_cost[cxframe.stage],floor_f)) {
        const int cx_stage=cxframe.stage;
        const auto cx_start=bc::fuel_remaining();const auto cx_round=bc::round_number();
#if CODEX_FINE
        CODEX_FINE_MARK("frame_step_begin",static_cast<int>(type),round,cx_stage,cxframe_cost[cx_stage]);
#endif
        cxframe.advance();
        const auto cx_used=100000ull*(bc::round_number()-cx_round)+cx_start-bc::fuel_remaining();
        cxframe_learn(cxframe_cost[cx_stage],cx_used);
#if CODEX_FINE
        CODEX_FINE_MARK("frame_step_end",static_cast<int>(type),round,cx_stage,cx_used);
#endif
        if(bc::round_number()!=cx_round)cxframe_pending=false;
    }
    if(cxframe_pending&&cxframe.ready()&&cxframe_fits(cxframe_publish_cost,floor_f)) {
        const auto cx_start=bc::fuel_remaining();const auto cx_round=bc::round_number();
        if(cxframe.fresh(round,A2_NN_LAZY_TTL)) {
            std::copy(cxframe.output.target,cxframe.output.target+kC+1,nn_lo.target);
            nn_pub=nn_make_pub(cxframe.features.data(),nn_lo.target,kC+1,kC,kCOffL,-1,cxframe.captured_at);
            // Target encoders own these caches; retain all live slow blocks/trunk/head state.
            nn_lv.cache=cxframe.work.cache;nn_lv.sc=cxframe.work.sc;
            ++nn_c_camps;cx_published=true;
#if CODEX_FINE
            CODEX_FINE_MARK("frame_published",static_cast<int>(type),round,cxframe.captured_at,cxframe.input_hash()==cxframe_hash);
            if(codex_trace::active&&cxframe.captured_at==CODEX_TARGET_ROUND)codex_trace::frame_published=true;
#endif
        }
        const auto cx_used=100000ull*(bc::round_number()-cx_round)+cx_start-bc::fuel_remaining();
        cxframe_learn(cxframe_publish_cost,cx_used);cxframe_pending=false;
    }
    if(cx_published)nn_path=1;else ++nn_c_hold,nn_path=0;
