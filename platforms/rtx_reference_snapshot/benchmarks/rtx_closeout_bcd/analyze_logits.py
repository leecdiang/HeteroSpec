"""Offline float witnesses at the jointly reached natural decision boundary."""
import numpy as np
from close_base import HERE,read,save,sha

def main():
    records=read(HERE/'runs/c_boundary_cross/RECORDS.json');pairs=[]
    for r in records:
        d=(HERE/r['record_relative_path']).parent/'live';cp=r['checkpoint'];forks={(f['donor'],f['current_query_batch']):f for f in cp['cross_forks']}
        a=forks['on',True]['sampled_ids'];b=forks['off',False]['sampled_ids'];idx=next(i for i,(x,y) in enumerate(zip(a,b)) if x!=y)
        assert idx<len(a) and idx<len(b)
        arrays={};paths={}
        for donor in ['on','off']:
            for active in [False,True]:
                p=d/f'cross-{donor}-{"querybatch" if active else "ordinary"}-row{idx}.f32';x=np.fromfile(p,dtype='<f4');assert len(x)>max(a[idx],b[idx]) and np.isfinite(x).all()
                arrays[donor,active]=x.astype(np.float64);paths[donor,str(active)]={'file':p.relative_to(HERE).as_posix(),'sha256':sha(p)}
        margins={f'{donor}_{active}':float(x[b[idx]]-x[a[idx]]) for (donor,active),x in arrays.items()}
        result={'pair':r['pair'],'committed_cut':r['cut'],'jointly_reached_logits_row':idx,'first_different_generated_token_one_based':r['cut']+idx+1,'vocab_logits':len(next(iter(arrays.values()))),
                'reference_EOS_minus_alternative_margins':margins,
                'current_layout_logit_linf_by_state':{donor:float(np.max(np.abs(arrays[donor,False]-arrays[donor,True]))) for donor in ['on','off']},
                'state_logit_linf_by_current_layout':{str(active):float(np.max(np.abs(arrays['on',active]-arrays['off',active]))) for active in [False,True]},
                'bound_file_identities':[{'donor':k[0],'current_query_batch':k[1],**v} for k,v in paths.items()],
                'limit':'Actual float witnesses, not an operator-specific error bound or an online calibrated guard.'}
        pairs.append(result)
    save(HERE/'generated/C_LOGIT_WITNESSES.json',pairs);print([{k:v for k,v in x.items() if k!='bound_file_identities'} for x in pairs],flush=True)

if __name__=='__main__':main()
