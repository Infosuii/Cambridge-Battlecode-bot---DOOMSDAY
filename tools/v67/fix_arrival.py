"""Restore authenticated on-site acknowledgements in tagged team policies."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def fix(folder):
    edits={}
    for name in ['team_memory.h','bot.h','bot.cpp','v67_team.cpp']:
        p=folder/(name.replace('.cpp','.inc'));raw=p.read_bytes();e='\r\n' if b'\r\n' in raw else '\n'
        edits[name]=[p,raw.decode().replace('\r\n','\n'),e]
    def replace(name,old,new):
        assert old in edits[name][1],str(folder/name)+' missing '+old[:70]
        edits[name][1]=edits[name][1].replace(old,new,1)
    replace('team_memory.h','inline int job(std::uint64_t m,int s) { return job_message(m,s) ? int(byte(m,s))-1 : -1; }',
            'inline int job(std::uint64_t m,int s,bool compact=false) { return job_message(m,s) ? int(byte(m,s)&(compact?63:127))-1 : -1; }\ninline bool onsite(std::uint64_t m,int s,bool compact) { return compact && job_message(m,s) && (byte(m,s)&64); }')
    replace('team_memory.h','inline std::uint64_t put_job(std::uint64_t m,int s,int g) { return put_byte(m,s,g>=0&&g<126 ? unsigned(g+1) : 0); }',
            'inline std::uint64_t put_job(std::uint64_t m,int s,int g,bool arrived=false,bool compact=false) { return put_byte(m,s,g>=0&&g<(compact?62:126) ? unsigned(g+1)|(compact&&arrived?64:0) : 0); }')
    replace('bot.h','bool alive = false, exact = false;','bool alive = false, exact = false, onsite = false;')
    replace('v67_team.cpp','memory = team67::put_job(memory, slot, job);','memory = team67::put_job(memory, slot, job, (onsite_bits & (1u<<slot)) != 0, w.groups.size()<=62);')
    replace('v67_team.cpp','a.job = team67::job(memory,s); a.job_seen = round;',
            'a.job = team67::job(memory,s,w.groups.size()<=62); a.job_seen = round;\n                a.onsite = team67::onsite(memory,s,w.groups.size()<=62);')
    replace('v67_team.cpp','claim_cache[s] = static_cast<std::int16_t>(a.job);\n            if (a.exact)',
            'claim_cache[s] = static_cast<std::int16_t>(a.job);\n            if(a.onsite) onsite_bits |= 1u<<s;\n            if (a.exact)')
    replace('v67_team.cpp','''        if (a.job >= 0 && a.job < static_cast<int>(w.groups.size()) && a.exact)
            for(int ci:w.groups[a.job].camps) if(cheb(a.pos,w.camps[ci].pos)<=5) onsite_bits|=1u<<s;''','''        if (a.job >= 0 && a.job < static_cast<int>(w.groups.size()) && a.exact) {
            bool near=false;
            for(int ci:w.groups[a.job].camps) near|=cheb(a.pos,w.camps[ci].pos)<=5;
            if(near) onsite_bits|=1u<<s;
            else if(s==slot) { a.onsite=false; onsite_bits&=~(1u<<s); }
        }''')
    replace('bot.cpp','''        auto memory = team67::put_job(read_shared(),slot,group);
        bc::shared_memory.write(0,std::span<std::uint64_t,1>{&memory,1});''','''        const bool arrived=onsite || (slot>=0 && slot<6 && team67_[slot].job==group && claim_onsite(slot));
        auto memory = team67::put_job(read_shared(),slot,group,arrived,w.groups.size()<=62);
        bc::shared_memory.write(0,std::span<std::uint64_t,1>{&memory,1});''')
    replace('bot.cpp','team67_[slot].job=group; team67_[slot].job_seen=round;',
            'team67_[slot].job=group; team67_[slot].job_seen=round; team67_[slot].onsite=arrived;')
    replace('bot.cpp','            if(onsite) onsite_bits |= 1u<<slot;',
            '            if(arrived) onsite_bits |= 1u<<slot;\n            else onsite_bits &= ~(1u<<slot);')
    replace('bot.cpp','''void Bot::unmark_onsite() {
    if (V67_TEAMPLAY) return;''','''void Bot::unmark_onsite() {
    if (V67_TEAMPLAY) {
        onsite_bits &= ~(1u<<slot);
        team67_[slot].onsite=false;
        auto memory=team67::put_job(read_shared(),slot,team67_[slot].job,false,w.groups.size()<=62);
        bc::shared_memory.write(0,std::span<std::uint64_t,1>{&memory,1});
        return;
    }''')
    replace('bot.cpp','onsite_ok = V54_ONSITE && w.groups.size() <= static_cast<std::size_t>(kOnsiteGroups);',
            'onsite_ok = V54_ONSITE && w.groups.size() <= static_cast<std::size_t>(V67_TEAMPLAY ? 62 : kOnsiteGroups);')
    replace('bot.cpp','''void Bot::mark_onsite(int group) {
#if V54_ONSITE''','''void Bot::mark_onsite(int group) {
    if(V67_TEAMPLAY) {
        if(onsite_ok && group>=0 && group<62) write_claim(group,true);
        return;
    }
#if V54_ONSITE''')
    for p,text,e in edits.values():p.write_bytes(text.replace('\n',e).encode())
    print('fixed',folder.relative_to(ROOT))


if __name__=='__main__':
    for name in ['p14','p15']:fix(ROOT/'bots/v67/src/policies'/name)
