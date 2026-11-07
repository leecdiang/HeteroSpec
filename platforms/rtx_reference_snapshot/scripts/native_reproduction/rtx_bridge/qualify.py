"""Independent qualification of endpoint, complete decision/state and raw vectors."""
import argparse,json,pathlib,statistics,sys,re
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from rtx_recover import read,sha,save
P=pathlib.Path
END=('ids','eog','length','terminal_id','stop_reason')
STATE=('cycles','target_final_kv','draft_final_kv')
def equal(a,b,keys):return all(a[k]==b[k] for k in keys)
def vectors(folder):return {str(p.relative_to(folder)):sha(p) for p in folder.rglob('*.f32')}
def inspect(root,name):
    root=P(root);data=read(root/name/'result.json');rows=data['requests'];checks=[]
    for task in sorted({r['slot']['task'] for r in rows}):
        rr=[r for r in rows if r['slot']['task']==task];refs=[r for r in rr if r['arm']=='R'];assert len(refs)==1
        ref=refs[0]
        for r in rr:
            checks.append(dict(slot=r['slot']['slot_id'],check='R_endpoint',passed=equal(ref,r,END)))
        for k in (1,3):
            group=[r for r in rr if r['arm']!='R' and r['k']==k]
            bases=[r for r in group if r['arm']=='PQ' and r['lifecycle']=='fresh' and r['capture']];assert len(bases)==1;base=bases[0];v=vectors(root/name/base['folder']);assert v
            for r in group:
                checks.append(dict(slot=r['slot']['slot_id'],check='matched_state',passed=equal(base,r,STATE)))
                if r['capture']:
                    current=vectors(root/name/r['folder']);checks.append(dict(slot=r['slot']['slot_id'],check='all_logits_including_discarded_rows',passed=current==v,vector_count=len(current)))
                    checks.append(dict(slot=r['slot']['slot_id'],check='actual_width',passed=str(k+1) in r['target_physical_width_hist']))
                    checks.append(dict(slot=r['slot']['slot_id'],check='geometry_present',passed=bool(r.get('geometry_count',len(r.get('geometry',[]))))))
                    full=read(root/name/(r['folder']+'.json'));geometry=full['geometry']
                    prefix='hs_attn_query_batch-' if r['arm']=='QB' else 'hs_attention_q-'
                    g=[x for x in geometry if x['name'].startswith(prefix)]
                    layers={int(x['name'].rsplit('-',1)[1]) for x in g}
                    shapes=all(x['ne'][1]==1 and x['ne'][2]==32 and x['ne'][3]==(k+1 if r['arm']=='QB' else 1) and '5070' in x['device'] for x in g)
                    checks.append(dict(slot=r['slot']['slot_id'],check='all36_target_layers_actual_layout_and_GPU',passed=layers==set(range(36)) and shapes,layers=len(layers)))
    status='PASS' if data['status']=='COMPLETE' and all(c['passed'] for c in checks) else 'FAIL'
    result=dict(status=status,process_status=data['status'],requests=len(rows),checks=checks,result_sha256=sha(root/name/'result.json'),independent='Python exact endpoint/state and SHA256 of every full-vocabulary vector; timers not qualification evidence')
    historical=root/'HISTORICAL_R_ENDPOINTS.json'
    if historical.exists():
        refs=read(historical)['endpoints'];oldchecks=[]
        for r in rows:
            old=refs[r['input_id']];oldchecks.append(dict(slot=r['slot']['slot_id'],passed=r['ids']==old['ids'] and r['eog']==old['eog_flags'] and r['length']==old['length'] and r['terminal_id']==old['terminal_id'] and r['stop_reason']==old['stop_reason']))
        result['historical_endpoint_checks']=oldchecks
        if not all(c['passed'] for c in oldchecks):result['status']='FAIL'
    save(root/(name+'-QUALIFICATION.json'),result)
    print(json.dumps(dict(status=status,requests=len(rows),checks=len(checks),failed=[c for c in checks if not c['passed']])));return result
def make_panel(root):
    root=P(root);slots=[]
    for task in range(12):
        specs=[('R',1,'fresh',True)]+[(arm,k,life,True) for k in (1,3) for life in ('fresh','resident') for arm in ('PQ_A','QB')]
        specs +=[(arm,k,life,False) for k in (1,3) for life in ('fresh','resident') for arm in ('PQ_A','QB')]
        for arm,k,life,capture in specs:
            slots.append(dict(slot_id=f'qual-{len(slots):04d}',task=task,label=arm,k=k,lifecycle=life,capture=capture,counters=False,category='qualification',attempt=0))
    save(root/'QUALIFICATION_SLOTS.json',slots);print('qualification slots',len(slots))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('name');a=ap.parse_args()
    if a.name=='prepare':make_panel(a.root)
    else:inspect(a.root,a.name)
