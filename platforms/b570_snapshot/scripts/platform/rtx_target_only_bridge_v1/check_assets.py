"""Post-matrix hash/device readback without model execution."""
import platform
from common import *
def main():
    before=load(DOC/'ASSET_ENVIRONMENT.json');files={}
    for label,b in before['assets'].items():
        p=pathlib.Path(b['path']);h=sha(p);assert h==b['sha256'] and p.stat().st_size==b['bytes'],label
        files[label]={'sha256':h,'bytes':p.stat().st_size}
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,uuid,driver_version,memory.total,pci.bus_id','--format=csv,noheader'],text=True).strip()
    assert gpu==before['gpu'] and platform.platform()==before['os']
    save(DOC/'ASSET_POSTCHECK.json',{'status':'PASS','utc':now(),'files_checked':len(files),'files':files,'gpu':gpu,'os':platform.platform(),'scope':'local pre/post content and device consistency; not independent machine authentication'})
    print(json.dumps({'status':'PASS','files':len(files),'gpu':gpu}),flush=True)
if __name__=='__main__':main()
