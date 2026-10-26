"""Report-level arithmetic and manuscript consistency checks; no model/GPU/network.
Run: python -B anc/check.py [--output new-result.json]
Python 3.11+. Output files are created exclusively and never overwritten.
"""
from __future__ import annotations
import argparse,csv,json,math,re,hashlib
from collections import Counter
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'anc'
checks=[]
def check(name,condition):
    if not condition:raise ValueError('FAILED: '+name)
    checks.append(name)
def load(name):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError('Duplicate JSON key: '+k)
            out[k]=v
        return out
    return json.loads((DATA/name).read_text(encoding='utf-8'),object_pairs_hook=pairs,
                      parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
def geo(values):return math.exp(sum(math.log(x) for x in values)/len(values))
def test():
    with (DATA/'rtx_repair_cost.csv').open(newline='',encoding='utf-8') as stream:
        rows=list(csv.DictReader(stream))
    cost={(r['family'],r['comparison']):float(r['ratio']) for r in rows}
    check('21 unique completed cost comparisons',len(rows)==len(cost)==21)
    check('All original 12-task qualification flags retained',all(r['tasks']=='12' and r['qualified']=='True' for r in rows))
    reg=load('task_regressions.json');plots=load('plot_values.json')
    check('12 fixed task identities',len(reg['panel'])==len(set(reg['panel']))==12)
    check('Regression counts match all 21 source lists',all(len(reg['regressions'][r['family']][r['comparison']])==int(r['regressed_tasks']) for r in rows))
    table=(ROOT/'supplement/02_cuda_cost.tex').read_text()
    matched=[]
    for line in table.splitlines():
        if re.match(r'(Qwen3|SmolLM2|Llama) &',line):
            fields=[f.strip() for f in line.rstrip('\\').split('&')]
            matched.append((fields[0],float(fields[2]),fields[3]))
    check('All 21 six-decimal table values and regression denominators match',matched==[(r['family'],float(r['ratio']),r['regressed_tasks']+'/12') for r in rows])
    draft={}
    for fam in ('Qwen3','SmolLM2','Llama'):
        q=cost[fam,'M_QB/C_QB']
        draft[fam]={'QB':q,**{l:cost[fam,f'M_{l}/M_QB']*q/cost[fam,f'C_{l}/C_QB'] for l in ('PQ','GS')}}
        check(f'{fam}: common-panel reference ratio identity',abs(cost[fam,'R/M_QB']*q-cost[fam,'R/C_QB'])<2e-6)
        for i,comp in enumerate(('C_PQ/C_QB','M_QB/C_QB')):
            vals=plots['task_ratios'][fam][i]
            check(f'{fam}/{comp}: all 12 plotted values finite and positive',len(vals)==12 and all(math.isfinite(x) and x>0 for x in vals))
            check(f'{fam}/{comp}: plot geomean matches rounded source',abs(geo(vals)-cost[fam,comp])<.500001e-6)
            check(f'{fam}/{comp}: exact task regression identities',[reg['panel'][j] for j,v in enumerate(vals) if v<1]==reg['regressions'][fam][comp])
    check('GS unprofitable in all three recorded families',all(v['GS']<1 for v in draft.values()))
    check('PQ and QB cross draft parity only for Qwen3/Llama',all((v[l]>1)==(f!='SmolLM2') for f,v in draft.items() for l in ('PQ','QB')))
    check('Near-parity Llama regression retained',plots['task_ratios']['Llama'][0][9]<1)
    sourcefig=(ROOT/'figures/task_cost.tex').read_text()
    coords=[float(x) for x in re.findall(r'\(([0-9]+\.[0-9]{12}),[0-9]+\.[0-9]{2}\)',sourcefig)]
    check('All 72 task plot source coordinates retained',len(coords)==72 and coords==[round(v,12) for fam in plots['task_ratios'].values() for series in fam for v in series])
    ss=plots['original_session_ratios']
    check('Original Qwen3 and Llama target-only reversals retained',all(ss[k][0]<1<ss[k][1] for k in ('Qwen3 M','Llama M')))
    check('Original six speculative session directions retained',all(v>1 for k in ('Qwen3 C','SmolLM2 C','Llama C') for v in ss[k]))
    sd=load('state_and_pilot.json')
    counts=Counter(v for row in sd['subsets'].values() for v in row)
    check('80 distinct subset/direction cells',sum(counts.values())==80)
    check('30 donor, 54 third, 76 changed-byte null requests',{k:v*2 for k,v in counts.items()}=={'B':30,'C':54,'D':76})
    check('192 total requests including 32 controls',sum(counts.values())*sd['repeats_per_coordinate']+sd['controls']==192)
    matrix=(ROOT/'supplement/05_components.tex').read_text()
    actual=[]
    for line in matrix.splitlines():
        if re.fullmatch(r'.+&\s*[BCD](?:&[BCD]){7}\\\\(?:\\bottomrule)?',line):
            actual.append(re.findall(r'(?<=&)[BCD]',line.replace(' ','')))
    check('All 80 printed subset table cells match data',actual==list(sd['subsets'].values()))
    check('Nonmonotone V0 to K0+V0 counterexample retained',sd['subsets']['V0'][1]=='B' and sd['subsets']['K0+V0'][1]=='D')
    check('Stable-input mixed-state contrast retained',sum(row[4]=='C' for row in sd['subsets'].values())+sum(row[5]=='C' for row in sd['subsets'].values())==16 and all(row[6:]==['D','D'] for row in sd['subsets'].values()))
    q=sd['quartet_1248_B_to_A_t47'];e,k,v,j=[Fraction.from_float(float(x)) for x in q['d']]
    check('Exact reported binary64 four-cell residual',j-k-v+e==Fraction.from_float(float(q['residual'])))
    check('Exact reported additive prediction',k+v-e==Fraction.from_float(float(q['additive_prediction'])))
    check('Additive and observed joint signs differ',k+v-e>0 and j<0)
    check('Actual reported full-vocabulary argmax retained',q['argmax']==[220,220,832,220])
    canon=sd['canonical_1248_t47'];check('POSITION pair reversal has one canonical scalar',float(canon['forward_I'])==-float(canon['reverse_I'])==float(canon['canonical_I']))
    cov=sd['coverage'];check('44/112 coverage and 240 vector gap preserved',cov['available_repeat_level']==44 and cov['planned_repeat_level']==112 and cov['missing_unique_vectors']==240 and cov['new_qualified_quartets']==0)
    check('Logical counts not promoted to independent inputs',cov['canonical_POSITION_conditions']+cov['L0_oriented_conditions']==16 and cov['independent_inputs']==4)
    norms=sorted(sd['full_KV_norms_B_relative_to_A'],key=lambda x:x['relative_L2'])
    check('Four-norm monotone-threshold counterexample',[x['natural_different'] for x in norms]==[True,False,False,True])
    check('Seven available frontier rows retained',len(sd['frontier_rows'])==7)
    check('No missing /831 recipient-A L0 frontier imputed',not any(row[0]==831 and row[1]=='B->A' and row[2]=='L0' for row in sd['frontier_rows']))
    p=sd['pilot'];check('Pilot 48 complete, one interrupted, 31 unstarted',p['complete_requests']+p['interrupted']==p['process_attempts']==49 and p['process_attempts']+p['unstarted']==80)
    check('All 14 pilot counterexamples retained',sum(x is not None for row in p['first_difference_rows'] for x in row)==14)
    check('All eight candidate match counts retained',[sum(x is None for x in row) for row in p['first_difference_rows']]==p['expected_matches'])
    check('Forward counts are distinct from requests',p['old_R_callers']+p['new_callers']==p['total_callers']==8110)
    check('Pilot invalidity and absent speedup preserved',p['qualified_speedup'] is None and not p['execution_contract_qualified'] and not p['P2_executed'] and not p['P3_executed'])
    check('Charged and exact lifecycle remain distinct',p['charged_seconds']>p['owned_PID_seconds'] and p['wall_seconds']>p['charged_seconds'])
    with (DATA/'historical_disposition.csv').open(newline='',encoding='utf-8') as stream:
        ledger=list(csv.DictReader(stream))
    check('All 28 legacy groups retained',[r['id'] for r in ledger]==[f'E{i:02}' for i in range(1,29)])
    texfiles=[p for p in ROOT.rglob('*.tex') if 'anc' not in p.parts]
    texts='\n'.join(p.read_text() for p in texfiles)
    labels=re.findall(r'\\label\{([^}]+)\}',texts)
    refs=[x for x in re.findall(r'\\(?:ref|eqref|pageref|sref)\{([^}]+)\}',texts) if not x.startswith('#')]
    check('Unique source labels',len(labels)==len(set(labels)))
    check('Every source cross-reference resolves',set(refs)<=set(labels))
    bib=(ROOT/'references.bib').read_text();keys=re.findall(r'^@\w+\{([^,]+),',bib,re.M)
    cites=set(x.strip() for group in re.findall(r'\\cite(?:\[[^\]]*\])?\{([^}]+)\}',texts) for x in group.split(','))
    check('37 unique bibliography entries: original 25, ten follow-up records and two FlashAttention papers',len(keys)==len(set(keys))==37)
    check('Every citation resolves with no unused entry',cites==set(keys))
    check('Single TeX document entry',sum(r'\documentclass' in p.read_text() for p in texfiles)==1)
    check('Shared bibliography and continuous pages',texts.count(r'\bibliography{references}')==1 and r'\setcounter{page}' not in texts)
    check('All main/supplement figure definitions present',len(list((ROOT/'figures').glob('*.tex')))==10)
    check('No undeclared external document or shell escape',not any(s in texts for s in ('\\externaldocument','\\write18','\\tikzexternalize')))
    for match in re.findall(r'\\input\{([^}]+)\}',texts):
        check('Input dependency: '+match,(ROOT/(match if match.endswith('.tex') else match+'.tex')).is_file())
    src=load('source_manifest.json')
    check('All companion records are full commit pins',all(re.fullmatch('[0-9a-f]{40}',s['commit']) for s in src['sources']))
    check('No new model run or complete raw-audit claim',src['new_model_executions_in_this_release']==0 and src['complete_native_archive_restore_performed_here'] is False)
    check('Completed RTX replaces obsolete status',not any(x in texts for x in ('five of six','broader E1 captures remain pending','final confirmation and broader E1')))
    from check_rtx104 import verify as verify_rtx
    rtx=verify_rtx(check,ROOT)
    from check_portability import verify
    verify(load('portability111.json'),check)
    from check_closure import verify as verify_closure
    closure=verify_closure(check,ROOT)
    import importlib.util
    spec=importlib.util.spec_from_file_location('generate_e2_absolute_cost',ROOT/'scripts/generate_e2_absolute_cost.py')
    absolute_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(absolute_module)
    absolute=absolute_module.verify(check,ROOT)
    followup_spec=importlib.util.spec_from_file_location('generate_native_followup',ROOT/'scripts/generate_native_followup.py')
    followup_module=importlib.util.module_from_spec(followup_spec);followup_spec.loader.exec_module(followup_module)
    followup=followup_module.verify(check,ROOT)
    from check_repair_interaction import verify as verify_interaction
    interaction=verify_interaction(check,ROOT)
    return {'status':'PASS','closure':closure,'repair_interaction':interaction,'checks_passed':len(checks),'checks':checks,'derived_draft_ratios':draft,'rtx104':rtx,'e2_absolute_cost':absolute,'native_followup':followup,
            'scope':'Reported-value/source checks, not native execution, full-vector reconstruction, all-input correctness or arXiv-server validation.',
            'new_model_executions':0}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=test();body=json.dumps(result,indent=2,allow_nan=False)+'\n'
    if args.output:
        with args.output.open('x',encoding='utf-8') as f:f.write(body)
    print(body)
