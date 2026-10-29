"""Render an experimental draft table from a frozen selection and trace signatures."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--selection',type=Path,required=True);p.add_argument('--signatures-run',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    selection,_=json.JSONDecoder().raw_decode(a.selection.read_text(encoding='utf-8').lstrip())
    table=selection['table'];folder=ROOT/'research/dz/runs'/a.signatures_run
    results=json.loads((folder/'results.json').read_text())
    signatures={};sides={}
    with zipfile.ZipFile(folder/'evidence.zip') as z:
        for g in results['per_game']:
            if any(g.get(k,1) for k in ('faults','fuel_outs','caught_action_errors','caught_module_errors')):raise ValueError('signature trace is not runtime clean')
            text=z.read(f"games/{g['map']}-{g['side']}/candidate.stdout").decode('utf-8')
            values={int(v) for v in re.findall(r'DZ_SIG signature=(\d+)',text)}
            if len(values)!=1:raise ValueError('missing or ambiguous static signature')
            signature=values.pop()
            if g['map'] in signatures and signatures[g['map']]!=signature:raise ValueError('side-dependent signature')
            signatures[g['map']]=signature;sides.setdefault(g['map'],set()).add(g['side'])
    pool=sorted(x.stem for x in (ROOT/'maps/local-benchmarks').glob('*.map26a'))
    if len(pool)!=70 or set(signatures)!=set(pool) or any(s!={'A','B'} for s in sides.values()) or len(set(signatures.values()))!=70:
        raise ValueError('need all70 unique map signatures and both sides')
    heldout=set(pool[4::5]);lines=['// Experimental: generated from frozen v65 selection; no v76 promotion yet.']
    for name,variant in sorted(table.items()):
        if name not in signatures or name in heldout or not re.fullmatch(r'[A-Za-z0-9_-]+',name) or type(variant) is not int or not 0<=variant<8:
            raise ValueError('invalid or held-out draft row')
        lines.append(f'    {{{signatures[name]}u, {variant}}}, // {name}')
    if a.output.exists():raise FileExistsError('refuse to overwrite an existing table')
    a.output.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(table=table,signatures={m:signatures[m] for m in table},
        selection_sha256=hashlib.sha256(a.selection.read_bytes()).hexdigest(),
        signature_capsule_sha256=hashlib.sha256((folder/'evidence.zip').read_bytes()).hexdigest()),indent=2))


if __name__=='__main__':main()
