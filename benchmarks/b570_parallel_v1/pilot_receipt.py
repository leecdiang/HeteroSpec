"""Publish every first-pilot cell, including capacity misses and native divergences."""
from experiment import *
def write_pilot():
    dest=HERE/'evidence';dest.mkdir(exist_ok=True)
    short=read(ROOT/'pilot-candidate-O-qwen-1024.json')
    experiments=[dict(family=r['family'],context=r['C'],B=r['B'],head=r['head'],q=r['q'],groups=r['groups'],arm=r['arm'],observed=r['success'],equal=r['equal'],diff=r['differing_rows'],error=r['error']) for r in short]
    ref=read(ROOT/'units/first-ref-smol-4096/native/result.json')['records']
    for a in ARMS:
        rr=read(ROOT/f'units/first-smol-4096-{a}/native/result.json')['records']
        for r,s in zip(rr,ref,strict=True):
            experiments.append(dict(family='smol',context=4096,B=256,head=r['slot']['base'],q=len(r['vectors']),arm=a,
                observed=True,equal=r['vectors']==s['vectors'],diff=[i for i,(x,y) in enumerate(zip(r['vectors'],s['vectors'],strict=True)) if x!=y],
                greedy_equal=r['greedy']==s['greedy'],reference=s['vectors'],actual=r['vectors'],calls=r['graph_calls']))
    receipts=[]
    for folder in sorted((ROOT/'units').iterdir()):
        if not (folder/'RECEIPT.json').is_file() or not folder.name.startswith(('pilot-','r-grid-','first-smol-','original-P1-','alloc128-')):continue
        receipt=read(folder/'RECEIPT.json');n=read(folder/'native/result.json') if (folder/'native/result.json').exists() else {}
        receipts.append(dict(name=folder.name,**receipt,minimum_device=n.get('min_free_device'),minimum_host=n.get('min_free_ram'),error=n.get('error'),native_sha256=sha(folder/'native/result.json') if n else None))
    put_once(dest/'first-pilots.json',dict(status='development',anchor=read(ROOT/'ORIGINAL_ANCHOR.json'),cells=experiments,receipts=receipts))
if __name__=='__main__':write_pilot()
