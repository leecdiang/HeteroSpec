"""Include unchanged shared fan/predictor provenance in derived evidence capsules.

The frozen independent supplemental verifier requires original predictor records
and the pre-live host observation in either arm. B keeps its 171 fresh timings;
the copied A records are provenance dependencies, never B observations. Anonymous
copies obtain the host observation from a member already redacted by the frozen
anonymizer. No verifier assertion or raw numerical evidence is modified.
"""
import shutil
from pathlib import Path

HOST='HOST_OBSERVATION_A_PRE_LIVE_AFTER.json'
def augment(stage,original_root,anonymous=False):
    stage=Path(stage);original_root=Path(original_root)
    pre=stage/'work/A-pre-live'
    if not pre.exists():
        if anonymous:raise RuntimeError('Anonymous capsule missing redacted predictor provenance')
        shutil.copytree(original_root/'work/A-pre-live',pre)
    shared=pre/HOST
    if not shared.exists():
        if anonymous:raise RuntimeError('Anonymous capsule missing previously redacted host dependency')
        shutil.copy2(original_root/'work'/HOST,shared)
    canonical=stage/'work'/HOST
    if not canonical.exists():shutil.copy2(shared,canonical)
    if anonymous:
        payload=canonical.read_bytes()
        if any(x in payload for x in [b'ASUS',b'wxid_',b'leecdiang']):raise RuntimeError('Redacted host dependency privacy check failed')
    return {'original_predictor_observations_reused_unchanged':228,'extra_B_model_runs':0,'shared_host_dependency_present':True,'anonymous_host_dependency_already_redacted':anonymous}
