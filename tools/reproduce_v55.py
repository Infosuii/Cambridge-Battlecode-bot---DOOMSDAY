"""Reconstruct an exact v55 experiment from its frozen-v54 patch, without changing either bot.
Usage: python tools/reproduce_v55.py e6 artifacts/tmp/reproduced-e6
Destination must be new and inside this repository. Raw replays are not required.
"""
import argparse,hashlib,json,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(src):
 h=hashlib.sha256()
 for f in sorted(x for x in src.rglob('*') if x.is_file()):h.update(f.relative_to(src).as_posix().encode()+b'\0'+f.read_bytes()+b'\0')
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('experiment');ap.add_argument('destination');a=ap.parse_args()
 entries={}
 for name in ('V55_EXPERIMENTS.json','V55_RESTART_EXPERIMENTS.json'):
  entries.update(json.loads((ROOT/'artifacts/claude_ops'/name).read_text(encoding='utf8')))
 e=entries[a.experiment]
 dest=Path(a.destination).resolve()
 if not dest.is_relative_to(ROOT) or dest.exists():raise SystemExit('destination must be a new directory inside this repository')
 shutil.copytree(ROOT/'bots/v54/src',dest/'src')
 for p in (dest/'src').rglob('*'):
  if p.is_file():p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
 subprocess.run(['git','apply','--whitespace=nowarn','--unsafe-paths','--directory='+dest.relative_to(ROOT).as_posix(),str(ROOT/e['patch'])],cwd=ROOT,check=True)
 for p in (dest/'src').rglob('*'):
  if not p.is_file():continue
  ref=ROOT/'bots/v54/src'/p.relative_to(dest/'src')
  if e['line_endings'][p.relative_to(dest/'src').as_posix()] == 'CRLF':p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
 actual=digest(dest/'src')
 if actual!=e['tree_sha256']:raise SystemExit('reconstruction hash mismatch: '+actual)
 print(a.experiment,actual,'PASS')
if __name__=='__main__':main()
