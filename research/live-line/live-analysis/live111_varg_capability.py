"""EXP283: new shared geometry/forecast copies of exact111, never frozen-source edits."""
from shutil import copytree
import ablate_dev as bench
from engine3_pool import HERE,SDK_ROOT,read


def prepare(src,geometry,model):
    assert not model or geometry
    prerequisite=read(HERE/'VARG_GEOMETRY_PROOF_RECOUNT.json');assert prerequisite['pass'] and prerequisite['games']==180 and prerequisite['states']==39576
    identity=read(HERE/'LIVE111_SOURCE_VERIFIED.json');base=SDK_ROOT/'bots/live111/src'
    assert all(bench.digest(base/n)==h for n,h in identity['source_file_hashes'].items())
    copytree(base,src)
    p=src/'common.h';p.write_bytes(f'#define CODEX_VARG_GEOMETRY {int(geometry)}\n#define CODEX_VARG_CAPABILITY {int(model)}\n'.encode()+p.read_bytes())
    (src/'varg_group_geometry.h').write_bytes((HERE/'varg_group_geometry.h').read_bytes())
    p=src/'bot.h';text=p.read_text(encoding='utf8');anchor='#include "world.h"';assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'\n#if CODEX_VARG_GEOMETRY\n#include "varg_group_geometry.h"\n#endif')
    anchor='    float my_dps(const GroupRec* g) const;';assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'''
#if CODEX_VARG_GEOMETRY
    struct VargGroup {
        codex_varg::Shape shape;
        std::array<float,12> hp{};
        float damage=0, factor=1.6f;
        bool ready=false;
    };
    mutable std::vector<VargGroup> varg_groups;
    VargGroup& varg_geometry(const GroupRec& g) const;
    float varg_capability(const GroupRec& g) const;
    int varg_target(const GroupRec& g) const;
#endif''')
    p.write_text(text,encoding='utf8',newline='\n')
    p=src/'bot.cpp';text=p.read_text(encoding='utf8');anchor='float Bot::my_dps(const GroupRec* g) const {';assert text.count(anchor)==1
    methods='''#if CODEX_VARG_GEOMETRY
Bot::VargGroup& Bot::varg_geometry(const GroupRec& g) const {
    if(varg_groups.size()!=w.groups.size())varg_groups.resize(w.groups.size());
    auto& entry=varg_groups[static_cast<std::size_t>(&g-w.groups.data())];
    if(!entry.shape.built){
        std::array<codex_varg::Point,12> points{};
        if(g.camps.size()<=points.size())for(std::size_t i=0;i<g.camps.size();++i){const auto p=w.camps[g.camps[i]].pos;points[i]={p.x,p.y};}
        entry.shape=codex_varg::build(points.data(),g.camps.size());
    }
    return entry;
}
float Bot::varg_capability(const GroupRec& g) const {
    auto& entry=varg_geometry(g);
#if CODEX_VARG_CAPABILITY
    if(!entry.shape.valid||!entry.shape.cliques)return 1.6f;
    const float damage=strength*camp_dealt_mult;
    std::array<float,12> current{};bool changed=!entry.ready||entry.damage!=damage;
    for(std::size_t i=0;i<g.camps.size();++i){const auto& c=w.camps[g.camps[i]];current[i]=g.state==GroupState::alive?(c.dead?0:c.hp):c.max_hp;changed|=current[i]!=entry.hp[i];}
    if(changed){
        const auto cap=codex_varg::capability(entry.shape,current.data(),damage);
        entry.factor=cap.valid&&cap.attacks?cap.factor:1.6f;
        entry.hp=current;entry.damage=damage;entry.ready=true;
    }
    return entry.factor;
#else
    return 1.6f;
#endif
}
int Bot::varg_target(const GroupRec& g) const {
    const auto& shape=varg_geometry(g).shape;
    if(!shape.valid)return -2;
    unsigned alive=0;for(std::size_t i=0;i<g.camps.size();++i)if(!w.camps[g.camps[i]].dead)alive|=1u<<i;
    int best=-1;float best_hp=1e30f;
    for(std::size_t i=0;i<g.camps.size();++i){const int ci=g.camps[i];const auto& c=w.camps[ci];
        if(c.dead||!bit(w.visible,c.pos)||cheb(c.pos,pos)>range)continue;
        float key=c.hp-c.strength*1000.0f;
        key-=static_cast<float>(codex_varg::neighbours(shape,i,alive))*2000.0f;
        if(key<best_hp){best_hp=key;best=ci;}
    }
    return best;
}
#endif

'''
    text=text.replace(anchor,methods+anchor)
    anchor='    if (type == bc::champion_type::varg && g && g->camps.size() > 1) dps *= 1.6f;';assert text.count(anchor)==1
    text=text.replace(anchor,'''    if (type == bc::champion_type::varg && g && g->camps.size() > 1) {
#if CODEX_VARG_GEOMETRY
        dps *= varg_capability(*g);
#else
        dps *= 1.6f;
#endif
    }''')
    anchor='        const float dps = (type == bc::champion_type::varg && g.camps.size() > 1) ? base_dps * 1.6f : base_dps;';assert text.count(anchor)==1
    text=text.replace(anchor,'''        const float dps = (type == bc::champion_type::varg && g.camps.size() > 1) ? base_dps *
#if CODEX_VARG_GEOMETRY
            varg_capability(g)
#else
            1.6f
#endif
            : base_dps;''')
    anchor='''bool Bot::fight_camps(GroupRec& g, int need) {
    auto pick_target = [&]() {''';assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'''
#if CODEX_VARG_GEOMETRY
        if(type==bc::champion_type::varg){
            const int selected=varg_target(g);
            if(selected!=-2)return selected;
        }
#endif''')
    p.write_text(text,encoding='utf8',newline='\n')
