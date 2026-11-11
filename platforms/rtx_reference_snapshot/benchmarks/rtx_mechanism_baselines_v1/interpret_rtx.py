"""CPU descriptive direction checks and paired change in same-QB A/A."""
import argparse,collections,math,statistics as st
from pathlib import Path
from common import load,save
from prepare_rtx import root
from export_measurements import csvfile
from analyze import summary
def main(out):
    r=root();out=Path(out);out.mkdir();a=load(r/'core_analysis/ANALYSIS.json');p=load(r/'p0_analysis/ANALYSIS.json');directions=[]
    for cohort,data in [('core',a),('p0',p)]:
        for row in data['case_contrasts']:
            sessions=collections.defaultdict(list)
            for pair in row['summary']['pairs']:sessions[pair['session']].append(pair)
            for session,pairs in sessions.items():directions.append(dict(cohort=cohort,case_id=row['case_id'],mode=row['mode'],comparison=row['comparison'],session=session,blocks=len(pairs),ratio=math.exp(st.mean(x['log_ratio'] for x in pairs)),difference_us=st.mean(x['difference_us'] for x in pairs)))
    csvfile(out/'DIRECTION_CHECKS.csv',directions);changes=[]
    for gid in {x['geometry_id'] for x in a['geometry_contrasts']}:
        rows={x['mode']:x['summary'] for x in a['geometry_contrasts'] if x['geometry_id']==gid and x['comparison']=='AA'}
        if 'OFF' not in rows or 'ON' not in rows:continue
        off={x['block']:x for x in rows['OFF']['pairs']};on={x['block']:x for x in rows['ON']['pairs']};pairs=[]
        for b in sorted(off.keys()&on.keys()):
            assert off[b]['session']==on[b]['session'];pairs.append(dict(block=b,session=off[b]['session'],log_ratio=on[b]['log_ratio']-off[b]['log_ratio'],difference_us=on[b]['difference_us']-off[b]['difference_us']))
        changes.append(dict(geometry_id=gid,comparison='AA_ON_over_AA_OFF',summary=summary(pairs,4000)))
    changes.sort(key=lambda x:x['geometry_id']);save(out/'AA_MODE_CHANGES.json',changes)
    for key,label in [('QB_A','ON/OFF QB_A'),('QB_QH','mapping QB_A/QH'),('QB_QH_alt','mapping QB_B/QH')]:
        rows=[x for x in directions if x['cohort']=='core' and x['comparison']==key and (x['mode']=='ON/OFF' if key=='QB_A' else x['mode']=='ON')];print(label,'ratio<1',sum(x['ratio']<1 for x in rows),'/',len(rows))
    save(out/'SCOPE.json',dict(analysis='descriptive per-value/per-session direction;paired whole-block AA mode change',calibrated_significance=False,posthoc_threshold_selection=False,practical_scale='prior2%/1us;report AA and all intervals rather than automatic universal winner',source='actual audited core and P0 tables;no new GPU'))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();main(a.out)
