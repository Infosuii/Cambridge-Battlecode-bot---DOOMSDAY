#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

namespace dz {
// Restricted, SDK-free primitives. They do not estimate routes, combat, crews,
// survival or contest probability, and are not used by production decisions.
enum class QuoteStatus { Supported, Unsupported, Invalid };
struct DelayQuote {
    QuoteStatus status=QuoteStatus::Invalid;
    int rounds=0;
    bool supported() const { return status==QuoteStatus::Supported; }
};
enum class CapturePhase { Unavailable, AllyActive, Contested, EnemyActive, Available };
// Sample at the champion's own turn, with all members defeated. The caller must
// establish that this is the same sole capturer, staying on-site throughout.
// Available has not initialized the capturer's configured duration yet; its
// reported timer may still be the generic 5, even with a Capture emblem.
inline DelayQuote solo_capture_delay(CapturePhase phase,int live_timer,int configured,
                                     bool same_solo_capturer,bool onsite) {
    if (live_timer<0||live_timer>2000||configured<1||configured>=2000) return {};
    if (!same_solo_capturer||!onsite) return {QuoteStatus::Unsupported,0};
    switch (phase) {
    case CapturePhase::Available: return {QuoteStatus::Supported,configured+1};
    case CapturePhase::AllyActive:
        if (live_timer<1||live_timer>configured) return {};
        return {QuoteStatus::Supported,live_timer};
    case CapturePhase::Unavailable:
    case CapturePhase::Contested:
    case CapturePhase::EnemyActive: return {QuoteStatus::Unsupported,0};
    }
    return {};
}
// Runtime settings and a single effective Tribute magnitude. Float multiplication
// is intentional: widening 0.1f before multiplying an exact-decade bag can add
// a spurious round. The magnitude applies after the base duration is rounded.
inline DelayQuote tribute_delay(std::uint32_t bag,int fixed,int minimum,float per_gem,float reduction) {
    if (!bag||bag>1000000||fixed<0||fixed>2000||minimum<1||minimum>2000||
        !std::isfinite(per_gem)||per_gem<0||per_gem>2000||
        !std::isfinite(reduction)||reduction<0||reduction>=1) return {};
    const float raw=static_cast<float>(bag)*per_gem;
    if (!std::isfinite(raw)||raw>2000-fixed) return {QuoteStatus::Unsupported,0};
    const int base=std::max(minimum,fixed+static_cast<int>(std::ceil(raw)));
    const float reduced=static_cast<float>(base)*(1.f-reduction);
    return {QuoteStatus::Supported,std::max(minimum,static_cast<int>(std::ceil(reduced)))};
}
enum class RewardKind { GemCluster, GoldCluster, Wolf, Unsupported };
struct RewardQuote {
    QuoteStatus status=QuoteStatus::Invalid;
    std::uint64_t gems=0,gold_min=0,gold_max=0;
    int next_remainder=-1;
    bool supported() const { return status==QuoteStatus::Supported; }
};
// Single recipient, current pinned +25% Prospector and +33% Vesper only.
// Mixed groups, splitting, Treasure, other heroes and duplicate-family effects
// must be rejected by the caller. A denominator of 400 reproduces the tested
// sequences; it is not a claim about internal engine storage.
// Remainder -1 means unknown history: retain a one-unit interval, never invent
// an exact award. Integer purchases preserve a known remainder; death/unknown
// rewards must invalidate it until their effects have been verified.
inline RewardQuote solo_reward(RewardKind kind,std::uint32_t gems,std::uint32_t gold,
                               bool prospector,bool vesper,int remainder=-1) {
    if (remainder< -1||remainder>=400) return {};
    bool cluster=false;
    switch (kind) {
    case RewardKind::GemCluster: if (gold) return {}; cluster=true; break;
    case RewardKind::GoldCluster: if (gems) return {}; cluster=true; break;
    case RewardKind::Wolf: break;
    case RewardKind::Unsupported: return {QuoteStatus::Unsupported};
    default: return {};
    }
    const std::uint64_t factor=prospector&&cluster?5:4;
    const auto gem_award=static_cast<std::uint64_t>(gems)*factor/4;
    const auto units=static_cast<std::uint64_t>(gold)*factor*(vesper?133:100);
    if (remainder<0) return {QuoteStatus::Supported,gem_award,units/400,(units+399)/400,-1};
    const auto total=units+static_cast<unsigned>(remainder);
    return {QuoteStatus::Supported,gem_award,total/400,total/400,static_cast<int>(total%400)};
}
}
