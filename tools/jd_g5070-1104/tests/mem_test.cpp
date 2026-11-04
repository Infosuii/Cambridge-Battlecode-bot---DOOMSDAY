// Host fixtures for bots/jd-g5070-1104/src/jd_mem.h (the shared-word codec and draft-buffer owner/merge).
// Build: g++ -std=c++20 -O2 -Wall -Wextra -Werror -I bots/jd-g5070-1104/src tools/jd_g5070-1104/tests/mem_test.cpp
// Each FINDING line is a measured property of the current (v92) schema that MEMORY_SCHEMA.md cites.
#include <cstdio>
#include <cstring>
#include <vector>

#include "jd_mem.h"

using namespace jdmem;

static int fails = 0, checks = 0;
#define CHECK(cond)                                                                                                    \
    do {                                                                                                               \
        ++checks;                                                                                                      \
        if (!(cond)) {                                                                                                 \
            ++fails;                                                                                                   \
            std::printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #cond);                                                 \
        }                                                                                                              \
    } while (0)

// SDK draft-memory host model: a prefix submit overwrites [0, n) (truncated to capacity) and keeps the rest; the
// startup snapshot is captured once per VM and never changes.
struct DraftHost {
    std::uint8_t bytes[kDraftBytes] = {};
    void submit(const std::uint8_t* p, std::size_t n) {
        if (n > kDraftBytes) n = kDraftBytes;
        std::memcpy(bytes, p, n);
    }
};

static void test_claim_roundtrip() {
    // Every slot x every code: set_code/get_code round-trip and every other bit is preserved.
    const std::uint64_t patterns[] = {0, ~std::uint64_t{0}, 0x5A5A5A5A5A5A5A5Aull, 0xF0F0F0F0F0F0F0F0ull,
        set_event(all_idle(), 77, 201), set_sighting(all_idle(), 99, 98, 63, true)};
    for (std::uint64_t base : patterns)
        for (int s = 0; s < kClaimSlots; ++s)
            for (std::uint64_t c = 0; c <= kClaimMask; ++c) {
                const std::uint64_t w = set_code(base, s, c);
                CHECK(get_code(w, s) == c);
                const std::uint64_t keep = ~(kClaimMask << (s * kClaimBits));
                CHECK((w & keep) == (base & keep));
            }
    // Out-of-range slots never write (bodies beyond 6 have no slot).
    CHECK(set_code(0x1234, 6, 5) == 0x1234 && set_code(0x1234, -1, 5) == 0x1234);
    // Group/dead/idle/onsite encodings decode back to what was claimed.
    for (int ng = 1; ng <= 200; ++ng) {
        const bool onsite_ok = ng <= kOnsiteGroups;
        for (int g = 0; g < ng; ++g) {
            const Claim c = decode_code(claim_code(g, false, onsite_ok), onsite_ok, ng);
            if (g < static_cast<int>(kCodeDead)) CHECK(c.kind == Kind::group && c.group == g && !c.onsite);
            else CHECK(c.kind == Kind::idle); // dropped, not aliased
            if (onsite_ok) {
                const Claim o = decode_code(claim_code(g, true, true), true, ng);
                CHECK(o.kind == Kind::group && o.group == g && o.onsite);
            }
        }
        CHECK(decode_code(claim_code(-2, false, onsite_ok), onsite_ok, ng).kind == Kind::dead);
        CHECK(decode_code(claim_code(-1, false, onsite_ok), onsite_ok, ng).kind == Kind::idle);
    }
}

static void test_reserved_collisions() {
    // Largest maps: which group ids lose their claim, and does any code alias another group's or an order code?
    int first_drop = -1, aliased = 0, order_alias = 0;
    for (int ng = 1; ng <= 255; ++ng) {
        const bool onsite_ok = ng <= kOnsiteGroups;
        for (int g = 0; g < ng; ++g) {
            const Claim c = decode_code(claim_code(g, false, onsite_ok), onsite_ok, ng);
            if (c.kind == Kind::group && c.group != g) ++aliased;
            if (c.kind == Kind::order) ++order_alias;
            if (!representable(g, ng) && first_drop < 0) first_drop = g;
        }
        // Fight orders exist only with < 112 groups; then no group id reaches 112, so 112-118 are free.
        if (ng < kOrderMaxGroups)
            for (int k = kOrderBase; k <= kOrderLast; ++k) CHECK(decode_code(static_cast<std::uint64_t>(k), onsite_ok, ng).kind == Kind::order);
    }
    CHECK(aliased == 0);
    CHECK(order_alias == 0);
    CHECK(first_drop == static_cast<int>(kCodeDead)); // groups 126+ are published as idle (claim lost)
    int dropped_255 = 0;
    for (int g = 0; g < 255; ++g) dropped_255 += !representable(g, 255);
    std::printf("FINDING claims: no group aliases another or an order code for 1..255 groups; groups >= %d are published "
                "as idle (on a 255-group map %d ids lose their claim); onsite marks only with <= %d groups\n",
        first_drop, dropped_255, kOnsiteGroups);
}

static void test_sighting_age_wrap() {
    // A sighting published at round 100 and never overwritten: the current mod-64 rule reads it as fresh again.
    std::uint64_t w = set_sighting(all_idle(), 30, 40, 100, false);
    int phantom_rounds = 0, first_phantom = -1;
    SightClock clock;
    int clock_phantoms = 0;
    for (int r = 100; r <= 400; ++r) {
        const Sighting s = read_sighting(w, r);
        if (r - 100 > kSightAgeLimit && s.present) {
            ++phantom_rounds;
            if (first_phantom < 0) first_phantom = r;
        }
        const int a = clock.age(w, r);
        CHECK(a == r - 100); // the reader's own clock keeps the true age
        if (r - 100 > kSightAgeLimit && a <= kSightAgeLimit) ++clock_phantoms;
    }
    CHECK(first_phantom == 164);
    CHECK(phantom_rounds == 4 * (kSightAgeLimit + 1));
    CHECK(clock_phantoms == 0);
    std::printf("FINDING sighting: an unchanged sighting reads fresh again %d times in 300 rounds (first at +%d rounds); "
                "SightClock (JD_SIGHTAGE) reads 0\n", phantom_rounds, first_phantom - 100);
    // A new publication resets the clock; claims written between reads do not.
    w = set_code(w, 2, 17);
    CHECK(clock.age(w, 401) == 301);
    w = set_sighting(w, 31, 40, 402, false);
    CHECK(clock.age(w, 402) == 0 && clock.age(w, 405) == 3);
    CHECK(get_code(w, 2) == 17); // sighting writes preserve claims
    // Distress bit is part of the sighting and survives claim writes.
    w = set_code(set_sighting(all_idle(), 1, 2, 7, true), 0, 3);
    CHECK(read_sighting(w, 9).distress && read_sighting(w, 9).age == 2);
    CHECK(!read_sighting(all_idle(), 5).present); // nothing published
}

static void test_event_phantom() {
    // Group 5's ready round 130, published at round 100 and left in the word.
    std::uint64_t w = set_event(all_idle(), 5, 130);
    CHECK(is_event(w) && event_group(w) == 5);
    CHECK(event_ready(w, 100) == 130 && event_ready(w, 129) == 130 && event_ready(w, 194) == 130);
    int phantom_turns = 0, worst_ahead = 0, first_phantom = -1;
    for (int r = 101; r <= 600; ++r) {
        const int ready = event_ready(w, r);
        if (ready > r && ready != 130) {
            ++phantom_turns;
            if (first_phantom < 0) first_phantom = r;
            worst_ahead = ready - r > worst_ahead ? ready - r : worst_ahead;
        }
    }
    CHECK(first_phantom == 195);
    CHECK(worst_ahead == 191);
    // X1_RESPAWNFIX-style bound alone (ready <= round + 160) still lets phantoms through.
    int bounded = 0;
    for (int r = 101; r <= 600; ++r) {
        const int ready = event_ready(w, r);
        bounded += ready > r && ready != 130 && ready <= r + 160;
    }
    CHECK(bounded > 0);
    // EventOnce (JD_EVTONCE): applied once at publication, never again while the word is unchanged.
    EventOnce once;
    int applied = 0;
    for (int r = 100; r <= 600; ++r) applied += once.accept(w, r, 160);
    CHECK(applied == 1);
    // A different event (or a sighting in between, then the same event again) is accepted anew.
    CHECK(once.accept(set_event(w, 6, 140), 601, 160));
    CHECK(!once.accept(set_event(w, 6, 140), 602, 160));
    // Claims written between reads do not make an old event look new.
    EventOnce o2;
    CHECK(o2.accept(w, 100, 160));
    CHECK(!o2.accept(set_code(w, 3, 9), 101, 160));
    // Limitation: a reader that first sees the word after it wrapped (dead from before publication until round 300)
    // decodes ready 386 (+86 rounds) and the 160-round horizon cannot tell. The horizon only rejects the >160 cases.
    EventOnce o3;
    CHECK(o3.accept(w, 300, 160) && event_ready(w, 300) == 386);
    EventOnce o4;
    CHECK(!o4.accept(w, 205, 160)); // 205 -> ready 386 (+181): rejected by the horizon
    std::printf("FINDING events: an unchanged respawn event decodes as a future respawn on %d of 500 later turns "
                "(from +%d rounds, up to %d rounds ahead); a 160-round bound alone still passes %d; EventOnce applies it once\n",
        phantom_turns, first_phantom - 100, worst_ahead, bounded);
}

static void test_draft_regions() {
    DraftHost host;
    // Brain header the way record_draft writes it (prefix 6), roster the way economy_record_roster writes it.
    std::uint8_t cur[kDraftBytes];
    const std::uint8_t brain[6] = {kBrainMagic, 5, 2, 5, 40, 3};
    std::memcpy(cur, host.bytes, kDraftBytes);
    host.submit(cur, merge(cur, kDraftBytes, kBrain, brain, 6));
    std::uint8_t ros[8];
    const int picks5[] = {1, 3, 6, 0, 2}; // vesper, cassi+issac, marcella, ryth, vendetta -> 6 bodies
    CHECK(encode_roster(picks5, 5, ros) == 6);
    std::memcpy(cur, host.bytes, kDraftBytes);
    host.submit(cur, merge(cur, kDraftBytes, kRoster, ros, 8));
    CHECK(read_brain(host.bytes, kDraftBytes).valid && read_brain(host.bytes, kDraftBytes).team_size == 5);
    int types[kMaxBodies] = {};
    CHECK(read_roster(host.bytes, kDraftBytes, 6, types) == 6);
    CHECK(types[0] == 1 && types[1] == kTypeCassi && types[2] == kTypeIssac && types[3] == 7 && types[4] == 0 && types[5] == 2);
    // Region bounds: oversized payloads are refused, nothing is submitted.
    std::uint8_t big[9] = {};
    std::memcpy(cur, host.bytes, kDraftBytes);
    CHECK(merge(cur, kDraftBytes, kRoster, big, 9) == 0);
    CHECK(merge(cur, kDraftBytes, kBrain, big, 7) == 0);
    CHECK(merge(cur, 1000, kRoster, ros, 8) == 0); // truncated host buffer
    // ML plan + DPLAN in one draft turn, as draft.cpp orders them (ML at the last pick, then DPLAN, then the header).
    // Current writers: ML submits 8 bytes (zeros + byte 7), DPLAN submits 8 zero bytes + plan, header submits 6.
    {
        DraftHost h;
        std::vector<std::uint8_t> ml(8, 0);
        ml[7] = kMlFlag | 3;
        h.submit(ml.data(), ml.size());
        std::vector<std::uint8_t> dp(8, 0);
        for (int i = 0; i < 20; ++i) dp.push_back(static_cast<std::uint8_t>(i + 1));
        h.submit(dp.data(), dp.size());
        h.submit(brain, 6);
        CHECK(read_ml_plan(h.bytes, kDraftBytes) == -1); // the DPLAN write erased the ML plan byte
        // Same sequence through the owner/merge: every region survives.
        DraftHost m;
        std::uint8_t c2[kDraftBytes];
        const std::uint8_t mlb = kMlFlag | 3;
        std::memcpy(c2, m.bytes, kDraftBytes);
        m.submit(c2, merge(c2, kDraftBytes, kMlPlan, &mlb, 1));
        std::memcpy(c2, m.bytes, kDraftBytes);
        m.submit(c2, merge(c2, kDraftBytes, kDPlan, dp.data() + 8, 20));
        std::memcpy(c2, m.bytes, kDraftBytes);
        m.submit(c2, merge(c2, kDraftBytes, kBrain, brain, 6));
        CHECK(read_ml_plan(m.bytes, kDraftBytes) == 3);
        CHECK(m.bytes[8] == 1 && m.bytes[27] == 20 && read_brain(m.bytes, kDraftBytes).valid);
        std::printf("FINDING draft: with A2_MLPLAN and A2_DPLAN both on, the DPLAN write erases the ML plan byte 7 "
                    "(latent: both default off); merge() keeps all regions\n");
    }
    // Stale-snapshot merge: a writer that starts from its VM's startup snapshot (bc::draft_memory) instead of the
    // current host bytes overwrites what an earlier draft turn wrote this game.
    {
        DraftHost h;
        const std::uint8_t snapshot[kDraftBytes] = {}; // captured at VM start, before any draft write
        h.submit(brain, 6);                             // draft turn 1 header
        std::uint8_t stale[kDraftBytes];
        std::memcpy(stale, snapshot, kDraftBytes);
        stale[1008] = kRosterMagic;
        h.submit(stale, 1016);                          // turn 2 roster from the stale snapshot
        CHECK(!read_brain(h.bytes, kDraftBytes).valid); // header lost
        DraftHost g;
        g.submit(brain, 6);
        std::uint8_t c3[kDraftBytes];
        std::memcpy(c3, g.bytes, kDraftBytes); // current host bytes (what economy_record_roster reads)
        g.submit(c3, merge(c3, kDraftBytes, kRoster, ros, 8));
        CHECK(read_brain(g.bytes, kDraftBytes).valid && read_roster(g.bytes, kDraftBytes, 6, types) == 6);
    }
}

static void test_payload_validation() {
    std::uint8_t b[kDraftBytes] = {};
    // Absent payload: nothing written -> invalid header, no roster, no plan.
    CHECK(!read_brain(b, kDraftBytes).valid && read_ml_plan(b, kDraftBytes) == -1);
    int types[kMaxBodies];
    CHECK(read_roster(b, kDraftBytes, 5, types) == 0);
    // Truncated buffers.
    const std::uint8_t hdr[6] = {kBrainMagic, 4, 1, 3, 25, 1};
    std::memcpy(b, hdr, 6);
    CHECK(!read_brain(b, 3).valid);
    CHECK(read_brain(b, 4).valid && read_brain(b, 4).max_group == 0);
    CHECK(read_brain(b, 5).max_group == 25 && !read_brain(b, 5).race);
    CHECK(read_brain(b, 6).race);
    const int picks[] = {0, 1, 2, 5};
    std::uint8_t ros[8];
    encode_roster(picks, 4, ros);
    std::memcpy(b + 1008, ros, 8);
    CHECK(read_roster(b, 1015, 4, types) == 0 && read_roster(b, 1016, 4, types) == 4);
    // Corrupt: wrong magic, impossible team size or class, roster body count != this game's bodies.
    b[0] = 0xA4;
    CHECK(!read_brain(b, kDraftBytes).valid);
    b[0] = kBrainMagic, b[1] = 9;
    CHECK(!read_brain(b, kDraftBytes).valid);
    b[1] = 4, b[3] = 7;
    CHECK(!read_brain(b, kDraftBytes).valid);
    b[3] = 3;
    CHECK(read_roster(b, kDraftBytes, 5, types) == 0);
    b[1009] = 7;
    CHECK(read_roster(b, kDraftBytes, 7, types) == 0);
    // Map mismatch: the header's class must equal the class recomputed from this map; the current reader trusts it.
    b[1009] = 4;
    const Brain br = read_brain(b, kDraftBytes);
    CHECK(br.valid && br.cls == 3);
    CHECK(map_class(60, 60, 4) == 3 && map_class(40, 40, 4) == 2);
    CHECK(br.cls != map_class(40, 40, 4)); // detectable mismatch on a 40x40 map
}

static void test_team_sizes_and_recovery() {
    // All team sizes 3-5 plus Cassi+Issac (6 bodies), first and last pick positions: each body slot rebuilds its
    // role/intent from the draft bytes and the shared word alone.
    for (int size = 3; size <= 5; ++size)
        for (int ci_at = -1; ci_at < size; ++ci_at) { // -1 = no Cassi+Issac pick, else its pick position
            int picks[5];
            for (int i = 0; i < size; ++i) picks[i] = (i == ci_at) ? kDraftCassiIssac : (i < 3 ? i : i + 2);
            std::uint8_t ros[8];
            const int bodies = encode_roster(picks, size, ros);
            CHECK(bodies == size + (ci_at >= 0 ? 1 : 0));
            CHECK(bodies <= kMaxBodies);
            DraftHost host;
            std::uint8_t cur[kDraftBytes];
            const std::uint8_t brain[6] = {kBrainMagic, static_cast<std::uint8_t>(size), 1,
                static_cast<std::uint8_t>(map_class(80, 80, size)), 30, 0};
            // First pick writes the header, last pick writes header + roster (order of draft turns).
            std::memcpy(cur, host.bytes, kDraftBytes);
            host.submit(cur, merge(cur, kDraftBytes, kBrain, brain, 6));
            std::memcpy(cur, host.bytes, kDraftBytes);
            host.submit(cur, merge(cur, kDraftBytes, kRoster, ros, 8));
            std::memcpy(cur, host.bytes, kDraftBytes);
            host.submit(cur, merge(cur, kDraftBytes, kBrain, brain, 6));
            // Shared word: body s claims group 10+s, body 0 is dead, the last body is on site at group 3.
            std::uint64_t w = all_idle();
            for (int s = 0; s < bodies; ++s) w = set_code(w, s, claim_code(10 + s, false, true));
            w = set_code(w, 0, claim_code(-2, false, true));
            w = set_code(w, bodies - 1, claim_code(3, true, true));
            w = set_sighting(w, 12, 13, 50, false);
            int types[kMaxBodies] = {};
            CHECK(read_roster(host.bytes, kDraftBytes, bodies, types) == bodies);
            const Brain b = read_brain(host.bytes, kDraftBytes);
            CHECK(b.valid && b.team_size == size && b.cls == map_class(80, 80, size));
            for (int s = 0; s < bodies; ++s) {
                const Claim c = decode_code(get_code(w, s), true, 40);
                if (s == 0) CHECK(c.kind == Kind::dead);
                else if (s == bodies - 1) CHECK(c.kind == Kind::group && c.group == 3 && c.onsite);
                else CHECK(c.kind == Kind::group && c.group == 10 + s);
                if (ci_at >= 0) {
                    // the two bodies of the Cassi+Issac pick sit at consecutive slots starting at its pick position
                    CHECK(types[ci_at] == kTypeCassi && types[ci_at + 1] == kTypeIssac);
                }
            }
            // Unused slots of a smaller team stay idle.
            for (int s = bodies; s < kClaimSlots; ++s) CHECK(decode_code(get_code(w, s), true, 40).kind == Kind::idle);
            CHECK(read_sighting(w, 52).present && read_sighting(w, 52).x == 12);
        }
    // 5 picks with Cassi+Issac fill all 6 slots: no spare slot for multiplexing.
    const int p6[] = {kDraftCassiIssac, 0, 1, 2, 5};
    std::uint8_t r6[8];
    CHECK(encode_roster(p6, 5, r6) == kClaimSlots);
    std::printf("FINDING slots: 5 picks with Cassi+Issac use all %d claim slots; without the V58 roster (default off) "
                "unseen allies' body types are unknown at init (bot.cpp falls back to vesper_vale)\n", kClaimSlots);
}

static void test_rmw_turn_order() {
    // Read-modify-write from the latest host word: two bodies writing in one round keep each other's fields.
    std::uint64_t host = all_idle();
    const std::uint64_t a_snapshot = host; // body A's turn-start copy (Bot::shared)
    host = set_code(host, 1, 20);          // body B writes first this round
    // A writes from the latest host word (bot.cpp write_claim reads read_shared() first): B's claim survives.
    std::uint64_t latest = set_code(host, 0, 7);
    CHECK(get_code(latest, 1) == 20 && get_code(latest, 0) == 7);
    // A writing from its stale turn-start copy would erase B's claim.
    const std::uint64_t stale = set_code(a_snapshot, 0, 7);
    CHECK(get_code(stale, 1) == kCodeIdle);
    // A sighting write after claims keeps all claims; a claim write keeps the sighting.
    latest = set_sighting(latest, 5, 6, 9, false);
    CHECK(get_code(latest, 0) == 7 && get_code(latest, 1) == 20);
    latest = set_code(latest, 2, kCodeDead);
    CHECK(read_sighting(latest, 10).present && read_sighting(latest, 10).x == 5);
}

int main() {
    test_claim_roundtrip();
    test_reserved_collisions();
    test_sighting_age_wrap();
    test_event_phantom();
    test_draft_regions();
    test_payload_validation();
    test_team_sizes_and_recovery();
    test_rmw_turn_order();
    std::printf("mem_test: %d checks, %d failures\n", checks, fails);
    return fails ? 1 : 0;
}
