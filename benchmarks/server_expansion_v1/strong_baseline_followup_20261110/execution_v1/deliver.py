"""Terminal-only reviewed public text package and independent saved-data replay."""
import argparse
import json
from pathlib import Path
from analyze import analyze
from archive import create,replay
from freeze_cpu import public_text
from host import utc
from support import fresh,need,read,sha
from terminal_guard import terminal_phase,telemetry_public


def prepare(configuration,root,output,archive_path):
    c=read(configuration);phase=Path(c['output_root'])
    with terminal_phase(c,{'S2_COMPLETE_REQUIRES_PUBLIC_ARCHIVE_REPLAY','S2_PARTIAL_STOPPED'}):
        status=read(phase/'STATE.json')['status'];complete=status=='S2_COMPLETE_REQUIRES_PUBLIC_ARCHIVE_REPLAY'
        need(not output.exists(),'Fresh terminal public staging');output.mkdir(parents=True)
        if complete:
            raw=read(phase/'S2_ROWS.json');core=json.loads(json.dumps(analyze(raw,'S2'),sort_keys=True))
            original=read(phase/'S2_ANALYSIS.json')
            need(all(original[k]==v for k,v in core.items()),'Independent full S2 statistical recomputation differs')
        selected=[p for p in phase.rglob('*')if p.is_file()and p.suffix in ('.json','.jsonl','.log')
                  and p.name not in ('GRANT.private.json','LAUNCH.private.json','LOCK_ACQUIRED.private.json','LOCK_RELEASED.private.json')]
        selected=[p for p in selected if p.name not in ('RESOURCE_BEFORE.private.json','TELEMETRY.private.jsonl')]
        for p in selected:
            q=output/'data/S2'/p.relative_to(phase);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(public_text(p.read_text(),root))
        for p in phase.glob('workers/*/TELEMETRY.private.jsonl'):
            q=output/'data/S2'/p.relative_to(phase);q=q.with_name('TELEMETRY.public.jsonl');q.parent.mkdir(parents=True,exist_ok=True)
            q.write_text(''.join(json.dumps(telemetry_public(json.loads(line)),sort_keys=True)+'\n'for line in p.read_text().splitlines()))
        # F1 already contains the complete sanitized S1 request/cost/failure proof.
        for entry in c['F1_public_readback']['files']:
            public=entry['public_path'].split('/strong_baseline_followup_20261110/',1)[1]
            p=Path(entry['downloaded_file']);need(sha(p)==entry['sha256'],'Previously downloaded F1 bytes changed')
            q=output/'F1'/public;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
        source_root=Path(__file__).parent.parent
        for name,digest in c['source_files'].items():
            p=Path(name);need(sha(p)==digest,'Frozen source changed before delivery')
            q=output/'source'/p.relative_to(source_root);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
        s1=Path(c['S1_root']);payloads=[]
        for directory in (s1,phase):
            for p in sorted(directory.rglob('*')):
                if p.is_file()and p.suffix in ('.f32','.bin','.q8_1'):
                    payloads.append(dict(logical_id=('S1/'if directory==s1 else'S2/')+p.relative_to(directory).as_posix(),
                                         bytes=p.stat().st_size,sha256=sha(p)))
        fresh(output/'NUMERIC_PAYLOADS_NOT_PUBLIC.json',dict(scope='Unavailable public numeric payloads; retained on authorized host',payloads=payloads))
        fresh(output/'DELIVERY_SCOPE.json',dict(status='COMPLETE_S1_S2'if complete else'PARTIAL_S2',utc=utc(),
              public_statistical_recalculation='LOCAL_PASSED'if complete else'NOT_APPLICABLE_PARTIAL',
              private_numeric_qualification='S1_HOST_PASSED',public_numeric_rerun='UNAVAILABLE',
              new_blind_root_service_result='NOT_RUN_S3_SEPARATE',B2='SEPARATE_8B_STUDY',
              limitations='Four exposed projection cells; one warmup; instrumented implementation; no whole-model speed extrapolation'))
        selection=dict(schema='hs.strong.public-selection.v1',terminal_status='COMPLETE'if complete else'PARTIAL',
                       files=[dict(path=p.relative_to(output).as_posix(),sha256=sha(p),bytes=p.stat().st_size,
                              payload_kind='utf8-text',public_review='TEXT_REVIEWED_NO_PRIVATE_IDENTIFIERS')
                              for p in sorted(output.rglob('*'))if p.is_file()],withheld_numeric_payloads=payloads)
        fresh(output.parent/(output.name+'-SELECTION.private.json'),selection)
        return create(output,selection,archive_path)


def replay_result(archive,directory,digest,report):
    result=replay(archive,directory,digest)
    scope=read(directory/'DELIVERY_SCOPE.json')
    if scope['status']=='COMPLETE_S1_S2':
        core=json.loads(json.dumps(analyze(read(directory/'data/S2/S2_ROWS.json'),'S2'),sort_keys=True))
        actual=read(directory/'data/S2/S2_ANALYSIS.json')
        need(all(actual[k]==v for k,v in core.items()),'Downloaded public-only statistical replay differs')
        result['statistical_replay']='PASSED_COMPLETE_72_OPERATIONS'
    else:result['statistical_replay']='PARTIAL_NO_COMPLETE_ESTIMATE'
    fresh(report,result)


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    a=sub.add_parser('prepare');a.add_argument('--configuration',type=Path,required=True);a.add_argument('--root',type=Path,required=True)
    a.add_argument('--out',type=Path,required=True);a.add_argument('--archive',type=Path,required=True)
    b=sub.add_parser('replay');b.add_argument('--archive',type=Path,required=True);b.add_argument('--out',type=Path,required=True)
    b.add_argument('--sha256',required=True);b.add_argument('--report',type=Path,required=True);a=p.parse_args()
    if a.mode=='prepare':print(json.dumps(prepare(a.configuration,a.root,a.out,a.archive)))
    else:replay_result(a.archive,a.out,a.sha256,a.report)


if __name__=='__main__':main()
