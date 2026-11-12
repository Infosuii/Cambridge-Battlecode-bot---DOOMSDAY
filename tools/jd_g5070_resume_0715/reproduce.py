"""One-command clean source-archive rebuild and official-fuel reproduction smoke."""
import argparse,json,subprocess,sys,zipfile
from pathlib import Path,PurePosixPath
import run as bridge
r=bridge.runner
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def cmd(args):subprocess.run([sys.executable,str(HERE/'run.py'),*args],check=True)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--name',required=True);p.add_argument('--archive',type=Path);p.add_argument('--variant',choices=['cg','cpg'],default='cg');a=p.parse_args()
    package=json.loads((ROOT/'research/jd-g5070-resume-0715'/('PACKAGE_'+a.variant.upper()+'.json')).read_text())
    archive=a.archive or Path(package['path'])
    assert r.sha_file(archive)==package['sha256'],'Archive checksum mismatch'
    dest=r.EVAL/'resume/reproduction'/a.name
    if dest.exists():raise SystemExit('Fresh --name required')
    dest.mkdir(parents=True)
    with zipfile.ZipFile(archive) as z:
        for member in z.namelist():
            pp=PurePosixPath(member)
            assert not pp.is_absolute() and '..' not in pp.parts and pp.parts[0]=='src'
        z.extractall(dest)
    alias='repro-'+a.name
    cmd(['freeze','jd-g5070-resume-0715','--src',str(dest/'src'),'--alias',alias])
    actual=r.load_frozen()['bots'][r.resolve(alias)]['wasm_sha256']
    expected=package['wasm_sha256']
    assert actual==expected,(actual,expected)
    name='repro-'+a.name
    cmd(['run','--name',name,'--cand',alias,'--base','v92','--opps','v92,x3inv,p65pack','--maps','conf','--limit','3','--jobs','2','--task','candidate-integration'])
    cmd(['report','--name',name])
    subprocess.run([sys.executable,str(HERE/'audit.py'),name],check=True)
    print('Clean archive reproduction passed:',actual)
if __name__=='__main__':main()
