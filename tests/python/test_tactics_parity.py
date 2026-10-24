"""Synthetic tactical candidate parity. No learning or engine gameplay is performed."""
import json
import os
from pathlib import Path
import subprocess
import unittest
import numpy as np
from nfs.heads import tactics

ROOT=Path(__file__).resolve().parents[2]
TMP=ROOT/'artifacts/tmp/E2'

class TacticalParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TMP.mkdir(parents=True,exist_ok=True)
        cls.exe=TMP/'test_tactics_parity.exe'
        cxx=json.loads((ROOT/'config/paths.json').read_text())['native_cxx']
        env=dict(os.environ,PATH=str(Path(cxx).parent)+os.pathsep+os.environ.get('PATH',''),TMP=str(TMP),TEMP=str(TMP))
        subprocess.run([cxx,'-std=c++20','-O2','-ffp-contract=off','-I'+str(ROOT/'bot/src'),
                        str(ROOT/'tests/cpp/test_tactics_parity.cpp'),'-o',str(cls.exe)],check=True,capture_output=True,env=env)
        cls.env=env

    def native(self,head,raw,ids=None,legal=None,context=0):
        x=np.asarray(raw,dtype=np.float32); ident=tactics.schema(head)['id']
        rows=[f'{ident} {len(x) if x.ndim==2 else 1} {context}']
        if head=='ts_leaf': rows.append(' '.join(format(float(v),'.9g') for v in x))
        else:
            ids=np.arange(len(x)) if ids is None else ids; legal=np.ones(len(x),dtype=int) if legal is None else legal
            for j,row in enumerate(x): rows.append(f'{int(ids[j])} {int(legal[j])} '+' '.join(format(float(v),'.9g') for v in row))
        got=subprocess.run([str(self.exe)],input='\n'.join(rows)+'\n',text=True,capture_output=True,check=True,env=self.env).stdout.splitlines()
        hdr=list(map(int,got[0].split()))
        if head=='ts_leaf': return np.asarray(list(map(float,got[1].split())),dtype=np.float32)
        ret=dict(head=hdr[0],K=hdr[1],F=hdr[2],context=hdr[3],id=[],legal=[],prior=[],feat=[])
        for row in got[1:]:
            vals=row.split(); ret['id'].append(int(vals[0])); ret['legal'].append(int(vals[1])); ret['prior'].append(float(vals[2])); ret['feat'].append(list(map(float,vals[3:])))
        for k in ('id','legal','prior','feat'): ret[k]=np.asarray(ret[k],dtype=np.uint32 if k=='id' else np.uint8 if k=='legal' else np.float32)
        ret['feat']=ret['feat'].reshape(hdr[1],hdr[2]); return ret

    def test_varied_synthetic_feature_mask_parity(self):
        rng=np.random.default_rng(20261024)
        for h in tactics.HEADS[:4]:
            scales=np.asarray([f['scale'] for f in tactics.schema(h)['features']],dtype=np.float32)
            for n in (0,1,2,8,16,19):
                raw=(rng.normal(0,2,(n,24)).astype(np.float32)*scales).astype(np.float32)
                ids=np.arange(n,dtype=np.uint32)*100000+7
                legal=(rng.random(n)>.4).astype(np.uint8)
                if n: legal[0]=1
                for ctx in (0,1,2,3):
                    with self.subTest(head=h,n=n,context=ctx):
                        want=tactics.build(h,raw,ids,legal,ctx); got=self.native(h,raw,ids,legal,ctx)
                        for k in ('head','K','F','context'): self.assertEqual(want[k],got[k])
                        for k in ('id','legal','prior','feat'): np.testing.assert_array_equal(want[k],got[k])

    def test_leaf_synthetic_parity(self):
        rng=np.random.default_rng(681)
        for _ in range(30):
            x=(rng.normal(size=8)*[900,900,4,4,1,60,50,1]).astype(np.float32)
            np.testing.assert_array_equal(self.native('ts_leaf',x),tactics.normalise(x,'ts_leaf'))

    def test_alternative_permutation_and_teacher_mask(self):
        rng=np.random.default_rng(91); raw=rng.uniform(-1,1,(8,24)).astype(np.float32)
        for h in tactics.HEADS[:4]:
            ids=np.arange(8); legal=np.asarray([1,0,1,0,1,1,1,0],dtype=np.uint8)
            a=self.native(h,raw,ids,legal); p=np.asarray([0,5,7,1,2,4,3,6])
            b=self.native(h,raw[p],ids[p],legal[p])
            np.testing.assert_array_equal(a['feat'][p],b['feat']); np.testing.assert_array_equal(a['legal'][p],b['legal'])
            np.testing.assert_array_equal(a['prior'][p],b['prior']); self.assertEqual(0,int(np.argmax(a['prior'])))
            legal[0]=0
            # Pure preprocessing must not turn invalid teacher input into a falsely legal action.
            self.assertEqual(0,self.native(h,raw,ids,legal)['legal'][0])

    def test_nonfinite_preserved_for_runtime_fallback(self):
        raw=np.zeros((2,24),dtype=np.float32); raw[0,0]=np.nan; raw[1,2]=np.inf
        for h in tactics.HEADS[:4]:
            a=self.native(h,raw); b=tactics.build(h,raw)
            np.testing.assert_array_equal(a['feat'],b['feat'])
            self.assertTrue(np.isnan(a['feat'][0,0])); self.assertTrue(np.isinf(a['feat'][1,2]))

    def test_schema_feature_counts_and_teacher_label(self):
        for h in tactics.HEADS:
            s=tactics.schema(h); self.assertEqual(s['F'],len(s['features'])); self.assertEqual('untrained',s['status'])
            self.assertEqual(0,tactics.teacher_label(dict(head=h,teacher=0)))
            with self.assertRaises(ValueError): tactics.teacher_label(dict(head=h,teacher=1))

    def test_belief_sector_and_bounded_feature_parity(self):
        from nfs.transforms import sector_of
        rows=[]; want=[]
        for dx in range(-18,19):
            for dy in range(-18,19):
                x=np.float32((dx-dy)/3)
                rows.append(f'10 {dx} {dy} {float(x):.9g}')
                want.append((sector_of(dx,dy),tactics.bounded_belief(x)))
                self.assertEqual(sector_of(dx,dy),tactics.belief_sector(dx,dy))
        got=subprocess.run([str(self.exe)],input='\n'.join(rows)+'\n',text=True,capture_output=True,check=True,env=self.env).stdout.splitlines()
        self.assertEqual(len(want),len(got))
        for (sector,value),line in zip(want,got):
            s,v=line.split(); self.assertEqual(sector,int(s)); self.assertEqual(value,np.float32(v))

if __name__=='__main__': unittest.main()
