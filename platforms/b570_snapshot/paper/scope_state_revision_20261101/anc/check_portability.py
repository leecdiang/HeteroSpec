"""Reported-value and necessary-condition checks only; no CPU graph or GPU run."""
import itertools,json,math,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def evaluate_necessary_condition(left,right,version_bound=True):
    """Never return positive complete support from one necessary condition."""
    if not version_bound:return {'batch_equal':None,'full_support':None}
    if any(type(n) is not int or n<1 for n in (left,right)):
        raise ValueError('positive integer extents required')
    equal=left==right
    return {'batch_equal':equal,'full_support':None if equal else False}

def verify(data,check):
    c=data['cpu'];b=data['backend']
    check('PR111 fixed result identity',data['commit']=='9fafc4ba49119f1c52e1606d295bd0b9a55a06d1')
    check('PR111 72 geometric coordinates',len(list(itertools.product(c['q'],c['key_extent'],c['heads'],range(c['storage_conditions']))))==c['geometries']==72)
    check('PR111 432 synthetic fixtures',c['geometries']*c['mask_conditions']*c['data_patterns']==c['fixtures']==432)
    check('PR111 development and holdout not GPU samples',c['development']+c['holdout']==432 and [c['development'],c['holdout']]==[144,288])
    check('PR111 actual graph count',c['graph_computes']==3*c['fixtures']==1296 and c['q1_common_graphs']+c['q2_distinct_graphs']==1296)
    check('PR111 q1 actually executed as common chain',c['q1_common_graphs']==648)
    check('PR111 structured subset counts',c['single_key_structured']==72 and c['structured_fixtures']==216<=432)
    check('PR111 exact structural failures absent',c['exact_structured_failures']==c['crashes']==c['nonfinite_outputs']==0 and c['symbolic_faults_detected']==4)
    check('PR111 general errors preserved without tolerance',c['general_pass_tolerance'] is None and math.isclose(c['max_abs']['AV_final'],5.513250481611193e-5,rel_tol=1e-14) and math.isclose(c['max_abs']['softmax'],5.36080310351017e-9,rel_tol=1e-14))
    check('PR111 adds no model or GPU observations',c['new_gpu_calls']==c['new_model_requests']==0)
    check('PR111 final descriptor closeout is distinct',c['checker_schema']==2 and c['closeout_descriptor_tests']==13)
    check('PR111 source identity and shader boundary',b['source_sha256']=='04615c97998a76d2d0b15d2ebb93bf381eb3fb565492d7714d3fc9d1c333b98d' and b['bound_core_files']==7 and b['unbound_shader_bodies']==3)
    for row in b['rows']:
        for op in ('QK','AV'):
            result=evaluate_necessary_condition(*row[op+'_src_ne3'])
            check('PR111 '+row['layout']+'/'+op+' support semantics',result=={'batch_equal':row['necessary_condition'],'full_support':row['full_support']})
    check('PR111 actual placement and cause remain unknown',all(b[k] is None for k in ('actual_native_assignment','actual_fallback_transfers','root_cause_of_native_endpoint')))
    check('PR111 unbound backend remains unknown',evaluate_necessary_condition(1,2,False)=={'batch_equal':None,'full_support':None})
    p=json.loads((ROOT/'anc/state_and_pilot.json').read_text())['pilot']
    indexes={task:{a:i for i,g in enumerate(groups) for a in g} for task,groups in data['endpoint_classes'].items()}
    check('PR111 all four endpoint maps contain all ten arms',len(indexes)==4 and all(len(m)==10 for m in indexes.values()))
    for left,right in [('M_B_QB','C_B_PQ'),('M_R_QB','C_R_PQ'),('C_B_MQ','C_B_QB')]:
        check('PR111 full endpoint relation '+left+'='+right,all(m[left]==m[right] for m in indexes.values()))
    check('PR111 same first difference can have different full endpoint',indexes['1011']['C_R_MQ']!=indexes['1011']['C_R_QB'])
    check('PR111 classes preserve all14 pilot counterexamples',sum(indexes[t][a]!=indexes[t]['R'] for t in p['tasks'] for a in p['arms'])==14)
    check('PR111 classes preserve per-arm pilot match counts',[sum(indexes[t][a]==indexes[t]['R'] for t in p['tasks']) for a in p['arms']]==p['expected_matches'])
    text=(ROOT/'sections/06_boundaries.tex').read_text()
    supp=(ROOT/'supplement/06_backend_port.tex').read_text()
    check('PR111 mathematical legality and backend rejection separate',r'\label{sec:backend}' in text and 'necessary condition' in text and 'Actual placement and fallback transfers' in text)
    check('PR111 exact batch-dimension pairs preserved','extent 1' in text and 'extent 2' in text and 'Both are rejected' in text)
    check('PR111 synthetic tests are not GPU qualification','432' in supp and 'synthetic' in supp and 'unknown' in supp)
    check('PR111 old pilot remains unqualified','31 unstarted' in supp and '14 endpoint counterexamples' in supp)
    return {'scope':'Reported-value arithmetic and necessary-condition checks, not the original graph harness or source/binary rebuild','new_gpu_executions':0}

if __name__=='__main__':
    names=[]
    def check(name,ok):
        if not ok:raise ValueError(name)
        names.append(name)
    data=json.loads((ROOT/'anc/portability111.json').read_text())
    result=verify(data,check)
    print(json.dumps(dict(status='PASS',checks=len(names),names=names,**result),indent=2))
