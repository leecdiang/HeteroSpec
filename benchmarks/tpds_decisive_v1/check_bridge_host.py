"""Finite old-R correspondence; this alone does not qualify candidate lanes."""
from build_host import *
def main():
    old=ROOT/'bridge-old-r-01/native';obs=ROOT/'bridge-observer-r-01/native'
    for p in (old,obs):assert json.loads((p/'result.json').read_bytes())['status']=='COMPLETE'
    reference=json.loads((old/'r0.json').read_bytes());vectors={p.name:sha(p) for p in (old/'r0/target').glob('*.f32')};checks=[]
    assert len(vectors)==len(reference['ids'])
    for label,base in [('old-repeat',old/'r1'),('observer-0',obs/'r0'),('observer-1',obs/'r1')]:
        row=json.loads(base.with_suffix('.json').read_bytes())
        check=dict(label=label,endpoint_equal=row['endpoint']==reference['endpoint'],full_vectors_equal={p.name:sha(p) for p in (base/'target').glob('*.f32')}==vectors)
        checks.append(check);assert check['endpoint_equal'] and check['full_vectors_equal']
    states=[]
    for p in sorted((obs/'r0/target/state').iterdir()):
        other=obs/'r1/target/state'/p.name;meta=dict(x.split('=',1) for x in (p/'capture.txt').read_text().splitlines())
        check=dict(key=p.name,raw_sequence_sha256=sha(p/'sequence.bin'),state_repeat_equal=sha(p/'sequence.bin')==sha(other/'sequence.bin'),frontier_matches_old=sha(p/'frontier.f32')==vectors[p.name+'.f32'],position_min=int(meta['position_min']),position_max=int(meta['position_max']))
        assert check['state_repeat_equal'] and check['frontier_matches_old'];states.append(check)
    put(ROOT/'OLD_R_OBSERVER_BRIDGE.json',dict(status='FINITE_OLD_OUTPUT_BRIDGE_PASS',requests=4,full_vocabulary_vectors_per_request=len(vectors),comparisons=checks,states=states,old_executable_sha256=sha(OLD/'bin/rtx-scope-transfer.exe'),observer=json.loads((ROOT/'draft/reference-observer/BUILD.json').read_bytes()),scope='Original R had no KV captures. Observer repeated raw target sequence bytes and each frontier match here; independent forced-reference active-KV and candidate clean/heavy qualification remain required.',candidate_lane_qualified=False,writer_sha256=sha(OLD/'source/src/llama-kv-cache.cpp')))
    print('Finite old-R/observer full-vector bridge passed; candidate qualification still pending.')
if __name__=='__main__':main()
