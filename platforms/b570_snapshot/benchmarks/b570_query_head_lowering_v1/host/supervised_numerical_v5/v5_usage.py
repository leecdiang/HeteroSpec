"""Charge the external launcher capture AND its export at the fixed maximum."""
from storage import bounded_usage as original_bounded_usage

def bounded_usage(job):
    row=original_bounded_usage(job)
    row['external_log_and_export_reserved_bytes']=job.get('external_log_reserved_bytes',0)
    row['output_bytes']+=row['external_log_and_export_reserved_bytes']
    return row
