"""Bounded workload-specific limits. Review helpers are not experimental actors."""
import math
MiB=1024**2
PROFILES={
 'case':dict(live=8,per_process=256*MiB,aggregate=1536*MiB,max_seconds=900),
 'aux':dict(live=32,per_process=256*MiB,aggregate=1536*MiB,max_seconds=900),
 'review':dict(live=32,per_process=2048*MiB,aggregate=4096*MiB,max_seconds=900),
}
def profile(kind,seconds):
    if kind not in PROFILES or not math.isfinite(seconds) or not 0<seconds<=PROFILES[kind]['max_seconds']:
        raise ValueError('invalid observer profile/deadline')
    return dict(PROFILES[kind],observer=512*MiB)
def violations(limits,members,own,active_count=None):
    bad=[]
    if not isinstance(own,int) or own<0:raise ValueError('invalid observer RSS')
    if any(type(x['rss_bytes']) is not int or x['rss_bytes']<0 for x in members):
        raise ValueError('invalid member RSS')
    if own>limits['observer']:bad.append('observer_rss')
    if (len(members) if active_count is None else active_count)>limits['live']:bad.append('live_process_count')
    if any(x['rss_bytes']>limits['per_process'] for x in members):bad.append('per_process_rss')
    if own+sum(x['rss_bytes'] for x in members)>limits['aggregate']:bad.append('aggregate_rss')
    return bad
