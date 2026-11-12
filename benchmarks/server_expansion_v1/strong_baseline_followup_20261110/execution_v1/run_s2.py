"""Consume exactly the 36 F1 workers; stop on any error, retain partial bytes."""
import argparse
import time
from pathlib import Path
from analyze import analyze
from host import Host,utc
from materialize import projection_job
from qualify import projection_checks
from support import fresh,need,read,sha,write


def run(configuration):
    started=time.monotonic();h=Host(configuration);s1=Path(h.c['S1_root'])
    certificate=read(h.c['S1_certificate']);inputs=read(s1/'real-inputs/INPUT_BINDINGS.private.json')
    need(sha(s1/'real-inputs/INPUT_BINDINGS.private.json')==certificate['input_bindings_sha256'],'Qualified input registry changed')
    need(certificate['manifest_sha256']==h.c['manifest_sha256']and
         certificate['compiled_closure_sha256']==h.c['compiled_closure_sha256'],'S1 source/module/manifest differs')
    golds={}
    for c,digest in certificate['gold_registry_sha256'].items():
        path=s1/'gold-bindings'/('GOLD-'+c+'.private.json');need(sha(path)==digest,'Qualified gold registry changed');golds[c]=read(path)
    rows=[];caller=[]
    with h:
        try:
            for worker in h.manifest['workers']:
                if worker['kind']!='S2-fixed-diagnostic':continue
                write(h.root/'STATE.json',dict(status='S2_RUNNING',worker=worker['worker_id'],completed_operations=len(rows),utc=utc()))
                job,_=projection_job(worker,inputs,h.manifest,'S2');output=h.run(worker,job,'operand',phase='S2')
                checks=projection_checks(worker,output,inputs,golds)
                fresh(output/'OFFLINE_NUMERIC_AND_PHYSICAL.json',dict(proofs=checks,heavy_quantized_capture_disabled=True))
                actual=read(output/'native/result.json')
                rows.extend(actual['operations']);caller.append(dict(worker_id=worker['worker_id'],HOST=read(output/'HOST.json'),
                    startup_work_counters=actual['startup_work_counters'],graph_nodes=actual['graph_nodes'],
                    GPU_memory_samples=actual['GPU_memory_samples']))
                write(h.root/'PARTIAL_ROWS.json',rows)
            result=analyze(rows,'S2')
            result.update(instrumented_implementation=True,complete_caller_records=caller,
                    caller_total_s=sum(r['HOST']['caller_s']for r in caller),
                    fixed_worker_gaps_total_s=len(caller)*h.c['fixed_worker_gap_s'],
                    phase_wall_s=time.monotonic()-started,limitations=[
                        'Four exposed real-input cells, three blocks; descriptive only',
                        'One matched full warmup does not establish steady state',
                        'G/B/C include different graph, batch quantization and dispatch organization',
                        'API counters exclude opaque library internals; memory samples are not guaranteed peaks',
                        'No full-model service extrapolation; S3 requires separate complete admission'])
            fresh(h.root/'S2_ANALYSIS.json',result);fresh(h.root/'S2_ROWS.json',rows)
            write(h.root/'STATE.json',dict(status='S2_COMPLETE_REQUIRES_PUBLIC_ARCHIVE_REPLAY',utc=utc(),operations=len(rows),workers=len(caller)))
        except BaseException as error:
            write(h.root/'STATE.json',dict(status='S2_PARTIAL_STOPPED',reason=str(error),error_type=type(error).__name__,
                     utc=utc(),completed_operations=len(rows),no_native_retry=True))
            raise


def main():
    p=argparse.ArgumentParser();p.add_argument('--configuration',required=True);a=p.parse_args();run(a.configuration)


if __name__=='__main__':main()
