"""Meter the frozen coordinator, including validation outside native service."""
from confirmation import *

def main():
    began=time.monotonic();started=datetime.datetime.now(datetime.timezone.utc).isoformat();status='FAILED'
    try:run();status='COMPLETE'
    finally:
        put(DEST/('COORDINATOR-'+str(time.time_ns())+'.json'),dict(status=status,started_utc=started,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),wall_s=time.monotonic()-began,source_sha256=sha(Path(__file__)),native_attempts_and_service_are_nested_components=True,includes_original_R_and_endpoint_trace_validation=True,not_additive_to_native_host_wall=True))

if __name__=='__main__':main()
