"""Fail-closed phase, authorization and protected-byte checks before process launch."""
import hashlib,json,os,subprocess
from pathlib import Path
from prepare import ROOT,STUDY,ENGINEERING,sha,ledger,now

def read(name,study=STUDY):return json.loads((study/name).read_text(encoding='utf-8'))
def check_manifest(name,study=STUDY,root=ROOT):
    m=read(name,study)
    for p,v in m['files'].items():
        q=root/p
        if not q.is_file() or sha(q)!=v['sha256']:raise RuntimeError('FROZEN_BYTES_CHANGED: '+p)
    return m
def receipt(stage,study=STUDY):
    r=read(stage+'_REMOTE_RECEIPT.json',study)
    if r['commit']!=r['remote_ref'] or r['remote_ack_utc']>=now():raise RuntimeError('REMOTE_FREEZE_INVALID: '+stage)
    if not r.get('retrieved_files') or not r.get('full_retrieval_verified'):raise RuntimeError('REMOTE_CONTENT_NOT_RETRIEVED: '+stage)
    if r.get('synthetic_fixture'):
        if Path(study).resolve()==STUDY.resolve():raise RuntimeError('TEST_RECEIPT_FORBIDDEN_IN_REAL_METADATA')
    else:
        path=Path(study)/(stage+'_MANIFEST.json')
        if sha(path)!=r['manifest_sha256']:raise RuntimeError('CHECKPOINT_MANIFEST_CHANGED: '+stage)
        relative=path.relative_to(ROOT).as_posix()
        committed=subprocess.check_output(['git','show',r['commit']+':'+relative],cwd=ROOT)
        if hashlib.sha256(committed).hexdigest()!=r['manifest_sha256']:raise RuntimeError('CHECKPOINT_NOT_BOUND_TO_EXACT_COMMIT: '+stage)
    return r
def authorize(task,condition,phase=None,study=STUDY,root=ROOT):
    phase=phase or os.environ.get('HS_PHASE','ENGINEERING')
    try:
        if phase=='ENGINEERING':
            if task not in ENGINEERING and task!='HumanEval/59' and not task.startswith('SYNTH_'):raise RuntimeError('ENGINEERING_TASK_NOT_EXPOSED')
            audit=read('EXPOSURE_AUDIT.json',study)
            if audit['status'] not in ['PASS','RESERVED_POOL_BLOCKED'] or audit['errors'] or audit.get('auditor_sha256')!=sha(Path(__file__).with_name('audit.py')):raise RuntimeError('EXPOSURE_AUDIT_NOT_COMPLETE')
            return
        if phase not in ['A_PRE_LIVE','A_LIVE','B_FORMAL']:raise RuntimeError('UNRECOGNIZED_PHASE')
        if (study/'JOINT_BLOCKED.json').exists():raise RuntimeError('JOINT_IDENTITY_OR_PROVENANCE_BLOCK_IRREVERSIBLE')
        auth=read('AUTHORIZATION.json',study);f0=receipt('F0',study)
        if auth.get('instruction')!='EXECUTE_FROZEN' or auth.get('reviewed_source_sha')!=f0['commit']:raise RuntimeError('EXACT_F0_REVIEW_REQUIRED')
        check_manifest('F0_MANIFEST.json',study,root)
        p=read('JOINT_PROTOCOL.json',study)
        tasks=p['A']['task_ids'] if phase.startswith('A_') else p['B']['task_ids']
        if task not in tasks:raise RuntimeError('TASK_OUTSIDE_FROZEN_COHORT')
        if phase.startswith('A_') and (study/'A_TERMINAL.json').exists():raise RuntimeError('A_TERMINAL_IRREVERSIBLE')
        if phase=='A_PRE_LIVE':
            receipt('F1',study);check_manifest('F1_MANIFEST.json',study,root)
            if condition not in p['A']['pre_live_wire_conditions']:raise RuntimeError('LIVE_BEFORE_F2')
        elif phase=='A_LIVE':
            if condition!='RTX_BATCHED_K2':raise RuntimeError('A_LIVE_CONDITION_INVALID')
            receipt('F2',study);check_manifest('F2_MANIFEST.json',study,root)
            if read('PRE_LIVE_QUALIFICATION.json',study)['status']!='PRE_LIVE_QUALIFIED':raise RuntimeError('REPLAY_NOT_QUALIFIED')
        else:
            if condition not in p['B']['wire_conditions']:raise RuntimeError('B_CONDITION_INVALID')
            receipt('B_START',study)
            if p['mode']=='A19_B19':
                if (study/'A_TERMINAL.json').exists():
                    if read('A_TERMINAL.json',study)['status'] not in ['INCOMPLETE_OPERATIONAL_FAILURE','REPLAY_QUALIFICATION_FAILED','REPEAT_INSTABILITY','PROVENANCE_INVALID']:raise RuntimeError('INVALID_A_TERMINAL')
                else:
                    receipt('F2',study);check_manifest('F2_MANIFEST.json',study,root)
                    if not read('A_trajectory/REPORT.json',study).get('execution_complete'):raise RuntimeError('A_NOT_COMPLETE_OR_TERMINAL')
    except Exception as exc:
        ledger({'phase':phase,'study':'RTX_TRAJECTORY_AND_MATCHED_COST_V4','event':'launch_rejected','task_id':task,'condition':condition,'status':'REJECTED','reason':str(exc)})
        raise
