"""Isolated shadow probe at the final contact-verdict boundary; no action changes."""
from pathlib import Path
import shutil
r=Path(__file__).resolve().parents[1];p=r/'native-contact-probe';assert not p.exists();(p/'bots/submission').mkdir(parents=True);src=p/'bots/submission/src';shutil.copytree(r/'native-upper-greedy/bots/submission/src',src)
for name in ('sdk','cmake'):(p/name).symlink_to(r/'mac-project'/name,target_is_directory=True)
shutil.copyfile(r/'mac-project/cambc.toml',p/'cambc.toml')
f=src/'bot.cpp';s=f.read_text().replace('#include "bot.h"','#include "bot.h"\n#include "jd_contact_probe.h"',1);needle='bool Bot::handle_enemies() {';assert s.count(needle)==1;s=s.replace(needle,needle+'\n    ++jd_contact::calls;',1)
needle='    if (tune::kTribDeny & 2) {\n        if (in_danger && !winning) try_lock_altar();';assert s.count(needle)==1
s=s.replace(needle,'#include "jd_contact_features.inc"\n'+needle,1);f.write_text(s)
for name in ['jd_contact_probe.h','jd_contact_features.inc']:shutil.copyfile(Path(__file__).parent/name,src/name)
print(p)
