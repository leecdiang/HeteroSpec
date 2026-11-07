"""Derived reached-stage reports, joint index and counts; never launches inference."""
import json
from pathlib import Path
from prepare import ROOT,STUDY,save,sha,now
import verify_joint

def index():
    rows=[]
    for f in sorted(STUDY.glob('*_ARCHIVE.json')):
        r=json.loads(f.read_text(encoding='utf-8'));rows.append({'arm':r['arm'],'mode':r['mode'],'anonymous':r['anonymous'],'index':r['path'],'index_sha256':sha(ROOT/r['path']),'archive_sha256':r['sha256'],'bytes':r['bytes'],'parts':r['parts'],'actual_offline_result':r['offline_reconstruction']})
    save(STUDY/'ARTIFACT_MANIFEST.json',{'schema':'RTX_V3.joint_artifact_index','created_utc':now(),'archives':rows,'formal_observations_shared':False,'shared_engineering':'identical actual engineering run IDs disclosed in two author archives; not independent A/B samples','external_binary_assets_omitted':True})
    return rows

def reached():
    result=verify_joint.all_reached(ROOT);counts=verify_joint.counts(ROOT,STUDY);save(STUDY/'EXECUTION_COUNTS.json',{'actual':counts,'reached':{k:v for k,v in result.items() if k not in ['engineering','counts','selection']}})
    states={}
    for arm,label,key in [('A_trajectory','A','A'),('B_matched_cost','B','B')]:
        report=STUDY/arm/'REPORT.json';current=json.loads(report.read_text(encoding='utf-8')) if report.exists() else {'status':'NOT_REACHED','execution_complete':False,'actual_complete_runs':0}
        if key in result and not result[key].get('execution_complete',True):current=result[key];save(report,current)
        elif key=='A' and key not in result and 'A_pre_live' in result:
            terminal=json.loads((STUDY/'A_TERMINAL.json').read_text(encoding='utf-8')) if (STUDY/'A_TERMINAL.json').exists() else {'status':'PRE_LIVE_ONLY'}
            current={'status':terminal['status'],'execution_complete':False,'actual_pre_live_runs':result['A_pre_live'].get('valid_complete_runs',result['A_pre_live'].get('actual_valid_complete_runs',0)),'actual_live_runs':0,'pre_live':result['A_pre_live'],'terminal':terminal};save(report,current)
        states[label]=current['status'];validation=result.get(key,{'status':'NOT_REACHED','actual_formal_runs':0});save(STUDY/arm/'INDEPENDENT_VALIDATION.json',validation)
        lines=['# '+label+' actual reached result','',json.dumps(current,indent=2),'','Interpretation: fixed full cohort only. Any incomplete prefix has no speedup/CI claim. See raw archive and independent validation.','']
        (STUDY/arm/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    if (STUDY/'A_TERMINAL.json').exists():states['A_terminal']=json.loads((STUDY/'A_TERMINAL.json').read_text(encoding='utf-8'))
    stages={}
    for name in ['F0','F1','F2','B_START']:
        f=STUDY/(name+'_REMOTE_RECEIPT.json');stages[name]=json.loads(f.read_text(encoding='utf-8'))['commit'] if f.exists() else 'NOT_REACHED'
    complete=all(json.loads((STUDY/arm/'REPORT.json').read_text(encoding='utf-8')).get('execution_complete',False) for arm in ['A_trajectory','B_matched_cost'])
    out={'status':'FORMAL_COMPLETE' if complete else 'REACHED_PREFIX_DELIVERY','updated_utc':now(),'mode':json.loads((STUDY/'JOINT_PROTOCOL.json').read_text(encoding='utf-8'))['mode'],'states':states,'actual_counts':counts,'checkpoints':stages,'independent_status':result['status'],'formal_planned_is_not_actual':True}
    save(STUDY/'CLOSEOUT.json',out);save(STUDY/'JOINT_CHRONOLOGY.json',{'updated_utc':now(),'checkpoints':stages,'states':states,'ledger_sha256':sha(STUDY/'EXECUTION_LEDGER.jsonl'),'time_limit':'Git proves object membership and ancestry; host UTC/monotonic and HTTP server Date are disclosed finite-resolution observations, not a trusted timestamp service'})
    (STUDY/'CLOSEOUT.md').write_text('# Actual joint closeout\n\n'+json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n');return out
