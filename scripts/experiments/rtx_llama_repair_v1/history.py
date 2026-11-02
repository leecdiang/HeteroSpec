"""Reconstruct the old Llama failure before native development. No model launch."""
from __future__ import annotations
import argparse, array, json, math, sys
from pathlib import Path
from lr_common import *
MANIFEST_SHA='2e52aee27acb551f3f3556a566ec5f83b123aa0d50a9c01da3666ac33a2fa4b9'
INDICES=(8,6,3)
IDS=('CodeContests/valid/108','CodeContests/valid/43','GSM8K/test/496')

def decision_rows(r):
    """Output position -> actual committed decision vector, including correction/bonus.
    Do not infer cycle/row from output_index//k; accepted prefixes vary.
    """
    ids=r['ids'];result={0:{'file':'target/initial.f32','cycle':None,'row':None}}
    if not r['draft_enabled']:
        result.update({i:{'file':f'target/ordinary-{i}.f32','cycle':None,'row':0} for i in range(1,len(ids))})
        return result
    previous=1
    for c in r['cycles']:
        end=c['output_length'];need(previous<end<=len(ids),'cycle output interval')
        emitted=end-previous;need(emitted<=len(c['decisions']),'more commits than decisions')
        need(c['seed']==ids[previous-1],'cycle pending seed differs')
        for row in range(emitted):
            need(c['decisions'][row]==ids[previous+row],'committed row mismatch')
            result[previous+row]={'file':f'target/verify-{c["cycle"]}-{row}.f32',
              'cycle':c['cycle'],'row':row,'base':c['base'],
              'input_position':c['base']+row,'output_index':previous+row,
              'verify_tokens':[c['seed']]+c['proposals'], 'cycle_output_begin':previous,
              'prior_context_row_tokens':([c['seed']]+c['proposals'])[:row+1]}
        previous=end
    need(previous==len(ids) and len(result)==len(ids),'incomplete decision map');return result

def vector(path):
    p=Path(path);need(p.stat().st_size==4*VOCAB,'truncated/full-vector vocabulary mismatch')
    a=array.array('f');a.frombytes(p.read_bytes())
    if sys.byteorder!='little':a.byteswap()
    need(all(math.isfinite(v) for v in a),'nonfinite vector');return a

def first_difference(a,b):
    for i,(x,y) in enumerate(zip(a,b)):
        if x!=y:return i
    return None if len(a)==len(b) else min(len(a),len(b))

def compare_records(a,b,afolder,bfolder):
    ea,eb=endpoint(a),endpoint(b);fd=first_difference(ea['ids'],eb['ids'])
    am,bm=decision_rows(a),decision_rows(b);common=min(len(ea['ids']),len(eb['ids']))
    limit=common if fd is None else min(common,fd+1);earliest=None
    for i in range(limit):
        ap=Path(afolder)/am[i]['file'];bp=Path(bfolder)/bm[i]['file']
        if file_hash(ap)!=file_hash(bp):earliest=i;break
    detail=None
    if fd is not None and fd<common:
        av,bv=vector(Path(afolder)/am[fd]['file']),vector(Path(bfolder)/bm[fd]['file'])
        top=lambda v:sorted(range(len(v)),key=lambda j:(-v[j],j))[:2]
        at,bt=top(av),top(bv)
        need(at[0]==ea['ids'][fd] and bt[0]==eb['ids'][fd],'greedy/vector endpoint mismatch')
        detail={'output_index':fd,'common_token_prefix':ea['ids'][:fd]==eb['ids'][:fd],
          'R_token':ea['ids'][fd],'candidate_token':eb['ids'][fd],
          'R_top2':at,'candidate_top2':bt,'R_margin':float(av[at[0]]-av[at[1]]),
          'candidate_margin':float(bv[bt[0]]-bv[bt[1]]),
          'R_vector':am[fd],'candidate_vector':bm[fd],
          'scope':'Same token prefix is NOT evidence of identical internal state.'}
    return {'endpoint_equal':ea==eb,'first_output_difference':fd,
      'earliest_saved_decision_vector_difference_on_common_prefix':earliest,'first_divergence':detail}

def reconstruct(repo,raw_root,out):
    out=Path(out);need(not out.exists(),'fresh history output required')
    manifest=git_read(repo,HISTORY,DIAG+'REQUESTS.jsonl');need(sha(manifest)==MANIFEST_SHA,'old request manifest identity')
    rows=[json.loads(l) for l in manifest.decode().splitlines() if l.strip()]
    need(len(rows)==54,'historical request count')
    panel=json.loads(git_read(repo,HISTORY,DIAG+'PANEL.json'))
    inputs=[panel['inputs'][i] for i in INDICES];need(tuple(x['id'] for x in inputs)==IDS,'old panel IDs/order changed')
    identity=json.loads(git_read(repo,HISTORY,DIAG+'EXECUTION_IDENTITY.json'))
    oldrefs=json.loads(git_read(repo,HISTORY,DIAG+'REFERENCES.json'))
    refs={x['id']:endpoint(oldrefs[str(i)]['R']) for i,x in zip(INDICES,inputs)}
    native={};vectors=0
    for row in rows:
        pin=row['raw_native_record'];p=confined(raw_root,pin['path'])
        need(p.stat().st_size==pin['bytes'] and file_hash(p)==pin['sha256'],'historical native record changed/missing')
        r=read(p);endpoint(r)
        need(r['input_id']==row['input_id'],'native input mismatch')
        for v in row['raw_vectors']:
            f=confined(raw_root,v['path']);need(file_hash(f)==v['sha256'],'raw vector hash mismatch')
            vals=vector(f);need(len(vals)==VOCAB,'vocabulary');vectors+=1
        key=(row['stage'],row['source_index'],row['producer'],row['arm'],row['observer'])
        need(key not in native,'duplicate historical coordinate');native[key]=(r,p)
    a1={}
    for i,x in zip(INDICES,inputs):
        rr,rp=native['diagnostic_A1',i,'NATIVE','R','heavy']
        need(endpoint(rr)==refs[x['id']],'historical strict R no longer matches')
        item={}
        for arm in ('C_PQ','C_QB'):
            r,p=native['diagnostic_A1',i,'NATIVE',arm,'heavy']
            item[arm]=compare_records(rr,r,rp.with_suffix(''),p.with_suffix(''))
        a1[x['id']]=item
    outcome=[]
    for key,(r,p) in native.items():
        stage,i,producer,arm,observer=key
        outcome.append({'stage':stage,'source_index':i,'input_id':r['input_id'],
          'producer':producer,'arm':arm,'observer':observer,
          'reference_equal':endpoint(r)==refs[r['input_id']], 'record_sha256':file_hash(p)})
    report={'status':'HISTORICAL_RAW_RECONSTRUCTED','requests':len(rows),'vectors_checked':vectors,
      'manifest_sha256':sha(manifest),'source_commit':HISTORY,'A1':a1,'outcomes':outcome,
      'root_cause':'UNRESOLVED; do not import Qwen RoPE diagnosis',
      'evidence_scope':'Hash/complete decision-vector replay and output-row mapping; no new native execution'}
    out.mkdir(parents=True)
    for name,obj in [('HISTORY.json',report),('DEV.json',{'inputs':inputs}),('REFERENCES.json',refs),('ORIGINAL_BINDING.json',identity)]:save(out/name,obj,exclusive=True)
    (out/'REQUESTS.original.jsonl').write_bytes(manifest)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('repo','raw-root','out'):p.add_argument('--'+n,required=True)
    a=p.parse_args();r=reconstruct(a.repo,a.raw_root,a.out);print(r['status'],r['requests'],r['vectors_checked'])
