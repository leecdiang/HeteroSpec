"""Bounded B2 execution and terminal local export/replay without AI/SSH input."""
import argparse
from pathlib import Path
import traceback
import execute
import deliver


def run(configuration):
    c=execute.read(configuration);work=Path(c['work_root']);error=None
    try:
        execute.need(set(__import__('os').sched_getaffinity(0))=={32,33},'Frozen two-core B2 affinity')
        execute.run(configuration)
    except BaseException as exc:
        error=exc
    finally:
        if (work/'STATE.json').exists()and(work/'LOCK_RELEASED.private.json').exists():
            try:
                out=Path(c['local_export'])
                meta=deliver.export(work,Path(c['study_root']),Path(c['execution_source']),out,Path(c['archive_source']))
                restored=out.parent/(out.name+'_LOCAL_REPLAY')
                report=deliver.replay(out.parent/(out.name+'.tar.gz'),meta['archive_sha256'],restored,Path(c['archive_source']))
                report.update(byte_source='LOCAL_ARCHIVE_SELFTEST_NOT_REMOTE_READBACK')
                execute.save(out.parent/'B2_LOCAL_REPLAY_PASS.json',report)
            except BaseException as export_error:
                execute.save(work/'EXPORT_FAILURE.json',dict(reason=str(export_error),traceback=traceback.format_exc()))
                if error is None:raise
    if error is not None:raise error


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--configuration',type=Path,required=True)
    run(p.parse_args().configuration)
