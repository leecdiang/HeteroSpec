"""Offline Git object membership, retrieved content and host-clock ordering.

No execution or producer imports. Git proves membership, not a trusted time.
"""
import argparse,base64,hashlib,json
from pathlib import Path
from verify_common import read,require,sha

def object_id(kind,data):
    return hashlib.sha1(kind.encode()+b' '+str(len(data)).encode()+b'\0'+data).hexdigest()

def tree_entries(data):
    result={};position=0
    while position<len(data):
        nul=data.index(b'\0',position);mode,name=data[position:nul].split(b' ',1)
        result[name.decode('utf-8')]=(mode.decode(),data[nul+1:nul+21].hex());position=nul+21
    return result

def checkpoint(root,metadata,stage):
    root=Path(root);metadata=Path(metadata);r=read(metadata/(stage+'_REMOTE_RECEIPT.json'))
    require(not r.get('synthetic_fixture') and r['commit']==r['remote_ref'] and r['full_retrieval_verified'],'real retrieved receipt required')
    manifest=metadata/(stage+'_MANIFEST.json');require(sha(manifest)==r['manifest_sha256'],'manifest receipt digest')
    m=read(manifest);snapshot=root/'work/frozen-checkpoints'/stage;proof=read(snapshot/'GIT_MEMBERSHIP.json');commit=(snapshot/'commit.object').read_bytes()
    require(object_id('commit',commit)==r['commit']==proof['commit'],'commit object identity')
    root_tree=commit.splitlines()[0].decode().removeprefix('tree ');require(root_tree==r['tree_sha']==proof['root_tree'],'commit root tree')
    trees={}
    for d,h in proof['trees'].items():
        payload=(snapshot/'trees'/(h+'.object')).read_bytes();require(object_id('tree',payload)==h,'tree object identity');trees[d]=tree_entries(payload)
    require(proof['trees']['']==root_tree,'root tree proof')
    for d,h in proof['trees'].items():
        if not d:continue
        parent=Path(d).parent.as_posix();parent='' if parent=='.' else parent
        require(trees[parent][Path(d).name][1]==h,'tree ancestor membership')
    for name,v in r['retrieved_files'].items():
        payload=(snapshot/'files'/name).read_bytes();require(len(payload)==v['bytes'] and hashlib.sha256(payload).hexdigest()==v['sha256'],'retrieved bytes')
        blob=object_id('blob',payload);parent=Path(name).parent.as_posix();parent='' if parent=='.' else parent
        require(blob==v['git_blob']==trees[parent][Path(name).name][1],'blob membership')
        if name in m['files']:require(v['sha256']==m['files'][name]['sha256'],'frozen file digest')
        require(v['retrieved_utc']<=r['remote_ack_utc'],'ack before retrieval')
    require(set(m['files'])<=set(r['retrieved_files']),'manifest files not all retrieved')
    # F2 is also a full raw prediction package: authenticate actual concatenation.
    if stage=='F2':
        indexes=[n for n in r['retrieved_files'] if n.startswith('artifacts/rtx_trajectory_sufficiency_v3/pre-live-') and n.endswith('.parts.json')]
        require(len(indexes)==1,'F2 pre-live author archive missing/duplicate')
        index=read(snapshot/'files'/indexes[0]);h=hashlib.sha256();total=0
        for part in index['parts']:
            b=(snapshot/'files'/part['path']).read_bytes();require(len(b)==part['bytes'] and hashlib.sha256(b).hexdigest()==part['sha256'],'retrieved F2 archive part');h.update(b);total+=len(b)
        require(h.hexdigest()==index['sha256'] and total==index['bytes'],'retrieved F2 complete archive')
    return {'status':'PASS','stage':stage,'commit':r['commit'],'retrieved_files':len(r['retrieved_files']),'trusted_timestamp':False}

def host_run(row,expected_gpu=None):
    require(row['started_utc']<row['ended_utc'] and row['started_monotonic_ns']<row['ended_monotonic_ns'],'run host interval')
    for label in ['device_before','device_after']:
        s=row[label];require(len(s['values'])==10,'device snapshot fields')
        if expected_gpu:require(s['values'][:3]==expected_gpu,'device identity')
    require(row['device_before']['utc']<row['ended_utc'] and row['device_after']['utc']>=row['ended_utc'],'pre/post device ordering')

def thermal(metadata):
    r=read(Path(metadata)/'B_THERMAL_ENTRY.json');require(r['status']=='PASS' and 120<=r['elapsed_seconds']<=600 and r['minimum_idle_seconds']==120,'thermal entry wait')
    last=r['samples'][-3:];require(len(last)==3,'thermal samples');temps=[float(x['values'][3]) for x in last];utils=[float(x['values'][6]) for x in last]
    require(max(utils)<=5 and max(temps)<=55 and max(temps)-min(temps)<=2,'thermal thresholds')
    require(all(b['monotonic_ns']-a['monotonic_ns']>=10_000_000_000 for a,b in zip(last,last[1:])),'thermal spacing')
    return last[-1]['utc']

def checkout(root,stage):
    root=Path(root);metadata=root/'benchmarks/rtx_trajectory_cost_v3';r=read(metadata/(stage+'_REMOTE_RECEIPT.json'));p=read(metadata/(stage+'_GIT_PROOF.json'))
    commit=base64.b64decode(p['commit_base64']);require(object_id('commit',commit)==r['commit']==p['commit'],'portable commit object')
    root_tree=commit.splitlines()[0].decode().removeprefix('tree ');require(root_tree==r['tree_sha']==p['root_tree'],'portable root tree')
    require(p['trees']['']['sha']==root_tree,'portable root tree membership')
    trees={}
    for d,v in p['trees'].items():
        b=base64.b64decode(v['base64']);require(object_id('tree',b)==v['sha'],'portable tree object');trees[d]=tree_entries(b)
    for d,v in p['trees'].items():
        if not d:continue
        parent=Path(d).parent.as_posix();parent='' if parent=='.' else parent;require(trees[parent][Path(d).name][1]==v['sha'],'portable directory membership')
    m=metadata/(stage+'_MANIFEST.json');require(sha(m)==r['manifest_sha256'],'portable checkpoint manifest');require(set(read(m)['files'])<=set(r['retrieved_files']),'portable retrieval coverage')
    for name,v in r['retrieved_files'].items():
        b=(root/name).read_bytes();require(len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256'],'checkout frozen bytes '+name)
        parent=Path(name).parent.as_posix();parent='' if parent=='.' else parent;require(object_id('blob',b)==v['git_blob']==trees[parent][Path(name).name][1],'checkout blob membership '+name)
    return {'status':'PASS','stage':stage,'commit':r['commit'],'full_frozen_files':len(r['retrieved_files']),'GPU_required':False,'network_required':False,'trusted_timestamp':False}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--checkout-root',type=Path,required=True);ap.add_argument('--stage',choices=['F0','F1','F2','B_START'],required=True);a=ap.parse_args();print(json.dumps(checkout(a.checkout_root,a.stage)))
