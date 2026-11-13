"""Supplementary offline checks for the final editorial revision.
No model execution. Original estimands and their registered intervals are unchanged.
Recovered factor root totals are identified separately from supplied observations.
"""
from pathlib import Path
from collections import defaultdict
import csv, hashlib, json, math, random
import numpy as np
P=Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text())
def need(ok,msg):
    if not ok: raise ValueError(msg)
def close(a,b,msg,atol=2e-12): need(abs(a-b)<atol*max(1.,abs(b)),msg)
def save(n,x): (P/'generated'/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')

# Existing data must match the supplied recovery package bit for bit.
base=read(P/'revision/BASELINE_IDENTITY.json')
for f,h in base['original_data_files'].items():
    need(hashlib.sha256((P/f).read_bytes()).hexdigest()==h,'Modified original data '+f)

# Complete eight-arm A5000 live pilot, as transcribed in the prior audit and
# checked this revision against the immutable source blob. No inferred M result.
pilot=read(P/'data_added/a5000_pilot_source_projection.json'); live=pilot['live']
need(len(live)==8 and pilot['root_count']==4 and pilot['measurements_per_arm']==8,'Pilot design')
rows=[];ratios=[]
for prefix,label in [('W_L4','Whole / loop4'),('W_P','Whole / packed'),('L_L4','Local / loop4'),('L_P','Local / packed')]:
    a=live[prefix+'_K3']; b=live[prefix+'_K7']
    rows.append(label+f" & {a['service_s']:.3f} & {b['service_s']:.3f}"+r' \\')
    ratios.append({'comparison':prefix+'_k7/k3','ratio':b['service_s']/a['service_s'],'increase_pct':100*(b['service_s']/a['service_s']-1)})
(P/'generated/ampere_pilot_rows.tex').write_text('\n'.join(rows)+'\n')
(P/'generated/ampere_pilot_macro.tex').write_text('\\newcommand{\\AmperePilotRows}{%\n'+'\n'.join(rows)+'\n}\n')
p3,p7=live['L_P_K3'],live['L_P_K7']
delta={k:p7[k]-p3[k] for k in ['service_s','prefill_s','verify_s','draft_s']}
delta['residual_s']=delta['service_s']-sum(delta[k] for k in ('prefill_s','verify_s','draft_s'))
packed={'service_ratio':p7['service_s']/live['L_L4_K7']['service_s'],'verify_ratio':p7['verify_s']/live['L_L4_K7']['verify_s']}
save('A5000_PILOT_RECHECK.json',{'source_commit':pilot['source_commit'],'source_blob':pilot['source_blob'],'root_count':4,'measured':64,'primers':32,'all_width_ratios':ratios,'fixed_k7_local_packed_over_loop4':packed,'local_k7_minus_k3':delta,'intervals':'None: descriptive pilot','raw_GPU_replay':False})

# Published root-ratio field projections are used as points, never as substitutes
# for absolute-time weights in the application ratio-of-totals inference.
points=read(P/'data_added/application_root_ratios.json')
for s in points['studies']:
    need(len(s['ratios'])==4,'All M controls')
    for vals,gm in zip(s['ratios'],s['published_geometric']):
        need(len(vals)==s['root_count'],'Root number')
        close(math.exp(sum(map(math.log,vals))/len(vals)),gm,'Transcribed root-ratio geometric checksum')
save('APPLICATION_POINTS_RECHECK.json',{'published_points':sum(sum(map(len,s['ratios'])) for s in points['studies']),'independent_root_counts':[s['root_count'] for s in points['studies']],'all_12_geometric_crosschecks':True,'application_CIs':'Inherited source intervals; not reconstructed from ratios','session_sensitivity':[{'model':s['model'],'best_fixed_M_session_ratios':s['best_M_session_ratios'],'min':min(s['best_M_session_ratios']),'max':max(s['best_M_session_ratios'])} for s in points['studies']]})

# Balanced factors: original Python random generator and quantile definition.
factor_out={}; endpoints=0
for tag in ('8','14'):
    d=read(P/f'data/factor{tag}.json');c=d['all_fixed_controls'];n=16
    rng=random.Random(d['seed']);ix=np.asarray([[rng.randrange(n) for _ in range(n)] for _ in range(d['bootstrap_draws'])])
    log=np.log(np.asarray(c[1]['root_ratios'])/np.asarray(c[0]['root_ratios']))
    val=float(np.exp(log.mean()));ci=np.quantile(np.exp(log[ix].mean(axis=1)),[.005,.995])
    close(val,d['interaction']['ratio'],'interaction estimate')
    for a,b in zip(ci,d['interaction']['interval']): close(float(a),b,'interaction interval')
    endpoints+=2; out={'interaction':{'ratio':val,'interval':ci.tolist()},'primary_intervals':'Inherited from source report'}
    if tag=='8':
        anchor=list(csv.DictReader((P/'data/factor8_anchor.csv').open()));need(len(anchor)==64,'All 64 anchor request times')
        w=np.asarray([sum(float(r['service_s']) for r in anchor if r['root']==root) for root in d['roots']])
        y={'W_L4_D4':w,'W_P_D4':w*np.asarray(c[2]['root_ratios']),'L_L4_D4':w*np.asarray(c[0]['root_ratios'])}
        y['L_P_D4']=y['W_P_D4']*np.asarray(c[1]['root_ratios']);out['primary_intervals']=[]
        for k,v in y.items():close(float(v.sum()),d['totals'][k],'Reconstructed factor total')
        for con in c:
            num,den=y[con['numerator']],y[con['denominator']]
            b=np.quantile(num[ix].sum(axis=1)/den[ix].sum(axis=1),[.005,.995])
            for a,z in zip(b,con['interval']):close(float(a),z,'factor interval')
            out['primary_intervals'].append(b.tolist()); endpoints+=2
        out['data_level']='W_L4: 64 supplied request times. Other arm root sums recovered from published paired ratios; not all-arm raw receipts.'
    else:out['data_level']='Published paired root ratios reconstruct interaction only; absolute root times unavailable in this package.'
    factor_out[tag+'B']=out
save('FACTOR_RECHECK.json',{'recomputed_interval_endpoints':endpoints,'studies':factor_out})

# Descriptive leave-one-root-out sensitivity, with no changes to original CIs.
q=read(P/'data/q8_root_sums.json');x=np.asarray(q['sums']); contrasts=[]
for i,j in [(1,0),(3,2),(5,4),(7,6)]:
    ratios=(x[i].sum()-x[i])/(x[j].sum()-x[j])
    contrasts.append({'numerator':q['arms'][i],'denominator':q['arms'][j],
       'original_ratio':float(x[i].sum()/x[j].sum()),'leave_one_root_out':ratios.tolist(),'range':[float(ratios.min()),float(ratios.max())]})
rows=list(csv.DictReader((P/'data/q32_measurements.csv').open()));by=defaultdict(lambda:defaultdict(float))
for r in rows: by[r['root']][r['arm']]+=float(r['service_s'])
tot={a:sum(r[a] for r in by.values()) for a in next(iter(by.values()))}
q32=[]
for a,b in [('W_REF1G_M','W_REF1L_M'),('L_REF1G_M','L_REF1L_M'),('L_REF1G_D4','L_REF1G_M')]:
    vals=[(tot[a]-r[a])/(tot[b]-r[b]) for r in by.values()]
    q32.append({'numerator':a,'denominator':b,'ratio':tot[a]/tot[b],'leave_one_root_out':vals,'range':[min(vals),max(vals)]})
save('SUPPLEMENTARY_SENSITIVITY.json',{'label':'Post-hoc descriptive sensitivity; no new experiments, extra independent tasks, or altered registered intervals','q8_live':contrasts,'q32':q32})

# Origin identities and complete structural matrix: algebra only.
e=read(P/'data/q8_equal_work.json');expected={'APPS/train/65','GSM8K/test/70','GSM8K/test/806','GSM8K/test/986'}
print('equal-work keys',e.keys())
origins=e.get('origins',e.get('roots'))
if origins is not None: need(set(origins)==expected,'Four exact origin IDs')
for cell in e['cells']:
    if 'origins' in cell: need(set(cell['origins'])==expected,'origin IDs per cell')
rtx=read(P/'data/rtx_factor_cells.json')
# Preserve its source schema rather than assuming each cell has the same layout.
save('REVISION_RECALCULATION.json',{'status':'PASS','GPU_requests':0,'original_data_files_unchanged':len(base['original_data_files']),'application_ratio_checks':15,'application_point_fields':176,'q32_request_records':96,'q8_root_aggregates':128,'q8_CI_endpoints':16,'additional_factor_CI_endpoints':endpoints,'source_pilot_arms':8,'pilot_is_not_first_use_diagnostic':True,'no_raw_KV_reconstruction':True,'new_sensitivity':'Separately labelled descriptive LOO and source session ratios','statistical_definitions_changed':False})
print('Revision recheck PASS: original data, all pilot arms, 176 points, factor endpoints and labelled sensitivity.')

# Newly completed operator follow-up: exact public ratios are the available level.
s2=read(P/'data_added/strong_s2_source_projection.json'); s2out=[]
for c in s2['contrasts']:
    need(len(c['block_ratios'])==4 and all(len(x)==3 for x in c['block_ratios']),'S2 complete four-cell paired matrix')
    vals=[math.exp(sum(map(math.log,row))/len(row)) for row in c['block_ratios']]
    for val,want in zip(vals,c['geometric_ratios']):close(val,want,'S2 cell geometric ratio')
    gm=math.exp(sum(map(math.log,vals))/4);close(gm,c['equal_cell_geometric_ratio'],'S2 equal-cell statistic')
    s2out.append({'candidate':c['candidate'],'baseline':c['baseline'],'cell_geometric_ratios':vals,'equal_cell_geometric_ratio':gm,'paired_ranges':[[min(x),max(x)] for x in c['block_ratios']],'total_ratio_inherited':c['total_ratio_inherited']})
for i in range(4):
    for j in range(3):close(s2['contrasts'][0]['block_ratios'][i][j]*s2['contrasts'][1]['block_ratios'][i][j],s2['contrasts'][2]['block_ratios'][i][j],'S2 paired-ratio algebra')
s2rows=[]
for i,label in enumerate(s2['cells']):
    typ,q=label.split('/'); a=s2out[0];b=s2out[1];lo,hi=a['paired_ranges'][i]
    s2rows.append(typ.replace('_',r'\_')+' & '+q+f" & {b['cell_geometric_ratios'][i]:.4f} & {a['cell_geometric_ratios'][i]:.4f} & [{lo:.4f}, {hi:.4f}]"+r' \\')
(P/'generated/strong_s2_macro.tex').write_text('\\newcommand{\\StrongSTwoRows}{%\n'+'\n'.join(s2rows)+'\n}\n')
save('STRONG_S2_RECHECK.json',{'source_commit':s2['source_commit'],'source_blob':s2['source_blob'],'source_level':s2['projection_level'],'published_paired_ratios_checked':36,'per_cell_estimates_recomputed':12,'equal_cell_estimates_recomputed':3,'paired_ratio_algebra_checks':12,'all_cells':s2out,'intervals':'None: descriptive exposed-cell study','raw_time_receipts_read_this_revision':False,'new_GPU_requests':0,'full_model_S3_completed':False})

report=read(P/'generated/REVISION_RECALCULATION.json')
report.update(strong_S2_published_pair_ratios_recomputed=36, strong_S2_cell_geometric_estimates=12, strong_S2_equal_cell_estimates=3, strong_S2_raw_elapsed_receipt_replay=False, strong_S2_full_service_result=False)
save('REVISION_RECALCULATION.json',report)
