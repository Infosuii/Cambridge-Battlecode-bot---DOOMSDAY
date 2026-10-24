"""Create/check the user's private recovery repository using an existing Git credential. Never prints credentials."""
import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request

OWNER='Infosuii'
NAME='neural-networkk-battlecode'

def api(method,path,body=None):
    env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    result=subprocess.run(['git','credential','fill'],input=f'protocol=https\nhost=github.com\nusername={OWNER}\n\n',
                          capture_output=True,text=True,env=env,timeout=30)
    if result.returncode:raise RuntimeError('Existing GitHub credential unavailable; no interactive login attempted')
    credential=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
    data=None if body is None else json.dumps(body).encode()
    request=urllib.request.Request('https://api.github.com'+path,data=data,method=method,headers={
        'Authorization':'Bearer '+credential['password'],'Accept':'application/vnd.github+json',
        'Content-Type':'application/json','User-Agent':'battlecode-recovery'})
    with urllib.request.urlopen(request,timeout=60) as response:
        if response.status==204:return {}
        return json.load(response)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['create','check'])
    args=parser.parse_args()
    user=api('GET','/user')
    if user['login'].casefold()!=OWNER.casefold():raise SystemExit('Refusing wrong GitHub account')
    try:repo=api('GET',f'/repos/{OWNER}/{NAME}')
    except urllib.error.HTTPError as error:
        if error.code!=404 or args.action!='create':raise
        repo=api('POST','/user/repos',dict(name=NAME,private=True,auto_init=False,
            description='Complete neural Battlecode project recovery: source, tests, evidence, data and local dependencies. Untrained direct-policy work in progress.'))
    if not repo['private']:raise SystemExit('Recovery repository must remain private')
    print(json.dumps({key:repo.get(key) for key in ['full_name','html_url','private','default_branch','size','ssh_url','clone_url']},indent=2))
