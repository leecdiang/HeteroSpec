"""Compare complete native trajectories and saved vectors across factor settings."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha,endpoint

def compare(a,b,out):
    a=Path(a);b=Path(b);rows=[]
    for role in ('oracle','candidate'):
        sa=read(a/f'units/baseline-{role}/SLOTS.json');sb=read(b/f'units/baseline-{role}/SLOTS.json');need(sa==sb,'identical complete natural schedule')
        for s in sa:
            pa=a/f'units/baseline-{role}/native'/s['id'];pb=b/f'units/baseline-{role}/native'/s['id'];ra=read(pa.with_suffix('.json'));rb=read(pb.with_suffix('.json'))
            need(endpoint(ra)==endpoint(rb) and ra['cycles']==rb['cycles'],'complete trajectory not restored')
            va={p.relative_to(pa).as_posix():sha(p) for k in ('target','draft') for p in (pa/k).glob('*.f32')};vb={p.relative_to(pb).as_posix():sha(p) for k in ('target','draft') for p in (pb/k).glob('*.f32')}
            need(va==vb,'complete saved vector set not restored')
            rows.append({'role':role,'slot':s['id'],'vectors':len(va),'original_record_sha256':sha(pa.with_suffix('.json')),'ablation_record_sha256':sha(pb.with_suffix('.json'))})
    write(out,{'status':'COMPLETE_FACTOR_REVERSAL_PASS','requests':len(rows),'vectors':sum(x['vectors'] for x in rows),'original_epoch':str(a),'ablation_epoch':str(b),'rows':rows,'scope':'Full endpoint/cycle and every saved target/draft vector; not just the first failure or a successful subset'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--original',required=True);p.add_argument('--ablation',required=True);p.add_argument('--out',required=True);a=p.parse_args();compare(a.original,a.ablation,a.out)
