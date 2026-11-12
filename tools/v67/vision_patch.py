"""Repair camp approach liveness in a separate flat-source bot copy."""
import argparse
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]


def patch_folder(src, persistent=True):
    p=src/'bot.cpp';s=p.read_bytes().decode();e='\r\n' if '\r\n' in s else '\n'
    start=s.index('bool Bot::reveal_bush_camp(const GroupRec& g) {')
    stop=s.index('// Spell damage per turn we can deal',start)
    implementation='''bool Bot::reveal_bush_camp(const GroupRec& g) {
    int hidden=-1,distance=999;
    for(int ci:g.camps) {
        const auto& c=w.camps[ci];
        if(c.dead||bit(w.visible,c.pos))continue;
        const int d=cheb(pos,c.pos);
        if(d<distance)distance=d,hidden=ci;
    }
    if(hidden<0||distance>range)return false;
    const auto at=w.camps[hidden].pos;
    auto& me=bc::self();
    if(distance<=2&&me.ward_cooldown()==0) {
        try {
            if(me.place_ward(at))ward_pos=at;
            w.update(round);
            if(bit(w.visible,at))return true;
        }catch(...){}
    }
    // Attack range alone is not an attack position: a camp in another bush
    // cluster is invisible. Do not wait on the outer range ring for a ward.
    bc::bitboard entry;entry.clear();
    bc::bitboard near;near.clear();near.draw_chebyshev(at,float(std::min(range,2)));
    if(bit(w.bushes,at)) {
        w.cluster_board(at,entry);
        entry&=near;
    } else {
        entry.draw_chebyshev(at,1.0f);
    }
    entry&=~w.static_blocked&~w.unit_tiles;
    if(!entry.is_empty()&&!bit(entry,pos)) {
        mode="bush-enter";
        if(walk_toward(entry)) {
            w.update(round);
            return true;
        }
    }
    // A one-tile bush occupied by the camp needs a ward; stage inside ward
    // range rather than remaining at the outer attack ring.
    mode="bush-ward";
    if(distance>2) {
        bc::bitboard ward_ring;ward_ring.clear();ward_ring.draw_chebyshev(at,2.0f);
        walk_toward(ward_ring);
    }
    return false;
}

'''
    if persistent:
        implementation=implementation.replace('''    int hidden=-1,distance=999;''','''    int hidden=-1,distance=999;
    if(camp_entry67_>=0&&camp_entry67_<int(w.camps.size())&&
       w.camp_group[camp_entry67_]==int(&g-w.groups.data())&&
       !w.camps[camp_entry67_].dead&&!bit(w.visible,w.camps[camp_entry67_].pos)) {
        hidden=camp_entry67_;distance=cheb(pos,w.camps[hidden].pos);
    } else camp_entry67_=-1;
    const bool committed=hidden>=0;''')
        implementation=implementation.replace('''        if(d<distance)distance=d,hidden=ci;''',
            '''        if(!committed&&d<distance)distance=d,hidden=ci;''')
        implementation=implementation.replace('''    if(hidden<0||distance>range)return false;''','''    if(hidden<0) {camp_entry67_=-1;return false;}
    if(!committed&&distance>range)return false;
    camp_entry67_=hidden;''')
        h=src/'bot.h';header=h.read_bytes().decode();he='\r\n' if '\r\n' in header else '\n'
        assert 'int camp_entry67_' not in header
        assert header.index('private:')>header.index('class Bot {')
        h.write_bytes(header.replace('private:','private:'+he+'    int camp_entry67_=-1;',1).encode())
    s=s[:start]+implementation.replace('\n',e)+s[stop:]
    old='if (t < 0 && std::string_view(mode) == "bush-ward") return true;'
    assert s.count(old)==1
    s=s.replace(old,'if (t < 0 && (std::string_view(mode) == "bush-ward" || std::string_view(mode) == "bush-enter")) return true;')
    p.write_bytes(s.encode())


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--stateless',action='store_true',help='Historical first patch, for reproduction only')
    a=ap.parse_args()
    source=(ROOT/a.input/'src').resolve();out=(ROOT/a.out).resolve()
    assert source.is_relative_to(ROOT) and out.is_relative_to(ROOT/'artifacts/tmp/v67')
    assert not out.exists()
    shutil.copytree(source,out/'src')
    patch_folder(out/'src',persistent=not a.stateless)
    print('prepared',out)


if __name__=='__main__':main()
