#!/usr/bin/env python3
"""Export old anonymous bytes plus V4 arrays/times from exact retained inputs."""
import hashlib, json, shutil, zipfile
from pathlib import Path
from verify_rtx_v4_projection_v087 import validate, digest_ids
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'paper/mlsys2027';B=ROOT/'benchmarks/rtx_trajectory_cost_v4';C=P/'evidence/RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002';OUT=P/'manuscript/output';E=P/'evidence'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
    legacy=OUT/'anonymous-evidence-index-v0.8.6.zip'
    assert sha(legacy)=='7b83b97bea19c5d0ddf28d1cec49f103165849bff8a76ef5fac1da6de3a0f00f'
    with zipfile.ZipFile(legacy) as z:
        files={n:z.read(n) for n in z.namelist()}; old=json.loads(files.pop('SHA256SUMS.json'))
        assert set(old)==set(files) and all(hashlib.sha256(files[n]).hexdigest()==h for n,h in old.items())
    sources={}
    def bound(p): sources[p.relative_to(ROOT).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size};return read(p)
    pred=bound(B/'A_trajectory/RESERVED_PREDICTIONS.json');live=bound(C/'A-live.ORIGINAL_RECORDS.json');timed=bound(C/'B-formal.ORIGINAL_RECORDS.json')
    selection=bound(B/'RESERVED_SET.json');contract=bound(B/'EOG_VOCAB_CONTRACT.json');report=bound(B/'B_matched_cost/REPORT.json');schedule=bound(B/'B_matched_cost/schedule.json')
    # Source membership is independently checked against main's exact Git blobs at integration.
    live_by={(r['task_id'],r['repetition']):r for r in live['runs']};a=[]
    def item(r): return {'ids':r['generated_ids'],'ids_sha256':digest_ids(r['generated_ids']),'termination':r['termination']}
    for r in pred['rows']:
        c={k:item(v) for k,v in r['conditions'].items()};c['A_NATIVE_BATCHED_LIVE']=item(live_by[r['task_id'],r['repetition']]);a.append({'task_id':r['task_id'],'repetition':r['repetition'],'conditions':c})
    b=[]
    for r in timed['runs']:
        t=r['timer'];export={'qpc_delta':t['end_qpc']-t['start_qpc'],'frequency':t['frequency'],'steady_delta_ns':t['end_steady_ns']-t['start_steady_ns'],'milliseconds':t['milliseconds'],'secondary_milliseconds':t['secondary_milliseconds'],'count':t['count'],'terminal_id':t['terminal_id']}
        b.append({'task_id':r['task_id'],'repetition':r['repetition'],'condition':r['condition'],**item(r),'timer':export})
    data={'version':'v0.8.7','study':'RTX_V4','tasks':selection['selected_task_ids'],'eog_ids':contract['eog_token_ids'],'selection':{'salt':selection['salt'],'eligible':selection['eligible_pool'],'excluded':sorted({'HumanEval/'+str(i) for i in range(164)}-set(selection['eligible_pool'])),'v3_newly_exposed':['HumanEval/'+str(i) for i in (2,16,59,86,157,158,161)]},'formal_counts':{'A_pre_live':228,'A_live':57,'B':171,'total':456,'independent_prompts':19},'A':a,'B':b,'schedule':schedule,'reported_B':{k:{n:v[n] for n in ('status','speedup','CI','prompt_ratios')} for k,v in report['paths'].items()},'export_boundary':'Post-study exact array and interval projection. QPC/steady absolute counters removed; original author logs retain native endpoints. No future-live-input isolation or trusted chronology proof from this projection alone.'}
    result=validate(data)
    files['evidence/RTX_V4.json']=(json.dumps(data,indent=2)+'\n').encode()
    files['verify_v086.py']=files['verify.py']
    files['verify_v4.py']=(Path(__file__).parent/'verify_rtx_v4_projection_v087.py').read_bytes()
    files['verify.py']=b'''#!/usr/bin/env python3
"""Stdlib reviewer checks: preserved primary/derived assertions and RTX V4."""
import hashlib,json
from pathlib import Path
from verify_original import validate
from analysis import compute
from verify_v4 import validate as validate_v4
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def main():
 m=read(ROOT/'SHA256SUMS.json');assert {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}==set(m)|{'SHA256SUMS.json'}
 for n,h in m.items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
 studies={p.stem:read(p) for p in (ROOT/'evidence').glob('*.json') if p.stem!='RTX_V4'}
 old=validate(studies);derived,_=compute(read(ROOT/'derived/inputs.json'));assert json.loads(json.dumps(derived))==read(ROOT/'derived/results.json')
 v4=validate_v4(read(ROOT/'evidence/RTX_V4.json'))
 print(json.dumps({'status':'PASS','prior_studies':old,'post_study_replay':'PASS','RTX_V4':v4,'limits':'Retained finite-cohort arrays, raw timer intervals and arithmetic. No GPU execution, trusted absolute-time or omitted-asset authentication.'}))
if __name__=='__main__':main()
'''
    index=json.loads(files['INDEX.json']);index['version']='v0.8.7';index['studies'].append('RTX_V4');index['freeze_roles']['RTX_V4']=['F0 source/assets/selection/gates','F1 predefined candidates','F2 four pre-live arrays and tapes before native live; amended authority preserved','B_START timer/schedule before 171 fresh observations','known-outcome reviewer projection is not a new prospective study']
    index['RTX_V4_full_anonymous_capsules']=[{'arm':'A','parts_index':'complete-anonymous-befd156992138902624406a2c8c6f8854494caad7c7c00df3c4cf3de5bd6f6c7.parts.json','sha256':'befd156992138902624406a2c8c6f8854494caad7c7c00df3c4cf3de5bd6f6c7','bytes':89274896},{'arm':'B','parts_index':'complete-anonymous-7be6bd011a2f3741d6788f19768a1f2f5e40deceebb394ec9dd631a951fe2157.parts.json','sha256':'7be6bd011a2f3741d6788f19768a1f2f5e40deceebb394ec9dd631a951fe2157','bytes':116890414}]
    index['RTX_V4_offline_entry']='python3 -B EXTRACTED/frozen_source/scripts/platform/rtx_trajectory_cost_v4/offline.py EXTRACTED'
    files['INDEX.json']=(json.dumps(index,indent=2)+'\n').encode()
    files['README.md']=b'''# Anonymous evidence index v0.8.7

Run `python3 -B verify.py` at this ZIP root. Standard library only, no models, GPU or network.
The five prior primary study projections, prior calculators and all derived input/result/CSV bytes are preserved. RTX V4 adds 285 A complete arrays and 171 B arrays/native timer intervals on 19 distinct prompts, preserving gate-before-cost interpretation and the original paired-prompt estimator.
This compact projection is made after known outcomes. It is not a prospective freeze, independent model reproduction, input-isolation proof, or authentication of original absolute time/omitted binaries. QPC and steady absolute counters are removed while native durations remain exact; author capsules retain full endpoints and logs. Content hashes may enable linkage and do not guarantee unlinkability.
INDEX.json separately identifies the unchanged full V2 H2 capsule and the V4 A/B anonymous parts indexes, hashes, lengths and CPU offline entry. Full capsules preserve tapes, raw logs, failure regressions and source. V3 terminal prefixes never enter V4's denominator; repetitions and A/B are not independent prompt cohorts.
'''
    preserved=[n for n in old if n not in ('INDEX.json','README.md','verify.py')]
    assert all(hashlib.sha256(files[n]).hexdigest()==old[n] for n in preserved)
    sums={n:hashlib.sha256(v).hexdigest() for n,v in sorted(files.items())};files['SHA256SUMS.json']=(json.dumps(sums,indent=2)+'\n').encode()
    output=OUT/'anonymous-evidence-index-v0.8.7.zip'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for n,v in sorted(files.items()):
            info=zipfile.ZipInfo(n,(2026,10,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,v)
    receipt={'status':'PASS','source_inputs':sources,'old_zip_sha256':sha(legacy),'old_members_byte_identical':preserved,'new_projection_recomputed':result,'output_sha256':sha(output),'output_bytes':output.stat().st_size,'scope':'Known-outcome projection; old arrays/estimators preserved; no new science execution'}
    (E/'RTX_V4_PROJECTION_V087_QA.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':'PASS','members':len(files),'old_members_preserved':len(preserved),'output_bytes':output.stat().st_size}))
if __name__=='__main__':prepare()
