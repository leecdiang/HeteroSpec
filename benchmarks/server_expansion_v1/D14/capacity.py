"""File+KV planning ledger, not an allocation pass or an exact VRAM forecast."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'shared'))
from experiment import read,save,require
from gguf_inventory import kv_bytes

def estimate(target,draft,context):
    require(context in (1024,4096),'Two separately referenced capacities')
    tk=kv_bytes(target['metadata'],context);dk=kv_bytes(draft['metadata'],context)
    return dict(context=context,target_file_bytes=target['file_bytes'],draft_file_bytes=draft['file_bytes'],
        target_KV_bytes=tk,draft_KV_bytes=dk,file_plus_KV_bytes=target['file_bytes']+draft['file_bytes']+tk+dk,
        omitted=['workspace','graph cache','output buffers','alignment','CUDA contexts','driver','other users'],
        actual_admission='NOT_ESTABLISHED',disk_bytes_not_device_allocation=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('target');p.add_argument('draft');p.add_argument('out');a=p.parse_args()
    save(a.out,{str(c):estimate(read(a.target),read(a.draft),c) for c in (1024,4096)})
