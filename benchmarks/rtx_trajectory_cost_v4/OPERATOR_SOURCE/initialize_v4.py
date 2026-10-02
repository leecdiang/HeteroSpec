"""New authorized study; preserve all V3 source, records and frozen checkpoints."""
import sys,os,json,shutil,re,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PREVIOUS=ROOT.with_name('HeteroSpec-v3')
SOURCE=ROOT/'scripts/platform/rtx_trajectory_cost_v4'
META=ROOT/'benchmarks/rtx_trajectory_cost_v4'
SOURCE.mkdir(parents=True,exist_ok=False);META.mkdir(parents=True,exist_ok=False)
for p in (PREVIOUS/'scripts/platform/rtx_trajectory_cost_v3').iterdir():
    if p.suffix not in ['.py','.cpp']:continue
    if p.suffix=='.cpp':shutil.copy2(p,SOURCE/p.name);continue
    s=p.read_text(encoding='utf-8')
    for old,new in [('rtx_trajectory_cost_v3','rtx_trajectory_cost_v4'),('rtx_trajectory_sufficiency_v3','rtx_trajectory_sufficiency_v4'),('rtx_matched_qualification_cost_v2','rtx_matched_qualification_cost_v3'),('RTX_TRAJECTORY_AND_MATCHED_COST_V3','RTX_TRAJECTORY_AND_MATCHED_COST_V4'),('RTX_TRAJECTORY_SUFFICIENCY_V3','RTX_TRAJECTORY_SUFFICIENCY_V4'),('RTX_MATCHED_QUALIFICATION_COST_V2','RTX_MATCHED_QUALIFICATION_COST_V3'),('RTX_V3','RTX_V4'),('A24_B24','A19_B19'),('2026100103','2026100203'),('2026100104','2026100204')]:s=s.replace(old,new)
    (SOURCE/p.name).write_text(s,encoding='utf-8',newline='\n')
def edit(name,old,new):
    p=SOURCE/name;s=p.read_text(encoding='utf-8');assert old in s,(name,old);p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')
edit('native.py',"    if len(stops) != 1 or (stops[0] == 'limit' and len(ids) != 128):\n        raise ValueError('unsupported/missing termination status')", "    # Native b10839 logs both conditions when its inclusive EOG is token 128.\n    # Preserve both observations; canonical EOS takes precedence only for that\n    # exact endpoint. Missing, duplicate or contradictory stops still fail.\n    if stops == ['limit', 'EOS'] and len(ids) == 128 and ids[-1] in {151643,151645}:\n        termination = 'EOS'\n    elif len(stops) == 1 and (stops[0] != 'limit' or len(ids) == 128):\n        termination = stops[0]\n    else:\n        raise ValueError('unsupported/missing termination status')")
edit('native.py',"'termination':stops[0]","'termination':termination,'native_stop_observations':stops")
edit('verify_replay.py',"    stop=re.findall(r'process_toke:.*stopped by (EOS|limit)',text);require(len(stop)==1,'native stop event')\n    require(stop[0]!='limit' or len(ids)==128,'native cap missing')", "    stop=re.findall(r'process_toke:.*stopped by (EOS|limit)',text)\n    simultaneous=(stop==['limit','EOS'] and len(ids)==128 and ids[-1] in {151643,151645})\n    require(simultaneous or len(stop)==1,'native stop event')\n    require(simultaneous or stop[0]!='limit' or len(ids)==128,'native cap missing')\n    reason='EOS' if simultaneous else stop[0]")
edit('verify_replay.py',"return ids,stop[0]","return ids,reason")
# Independent producer/verifier implementations, with the new denominator.
edit('verify_a.py',"len(tasks)==24 and len(rows)==288","len(tasks)==19 and len(rows)==len(tasks)*12")
edit('verify_a.py',"'A fixed 24x3x4 denominator'","'A frozen 19x3x4 denominator'")
edit('verify_a.py',"'distinct_prompts':24","'distinct_prompts':len(tasks)")
edit('verify_a.py',"'total_pairs':72","'total_pairs':len(tasks)*3")
edit('verify_a.py',"len(sealed['rows'])==72","len(sealed['rows'])==len(tasks)*3")
edit('verify_a.py',"len(lookup)==360","len(lookup)==len(tasks)*15")
edit('verify_a.py',"v['exact_pairs']==72","v['exact_pairs']==len(tasks)*3")
edit('verify_a.py',"'valid_complete_runs':360","'valid_complete_runs':len(rows)")
edit('study.py',"'pre_live_runs':288","'pre_live_runs':len(tasks)*12".replace('len(tasks)','len(p[\'A\'][\'task_ids\'])'))
edit('configuration.py',"mode='A19_B19' if len(tasks)==24 else 'A_BLOCKED_B30'","mode='A19_B19' if len(tasks)==19 else 'AUDIT_BLOCKED'")
edit('configuration.py',"orders=[list(p) for p in perms for _ in range(N*3//6)];random.Random(2026100203).shuffle(orders)","orders=[list(p) for p in perms for _ in range(N*3//6)]\n    if N*3%6==3:orders += [B[i:]+B[:i] for i in range(3)]\n    assert len(orders)==N*3\n    random.Random(2026100203).shuffle(orders)")
edit('verify_b.py',"orders=[list(x) for x in perms for _ in range(N*3//6)];random.Random(2026100203).shuffle(orders)","orders=[list(x) for x in perms for _ in range(N*3//6)]\n    if N*3%6==3:orders += [cs[i:]+cs[:i] for i in range(3)]\n    require(len(orders)==N*3,'B balanced schedule length')\n    random.Random(2026100203).shuffle(orders)")
edit('guards.py',"task not in ENGINEERING and not task.startswith('SYNTH_')","task not in ENGINEERING and task!='HumanEval/59' and not task.startswith('SYNTH_')")
# Select every remaining untouched input, without results-based selection.
p=SOURCE/'verify_joint.py';s=p.read_text(encoding='utf-8')
start=s.index("    keys={t:hashlib.sha256((r['salt']+t).encode('utf-8')).hexdigest() for t in eligible}")
end=s.index("    return {'status':'PASS','mode':p['mode']",start)
s=s[:start]+"    keys={t:hashlib.sha256((r['salt']+t).encode('utf-8')).hexdigest() for t in eligible};ordered=sorted(eligible,key=lambda t:(keys[t],t))\n    require(keys==r['selection_keys'],'salt selection hashes')\n    require(len(eligible)==19 and ordered==r['selected_task_ids']==p['A']['task_ids']==p['B']['task_ids'] and p['mode']=='A19_B19','fixed untouched 19-task study')\n"+s[end:]
p.write_text(s,encoding='utf-8',newline='\n')
# Planned counts and protocol text are amended, without changing runtime values.
p=SOURCE/'finalize.py';s=p.read_text(encoding='utf-8')
for old,new in [("'planned_A_pre_live':288","'planned_A_pre_live':228"),("'planned_A_live':72","'planned_A_live':57"),("'planned_B_formal':216","'planned_B_formal':171"),("'planned_joint_formal':576","'planned_joint_formal':456"),('288 fresh pre-live','228 fresh pre-live'),('72 live observations','57 live observations'),('216 new B runs','171 new B runs'),('The 576','The 456'),('with 26 eligible and 138 conservatively excluded tasks','with 19 eligible and 145 conservatively excluded tasks'),('The 24 selected IDs','The 19 selected IDs'),('same frozen 24 tasks','same frozen 19 tasks')]:s=s.replace(old,new)
p.write_text(s,encoding='utf-8',newline='\n')
edit('configuration.py','H2/R_ONLY 72/72','H2/R_ONLY 57/57')
for name in ['BUILD_IDENTITY.json','timer_build_manifest.json','timer.patch','READ_RECEIPTS.json','SOURCE_ADAPTATION.json','SOURCE_FILE_INVENTORY.json','USER_SPECIFICATION.md']:
    shutil.copy2(PREVIOUS/'benchmarks/rtx_trajectory_cost_v3'/name,META/name)
for name in ['h2-bin','timer-build/bin','pinned-source']:
    dest=ROOT/'work'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(PREVIOUS/'work'/name,dest)
for name in ['BRANCH_SCOPE.json','RUNTIME_DEFAULTS.json','exposure_catalog.json']:
    if (PREVIOUS/'work'/name).exists():shutil.copy2(PREVIOUS/'work'/name,ROOT/'work'/('PREVIOUS_'+name))
(META/'.gitignore').write_text('EXECUTION_LEDGER.jsonl\n',encoding='utf-8')
(META/'.gitattributes').write_text('USER_SPECIFICATION.md -text\n',encoding='utf-8')
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
derivation={'previous_study':'RTX_TRAJECTORY_AND_MATCHED_COST_V3','previous_final_HEAD':'9ce203265c867bc847b13cb440c2339d54a50e6f','previous_state':'INCOMPLETE_OPERATIONAL_FAILURE','previous_records_reclassified_or_replaced':False,'new_study':'RTX_TRAJECTORY_AND_MATCHED_COST_V4','starting_main':'abff99356815371648dc38f1466e66701e96840e','user_authorization_verbatim':'能否自行修复后完成实验，我们的目的是完善论文，因此如果你能自行修复然后推进，得到同样有价值的结论，也可以继续','authorization_scope':'Explicit authorization to fix and advance a new study. Freeze a concrete amended protocol before new reserved forwards; retain prior terminal records and exclude newly exposed tasks. No second literal-approval pause is inferred. Paper incorporation requires evidence-based conclusions.','source_changes':'Capture accepts the exact simultaneous inclusive EOG/cap endpoint; independent verifier separately enforces it. New study paths, untouched 19-task denominator and balanced 57-block schedule are declared; fixed candidates, numerical kernels, model/DLL/timer bytes, observer and bootstrap definitions are unchanged.','numeric_cpp_same_as_V3':{p.name:h(p)==h(PREVIOUS/'scripts/platform/rtx_trajectory_cost_v3'/p.name) for p in SOURCE.glob('*.cpp')},'reused_build_identity_scope':'BUILD_IDENTITY/timer_build_manifest/read receipts retain their original V3 build/review timestamps and paths; identical bytes are copied into new uncommitted work directories and requalified by fresh V4 engineering. They are not claimed to have been rebuilt.','prior_specification_scope':'USER_SPECIFICATION.md preserves the V3 specification. V4 amendment supersedes its 24-task mode, salt, literal-review pause and stop-on-old-attempt restrictions only for this separately authorized new study; old frozen V3 remains unchanged.'}
(META/'NEW_STUDY_AUTHORIZATION.json').write_text(json.dumps(derivation,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('PASS: isolated V4 source and copied numeric binary bytes; V3 unchanged',flush=True)
