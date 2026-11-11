"""Normalize actual historical RTX/B570 request records and new observer bytes.
No inferred native states are manufactured. State bytes must come from the host.
"""
from __future__ import annotations
import argparse,hashlib,shutil
from pathlib import Path
from common import *
from trace import reconstruct
from active_kv import parse


def trace_from_row(row,prompt,vocab,eog_ids,platform):
    if platform=='rtx':
        ids=row['ids'];cycles=row.get('cycles',[])
        steps=[{'kind':'verify','base':c['base'],'seed':c['seed'],'proposals':c['proposals'],
                'decisions':c['decisions'],'accepted':c['accepted']} for c in cycles]
        spec=row['draft_enabled'];k=row['k'] if spec else 0
        stop=row['stop_reason']
    else:
        ids=row['endpoint']['ids'];cycles=row.get('cycles',[])
        steps=[{'kind':'verify','base':c['base'],'seed':c['seed_id'],'proposals':[c['proposal']],
                'decisions':c['decisions'],'accepted':c['accepted']} for c in cycles]
        # Explicit slot binding supplied by host; cap1 can have no cycles with draft enabled.
        spec=row['study_draft_enabled'];k=1 if spec else 0;stop=row['endpoint']['stop_reason']
    need(ids,'missing endpoint');need(type(row['study_cap']) is int,'actual cap binding missing')
    if not spec:
        need(not cycles,'ordinary arm contains speculative cycles')
        steps=[{'kind':'ordinary','base':len(prompt)+i-1,'seed':ids[i-1],'decision':ids[i]} for i in range(1,len(ids))]
    t={'prompt_ids':prompt,'cap':row['study_cap'],'vocab':vocab,'eog_ids':eog_ids,'k':k,'initial':ids[0],'steps':steps}
    d=reconstruct(t);need(d['tokens']==ids and d['stop_reason']==stop,'recorded endpoint disagrees with independent transaction')
    return t,d


def normalize(platform, row_path, native_root, prompt_path, binding_path, profile_path, role, invocation, out):
    need(role in ('candidate','free_reference'),'role')
    row=read(row_path);prompt=read(prompt_path)['prompt_ids'];binding=read(binding_path);profile=read(profile_path)
    need(profile['target_model_sha256']==binding['target_model_sha256'],'profile/model mismatch')
    need(binding['input_sha256']==digest(prompt),'prompt identity')
    t,d=trace_from_row(row,prompt,binding['vocab'],binding['eog_ids'],platform)
    need(t['cap']==binding['cap'],'cap identity');need(not out.exists(),'fresh normalized capture required');out.mkdir(parents=True)
    def save(data):
        sha=hashlib.sha256(data).hexdigest();p=out/'cas'/sha[:2]/sha;p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():p.write_bytes(data)
        else:need(p.read_bytes()==data,'CAS inconsistency')
        return {'path':p.relative_to(out).as_posix(),'bytes':len(data),'sha256':sha}
    def rtx_vector(key):
        name='initial' if key=='initial' else ('ordinary-'+str(int(key[4:].split('/')[0])+1) if t['k']==0 else 'verify-'+key[4:].replace('/','-'))
        return contained(native_root,name+'.f32').read_bytes()
    def b570_vector(key):
        name='target_initial' if key=='initial' else ('target_ordinary/'+str(int(key[4:].split('/')[0])+1) if t['k']==0 else 'target_verify/'+key[4:])
        desc=row['vectors'][name];return check_blob(native_root,desc,expected=4*binding['vocab']).read_bytes()
    vectors=[]
    for use in d['vector_uses']:
        raw=rtx_vector(use['key']) if platform=='rtx' else b570_vector(use['key'])
        need(len(raw)==4*binding['vocab'],'full target vocabulary not present')
        vectors.append({'key':use['key'],'prefix':use['prefix'],'blob':save(raw)})
    bstates={x['key']:x['snapshot'] for x in row.get('state_boundaries',[])}
    states=[]
    for i,s in enumerate(d['states']):
        key='initial' if i==0 else ('ordinary-'+str(i) if t['k']==0 else 'commit-'+str(i-1))
        if platform=='rtx':
            p=contained(native_root,'state/'+key+'/sequence.bin');raw=p.read_bytes()
            frontier=contained(native_root,'state/'+key+'/frontier.f32').read_bytes()
            meta={a:b for a,b in (line.split('=',1) for line in contained(native_root,'state/'+key+'/capture.txt').read_text().splitlines() if '=' in line)}
            need(int(meta['position_min'])==0 and int(meta['position_max'])==len(s['prefix'])-1,'actual state position differs')
        else:
            bk=key.replace('-','/');snap=bstates[bk]
            need(snap['kv_min']==0 and snap['kv_max']==len(s['prefix'])-1,'actual Vulkan KV bounds')
            raw=check_blob(native_root,snap['kv']).read_bytes();frontier=check_blob(native_root,snap['initial_logits'],expected=4*binding['vocab']).read_bytes()
        canonical,scope=parse(raw,list(range(len(s['prefix']))),profile)
        need(scope['bytes_per_token']==binding['active_kv_bytes_per_token'],'profile byte size')
        need(len(frontier)==4*binding['vocab'],'frontier byte size')
        states.append({**s,'active_kv':save(canonical),'frontier':save(frontier),
            'active_layout_sha256':scope['active_layout_sha256'],'raw_sequence_sha256':hashlib.sha256(raw).hexdigest(),
            'profile_sha256':digest(profile)})
    capture={'role':role,'invocation_id':invocation,'execution':'NATIVE','completed':True,
      'reference_bridge_passed':binding.get('reference_bridge_passed') is True,'fallback_count':row['study_fallback_count'],
      'binding':{k:binding[k] for k in ('reference_identity_sha256','target_model_sha256','producer_sha256','lifecycle_sha256','input_sha256','cap','vocab','active_kv_bytes_per_token')},
      'trace':t,'vectors':vectors,'states':states,'input_record_sha256':file_sha(row_path),
      'native_origin':'supplied by host; this normalizer does not attest execution'}
    if role=='free_reference':
        need(row.get('study_reference_received_forced_tape') is False,'autonomous reference input contaminated/unknown')
        capture.update(received_forced_tape=False,autonomous=True)
    write_new(out/'capture.json',capture);return capture


def reference_jobs(capture_paths:list[Path],producer:dict)->dict:
    """Prefix sharing only within each independent reference path; never import candidate KV."""
    captures=[read(p) for p in capture_paths];need(captures,'no captures')
    binding=captures[0]['binding'];prompt=captures[0]['trace']['prompt_ids'];prefixes={tuple(prompt)}
    for c in captures:
        need(c['binding']==binding and c['trace']['prompt_ids']==prompt,'mixed reference family')
        for v in c['vectors']:prefixes.add(tuple(v['prefix']))
        for s in c['states']:prefixes.add(tuple(s['prefix']))
    for pref in prefixes:need(pref[:len(prompt)]==tuple(prompt),'forced path has a different producer prefix')
    ordered=sorted(prefixes,key=lambda p:(-len(p),p));maximal=[]
    for p in ordered:
        if not any(q[:len(p)]==p for q in maximal):maximal.append(p)
    need(all(type(x) is int and x>0 for x in producer['caller_lengths']),'invalid producer width')
    need(sum(producer['caller_lengths'])==len(prompt),'historical producer callers missing')
    need(len(producer['last_output_flags'])==len(producer['caller_lengths']),'historical producer masks missing')
    need(all(type(x) is bool for x in producer['last_output_flags']) and producer['last_output_flags'][-1],'invalid historical producer output flags')
    jobs=[{'role':'forced_reference','prompt_ids':prompt,'forced_suffix':list(p[len(prompt):]),
           'producer':producer,'binding':binding,'no_candidate_payload':True} for p in sorted(maximal)]
    return {'schema':1,'jobs':jobs,'request_reservation':len(jobs),
            'decoded_token_rows_reservation':sum(len(p) for p in maximal),
            'prefixes_required':len(prefixes),'rule':'separate scalar replay, original prompt producer, no candidate state import',
            'free_reference_job':{'role':'free_reference','prompt_ids':prompt,'cap':binding['cap'],'producer':producer,'binding':binding}}


def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
    a=s.add_parser('capture');a.add_argument('platform',choices=['rtx','b570']);
    for name in ('row','native_root','prompt','binding','profile','out'):a.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    a.add_argument('--role',choices=['candidate','free_reference'],required=True);a.add_argument('--invocation',required=True)
    r=s.add_parser('reference-jobs');r.add_argument('--captures',nargs='+',type=Path,required=True);r.add_argument('--producer',type=Path,required=True);r.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.cmd=='capture':normalize(a.platform,a.row,a.native_root,a.prompt,a.binding,a.profile,a.role,a.invocation,a.out)
    else:write_new(a.out,reference_jobs(a.captures,read(a.producer)))
if __name__=='__main__':main()
