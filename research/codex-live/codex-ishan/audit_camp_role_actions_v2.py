"""Extract only the preregistered32 replay cells; no win-based selection."""
import os
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write


if __name__=='__main__':
    plan=read(HERE/'LIVE111_CAMP_ROLES_V2_PLAN.json')
    selected={name.removesuffix('.map26a') for name in sorted(plan['maps'],key=lambda n:plan['maps'][n])[:2]}
    raw=read(HERE/'LIVE111_CAMP_ROLES_V2_RAW.json')
    rows=[r for r in raw['rows'] if r['map'] in selected];assert len(rows)==32
    output=bench.CACHE/'camp-role-action-audit-v2-20261106';output.mkdir()
    jobs=[]
    for r in rows:
        native=bench.ROOT/r['native_path'];assert bench.digest(native)==r['native_sha256']
        archive,=native.parent.glob('*.repl26a')
        replay=output/f"{r['map']}-{r['side']}-{r['role']}-{r['mode']}.repl26a"
        with ZipFile(archive) as z:
            with replay.open('xb') as f:f.write(z.read('replay.repl26a'))
        jobs.append({**{k:r[k] for k in ('map','side','role','mode','actor_id')},'replay':str(replay),
                     'archive_sha256':bench.digest(archive),'native_sha256':r['native_sha256'],'replay_sha256':bench.digest(replay)})
    path=output/'jobs.json';write(path,jobs)
    subprocess.run(['node',HERE/'audit_camp_role_actions.mjs',path,HERE/'LIVE111_CAMP_ROLE_ACTION_AUDIT.json'],
                   cwd=bench.ROOT,env={**os.environ,'NFS_REPLAY_ENGINE':'3.0.0'},check=True)
