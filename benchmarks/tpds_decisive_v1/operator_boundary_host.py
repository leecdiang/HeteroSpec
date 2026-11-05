"""Finite trained-model widths and physical-head boundaries against original R."""
from operator_host import *
from active_kv import parse
import hashlib
CELLS=[(1,q) for q in (1,4,5,7,8,9,16,31,32)]+[(255,9),(256,32),(257,7),(511,5)]
def main():
    rows=[]
    for model in ('8B','0.6B'):
        profile=json.loads((ROOT/('O-profile-'+model)/'PROFILE.json').read_bytes());states=ROOT/('O-prefix-'+model);states.mkdir()
        units=[dict(id='prefix-'+str(n),mode='prefix',arm='S1',pos=n,width=1,state=str(states/(str(n)+'.bin'))) for n in sorted({p for p,q in CELLS})]
        execute_operator('O-prefix-v4-'+model,'original',dict(units=units),model)
        for arm in ('original','graph_tiles','backend_loop4','packed'):
            units=[dict(id='p'+str(p)+'-q'+str(q),mode='qual',arm='S1' if arm=='original' else 'QB-local',pos=p,width=q,state=str(states/(str(p)+'.bin'))) for p,q in CELLS]
            out=execute_operator('O-boundary-v4-'+model+'-'+arm,arm,dict(units=units),model)
            if arm=='original':continue
            original=RUNS/('O-boundary-v4-'+model+'-original')
            for p,q in CELLS:
                key='p'+str(p)+'-q'+str(q);a=out/key;r=original/key;vectors={x.name:sha(x) for x in a.glob('*.f32')};expected={x.name:sha(x) for x in r.glob('*.f32')}
                ca,scope=parse((a/'sequence.bin').read_bytes(),list(range(p+q+1)),profile);cr,_=parse((r/'sequence.bin').read_bytes(),list(range(p+q+1)),profile)
                rows.append(dict(model=model,arm=arm,prefix=p,width=q,all_target_vectors_equal=vectors==expected,vector_count=len(vectors),active_target_kv_equal=ca==cr,active_sha256=hashlib.sha256(ca).hexdigest(),reference_sha256=hashlib.sha256(cr).hexdigest(),physical_record=str(a/'receipt.json')))
            put(out/'STATE_QUALIFICATION.json',[x for x in rows if x['model']==model and x['arm']==arm]);print('boundary complete',model,arm,'equal',all(x['all_target_vectors_equal'] and x['active_target_kv_equal'] for x in rows if x['model']==model and x['arm']==arm),flush=True)
    put(ROOT/'O-BOUNDARY-QUALIFICATION.json',dict(rows=rows,all_equal=all(x['all_target_vectors_equal'] and x['active_target_kv_equal'] for x in rows),scope='finite explicit physical-prefix and width matrix; scalar continuation and full committed active target state; natural service qualification remains separate'))
if __name__=='__main__':main()
