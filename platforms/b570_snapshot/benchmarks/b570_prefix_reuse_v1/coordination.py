"""Release only after inspecting both real, published native freezes."""
from host import *
from campaign import common_gate

REMOTE_COMMIT='efd92438a08a4e9c37a422731ddd6850d8907f1b'
REMOTE_PATH='benchmarks/rtx_prefix_reuse_v1/execution/evidence/SOURCE_POLICY_FREEZE.json'

def release(local_commit):
 local=read(ROOT/'SOURCE_POLICY_FREEZE.json')
 remote=read(ROOT/'coordination/RTX_SOURCE_POLICY_FREEZE.json')
 assert local['status']=='NATIVE_CALIBRATION_SOURCE_POLICY_FROZEN' and local['main_output_exposures']==0
 assert remote['status']=='SOURCE_POLICY_FROZEN_AWAITING_PEER_FREEZE' and remote['common_heldout_outputs']==0
 assert remote['capacity']==4096 and remote['cache_granule']==1 and remote['padding']==256
 assert remote['model_sha256']==read(ROOT/'INHERITED_AUTHENTICATION.json')['model']['sha256']
 assert remote['template_sha256']==read(ROOT/'panel.json')['configuration']['template_sha256']
 assert remote['request_reservations_started']+remote['planned_remaining']<=remote['hard_tranche']
 panel=read(ROOT/'panel.json');peer=read(ROOT/'coordination/RTX_PANEL.json')
 keys=('id','root_id','request_token_sha256','cached_token_sha256','effective_head','physical_head','prompt_tokens','append_tokens')
 for split in ('calibration','test'):
  assert [{k:r[k] for k in keys} for r in panel[split]]==[{k:r[k] for k in keys} for r in peer[split]]
 assert not any((ROOT/'units').glob('main-*')),'Cannot retrospectively release an exposed panel'
 write(ROOT/'COORDINATION_RELEASE.json',dict(utc=utc(),released=True,independent_panel_fork=False,local_freeze_sha256=sha(ROOT/'SOURCE_POLICY_FREEZE.json'),remote_freeze_sha256=sha(ROOT/'coordination/RTX_SOURCE_POLICY_FREEZE.json'),local_commit=local_commit,remote_commit=REMOTE_COMMIT,remote_git_blob='8f063c47a0057892f6f2e07065bb171054309ad4',local_url=f'https://github.com/leecdiang/HeteroSpec/blob/{local_commit}/benchmarks/b570_prefix_reuse_v1/evidence/SOURCE_POLICY_FREEZE.json',remote_url=f'https://github.com/leecdiang/HeteroSpec/blob/{REMOTE_COMMIT}/{REMOTE_PATH}',cohort_match_sha256=sha(ROOT/'COHORT_MATCH.json'),matched_calibration_roots=12,matched_test_roots=32,lifecycle_difference='B570 host-memory snapshots vs RTX file-backed snapshots; per-host contrasts only, no pooled timing or pure hardware contrast'))
 common_gate()

if __name__=='__main__':release(sys.argv[1])
