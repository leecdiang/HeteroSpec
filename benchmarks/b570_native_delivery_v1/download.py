"""Download a pinned private-repository asset; never forward credentials across hosts."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,urllib.error,urllib.request
REPO='leecdiang/HeteroSpec'
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None
def token():
    value=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if value:return value
    result=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True)
    if result.returncode:raise RuntimeError('Authenticate GitHub using Git Credential Manager, or set GH_TOKEN/GITHUB_TOKEN')
    fields=dict(line.split('=',1)for line in result.stdout.splitlines()if '=' in line)
    if not fields.get('password'):raise RuntimeError('No GitHub credential available')
    return fields['password']
def open_asset(url):
    if not re.fullmatch(r'https://api\.github\.com/repos/leecdiang/HeteroSpec/releases/assets/[0-9]+',url):raise ValueError('Unexpected asset API URL')
    request=urllib.request.Request(url,headers={'Authorization':'Bearer '+token(),'Accept':'application/octet-stream','X-GitHub-Api-Version':'2022-11-28','Cache-Control':'no-cache'})
    try:return urllib.request.build_opener(NoRedirect).open(request,timeout=90)
    except urllib.error.HTTPError as error:
        if error.code not in (301,302,303,307,308):raise RuntimeError('GitHub asset download HTTP '+str(error.code))from None
        location=error.headers.get('Location','')
        from urllib.parse import urlparse
        parsed=urlparse(location)
        if parsed.scheme!='https' or parsed.username or parsed.password:raise ValueError('Invalid signed asset redirect')
        # The signed storage URL authorizes this request; no GitHub credential follows it.
        return urllib.request.urlopen(urllib.request.Request(location),timeout=90)
def download(row,dest):
    dest=Path(dest)
    if dest.exists() or dest.with_suffix(dest.suffix+'.partial').exists():raise ValueError('Fresh download path required')
    dest.parent.mkdir(parents=True,exist_ok=True);partial=dest.with_suffix(dest.suffix+'.partial')
    digest=hashlib.sha256();size=0
    with open_asset(row['asset_api_url'])as response,partial.open('xb')as output:
        while block:=response.read(1024*1024):output.write(block);digest.update(block);size+=len(block)
    if size!=row['bytes'] or digest.hexdigest()!=row['sha256']:raise ValueError('Downloaded size/SHA mismatch; partial file retained')
    partial.rename(dest)
    return {'status':'DOWNLOAD_SHA256_PASS','path':str(dest.resolve()),'bytes':size,'sha256':digest.hexdigest(),'asset_api_url':row['asset_api_url']}
def main():
    p=argparse.ArgumentParser();p.add_argument('--access',type=Path,required=True);p.add_argument('--asset',choices=['minimal','four_input_references'],required=True);p.add_argument('--dest',type=Path,required=True);a=p.parse_args()
    access=json.loads(a.access.read_text(encoding='utf-8'));row=access['assets'][a.asset]
    print(json.dumps(download(row,a.dest),indent=2))
if __name__=='__main__':main()
