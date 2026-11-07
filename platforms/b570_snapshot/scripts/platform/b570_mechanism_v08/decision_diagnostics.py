"""Descriptive same-prefix decision evidence; does not select a hypothesis."""
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
P=ROOT/'benchmarks/b570_mechanism_v08'
RAW=ROOT/'artifacts/b570_mechanism_v08/raw'

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    discovery=load(P/'DISCOVERY_ANALYSIS.json');rows=[]
    for pair in discovery['pairs']:
        task=pair['task_id'];rep=pair['repetition'];stem=task.replace('/','_')+f'-r{rep}'
        ref=load(RAW/'qualification'/(stem+'-ub128.capture.json'))
        candidate=load(RAW/'discovery_h1'/(stem+'-ub1.capture.json'))
        index=pair['relative_to_reference']['first_divergence_index']
        row={'task_id':task,'repetition':rep,'first_divergence_index':index,'same_prompt_ids':ref['prompt_ids']==candidate['prompt_ids'],'reference_n_ubatch':128,'candidate_n_ubatch':1}
        if index is not None:
            a=ref['generated_ids'][:index];b=candidate['generated_ids'][:index]
            row.update(same_committed_prefix=a==b,committed_prefix_ids=a,committed_prefix_sha256=hashlib.sha256(json.dumps(a,separators=(',',':')).encode()).hexdigest(),reference_decision=ref['decisions'][index],candidate_decision=candidate['decisions'][index],same_sequence_position=ref['decisions'][index]['sequence_position']==candidate['decisions'][index]['sequence_position'])
        rows.append(row)
    (P/'DISCOVERY_DECISION_DIAGNOSTICS.json').write_text(json.dumps({'schema':'heterospec.b570.mechanism.same_prefix.v08','purpose':'Descriptive raw target top1/top2/margin at the first differing decision under identical prompt and committed prefix; no additional selection thresholds or causal kernel claim.','observations':rows},indent=2)+'\n',encoding='utf-8')
    print('Same-prefix decision diagnostics recorded for',sum(r['first_divergence_index'] is not None for r in rows),'observations')

if __name__=='__main__':main()
