"""Explicitly authorized repair loop; per-case resource and scientific bounds unchanged."""
import json,re
from pathlib import Path
POLICY=dict(schema=1,mode='repair_until_verified',task_seconds=21600,development_seconds=18000,delivery_seconds=3600)
def validate(value):
    if value is not None and value!=POLICY:raise ValueError('unapproved continuation policy')
    return value
def load(root):
    path=Path(root)/'CONTINUATION_POLICY.json'
    return validate(json.loads(path.read_bytes())) if path.exists() else None
def review_id(name,policy):
    validate(policy)
    return bool(re.fullmatch(r'full-review(?:-[1-9][0-9]*)?',name)) if policy else name in ('full-review','full-review-2')
