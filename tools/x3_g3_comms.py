"""Serialize g3's campaign and heartbeat Git operations on the shared comms worktree."""
import msvcrt,os,pathlib,shutil,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parents[1]
os.chdir(root)
lock=root/'artifacts/tmp/g3-comms.lock'
lock.parent.mkdir(parents=True,exist_ok=True)
with lock.open('a+b') as f:
    if f.tell()==0:f.write(b'0');f.flush()
    until=time.monotonic()+180
    while True:
        try:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1);break
        except OSError:
            if time.monotonic()>until:raise RuntimeError('g3 comms serialization timeout')
            time.sleep(1)
    try:
        action=sys.argv[1]
        assert action in ('pull','push')
        # The campaign writes its status immediately before requesting this lock.
        # Publish those authorized g3 writes before a heartbeat tries to rebase.
        if action=='pull':
            c=str(root.parent/'x1-comms')
            dirty=subprocess.run(['git','-C',c,'status','--porcelain'],capture_output=True,text=True,check=True).stdout
            if dirty.strip():
                bash=shutil.which('bash') or 'C:/Program Files/Git/bin/bash.exe'
                subprocess.run([bash,'tools/x1_comms.sh','push','g3 campaign progress before heartbeat poll'],env=dict(os.environ,SIDE='g3'),check=True)
        for attempt in range(4):
            bash=shutil.which('bash') or 'C:/Program Files/Git/bin/bash.exe'
            result=subprocess.run([bash,'tools/x1_comms.sh',*sys.argv[1:]],env=dict(os.environ,SIDE='g3'))
            if result.returncode==0:
                if action=='push':
                    c=str(root.parent/'x1-comms')
                    subprocess.run(['git','-C',c,'pull','--rebase','origin','comms/x1'],check=True)
                    subprocess.run(['git','-C',c,'push','origin','comms/x1'],check=True)
                break
            if attempt==3:result.check_returncode()
            time.sleep(2)
    finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
