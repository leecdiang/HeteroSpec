"""Compare every committed decision's full vector to the frozen scalar reference."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha
from audit import transactions

def audit(epoch,out):
    epoch=Path(epoch);baseline=read(epoch/'BASELINE_AUDIT.json');need(baseline['all_reference_equal'],'complete development endpoints first')
    rows=[]
    for i,x in enumerate(read(epoch/'DEV.json')):
        ref=epoch/f'units/baseline-oracle/native/reference/i{i}/heavy'
        for arm in ('R','M_PQ','M_QB','C_PQ','C_QB'):
            p=epoch/f'units/baseline-candidate/native/baseline/i{i}/{arm}/heavy.json';r=read(p);mapping=transactions(r);hashes=[]
            for index,key in mapping.items():
                a=p.with_suffix('')/'target'/(key+'.f32');b=ref/'target'/('initial.f32' if index==0 else f'ordinary-{index}.f32')
                ah,bh=sha(a),sha(b);hashes.append({'output_index':index,'actual':key,'actual_sha256':ah,'reference_sha256':bh,'bitwise_equal':ah==bh})
            rows.append({'input_id':x['id'],'arm':arm,'record_sha256':sha(p),'all_committed_full_vectors_equal':all(h['bitwise_equal'] for h in hashes),'vectors':hashes})
            del r
    write(out,{'status':'COMMITTED_REFERENCE_VECTORS_PASS' if all(r['all_committed_full_vectors_equal'] for r in rows) else 'COMMITTED_REFERENCE_VECTOR_DIFFERENCE','baseline_sha256':sha(epoch/'BASELINE_AUDIT.json'),'cells':rows,'scope':'Only actually committed decisions are aligned to R; rejected/conditional suffix rows are retained but not mislabeled scalar-reference decisions.'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--epoch',required=True);p.add_argument('--out',required=True);a=p.parse_args();audit(a.epoch,a.out)
