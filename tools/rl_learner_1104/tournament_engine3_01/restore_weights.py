"""Apply this run's exact array patch to the exact v107 header (no third-party deps)."""
import argparse,base64,hashlib,json,re,zlib
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('initial_header',type=Path);ap.add_argument('destination',type=Path);a=ap.parse_args();assert not a.destination.exists()
p=json.loads(Path(__file__).with_name('WEIGHT_PATCH.json').read_text());s=a.initial_header.read_text();sha=lambda x:hashlib.sha256(x.encode()).hexdigest();assert sha(s)==p['initial_header_sha256']
for name,body in json.loads(zlib.decompress(base64.b64decode(p['payload']))).items():
 pattern=r'(inline constexpr (?:float|short) '+re.escape(name)+r'\[\] = \{)([^}]*)(\})'
 s,n=re.subn(pattern,lambda m:m.group(1)+body+m.group(3),s);assert n==1
assert sha(s)==p['trained_header_sha256'];a.destination.write_text(s);print(sha(s))
