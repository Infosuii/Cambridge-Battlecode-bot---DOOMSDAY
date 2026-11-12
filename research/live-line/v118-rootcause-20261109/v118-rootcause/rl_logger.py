"""Verified RL recorder repair (NRZ/NRQ/NRL) copied verbatim from merge.sources(); applied to rollout actors only."""
from merge import replace

def patch(out):
    n=out['nnrec.cpp']
    n=replace(n,'static std::int16_t nn_zf[kNF] = {}, nn_zfp[kNF] = {};',
        'static std::int16_t nn_zf[kNF] = {}, nn_zfp[kNF] = {};\nstatic float nn_published_logits[kC+1] = {};')
    marker='                nn_pub = nn_make_pub(nn_lf, nn_lo.target, kC + 1, kC, kCOffL, -1, fast_at);'
    n=replace(n,marker,'''#if defined(A2_NN_RLIVE) && A2_NN_RLIVE
                debug_block({
                    std::copy(nn_lf, nn_lf+kNF, nn_zf);
                    std::copy(nn_lo.target, nn_lo.target+kC+1, nn_published_logits);
                    ++nn_zid;
                });
#endif
'''+marker)
    start=n.index('int Bot::nn_ens_sample(int v92g) {');end=n.index('\n#endif',start)
    # The first nested #ifdef occurs later; operate on the complete function span.
    end=n.index('\n    return out;\n}',start)+len('\n    return out;\n}')
    sampler=n[start:end]
    sampler=replace(sampler,'        float v[kC + 1];','''        float v[kC + 1];
#if defined(A2_NN_NNUE) && defined(A2_NN_LAZY) && !defined(A2_NN_LAZYFULL)
        // Fast work may already be building a different observation. Sample and
        // log the last committed policy, never a mixture of its inputs and scores.
        const auto* sample_features = nn_zf;
        const auto* sample_logits = nn_published_logits;
#else
        const auto* sample_features = nn_lf;
        const auto* sample_logits = nn_lo.target;
#endif''')
    sampler=sampler.replace('std::copy(nn_lo.target, nn_lo.target + kC + 1, v);','std::copy(sample_logits, sample_logits + kC + 1, v);')
    sampler=sampler.replace('nn_lf[kCOffL +','sample_features[kCOffL +')
    sampler=sampler.replace('std::copy(nn_lf, nn_lf + kNF, xn);','std::copy(sample_features, sample_features + kNF, xn);')
    logline='            std::printf("NRL %d %d %d %.5f %d %d %d %s\\n", round, slot, a, lp, chg ? 1 : 0, nn_zid, bs, b64(xn, kNF).c_str());'
    sampler=replace(sampler,logline,'''            // Preserve the actual sampled quantized distribution for PPO checks.
            std::printf("NRQ %d %u %s\\n", round, my_id,
                b64(reinterpret_cast<const std::int16_t*>(v), 2*(kC+1)).c_str());
'''+logline)
    n=n[:start]+sampler+n[end:];out['nnrec.cpp']=n
    return out
