"""Supplementary strict endpoint-boundary audit; frozen reason-only metric is preserved."""
import argparse, hashlib, json, pathlib
import verify
def main(root,output):
    doc=root/'benchmarks/rtx_target_only_bridge_v1';out=root/'work/rtx-target-only-bridge-v1'
    selected=verify.load(out/'SELECTED_ATTEMPTS.json');raw={}
    for key,b in selected.items():
        if not key.startswith('formal/'):continue
        p=root/b['record'];assert verify.sha(p)==b['sha256'];r=verify.load(p)
        raw[r['key']]=verify.raw_native(p.parent/b['attempt']/'native.log')
    assert len(raw)==171
    rows=[];summary={};tasks=verify.load(doc/'COHORT.json')['tasks']
    for a,b in [('U2','N1'),('U2','N0'),('N0','N1')]:
        detail=[]
        for t in tasks:
            for rep in [1,2,3]:
                left,right=raw[f'{t}/{a}/{rep}'],raw[f'{t}/{b}/{rep}']
                boundary=lambda x:{'length':len(x['ids']),'reason':x['endpoint'],'terminal_id':x['ids'][-1]}
                x,y=boundary(left),boundary(right);d={'pair':a+'/'+b,'task':t,'rep':rep,'left_boundary':x,'right_boundary':y,'reason_equal':x['reason']==y['reason'],'full_boundary_equal':x==y,'array_equal':left['ids']==right['ids'],'joint_array_boundary_equal':left['ids']==right['ids'] and x==y};detail.append(d);rows.append(d)
        summary[a+'/'+b]={'pairs':57,'reason_equal':sum(d['reason_equal'] for d in detail),'full_boundary_equal':sum(d['full_boundary_equal'] for d in detail),'joint_array_boundary_equal':sum(d['joint_array_boundary_equal'] for d in detail),'all_three_boundary_equal_tasks':sum(all(d['full_boundary_equal'] for d in detail if d['task']==t) for t in tasks)}
    result={'status':'PASS','formal_raw_reparsed':171,'definition':'full endpoint boundary = (committed length, EOS/limit reason, terminal token ID); frozen primary reason-only endpoint metric is preserved separately','comparisons':summary,'rows':rows,'scope':'supplementary transparent endpoint-length clarification; no execution/predicate replacement or formal restart'}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[3]);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();main(a.root.resolve(),a.output)
