"""Read the official platform's release interface, without controlling a browser."""
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
import bulk_access as platform

ROOT = Path(__file__).resolve().parents[1] / 'phase2-two-hours/platform-interface'
ROOT.mkdir(parents=True, exist_ok=True)

class Scripts(HTMLParser):
    def __init__(self): super().__init__(); self.urls = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and attrs.get('src'): self.urls.append(attrs['src'])

def main():
    parser = Scripts()
    html = platform.open_url(platform.request(platform.ORIGIN + '/game/submissions'), timeout=30).read().decode()
    parser.feed(html)
    for i, path in enumerate(parser.urls):
        url = urllib.parse.urljoin(platform.ORIGIN, path)
        if urllib.parse.urlsplit(url).netloc != '2026a.battlecode.co.uk': continue
        print('Reading official interface:', url, flush=True)
        try:
            raw = platform.open_url(platform.request(url), timeout=30).read().decode()
        except urllib.error.HTTPError as exc:
            print('Interface HTTP', exc.code)
            continue
        (ROOT / ('asset-' + str(i) + '.js')).write_text(raw, encoding='utf-8')
        print('Official interface:', url, len(raw), 'bytes')
        for term in ['submissions', 'activeSubmission', 'activate', 'setActive', '/api/v1/teams']:
            for m in list(re.finditer(re.escape(term), raw))[:12]:
                print(raw[max(0,m.start()-150):m.end()+220])
    session = platform.cli_session()
    for path in ['/api/v1/submissions']:
        try:
            with platform.open_url(platform.request(platform.ORIGIN + path, session),timeout=30) as r:
                data = json.load(r)
                (ROOT / 'submissions-response.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
                print('Authenticated endpoint:', path, r.status, 'response type', type(data).__name__)
        except urllib.error.HTTPError as e:
            print('Authenticated endpoint:', path, 'HTTP',e.code)

if __name__ == '__main__': main()
