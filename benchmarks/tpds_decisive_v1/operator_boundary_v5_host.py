"""Continue finite boundary qualification after host-buffer registration repair."""
from operator_boundary_host import *

def main():
    rows=[]
    for model in ('8B','0.6B'):
        profile=json.loads((ROOT/('O-profile-'+model)/'PROFILE.json').read_bytes());states=ROOT/('O-prefix-'+model)
        if model=='8B':
            for label in ('O-prefix-v4-8B','O-boundary-v4-8B-original'):
                assert json.loads((RUNS/label/'exit.json').read_bytes())['status']=='COMPLETE'
            original=RUNS/'O-boundary-v4-8B-original'
        else:
            states.mkdir()
            units=[dict(id='prefix-'+str(n),mode='prefix',arm='S1',pos=n,width=1,state=str(states/(str(n)+'.bin'))) for n in sorted({p for p,q in CELLS})]
            execute_operator('O-prefix-v5-'+model,'original',dict(units=units),model,OP/'original-driver-v5')
            original=None
        for arm in (('graph_tiles','backend_loop4','packed') if original else ('original','graph_tiles','backend_loop4','packed')):
            units=[dict(id='p'+str(p)+'-q'+str(q),mode='qual',arm='S1' if arm=='original' else 'QB-local',pos=p,width=q,state=str(states/(str(p)+'.bin'))) for p,q in CELLS]
            out=execute_operator('O-boundary-v5-'+model+'-'+arm,arm,dict(units=units),model,OP/(arm+'-driver-v5'))
            if arm=='original':original=out;continue
            for p,q in CELLS:
                key='p'+str(p)+'-q'+str(q);a=out/key;r=original/key;vectors={x.name:sha(x) for x in a.glob('*.f32')};expected={x.name:sha(x) for x in r.glob('*.f32')}
                ca,scope=parse((a/'sequence.bin').read_bytes(),list(range(p+q+1)),profile);cr,_=parse((r/'sequence.bin').read_bytes(),list(range(p+q+1)),profile)
                rows.append(dict(model=model,arm=arm,prefix=p,width=q,all_target_vectors_equal=bool(vectors) and vectors==expected,vector_count=len(vectors),active_target_kv_equal=ca==cr,active_sha256=hashlib.sha256(ca).hexdigest(),reference_sha256=hashlib.sha256(cr).hexdigest(),physical_record=str(a/'receipt.json')))
            put(out/'STATE_QUALIFICATION.json',[x for x in rows if x['model']==model and x['arm']==arm]);print('boundary',model,arm,'equal',all(x['all_target_vectors_equal'] and x['active_target_kv_equal'] for x in rows if x['model']==model and x['arm']==arm),flush=True)
    put(ROOT/'O-BOUNDARY-QUALIFICATION.json',dict(rows=rows,all_equal=all(x['all_target_vectors_equal'] and x['active_target_kv_equal'] for x in rows),runtime_version=5,scope='finite physical-prefix and width matrix, scalar continuation and full active target state'))

if __name__=='__main__':main()
