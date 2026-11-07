"""CPU-only owned evidence disk budget and safe cleanup of rederivable restored replicas."""
import json,shutil,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];cap=json.loads((R/'PLAN.json').read_bytes())['limits']['total_disk_bytes']
def used():return sum(p.stat().st_size for p in R.rglob('*') if p.is_file())
def checkpoint(label):
 n=used();assert n<=cap,(label,n,cap)
 p=R/'receipts/DISK_CHECKPOINTS.jsonl'
 with p.open('a',encoding='utf8') as f:f.write(json.dumps(dict(label=label,bytes=n,cap=cap,status='PASS'))+'\n')
 return n
def remove_replica(which):
 allowed={'local_restore':R/'LOCAL_RESTORE.json','authenticated_remote_parts':R/'receipts/REMOTE_BYTES.json'}
 assert which in allowed and allowed[which].exists()
 target=(R/'receipts'/which).resolve();assert target.is_relative_to((R/'receipts').resolve()) and target.parent==(R/'receipts').resolve() and target.name==which
 shutil.rmtree(target)
 checkpoint('after_safe_cleanup_'+which)
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='cleanup':remove_replica(sys.argv[2])
 else:print(json.dumps(dict(bytes=checkpoint(sys.argv[1] if len(sys.argv)>1 else 'CHECK'),cap=cap)))
