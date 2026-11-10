"""Construct F1 from saved S1 evidence, then admit the fixed S2 after readback."""
import argparse
import json
from pathlib import Path
import time
from freeze_cpu import PREFIX,public_text
from host import epoch,utc,verify_files,verify_public_readback,resource
from support import fresh,need,read,sha,positive
from terminal_guard import terminal_phase,telemetry_public


def caller_cost_proof(classes,gap,archive_bound):
    need(len(classes)==12 and {(c['cell'],c['arm'])for c in classes}=={(cell,arm)for cell in range(4)for arm in 'GBC'},
         'All twelve projection caller classes required')
    caller=sum(3*positive(c['max_observed_caller_s'])*1.25 for c in classes)
    required=caller+36*gap+positive(archive_bound)+900
    return dict(caller_cost_classes=classes,caller_bound_s=caller,fixed_gaps_s=36*gap,
                archive_transfer_replay_bound_s=archive_bound,closeout_reserve_s=900,required_s=required,
                caller_includes_complete_warmup=True,warmup_multiplier=1,whole_phase_fits=False)


def prepare(configuration,root,output):
    c=read(configuration)
    with terminal_phase(c,{'S1_PASSED_WAITING_F1_PUBLIC_READBACK'}):
        _prepare(configuration,root,output)


def _prepare(configuration,root,output):
    started=time.monotonic();c=read(configuration);s1=Path(c['output_root']);certificate=read(s1/'S1_CERTIFICATE.json')
    need(certificate['status']=='ALL_REQUIRED_S1_GATES_PASSED','No complete S1 qualification')
    verify_files(c['source_files']);need(not output.exists(),'Fresh F1 staging');output.mkdir(parents=True)
    for proof in certificate['comparisons']:need(sha(proof['path'])==proof['sha256'],'S1 comparison bytes changed')
    bindings=dict(schema='hs.strong.F1-private-binding.v1',S1_certificate_raw_sha256=sha(s1/'S1_CERTIFICATE.json'),
                  manifest_sha256=c['manifest_sha256'],compiled_closure_sha256=c['compiled_closure_sha256'],
                  input_bindings_sha256=certificate['input_bindings_sha256'],gold_registry_sha256=certificate['gold_registry_sha256'],
                  graphs_policy='off_only',formal_operations=72,formal_workers=36)
    fresh(output/'F1_DATA/QUALIFIED_BINDINGS.json',bindings)
    fresh(output/'F1_DATA/S2_COMPLETE_WORKERS.json',[w for w in read(c['manifest'])['workers']if w['kind']=='S2-fixed-diagnostic'])
    selected=[s1/'S1_CERTIFICATE.json',s1/'STATE.json',s1/'R_ORACLE_CONTENT_FREEZE.json']
    selected+=sorted((s1/'comparisons').glob('*.json'))
    selected+=sorted((s1/'workers').glob('*/HOST.json'))
    selected+=sorted((s1/'workers').glob('*/JOB.json'))
    selected+=sorted((s1/'workers').glob('*/native/result.json'))
    selected+=sorted((s1/'workers').glob('*/native/**/receipt.json'))
    selected+=sorted((s1/'workers').glob('*/ACTUAL_MODULES.private.json'))
    selected+=sorted((s1/'workers').glob('*/stdout.log'))+sorted((s1/'workers').glob('*/stderr.log'))
    selected+=[Path(c['ledger'])]
    commitments=[]
    for source in selected:
        relative=source.relative_to(s1)if source.is_relative_to(s1)else Path('GLOBAL_LEDGER.jsonl')
        target=output/'F1_DATA/S1'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(public_text(source.read_text(),root))
        commitments.append(dict(public_path=target.relative_to(output).as_posix(),private_raw_sha256=sha(source),public_sha256=sha(target)))
    for p in sorted((s1/'workers').glob('*/TELEMETRY.private.jsonl')):
        q=output/'F1_DATA/S1'/p.relative_to(s1);q=q.with_name('TELEMETRY.public.jsonl');q.parent.mkdir(parents=True,exist_ok=True)
        q.write_text(''.join(json.dumps(telemetry_public(json.loads(line)),sort_keys=True)+'\n'for line in p.read_text().splitlines()))
        commitments.append(dict(public_path=q.relative_to(output).as_posix(),private_raw_sha256=sha(p),public_sha256=sha(q),
                                transform='Drop allocation UUID and process IDs, retain all numeric resource samples'))
    classes=[]
    for w in read(c['manifest'])['workers']:
        if w['kind']=='clean-operand-bridge':
            receipt=s1/'workers'/w['worker_id']/'HOST.json';host=read(receipt);need(host['status']=='COMPLETE','Incomplete cost observation')
            classes.append(dict(cell=w['cell'],arm=w['arm'],worker_kind='clean-resident-projection-one-warm-one-measured',
                                max_observed_caller_s=positive(host['caller_s']),caller_receipt_sha256=sha(receipt)))
    fresh(output/'F1_DATA/CALLER_CLASSES.json',classes)
    fresh(output/'F1_DATA/TRANSFORM_COMMITMENTS.json',commitments)
    fresh(output/'F1_DATA/REGISTRATION.json',dict(schema='hs.strong.F1.v1',export_started_utc=utc(),
          export_prepare_wall_s=time.monotonic()-started,clean_timing='NOT_STARTED',numeric_GPU_qualification='HOST_PASSED',
          raw_payloads='Retained privately; public text does not independently repeat numeric comparison',
          work_counters_scope='instrumented application API; opaque library internals unknown',
          graphs_policy='off_only',warm_policy='one identical full warm per fresh worker, then measurement',fixed_worker_gap_s=c['fixed_worker_gap_s']))
    files=[dict(path=p.relative_to(output).as_posix(),sha256=sha(p),bytes=p.stat().st_size)for p in sorted(output.rglob('*'))if p.is_file()]
    fresh(output/'F1_INDEX.json',dict(schema='hs.strong.public-freeze-index.v1',prefix=PREFIX,files=files))


def admit(configuration,public,proof_path,output):
    c=read(configuration);proof=read(proof_path);verify_public_readback(proof)
    need(proof['index_name']=='F1_INDEX.json','F0 readback cannot substitute for F1')
    bindings=read(public/'F1_DATA/QUALIFIED_BINDINGS.json');s1=Path(c['output_root'])
    need(bindings['S1_certificate_raw_sha256']==sha(s1/'S1_CERTIFICATE.json')and
         bindings['manifest_sha256']==c['manifest_sha256']and bindings['compiled_closure_sha256']==c['compiled_closure_sha256'],
         'F1 qualification/source identity differs')
    registered={e['source_file']:e['sha256']for e in proof['files']}
    need(registered.get(str(public/'F1_DATA/QUALIFIED_BINDINGS.json'))==sha(public/'F1_DATA/QUALIFIED_BINDINGS.json'),'Bindings not part of full public readback')
    registration=read(public/'F1_DATA/REGISTRATION.json')
    observed=epoch(proof['checked_utc'])-epoch(registration['export_started_utc'])+positive(registration['export_prepare_wall_s'])
    costs=caller_cost_proof(read(public/'F1_DATA/CALLER_CLASSES.json'),c['fixed_worker_gap_s'],max(observed,proof['download_elapsed_s'])*1.25)
    need(time.time()+costs['required_s']<=epoch(c['allocation_end_utc']),'Complete S2 plus archive/replay does not fit')
    costs['whole_phase_fits']=True
    c.update(execution_phase='S2',S1_root=str(s1),output_root=str(output/'S2'),
             S1_certificate=str(s1/'S1_CERTIFICATE.json'),S1_certificate_sha256=sha(s1/'S1_CERTIFICATE.json'),
             F1_public_readback=proof,S2_admission_cost_proof=costs)
    output.mkdir(parents=True);Path(c['output_root']).mkdir()
    fresh(output/'RESOURCE_ADMISSION.private.json',resource(c));fresh(output/'ADMISSION_S2.private.json',c)
    fresh(output/'S2_TIME_ADMISSION.json',costs)


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    a=sub.add_parser('prepare');a.add_argument('--configuration',type=Path,required=True)
    a.add_argument('--root',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    b=sub.add_parser('admit');b.add_argument('--configuration',type=Path,required=True);b.add_argument('--public',type=Path,required=True)
    b.add_argument('--proof',type=Path,required=True);b.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.mode=='prepare':prepare(a.configuration,a.root,a.out)
    else:admit(a.configuration,a.public,a.proof,a.out)


if __name__=='__main__':main()
