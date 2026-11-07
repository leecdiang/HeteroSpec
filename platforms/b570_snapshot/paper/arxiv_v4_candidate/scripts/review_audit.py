#!/usr/bin/env python3
"""Descriptive review diagnostics only; does not change registered estimates."""
from pathlib import Path
import csv, hashlib, json, math, re, statistics
ROOT=Path(__file__).resolve().parents[1]
def gm(values):
    return math.exp(statistics.fmean(math.log(float(x)) for x in values))
def contrast(rgb):
    c=[int(rgb[i:i+2],16)/255 for i in (0,2,4)]
    c=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c]
    lum=sum(v*w for v,w in zip(c,(.2126,.7152,.0722)))
    return 1.05/(lum+.05)
def main():
    with (ROOT/'anc/rtx104/E2_SESSION_CONTRASTS.csv').open(newline='') as stream:
        rows=list(csv.DictReader(stream))
    loo={}
    for f in ['Qwen','SmolLM2','Llama']:
        for path in ['M','C']:
            r=sorted((x for x in rows if x['family']==f and x['path']==path),key=lambda x:int(x['session']))
            vals=[math.exp(statistics.fmean(float(x['log_latency_contrast']) for i,x in enumerate(r) if i!=k)) for k in range(6)]
            loo[f+'/'+path]={'min_ratio':min(vals),'max_ratio':max(vals),'all_above_parity':all(v>1 for v in vals),'all_above_original_ratio_margin':all(v>1.02 for v in vals)}
    colors=dict(re.findall(r'\\definecolor\{([^}]+)\}\{HTML\}\{([A-Fa-f0-9]+)\}',(ROOT/'preamble.tex').read_text()))
    out={'scope':'Descriptive leave-one-session-out sensitivity and palette screen, not new inference, confidence intervals, power or formal evidence expansion.',
         'leave_one_session_out':loo,'text_color_contrast_on_white':{k:contrast(colors[k]) for k in ('target','qualified','draft','aux','linkblue')},
         'palette_limit':'This numeric white-background screen is not a full accessibility or color-vision certification.',
         'ratio_margin_translation':{'PQ_over_QB':1.02,'corresponding_QB_latency_reduction':1-1/1.02,'later_service_reduction_margin':.02},
         'new_native_executions':0}
    p=ROOT/'anc/review_round2/DESCRIPTIVE_AUDIT.json';p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__': main()
