#include "opening_catalog.h"
#include "clear_risk.h"
#include "objective_model.h"
#include <cassert>
#include <iostream>
#include <limits>
int main() {
    using namespace dz;using namespace opening_catalog;
    const Design designs[]{{120,0,0,2},{1350,20,3,0}};
    const Member members[]{{92,4,5,2},{7,1,2,0},{33,3,3,2}};
    Catalog catalog;auto bytes=encode(10,10,designs,members,4096);
    assert(catalog.load(bytes,10,10));assert(catalog.member(7)->x==1&&catalog.member(92)->kind==2&&!catalog.member(8));
    assert(catalog.design(0)->hp==1350&&!catalog.design(5));
    assert(!catalog.load(bytes,11,10)&&!catalog.member(7));
    assert(!catalog.load(std::span<const std::byte>(bytes.data(),bytes.size()-1),10,10));
    const auto capacity=sizeof(Header)+sizeof(designs)+sizeof(Member);
    bytes=encode(10,10,designs,members,capacity);assert(bytes.size()==capacity&&catalog.load(bytes,10,10));
    assert(catalog.member(7)&&!catalog.member(33)&&catalog.design(2)); // Missing records use the design fallback.
    assert(encode(10,10,designs,members,sizeof(Header)).empty());
    const Member duplicate[]{{7,1,1,0},{7,2,2,0}};
    assert(!catalog.load(encode(10,10,designs,duplicate,4096),10,10));
    const Member outside[]{{7,10,0,0}};assert(!catalog.load(encode(10,10,designs,outside,4096),10,10));
    auto bad=designs[0];bad.hp=std::numeric_limits<float>::quiet_NaN();
    assert(!catalog.load(encode(10,10,std::span<const Design>(&bad,1),{},4096),10,10));
    bytes=encode(10,10,designs,members,4096);bytes[0]=std::byte{0};assert(!catalog.load(bytes,10,10));
    std::vector<float> hp(65,1);auto risk=harmless_clear_risk(hp,100);
    assert(risk.complete()&&risk.attacks==65&&risk.damage==0); // The former 64-member exclusion.
    hp.assign(1000,120);risk=harmless_clear_risk(hp,70);
    assert(risk.complete()&&risk.attacks==2000&&risk.damage==0);
    hp.push_back(1);assert(harmless_clear_risk(hp,70).status==WorkStatus::BeyondHorizon);
    hp.push_back(-1);assert(harmless_clear_risk(hp,70).status==WorkStatus::Invalid);
    assert(!harmless_clear_risk(hp,0).complete());
    hp.assign(64,120);std::array<ClearMember,64> reference;reference.fill({120,0});
    assert(harmless_clear_risk(hp,70).attacks==solo_clear_risk(reference,70).attacks);
    const ClearMember cluster[]{ {120,0} };const unsigned counts[]{1000};
    objective::Encounter encounter{cluster,280,0};encounter.multiplicities=counts;
    objective::Actor actor;actor.hp=actor.max_hp=1000;actor.damage=70;actor.capture_rounds=0;
    encounter.horizon=2000;encounter.capture_remaining=0;const auto quote=objective::forecast(encounter,{&actor,1},0);
    assert(quote.complete()&&quote.survivable&&quote.clear==2000&&quote.gems==280);
    std::cout<<"opening catalog validation, bounded fallback and large resource work passed\n";
}
