// Included inside Bot::clna_explore after RNG initialization. Action is a
// TARGET COMMAND; fixed downstream executor may cancel/reassign it. It is not
// a claim of an executed movement/attack. No learned deterministic hold route.
#ifdef JD_NATIVE_ACTOR
{
    const int n = nn_pub.n;
    clna_round = -1; // no legacy end-of-turn CNX claim for command-action rows
    if (n < 0 || n > 10 || clna_snap.at != nn_pub.at || clna_snap.n != n ||
        bc::fuel_remaining() < JD_NATIVE_MIN) {
        ++clna_skips[2];
        return v92g; // parameter-independent handcrafted resource fallback
    }
    int groups[11], vslot = n;
    bool valid[11]; float native[11];
    for (int j=0;j<n;++j) {
        groups[j]=nn_pub.eg[j];native[j]=nn_pub.es[j];valid[j]=true;
        if(groups[j]==v92g)vslot=j;
        // Same newly-respawning exclusion as native rank selection; v92 command
        // remains available. Other support restrictions are state-only.
        if(groups[j]!=v92g && groups[j]>=0 && groups[j]<static_cast<int>(w.groups.size()) &&
           w.groups[groups[j]].state==GroupState::respawning && clna_snap.jd_state[j]!=static_cast<int>(GroupState::respawning))valid[j]=false;
    }
    groups[n]=v92g;native[n]=nn_pub.far;valid[n]=(vslot==n);
    double score[11],mx=-INFINITY;
    int arg=vslot;
    for(int j=0;j<=n;++j){
        score[j]=double(native[j])+(j==vslot?double(JD_NATIVE_BONUS):0.0);
        if(valid[j] && (score[j]>mx || (score[j]==mx && j==vslot)))mx=score[j],arg=j;
    }
    int chosen=arg; double prob=1.0;
#if !JD_NATIVE_DET
    double mass[11],total=0.0;
    for(int j=0;j<=n;++j)total+=(mass[j]=valid[j]?std::exp((score[j]-mx)/double(JD_NATIVE_TEMP)):0.0);
    const double u=clna_u01()*total;double accum=0.0;
    for(int j=0;j<=n;++j)if(valid[j]){chosen=j;accum+=mass[j];if(u<accum)break;}
    prob=mass[chosen]/total;
#endif
    ++clna_index;
#if JD_NATIVE_LOG
    // One bounded row per draw. Consumed native h1 is paired with the pointer;
    // no reconstruction from current x or a stale trunk-accumulator guess.
    char* o=clna_rstr(clna_rbuf,"JNP2 ");
    const int ids[]={round,slot,static_cast<int>(my_id),clna_index,v92g,ref,groups[chosen],n,nn_pub.at,clna_snap.jd_h1_at,static_cast<int>(bc::round_number())};
    for(int j=0;j<11;++j){o=clna_rint(o,ids[j]);*o++=' ';}
    o=clna_rdbl(o,prob);*o++=' ';o=clna_rf32(o,float(JD_NATIVE_TEMP));*o++=' ';o=clna_rf32(o,float(JD_NATIVE_BONUS));*o++=' ';
    o=clna_rh8(o,groups,n+1);*o++=' ';
    for(int j=0;j<=n;++j){*o++=valid[j]?'1':'0';}*o++=' ';
    for(int j=0;j<=n;++j)o=clna_rf32(o,native[j]);*o++=' ';
    const auto cap=[&]{return sizeof clna_rbuf-static_cast<std::size_t>(o-clna_rbuf);};
    o+=jd_codec::hex_simd(reinterpret_cast<const std::uint8_t*>(clna_snap.jd_h1),128,o,cap());*o++=' ';
    o+=jd_codec::hex_simd(reinterpret_cast<const std::uint8_t*>(&clna_snap.ec[0][0]),32*n,o,cap());
    *o++='\n';std::fwrite(clna_rbuf,1,static_cast<std::size_t>(o-clna_rbuf),stdout);
    // Immediate producer completion marker, before fixed downstream executor.
    o=clna_rstr(clna_rbuf,"JND1 "),o=clna_rint(o,static_cast<int>(my_id));*o++=' ';
    o=clna_rint(o,clna_index);*o++=' ';o=clna_rint(o,static_cast<int>(bc::round_number()));*o++=' ';
    o=clna_rint(o,static_cast<long>(bc::fuel_remaining()));*o++='\n';
    std::fwrite(clna_rbuf,1,static_cast<std::size_t>(o-clna_rbuf),stdout);
    std::fflush(stdout); // logging must complete before the command can affect the fixed executor
#endif
    return groups[chosen];
}
#endif
