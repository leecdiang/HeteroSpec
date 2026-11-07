"""CPU-only finite-range research tables from the unchanged frozen raw auditor."""
import collections,csv,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent;V=D.parent
sys.path.insert(0,str(V))
from common import load,save,sha
import analyzer
a=load(D/'RECONSTRUCTED.json');plan=load(V/'PLAN.json');refs=load(V/'REFERENCE_INDEX.json')
layers={'Qwen':(0,18,35),'SmolLM2':(0,12,23),'Llama':(0,16,31)}
bands=('first','middle','last');pairs=analyzer.PAIRS;stages=analyzer.STAGES
slots={(s['descriptor'],s['layout'],s['repeat']):s for s in plan['numerical_slots']}
def band(c):return bands[layers[c['family']].index(c['layer'])]
def valid(r):return 'relation' not in r
def equal(r):return valid(r) and r['first_divergence_operator'] is None
def csv_out(name,rows):
    with (D/name).open('x',encoding='utf-8',newline='') as out:
        w=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
table=[];stage_table=[];differences=[];flat=[]
for c in a['contexts']:
    row={k:c[k] for k in ('descriptor','family','layer','phase','q')};row['layer_band']=band(c)
    row['padded_key_extent']=c['visibility']['padded_key_extent']
    row['visible_keys_per_query']=json.dumps([x['count'] for x in c['visibility']['visible_keys_by_query']])
    for layout,entries in c['layouts'].items():row[layout+'_qualified_of_2']=sum(x is not None for x in entries)
    for left,right in pairs:
        rs=[r for r in c['pairwise'] if (r['left'],r['right'])==(left,right)]
        n=sum(valid(r) for r in rs);e=sum(equal(r) for r in rs)
        row[left+'__'+right]=f'{e} bitwise / {n} qualified / 2 planned'
    table.append(row)
    for r in c['pairwise']:
        meta={k:c[k] for k in ('descriptor','family','layer','phase','q')}|dict(layer_band=band(c),left=r['left'],right=r['right'],repeat=r['repeat'])
        flat.append((c,r))
        for stage in stages:
            values=r['stages'][stage] if valid(r) else {}
            stage_table.append(meta|dict(stage=stage,qualified=valid(r),bitwise_equal=values.get('bitwise_equal'),different_F32_words=values.get('different_words'),max_absolute_error=values.get('max_error'),max_ULP=values.get('max_ULP'),first_differing_word=values.get('first_differing_word'),first_logical_index=json.dumps(values.get('first_logical_index')),first_divergence_operator=r.get('first_divergence_operator'),withheld_reason=r.get('reason')))
        if valid(r) and not equal(r):
            ready_index=max(slots[c['descriptor'],l,r['repeat']]['index'] for l in (r['left'],r['right']))
            differences.append(meta|dict(acquisition_complete_index=ready_index,input_identity=refs[c['descriptor']]['files'],first_divergence_operator=r['first_divergence_operator'],stages=r['stages']))
csv_out('CONTEXT_RELATIONS.csv',table);csv_out('PAIRWISE_STAGE_RELATIONS.csv',stage_table)
summary=[]
for left,right in pairs:
    for scope in ('all','q1_public','q_gt_1'):
        group=[(c,r) for c,r in flat if (r['left'],r['right'])==(left,right) and (scope=='all' or ((c['q']==1)==(scope=='q1_public')))]
        summary.append(dict(left=left,right=right,scope=scope,planned_context_repeat_comparisons=len(group),qualified=sum(valid(r) for c,r in group),bitwise_equal=sum(equal(r) for c,r in group),finite_different=sum(valid(r) and not equal(r) for c,r in group),withheld=sum(not valid(r) for c,r in group),first_divergence_operators=dict(collections.Counter(r['first_divergence_operator'] for c,r in group if valid(r) and not equal(r)))))
csv_out('PAIR_SUMMARY.csv',[{**r,'first_divergence_operators':json.dumps(r['first_divergence_operators'])} for r in summary])
strata=[]
for dimension in ('family','layer_band','phase','q'):
    for value in dict.fromkeys((band(c) if dimension=='layer_band' else c[dimension]) for c in a['contexts']):
        for left,right in pairs:
            group=[(c,r) for c,r in flat if (band(c) if dimension=='layer_band' else c[dimension])==value and (r['left'],r['right'])==(left,right)]
            strata.append(dict(dimension=dimension,value=value,left=left,right=right,planned=len(group),qualified=sum(valid(r) for c,r in group),equal=sum(equal(r) for c,r in group),finite_different=sum(valid(r) and not equal(r) for c,r in group),withheld=sum(not valid(r) for c,r in group)))
csv_out('STRATIFIED_RELATIONS.csv',strata)
maxima={}
for stage in stages:
    for metric in ('max_error','max_ULP'):
        ds=[d for d in differences if not d['stages'][stage]['bitwise_equal']]
        if ds:
            worst=max(ds,key=lambda d:d['stages'][stage][metric]);maxima[stage+'_'+metric]={k:worst[k] for k in ('descriptor','family','layer','layer_band','phase','q','left','right','repeat','first_divergence_operator')}|dict(value=worst['stages'][stage][metric],stage=stage,first_differing_word_in_stage=worst['stages'][stage]['first_differing_word'],first_logical_index_in_stage=worst['stages'][stage]['first_logical_index'])
qualified=[x for c in a['contexts'] for es in c['layouts'].values() for x in es if x]
repeat1=[x for x in qualified if x['repeat']==1]
assert len(qualified)==474 and len(repeat1)==237 and all(x['repeatability']=='BITWISE_PASS' for x in repeat1)
assert not any(r['stages'][s]['nonfinite_mismatches'] for c,r in flat if valid(r) for s in stages)
contexts_any=sum(any(x for es in c['layouts'].values() for x in es) for c in a['contexts'])
contexts_complete=sum(all(all(x is not None for x in es) for es in c['layouts'].values()) for c in a['contexts'])
first=min(differences,key=lambda d:d['acquisition_complete_index'])
findings=dict(full_panel_status=a['status'],planned_independent_contexts=72,contexts_with_any_qualified_data=contexts_any,contexts_complete_all5x2=contexts_complete,fully_qualified_slots=474,not_started=246,control_failures=0,nonfinite_outputs=0,independent_same_layout_repeat_pairs=237,repeatability_bitwise_pass=237,pair_summaries=summary,maxima=maxima,first_observed_pair_difference=first,valid_difference_records=len(differences),valid_difference_contexts=len({d['descriptor'] for d in differences}),primary_QH='QH_C',interpretation='Finite operator-only correspondence in observed exposed snapshots. q1 is a common original path; q>1 QH/PQ/QB correspondence does not identify kernels/reduction trees, mathematical truth, actor state, acceptance or cost. Missing coordinates remain withheld. Exact signed-rank ULP distances can be large near zero/sign changes; no tolerance is imposed.')
save(D/'SCIENTIFIC_FINDINGS.json',findings);save(D/'ALL_VALID_DIFFERENCES.json',differences)
save(D/'REFERENCE_BINDINGS.json',dict(F0_sha256=sha(V/'F0.json'),PLAN_sha256=sha(V/'PLAN.json'),REFERENCE_INDEX_sha256=sha(V/'REFERENCE_INDEX.json'),auditor_sha256=sha(V/'analyzer.py'),raw_math_sha256=sha(V/'raw_math.py'),analysis_sha256=sha(D/'RECONSTRUCTED.json')))
print(json.dumps({k:findings[k] for k in ('contexts_with_any_qualified_data','contexts_complete_all5x2','independent_same_layout_repeat_pairs','valid_difference_records','maxima')},indent=2))
