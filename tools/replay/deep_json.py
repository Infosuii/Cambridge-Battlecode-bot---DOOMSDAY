"""Stable JSON tables with one record per line for reviewable data diffs."""
import json


def save_table(path,value):
    lines=['{'];items=list(value.items())
    encode=lambda v:json.dumps(v,separators=(',',':'),ensure_ascii=True,allow_nan=False)
    for index,(key,data) in enumerate(items):
        suffix=',' if index<len(items)-1 else ''
        if isinstance(data,list) and data:
            lines.append('  '+encode(key)+': [')
            lines.extend('    '+encode(row)+(',' if i<len(data)-1 else '') for i,row in enumerate(data))
            lines.append('  ]'+suffix)
        else:lines.append('  '+encode(key)+': '+encode(data)+suffix)
    path.write_bytes(('\n'.join(lines+['}'])+'\n').encode('utf-8'))
