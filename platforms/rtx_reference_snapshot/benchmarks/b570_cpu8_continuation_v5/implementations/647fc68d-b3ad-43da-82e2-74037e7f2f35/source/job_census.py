"""Resource census follows Job membership, including nested debugger children."""
def census(job,api):
    members=api.job_pids(job);rows=[];races=[]
    for pid in members:
        handle=api.open_process(0x100410,False,pid)
        if not handle:
            if pid in api.job_pids(job):raise RuntimeError('JOB_RESOURCE_OPEN_FAILED')
            races.append(dict(pid=pid,reason='left_job_before_open'));continue
        try:
            identity=api.os_times(handle)
            if not api.alive(handle):
                races.append(dict(pid=pid,created_filetime=identity['created_filetime'],reason='exited_before_read'));continue
            try:value=api.rss(handle)
            except OSError:
                if api.alive(handle):raise
                races.append(dict(pid=pid,created_filetime=identity['created_filetime'],reason='exited_during_read'));continue
            rows.append(dict(pid=pid,created_filetime=identity['created_filetime'],rss_bytes=value))
        finally:
            api.checked(api.close(handle),'job census process handle')
    return dict(job_pids=members,members=rows,exit_races=races)
