"""Strict extracted inventory and independent recomputation; no execution imports."""
import copy,hashlib,json,sys
from pathlib import Path
import verify_joint,verify_common,verify_B
def main(root):
    root=Path(root);m=verify_common.read(root/'MANIFEST.json');actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    verify_common.require(actual==set(m['files'])|{'MANIFEST.json'},'inventory extra/missing file')
    for name,v in m['files'].items():
        p=root/name;verify_common.require(p.stat().st_size==v['bytes'] and verify_common.sha(p)==v['sha256'],'inventory hash/size '+name)
    metadata=root/'metadata';engineering=verify_joint.engineering(root,metadata);selection=verify_joint.selection(metadata)
    negative=[]
    p=root/'work/negative-fixtures'
    if p.exists():
        for d in p.iterdir():
            if not (d/'record.json').exists():continue
            try:verify_common.check_run(d,metadata=metadata)
            except (ValueError,KeyError,IndexError,TypeError):negative.append(d.name)
            else:raise ValueError('negative raw evidence accepted offline '+d.name)
        for phase in ['A_LIVE','B_FORMAL']:
            try:verify_joint.launch_order(p/'state-fixture',phase,'2099-01-01T00:00:00+00:00')
            except ValueError:negative.append('premature_'+phase)
            else:raise ValueError('premature phase accepted offline')
        fixture=verify_common.read(p/'STATISTICAL_FIXTURE.json');expected=verify_B.calculate(fixture['rows'],fixture['protocol'],fixture['schedule'])
        verify_common.require(all(x['status']=='QUALIFIED' for x in expected['paths'].values()),'positive statistic fixture')
        try:verify_common.unique([{'run_id':'duplicate'},{'run_id':'duplicate'}])
        except ValueError:negative.append('duplicate_run')
        else:raise ValueError('duplicate collection accepted offline')
        cs=fixture['protocol']['conditions'];wrong=copy.deepcopy(expected);wrong['paths'][cs[1]]['speedup']=1/wrong['paths'][cs[1]]['speedup'];tests=[('wrong_ratio_direction',wrong,expected)]
        blocked_rows=copy.deepcopy(fixture['rows']);next(x for x in blocked_rows if x['canonical_condition']==cs[1])['generated_ids']=[999,101,102];blocked=verify_B.calculate(blocked_rows,fixture['protocol'],fixture['schedule'])
        verify_common.require(blocked['paths'][cs[1]]['speedup'] is None and blocked['paths'][cs[2]]['status']=='QUALIFIED','blocked independent path fixture')
        wrong=copy.deepcopy(blocked);wrong['paths'][cs[1]]['speedup']=2;wrong['paths'][cs[1]]['CI']=[1.9,2.1];tests.append(('BLOCKED_written_as_speedup',wrong,blocked))
        wrong=copy.deepcopy(expected);wrong['paths'][cs[1]]['total_pairs']=144;tests.append(('wrong_gate_denominator',wrong,expected))
        for name,actual_stat,expected_stat in tests:
            try:verify_B.check_numbers(actual_stat,expected_stat)
            except ValueError:negative.append(name)
            else:raise ValueError('negative statistic accepted offline '+name)
    previous_capture=[]
    for row in verify_common.read(metadata/'CAPTURE_REGRESSION.json')['actual_prior_failures_parsed_without_reclassification']:
        d=root/row['archived_copy'];record=verify_common.read(d/'record.json')
        verify_common.require(record['status']=='OPERATIONAL_FAILURE','original failed status lost')
        ids,reason=verify_common.replay.native_commits((d/'native.log').read_bytes().replace(b'\r\n',b'\n').decode('latin-1'))
        verify_common.require(len(ids)==128 and ids[-1]==151645 and reason=='EOS' and verify_common.arr(ids)==row['array_sha256'],'actual previous failure regression')
        if not m.get('anonymous',False):verify_common.require(verify_common.sha(d/'record.json')==row['original_record_sha256'] and verify_common.sha(d/'native.log')==row['native_log_sha256'],'original failed evidence changed')
        previous_capture.append(row['original_failed_run_id'])
    verify_common.require(len(previous_capture)==2,'previous capture regression coverage')
    capture_negative=[]
    for q in (root/'work/capture-regression').glob('*.log'):
        if q.name.startswith('POSITIVE_PREVIOUS_'):continue
        try:verify_common.replay.native_commits(q.read_bytes().replace(b'\r\n',b'\n').decode('latin-1'))
        except ValueError:capture_negative.append(q.name)
        else:raise ValueError('corrupted cap/EOG transport accepted offline '+q.name)
    verify_common.require(len(capture_negative)==14,'cap/EOG negative coverage incomplete')
    reached={}
    if (root/'work/A-live/records.json').exists() and verify_common.read(root/'work/A-live/records.json')['status']!='COMPLETE':reached['A']=verify_joint.partial(root,metadata,'A-live')
    elif (root/'work/A-live/records.json').exists():
        import verify_A
        reached['A']=verify_A.full(root,metadata)
    elif (root/'work/A-pre-live/records.json').exists() and verify_common.read(root/'work/A-pre-live/records.json')['status']!='COMPLETE':reached['A_pre_live']=verify_joint.partial(root,metadata,'A-pre-live')
    elif (root/'work/A-pre-live/records.json').exists():
        import verify_A
        reached['A_pre_live']=verify_A.pre_live(root,metadata);reached['A_pre_live'].pop('rows')
    if (root/'work/B-formal/records.json').exists():reached['B']=verify_joint.partial(root,metadata,'B-formal') if verify_common.read(root/'work/B-formal/records.json')['status']!='COMPLETE' else verify_B.full(root,metadata)
    receipts=[]
    if not m.get('anonymous',False):
        import verify_receipts
        for stage in ['F0','F1','F2','B_START']:
            if (metadata/(stage+'_REMOTE_RECEIPT.json')).exists():receipts.append(verify_receipts.checkpoint(root,metadata,stage))
    verify_common.require({p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}==actual,'verification wrote extra files')
    result={'status':'PASS','inventory_files':len(actual),'mode':m['mode'],'arm':m['arm'],'anonymous':m.get('anonymous',False),'selection':selection,'engineering_gates':engineering['gates'],'engineering_complete_runs':430,'capture_repair':engineering['capture_repair'],'capture_negative_rejections':capture_negative,'observer_pairs':20,'raw_negative_rejections':negative,'reached_formal':reached,'git_membership':receipts,'GPU_required':False,'network_required':False,'omitted_assets_authenticated':False,'anonymous_chronology_limit':m.get('anonymous',False)}
    print(json.dumps(result));return result
if __name__=='__main__':main(sys.argv[1])
