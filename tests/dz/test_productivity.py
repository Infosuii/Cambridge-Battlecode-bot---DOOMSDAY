"""Reject missing traces and reproduce productivity on a clean clone."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec=importlib.util.spec_from_file_location('productivity',Path(__file__).resolve().parents[2]/'tools/dz_productivity.py')
productivity=importlib.util.module_from_spec(spec);spec.loader.exec_module(productivity)


class Productivity(unittest.TestCase):
    def archive(self,root,text,outs=0):
        p=root/'research/dz/runs/example';p.mkdir(parents=True)
        game=dict(map='map',side='A',faults=0,fuel_outs=outs,caught_action_errors=0,caught_module_errors=0)
        (p/'results.json').write_text(json.dumps(dict(per_game=[game])))
        with zipfile.ZipFile(p/'evidence.zip','w') as z:z.writestr('games/map-A/candidate.stdout',text)

    def test_capsule_works_without_ignored_working_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.archive(root,'DZ_STUCK round=40 slot=0 kind=0 index=3 pos=1,2 fuel=50000 dist=4 state=0\nDZ_TIME round=1000 slot=0 prod 10 20 3 1 2\n')
            report,rows=productivity.analyse('example',root=root)
            self.assertEqual(report['stuck_episodes'],1)
            self.assertEqual(report['body_turns'],36)
            self.assertTrue(report['runtime_clean'])
            self.assertIn(('map-A',0),rows)

    def test_missing_trace_never_means_zero_stuck(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with self.assertRaises(ValueError):productivity.analyse('missing',root=root)
            self.archive(root,'release build has no productivity logging')
            with self.assertRaises(ValueError):productivity.analyse('example',root=root)

    def test_faulty_runtime_and_nonmatching_snapshots_are_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.archive(root,'DZ_TIME round=1000 slot=0 prod 10 20 3 1 2\n',outs=1)
            report,_=productivity.analyse('example',root=root)
            self.assertFalse(report['runtime_clean'])
        comparison=productivity.compare({('map-A',0):dict(work=5,stall=5),('other',0):dict(idle=1000)},
                                        {('map-A',0):dict(work=8,stall=2)})
        self.assertEqual(comparison['matching_body_snapshots'],1)
        self.assertEqual(comparison['percentage_point_change']['stall'],-30)


if __name__=='__main__':unittest.main()
