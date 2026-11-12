"""EXP234 bounded selected-group ground-AOE aim and existing pre-walk hook."""
from shutil import copytree

import ablate_dev as bench
from bounded_verdict import apply
from engine3_pool import HERE,SDK_ROOT,read


def patch(src,enabled):
    p=src/'common.h';p.write_bytes(f'#define CODEX_CAMP_ROLE_PLAY {int(enabled)}\n'.encode()+p.read_bytes())
    p=src/'bot.cpp'
    text=p.read_text(encoding='utf8');start=text.index('bool Bot::cast_on_camp(int ci) {');end=text.index('static bool enemy_stunned',start)
    old=text[start:end];new=old
    new=new.replace('    int best = -1;','''#if CODEX_CAMP_ROLE_PLAY
    vec2 camp_aim[2]={c.pos,c.pos};
#endif
    int best = -1;''',1)
    anchor='        if (cheb(pos, c.pos) > static_cast<int>(sp.range)) continue;'
    assert new.count(anchor)==1
    new=new.replace(anchor,'''#if CODEX_CAMP_ROLE_PLAY
        const bool ground_aoe=sp.kind==bc::ability_kind::aoe_damage&&sp.ground&&sp.camps;
        const int reach=static_cast<int>(sp.range+(ground_aoe?sp.radius:0));
        if(cheb(pos,c.pos)>reach)continue;
#else
'''+anchor+'''
#endif''')
    anchor='''            int hits = 0;
            for (int other : w.groups[w.group_of_camp_tile(c.pos)].camps)
                if (!w.camps[other].dead && cheb(w.camps[other].pos, c.pos) <= static_cast<int>(sp.radius)) ++hits;'''
    assert new.count(anchor)==1
    new=new.replace(anchor,'''#if CODEX_CAMP_ROLE_PLAY
            int hits=0;
            if(sp.ground) {
                const int gi=w.group_of_camp_tile(c.pos);
                if(gi<0||!bit(w.visible,c.pos))continue;
                const int rad=static_cast<int>(sp.radius),rng=static_cast<int>(sp.range);
                int best_hits=-1;bool best_centre=false;
                for(int dy=-rad;dy<=rad;++dy)for(int dx=-rad;dx<=rad;++dx) {
                    const vec2 aim{c.pos.x+dx,c.pos.y+dy};
                    if(!in_bounds(aim,w.width,w.height)||cheb(pos,aim)>rng||!bit(w.visible,aim))continue;
                    bool touches_other=false;
                    for(std::size_t oi=0;oi<w.groups.size()&&!touches_other;++oi)if(static_cast<int>(oi)!=gi)
                        for(int ci2:w.groups[oi].camps)if(cheb(w.camps[ci2].pos,aim)<=rad){touches_other=true;break;}
                    if(touches_other)continue;
                    int count=0;
                    for(int ci2:w.groups[gi].camps)if(!w.camps[ci2].dead&&bit(w.visible,w.camps[ci2].pos)&&cheb(w.camps[ci2].pos,aim)<=rad)++count;
                    const bool centre=dx==0&&dy==0;
                    if(count>best_hits||(count==best_hits&&centre&&!best_centre)) {
                        best_hits=count;best_centre=centre;camp_aim[s]=aim;
                    }
                }
                if(best_hits<=0)continue;
                hits=best_hits;
            } else {
                for(int other:w.groups[w.group_of_camp_tile(c.pos)].camps)
                    if(!w.camps[other].dead&&cheb(w.camps[other].pos,c.pos)<=static_cast<int>(sp.radius))++hits;
            }
#else
'''+anchor+'''
#endif''')
    anchor='        const bool ok = spells[best].kind == bc::ability_kind::aoe_damage ? ab.use(c.pos) : ab.use(c.camp);'
    assert new.count(anchor)==1
    new=new.replace(anchor,'''#if CODEX_CAMP_ROLE_PLAY
        const bool ok=spells[best].kind==bc::ability_kind::aoe_damage?ab.use(camp_aim[best]):ab.use(c.camp);
#else
'''+anchor+'''
#endif''')
    text=text[:start]+new+text[end:]
    anchor='''#if V58_ACT & 1
        if (act_camp_before_walk(g)) return true;
#endif'''
    assert text.count(anchor)==1
    text=text.replace(anchor,'''#if (V58_ACT & 1) || CODEX_CAMP_ROLE_PLAY
        if (act_camp_before_walk(g)) return true;
#endif''')
    p.write_text(text,encoding='utf8',newline='\n')
    p=src/'tactics.cpp'
    old='''        if (spell_ready(s) && spell.excludes_walk && spell.camps && spell.modifier > 0.0f)
            reach = std::max(reach, spell.range);'''
    new='''#if CODEX_CAMP_ROLE_PLAY
        if(spell_ready(s)&&spell.excludes_walk&&spell.camps&&spell.ground&&spell.kind==bc::ability_kind::aoe_damage&&spell.modifier>0.0f)
            reach=std::max(reach,spell.range+spell.radius);
#else
'''+old+'''
#endif'''
    apply(p,((old,new),))


def prepare(src,enabled):
    original=SDK_ROOT/'bots/live111/src';pins=read(HERE/'LIVE111_SOURCE_VERIFIED.json')
    assert all(bench.digest(original/n)==sha for n,sha in pins['source_file_hashes'].items())
    copytree(original,src);patch(src,enabled)


def fixture(src,hero):
    # Forced roster / idle allies are diagnostic-only and absent from clean builds.
    cd_name,type_id=hero
    p=src/'draft.cpp'
    anchor='void play_draft() {'
    block=f'''void play_draft() {{
    {{
        constexpr cd roles[]={{cd::{cd_name},cd::vendetta,cd::vesper_vale,cd::varg,cd::ren,cd::marcella}};
        const auto taken=bc::draft::current_draft(team::ally);
        for(auto c:roles)if(std::find(taken.begin(),taken.end(),c)==taken.end()){{bc::draft::pick(c);return;}}
    }}'''
    apply(p,((anchor,block),))
    p=src/'main.cpp'
    apply(p,(('''        try {
            if (bc::is_draft()) {''',f'''        try {{
            if(!bc::is_draft()&&static_cast<int>(bc::self().champion_name())!={type_id}){{bc::end_turn();continue;}}
            if (bc::is_draft()) {{'''),))
