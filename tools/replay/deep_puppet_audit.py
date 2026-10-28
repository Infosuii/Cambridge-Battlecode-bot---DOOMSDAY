"""Independent accepted-input focus counts and parser preservation on real fixtures."""
import json
from collections import defaultdict
from deep_preflight import ROOT
from deep_detector_report import save
from puppet.replay_format import parse


def main():
    local=ROOT/'artifacts/local-only/deep-2026-10-28';study=ROOT/'research/deep-2026-10-28';results=[];cal=[]
    for p in sorted((local/'replay-inputs').glob('*.json')):
        script=json.loads(p.read_text(encoding='utf-8'))
        if not script.get('validation',{}).get('replay_bytes_identical'):continue
        raw=local/'replays'/script['partition']/(script['match_id']+'.repl26a')
        actual=parse(raw.read_bytes(),(ROOT/script['map_file']).read_bytes())
        keys=lambda rows:[(v['tag'],v['action'],v['args']) for v in rows]
        assert keys(actual)==keys(script['inputs'])
        results.append({'match_id':script['match_id'],'partition':script['partition'],'accepted_inputs':len(actual),'unchanged':True})
        if script['partition']!='calibration-excluded':continue
        native=json.loads(raw.with_suffix('.summary.json').read_text(encoding='utf-8'));teams={c['id']:0 if c['team']=='teamA' else 1 for c in native['roster']['champions']}
        focus=defaultdict(set)
        for x in script['inputs']:
            # Official entity kind1 is champion. Attack is raw action2.
            if x['tag']==0 and x['action']==2 and x['args'][0]==1 and x['args'][1] in teams and teams[x['actor']]!=teams[x['args'][1]]:
                focus[x['r'],teams[x['actor']],x['args'][1]].add(x['actor'])
        counts=[[sum(k[1]==team for k in focus),sum(k[1]==team and len(v)>=2 for k,v in focus.items())] for team in (0,1)]
        measured=json.loads((local/'profile-calibration-v1'/(script['match_id']+'.json')).read_text(encoding='utf-8'))
        engine=[[t['basic_target_rounds'],t['multi_attacker_target_rounds']] for t in measured['teams']]
        assert counts==engine,(script['match_id'],counts,engine)
        cal.append({'match_id':script['match_id'],'accepted_input_target_rounds_and_focused':counts,'engine_counts':engine,'equal':True})
    assert len(results)==17 and len(cal)==5
    save(study/'PUPPET_AUDIT.json',{'parser_fixtures':17,'parser_accepted_input_records':sum(r['accepted_inputs'] for r in results),'unchanged':True,'focus_calibration_games':5,'focus_team_comparisons':10,'focus_equal':True,'hands_off_used':0,'rows':results,'focus':cal})
    print(json.dumps({'parser_fixtures':17,'focus_team_comparisons':10,'passed':True}))


if __name__=='__main__':main()
