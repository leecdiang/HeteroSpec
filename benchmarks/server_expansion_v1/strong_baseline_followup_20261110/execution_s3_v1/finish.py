"""Finite S3 execution and terminal local export/replay, independent of SSH/AI."""
import argparse
from pathlib import Path
import traceback
import run
import deliver
from support import read,fresh


def main(configuration):
    c=read(configuration);root=Path(c['execution_root']);error=None
    try:run.execute(configuration)
    except BaseException as exc:error=exc
    finally:
        if (root/'CONTROLLER_CLOSED.private.json').exists():
            try:
                out=root.parent/'RESULT_S3_TEXT';meta=deliver.export(configuration,out)
                report=deliver.replay(out.parent/(out.name+'.tar.gz'),meta['archive_sha256'],out.parent/'RESULT_S3_LOCAL_REPLAY')
                report['byte_source']='LOCAL_ARCHIVE_SELFTEST_NOT_REMOTE_READBACK'
                fresh(root.parent/'RESULT_S3_LOCAL_REPLAY_PASS.json',report)
            except BaseException as exc:
                fresh(root/'EXPORT_FAILURE.json',dict(reason=str(exc),traceback=traceback.format_exc()))
                if error is None:raise
    if error is not None:raise error


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--configuration',type=Path,required=True);main(p.parse_args().configuration)
