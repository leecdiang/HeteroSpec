"""Actual, paid 2x2 donor-state/current-call test at frozen natural boundaries."""
import json
from close_base import HERE,read,save,sha,head,now
from diagnostics import StateServer
from close_server import measure
from analyze_bcd import signature

def prepare():
    plan=read(HERE/'C_STATE_MANIFEST.json');rows=read(HERE/'runs/c_boundary_state/RECORDS.json');sessions=[]
    for pair in sorted({r['pair'] for r in rows}):
        on=next(r for r in rows if r['pair']==pair and r['donor']=='on');off=next(r for r in rows if r['pair']==pair and r['donor']=='off')
        assert on['checkpoint']['sampler']==off['checkpoint']['sampler']
        original=next(s for s in plan['sessions'] if s['pair']==pair and s['donor']=='on')
        states={label:{'path':str((HERE/r['record_relative_path']).parent/'live/donor.state'),'sha256':r['donor_state_sha256']} for label,r in [('on',on),('off',off)]}
        sessions.append({**original,'name':f'pair{pair}-cross','states':states,'on_record':on['record_relative_path'],'off_record':off['record_relative_path']})
    save(HERE/'C_CROSS_MANIFEST.json',{'utc':now(),'state_manifest_sha256':sha(HERE/'C_STATE_MANIFEST.json'),'state_records_sha256':sha(HERE/'runs/c_boundary_state/RECORDS.json'),
       'sessions':sessions,'paid_parent_requests':len(sessions),'warmups':len(sessions),'warmup_cap':1,'paid_auxiliary_target_decode_calls':4*len(sessions),
       'current_paths':'Same actual caller at same UB; only the pre-existing current query-layout switch is crossed on/off. No native prefix/proposal is forced.',
       'qualification':'Exact donor state roundtrip and matching sampler contracts; unchanged parent source; same-path fork reproduces native decision for both donors; full parent output unchanged.',
       'build_identity':read(HERE/'generated/CROSS_BUILD_IDENTITY.json'),'claim_limit':'Local verification decisions only; no unique CUDA-kernel/root-cause or full continuation counterfactual claim.'})
    print('Freeze actual crossing manifest.',flush=True)

def run():
    source=head();plan=read(HERE/'C_CROSS_MANIFEST.json');exe=HERE/'generated/x-build/bin/llama-server.exe';assert sha(exe)==plan['build_identity']['server_sha256']
    root=HERE/'runs/c_boundary_cross';root.mkdir(parents=True,exist_ok=False);save(root/'MANIFEST.json',{'utc':now(),'source_commit':source,'plan_sha256':sha(HERE/'C_CROSS_MANIFEST.json')});records=[]
    for s in plan['sessions']:
        d=root/s['name'];print('START '+d.name,flush=True)
        for st in s['states'].values():assert sha(st['path'])==st['sha256']
        extra={'HS_CROSS_STATE_ON':s['states']['on']['path'],'HS_CROSS_STATE_OFF':s['states']['off']['path']}
        with StateServer(d,s['condition'],s['cut'],exe=exe,extra=extra) as server:r=measure(server,s['task'],s['condition']['name'],s['pair'],source,s['cap'])
        cp=read(d/'live/checkpoint.json');assert cp['source_after_cross_unchanged'] and cp['source_capture_unchanged'] and len(cp['cross_forks'])==4
        assert signature(r)==signature(read(HERE/s['on_record']))
        assert cp['committed_ids']==s['expected_call']['committed_prefix']
        assert all(cp[k]==s['expected_call']['call'][k] for k in ['tokens','positions','sequence_ids','logits_mask'])
        own=next(x for x in cp['cross_forks'] if x['donor']=='on' and x['current_query_batch'])
        for label,active in [('on',True),('off',False)]:
            rr=read(HERE/s[label+'_record']);events=[json.loads(x) for x in (HERE/rr['record_relative_path']).parent.joinpath('trace.jsonl').read_text().splitlines()]
            marker=next(i for i,x in enumerate(events) if x['event']=='live_checkpoint' and x['committed_count']==s['cut'])
            natural=next(x for x in events[marker+1:] if x['event']=='verify_decision')
            fork=next(x for x in cp['cross_forks'] if x['donor']==label and x['current_query_batch']==active)
            assert fork['sampled_ids']==natural['sampled_ids'],('same-path sham changed',label)
        for fork in cp['cross_forks']:
            norms=[g for g in fork['graphs'] if g['name']=='attn_norm-0'];nodes=[g for g in fork['graphs'] if g['name']=='hs_attn_query_batch-0']
            assert norms and bool(nodes)==fork['current_query_batch'];assert fork['state_roundtrip_equal'] and fork['sampler_clone_equal']
        r.update({'pair':s['pair'],'cut':s['cut'],'source_unchanged':True,'both_same_path_shams_equal':True,'checkpoint':cp,'auxiliary_target_decode_calls':4})
        p=d/'REQUEST.json';r['record_relative_path']=p.relative_to(HERE).as_posix();save(p,r);records.append(r)
        for st in s['states'].values():assert sha(st['path'])==st['sha256']
        print('DONE '+d.name+' both_same_path_shams=True',flush=True)
    save(root/'RECORDS.json',records);print('COMPLETE actual crossings',flush=True)

def analyze():
    trace=read(HERE/'runs/c_boundary_trace/RECORDS.json');states=read(HERE/'runs/c_boundary_state/RECORDS.json');cross=read(HERE/'runs/c_boundary_cross/RECORDS.json');summary=[]
    for r in cross:
        forks=r['checkpoint']['cross_forks'];lookup={(x['donor'],x['current_query_batch']):x['sampled_ids'] for x in forks}
        summary.append({'pair':r['pair'],'cut':r['cut'],'both_same_path_shams_equal':True,'native_call_tokens':r['checkpoint']['tokens'],
           'decisions':[{k:x[k] for k in ['donor','current_query_batch','sampled_ids','accepted_proposals']} for x in forks],
           'current_path_effect_on_donor_on':lookup['on',False]!=lookup['on',True], 'current_path_effect_on_donor_off':lookup['off',False]!=lookup['off',True],
           'state_effect_current_on':lookup['on',True]!=lookup['off',True],'state_effect_current_off':lookup['on',False]!=lookup['off',False]})
    out={'status':'COMPLETE_QUALIFIED_LOCAL_CROSSINGS','paid_requests':len(trace)+len(states)+len(cross),'warmups':len(trace)+len(states)+len(cross),
        'auxiliary_target_decode_calls':4*len(cross),'paid_trace_results':[{'pair':r['pair'],'condition':r['condition'],'reference_equal':r['reference_equal'],'tokens':len(r['response']['tokens']),'endpoint':r['endpoint']} for r in trace],
        'state_comparisons':read(HERE/'generated/C_STATE_COMPARISONS.json'),'crossings':summary,'claim_limit':'Naturally aligned local verification boundary. State and query-layout current-call effects, not a unique operator/CUDA dispatch proof or full continuation counterfactual.'}
    save(HERE/'generated/C_BOUNDARY_DIAGNOSTICS.json',out);print({'status':out['status'],'paid_requests':out['paid_requests'],'auxiliary_decodes':out['auxiliary_target_decode_calls'],'crossings':summary},flush=True)

if __name__=='__main__':
    import sys
    globals()[sys.argv[1]]()
