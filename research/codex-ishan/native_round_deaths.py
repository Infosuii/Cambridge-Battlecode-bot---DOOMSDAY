"""Align sampled transition context with exact actor native deaths, without changing cutoffs."""
def correlate(contexts,native,team,until=600):
    tag='team'+'AB'[team]
    events=[(e['owner']['id'],x) for e in native['events'] if e['kind']=='death' and e['owner'].get('team')==tag for x in e['entries']]
    used=set();selected=[];alignment=[]
    for d in contexts:
        if d['team']!=team:continue
        choices=[i for i,(actor,x) in enumerate(events) if i not in used and actor==d['id'] and d['round']<=x['timestamp']['round']<=d['round']+1]
        assert len(choices)==1,('ambiguous_or_missing_native_death',team,d,[(a,x['timestamp']) for a,x in events])
        i,=choices;used.add(i);actor,event=events[i];time=event['timestamp'];inside=time['round']<=until
        alignment.append({'actor':actor,'sampled_round':d['round'],'native_round':time['round'],'native_input':time['input'],'native_phase':time['phase'],'inside_cutoff':inside})
        if inside:selected.append({**d,'native_round':time['round'],'native_input':time['input']})
    expected={i for i,(_,x) in enumerate(events) if x['timestamp']['round']<=until}
    assert expected<=used,('native_death_missing_context',team,[events[i] for i in expected-used])
    assert len(selected)==len(expected)
    return selected,alignment
