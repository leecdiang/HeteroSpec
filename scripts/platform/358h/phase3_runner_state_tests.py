#!/usr/bin/env python3
"""NON_FORMAL forced acceptance/state tests for the Phase-3 target adapter."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from phase3_heterogeneous_runner import LlamaAPI,LlamaTarget,TARGET

PROMPT="Write a Python function that returns the square of an integer."
FORMATTED=f"<|im_start|>user\n{PROMPT}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 api=LlamaAPI();t=LlamaTarget(api,TARGET);ids=t.tokenize(FORMATTED,True)
 t.reset_prefill(ids); baseline=t.baseline(12)
 t.reset_prefill(ids); cases=[]
 def one(name,proposals,expected_accept,expected_commit):
  before=len(t.history); got=t.verify(proposals); pos=t.a.ll.llama_memory_seq_pos_max(t.mem,0)
  accepted=len(got)-1
  ok=(got==expected_commit and accepted==expected_accept and pos==len(t.history)-1)
  cases.append({'case':name,'before':before,'proposals':proposals,'committed':got,'accepted':accepted,
                'expected_commit':expected_commit,'state_position':pos,'history_length':len(t.history),'pass':ok})
  if not ok: raise AssertionError(cases[-1])
 one('A_zero_accepted',[baseline[0]+1,baseline[1]],0,[baseline[0]])
 one('B_only_d1_accepted',[baseline[1],baseline[2]+1],1,[baseline[1],baseline[2]])
 one('C_D_two_accepted_plus_bonus',[baseline[3],baseline[4]],2,[baseline[3],baseline[4],baseline[5]])
 one('E_repeated_rejection_1',[baseline[6]+1,baseline[7]],0,[baseline[6]])
 one('E_repeated_rejection_2',[baseline[7]+1,baseline[8]],0,[baseline[7]])
 t.reset_prefill(ids); r1=t.baseline(8);t.reset_prefill(ids);r2=t.baseline(8)
 cases.append({'case':'F_reset_repeat','run1':r1,'run2':r2,'pass':r1==r2==baseline[:8]})
 result={'schema':'heterospec.358h.phase3.runner_state_tests.v1','formal':False,
         'claim_status':'NON_FORMAL / INVALID_FOR_CLAIMS','cases':cases,'pass':all(x['pass'] for x in cases)}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'pass':result['pass'],'cases':len(cases)},indent=2));return 0 if result['pass'] else 2
if __name__=='__main__':raise SystemExit(main())

