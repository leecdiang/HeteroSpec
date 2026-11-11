"""Bounded paid native trajectories and naturally aligned donor-state evidence."""
import importlib,json
from close_base import HERE,PHASE1,read,save,sha,head,now
from close_server import Server,measure
from analyze_bcd import signature
from run_c import inspect_trace

def prepare_trace():
    results=read(HERE/'generated/C_RESULTS.json');pairs=results['diagnostic_pairs'];assert len(pairs)<=2
    if not pairs:
        save(HERE/'generated/C_BOUNDARY_DIAGNOSTICS.json',{'status':'NOT_NEEDED','paid_requests':0,'warmups':0});print('No C boundary failures.',flush=True);return
    inputs={t['id']:t for t in read(HERE/'C_INPUTS.json')};mask=read(HERE/'generated/C_SELECTION.json')['condition']['mask'];sessions=[]
    for i,pair in enumerate(pairs,1):
        modes=[{'name':'scalar_reference','mask':0,'spec':False,'ub':1,'k':0},
               {'name':'matched_target','mask':3,'spec':False,'ub':pair['ub'],'k':0},
               {'name':'selected_speculation','mask':mask,'spec':True,'ub':pair['ub'],'k':pair['k']},
               {'name':'all_scopes','mask':15,'spec':True,'ub':pair['ub'],'k':pair['k']},
               {'name':'ordinary_speculation','mask':0,'spec':True,'ub':pair['ub'],'k':pair['k']}]
        for mode in modes:sessions.append({'name':f'pair{i}-{mode["name"]}','pair':i,'condition':mode,'task':inputs[pair['task']],'cap':pair['cap']})
    save(HERE/'C_DIAGNOSTIC_MANIFEST.json',{'utc':now(),'selection':'First at most two failed pairs by frozen width/cap/task ordering; no retuning.',
       'C_results_sha256':sha(HERE/'generated/C_RESULTS.json'),'C_records_sha256':sha(HERE/'runs/c/RECORDS.json'),'sessions':sessions,'paid_requests':len(sessions),'warmups':len(sessions),
       'capture':'Diagnostic forced-sync only; costs never claimed as speed. Additional all-on and ordinary controls are paid.',
       'alignment_rule':'Last actual target continuation call before reference divergence with identical committed prefix, tokens, positions, sequence IDs, logits mask and logical bounds in selected/ordinary paths. No forced prefix or proposal.'})
    print(f'Freeze diagnostic manifest: {len(sessions)} paid trajectories.',flush=True)

def trace():
    source=head();plan=read(HERE/'C_DIAGNOSTIC_MANIFEST.json');root=HERE/'runs/c_boundary_trace';root.mkdir(parents=True,exist_ok=False)
    save(root/'MANIFEST.json',{'utc':now(),'source_commit':source,'plan_sha256':sha(HERE/'C_DIAGNOSTIC_MANIFEST.json')});records=[]
    references={(r['task'],r['requested_cap']):signature(r) for r in read(HERE/'runs/c/RECORDS.json') if r['condition']=='scalar_reference' and r['repetition']==1 and r['width_k']==1}
    for s in plan['sessions']:
        d=root/s['name'];c=s['condition'];print('START '+d.name,flush=True)
        with Server(d,c,capture=True,exe=HERE/'generated/c-build/bin/llama-server.exe') as server:r=measure(server,s['task'],c['name'],s['pair'],source,s['cap'])
        r.update({'pair':s['pair'],'reference_equal':signature(r)==references[r['task'],r['requested_cap']]});p=d/'REQUEST.json';r['record_relative_path']=p.relative_to(HERE).as_posix();save(p,r)
        r['topology_proof']=inspect_trace(d/'trace.jsonl',c['mask'],2,c['ub'],c['spec']);save(p,r);records.append(r);print(f'DONE {d.name} reference_equal={r["reference_equal"]}',flush=True)
    save(root/'RECORDS.json',records);print('COMPLETE boundary trace',flush=True)

def calls(record):
    path=(HERE/record['record_relative_path']).parent/'trace.jsonl';events=[json.loads(s) for s in path.read_text().splitlines()]
    starts=[i for i,x in enumerate(events) if x['event']=='decode' and x['role']=='target' and x['positions'][0]==0];assert len(starts)==2
    events=events[starts[1]:];prefill=[x for x in events if x['event']=='decode' and x['role']=='target' and x['phase']=='prefill'];np=prefill[-1]['after']['max']+1
    result={}
    for x in events:
        if x['event']=='decode' and x['role']=='target' and x['phase']=='continuation':
            cut=x['positions'][0]-np+1;assert cut>=1 and record['response']['tokens'][cut-1]==x['tokens'][0]
            result[cut]={'call':{k:x[k] for k in ['tokens','positions','sequence_ids','logits_mask','before']},'committed_prefix':record['response']['tokens'][:cut],'prompt_tokens':np}
    return result

def prepare_state():
    rows=read(HERE/'runs/c_boundary_trace/RECORDS.json');plan=read(HERE/'C_DIAGNOSTIC_MANIFEST.json');sessions=[];alignments=[]
    for pair in sorted({r['pair'] for r in rows}):
        on=next(r for r in rows if r['pair']==pair and r['condition']=='selected_speculation');off=next(r for r in rows if r['pair']==pair and r['condition']=='ordinary_speculation');ref=next(r for r in rows if r['pair']==pair and r['condition']=='scalar_reference')
        a=calls(on);b=calls(off);eligible=[cut for cut in sorted(set(a)&set(b)) if a[cut]==b[cut] and a[cut]['committed_prefix']==ref['response']['tokens'][:cut]]
        alignment={'pair':pair,'status':'ALIGNED' if eligible else 'UNSUPPORTED','eligible_cuts':eligible,'selected_cut':max(eligible) if eligible else None}
        alignments.append(alignment)
        if not eligible:continue
        cut=max(eligible)
        for label,r in [('on',on),('off',off)]:
            original=next(s for s in plan['sessions'] if s['pair']==pair and s['condition']['name']==r['condition'])
            sessions.append({**original,'name':f'pair{pair}-{label}','donor':label,'cut':cut,'expected_call':a[cut],'expected_output_record':r['record_relative_path'],'expected_output_sha256':sha(HERE/r['record_relative_path'])})
    save(HERE/'C_STATE_MANIFEST.json',{'utc':now(),'diagnostic_records_sha256':sha(HERE/'runs/c_boundary_trace/RECORDS.json'),'alignments':alignments,'sessions':sessions,
        'paid_requests':len(sessions),'warmups':len(sessions),'warmup_cap':1,'capture':'Exact existing checkpoint; no forks, edits to source state or previous-logit consumption. Main native outputs must reproduce paid traces.'})
    print({'alignments':alignments,'paid_state_capture_requests':len(sessions)},flush=True)

class StateServer(Server):
    def __init__(self,directory,condition,cut,exe=None,extra=None):
        super().__init__(directory,condition,capture=True,exe=exe);self.first=True
        self.extra={'HS_LIVE_CAPTURE':str(directory/'live'),'HS_LIVE_CUT':str(cut),**(extra or {})}
    def complete(self,prompt,cap):
        if self.first:self.first=False;return super().complete(prompt,1)
        return super().complete(prompt,cap)
    def __enter__(self):
        module=importlib.import_module('server');original=module.env
        module.env=lambda mask,capture:{**original(mask,capture),**self.extra}
        try:return super().__enter__()
        finally:module.env=original

def state():
    source=head();plan=read(HERE/'C_STATE_MANIFEST.json');root=HERE/'runs/c_boundary_state';root.mkdir(parents=True,exist_ok=False)
    save(root/'MANIFEST.json',{'utc':now(),'source_commit':source,'plan_sha256':sha(HERE/'C_STATE_MANIFEST.json')});records=[]
    for s in plan['sessions']:
        d=root/s['name'];print('START '+d.name,flush=True)
        with StateServer(d,s['condition'],s['cut'],exe=HERE/'generated/c-build/bin/llama-server.exe') as server:r=measure(server,s['task'],s['condition']['name'],s['pair'],source,s['cap'])
        expected=read(HERE/s['expected_output_record']);assert sha(HERE/s['expected_output_record'])==s['expected_output_sha256'] and signature(r)==signature(expected)
        checkpoint=read(d/'live/checkpoint.json');assert checkpoint['source_capture_unchanged'] and checkpoint['committed_ids']==s['expected_call']['committed_prefix']
        assert all(checkpoint[k]==s['expected_call']['call'][k] for k in ['tokens','positions','sequence_ids','logits_mask']) and checkpoint['bounds']==s['expected_call']['call']['before']
        r.update({'pair':s['pair'],'donor':s['donor'],'cut':s['cut'],'capture_unchanged':True,'checkpoint':checkpoint,'donor_state_sha256':sha(d/'live/donor.state')})
        p=d/'REQUEST.json';r['record_relative_path']=p.relative_to(HERE).as_posix();save(p,r);records.append(r);print('DONE '+d.name+' capture_unchanged=True',flush=True)
    save(root/'RECORDS.json',records)
    spec=__import__('importlib.util',fromlist=['spec_from_file_location']);m=spec.module_from_spec(spec.spec_from_file_location('state_reader',PHASE1/'parse_state.py'));m.__spec__.loader.exec_module(m)
    comparisons=[]
    for pair in sorted({r['pair'] for r in records}):
        on=next(r for r in records if r['pair']==pair and r['donor']=='on');off=next(r for r in records if r['pair']==pair and r['donor']=='off')
        cp1=on['checkpoint'];cp2=off['checkpoint'];assert cp1['sampler']==cp2['sampler'] and cp1['bounds']==cp2['bounds']
        np=next(s['expected_call']['prompt_tokens'] for s in plan['sessions'] if s['pair']==pair)
        x=m.compare(m.State((HERE/on['record_relative_path']).parent/'live/donor.state'),m.State((HERE/off['record_relative_path']).parent/'live/donor.state'),np)
        comparisons.append({'pair':pair,'cut':on['cut'],'sampler_contract_equal':True,'comparison':x})
    save(HERE/'generated/C_STATE_COMPARISONS.json',comparisons);print('COMPLETE boundary state capture',flush=True)

if __name__=='__main__':
    import sys
    globals()[sys.argv[1]]()
