"""Strict raw reconstruction, kept separate from stage math and controller."""
import math
import pathlib
from panel_common import need,digest,LIMITS
from analyzer import META_OPS

def audit_lifecycle(life,events,f0,owned_before=0.):
    """Recheck recorded process, module and watchdog evidence without a device."""
    need(life['returncode']==0 and life['stop'] is None,'native process/observer failed')
    need(type(life['pid']) is int and life['pid']>0 and type(life['creation_FILETIME']) is int and life['creation_FILETIME']>0,'actual process identity')
    elapsed=life['owned_wall_s']
    need(0<elapsed<=LIMITS['per_host_seconds'] and owned_before+elapsed<=LIMITS['owned_seconds'],'owned-time ceiling')
    samples=life['watchdog_samples'];need(samples,'watchdog observations required');last=0.
    for s in samples:
        need(s['elapsed_s']>=last and s['gap_ms']<=LIMITS['maximum_actual_gap_ms'] and (s['elapsed_s']-last)*1000<=LIMITS['maximum_actual_gap_ms'],'observer cadence')
        need(s['RSS'] is not None and s['RSS']<=LIMITS['worker_RSS_bytes'] and s['host_available']>=LIMITS['host_available_bytes'] and s['disk_free']>=LIMITS['disk_free_bytes'],'host resource ceiling')
        need(s['output_bytes']+s['archive_reserve_bytes']<=LIMITS['output_bytes'],'artifact plus export reserve ceiling');last=s['elapsed_s']
    need(0<=elapsed-last<=LIMITS['maximum_actual_gap_ms']/1000,'final observer gap')
    required={pathlib.Path(x['path']).name.lower():x['sha256'] for x in f0['dependencies']}
    drivers={}
    for x in f0['driver_files']:drivers.setdefault(pathlib.Path(x['path']).name.lower(),set()).add(x['sha256'])
    for event_name,field in (('AWAIT_RUNTIME_GATE','actual_runtime_modules'),('CLOSE','closing_runtime_modules')):
        event=next(e for e in events if e['event']==event_name);rows=life[field]
        need([r['path'] for r in rows]==event['modules'],'actual module inventory identity');seen=set()
        for r in rows:
            name=pathlib.Path(r['path']).name.lower()
            if name.startswith(('ggml','llama')):
                need(name in required and r['sha256']==required[name],'unadmitted numerical module');seen.add(name)
            if name in drivers:need(r['sha256'] in drivers[name],'driver module hash')
        need(seen==set(required),'complete numerical module inventory')
    return dict(actual_PID=life['pid'],creation_FILETIME=life['creation_FILETIME'],module_gates=2,watchdog_samples=len(samples),owned_wall_s=elapsed)

def walk_ids(desc):
    ts={t['id']:t for t in desc['tensors']};seen=[]
    def visit(i):
        if i in seen:return
        for s in ts[i]['src']:visit(s)
        seen.append(i)
    visit(desc['final']);return seen

def audit_capability(desc,nodes,expected):
    need(desc==expected,'actual graph differs from CPU-frozen graph')
    need([n['id'] for n in nodes]==walk_ids(desc),'complete ordered supports_op inventory')
    ts={t['id']:t for t in desc['tensors']}
    for n in nodes:
        t=ts[n['id']]
        need(all(n[k]==t[k] for k in ('op','type','ne','nb','view_offset','op_parameters','bytes')),'capability node descriptor')
        need(type(n['supports_op']) is bool and n['executable']==(t['op'] not in META_OPS),'full backend support bool')
    return all(n['supports_op'] for n in nodes if n['executable'])

def audit_raw(events,request,pid,expected_graphs):
    need(events and events[0]['event']=='HOST_START' and events[0]['origin']=='NATIVE_VULKAN','native origin')
    need(events[0]['pid']==pid and events[0]['request']==request,'process/wire reconstruction')
    need(events[-1]['event']=='CLOSE','complete host close')
    names=[e['event'] for e in events]
    need(names.count('AWAIT_RUNTIME_GATE')==1 and names.count('DEVICE')==1,'single device/gate')
    device=next(e for e in events if e['event']=='DEVICE')
    need('B570' in device['description'] and device['backend_name']=='Vulkan0','actual device')
    need(device['actual_alignment']==request['required_alignment_bytes'],'actual alignment matches frozen condition')
    for e in events:
        if e['event']=='MEMORY_CHECKPOINT':need(e['free']>=512*1024**2 and e['total']>0 and e['continuous'] is False,'GPU checkpoint headroom')
    gate=names.index('AWAIT_RUNTIME_GATE')
    need(names.index('DEVICE')<gate,'device identity before runtime gate')
    checkpoints=[e['point'] for e in events if e['event']=='MEMORY_CHECKPOINT']
    need(checkpoints==(['BACKEND_READY','CLOSE'] if request['kind']=='census' else ['BACKEND_READY','BEFORE_GRAPH','AFTER_GRAPH','CLOSE']),'all declared device checkpoints')
    if request['kind']=='census':
        need(not any(n.startswith('GRAPH_') for n in names),'census performs no graph compute')
        rows=[e for e in events if e['event']=='CAPABILITY'];need(len(rows)==80,'complete80 census')
        seen=set();summary=[]
        for row in rows:
            key=digest(row['cell'])+'/'+row['mode'];need(key not in seen and key in expected_graphs,'unplanned/duplicate census coordinate');seen.add(key)
            need(row['graph_compute'] is False and names.index('CAPABILITY')>gate,'support-only after gate')
            ok=audit_capability(row['graph'],row['nodes'],expected_graphs[key])
            summary.append(dict(key=key,supported=ok,graph_sha256=digest(row['graph'])))
        need(seen==set(expected_graphs),'census covers exact matrix')
        need(all(x['supported'] for x in summary),'unsupported repaired graph; stop whole panel without selection')
        return dict(census=summary,fixed_primary_candidate='QH_C',graph_calls=0)
    need(names.count('GRAPH_START')==names.count('GRAPH_RETURN')==names.count('GRAPH_OUTPUT')==1,'one complete graph call')
    need(gate<names.index('PRECOMPUTE')<names.index('PHYSICAL_LAYOUT')<names.index('BINDINGS')<names.index('GRAPH_START')<names.index('GRAPH_RETURN')<names.index('GRAPH_OUTPUT'),'event order')
    pre=next(e for e in events if e['event']=='PRECOMPUTE');desc=pre['graph']
    key=digest(request['cell'])+'/'+request['mode'];need(audit_capability(desc,pre['nodes'],expected_graphs[key]),'supported actual graph')
    output=next(e for e in events if e['event']=='GRAPH_OUTPUT')
    need(output['graph']==desc and output['input_bytes_unchanged'] is True,'returned same graph and input identity')
    need(next(e for e in events if e['event']=='GRAPH_RETURN')['status']==0,'native graph success')
    physical=next(e for e in events if e['event']=='PHYSICAL_LAYOUT');a=physical['alignment']
    need(a==device['actual_alignment'] and a>0 and a&(a-1)==0,'actual power-of-two alignment')
    ts={t['id']:t for t in desc['tensors']};pts={t['id']:t for t in physical['tensors']}
    need(set(ts)==set(pts) and len(pts)==len(physical['tensors']),'all root/view physical identities')
    for i,t in pts.items():
        need(all(t[k]==ts[i][k] for k in ('op','type','ne','nb','view_offset','op_parameters','bytes','view_root')),'physical descriptor matches graph')
        need(t['device_matches'] and t['buffer_name']=='Vulkan0' and 0<=t['offset'] and t['offset']+t['bytes']<=t['buffer_bytes'],'actual bounds/device')
        if t['view_root']!=-1:
            root=pts[t['view_root']];need(root['offset']+t['view_offset']==t['offset'],'actual flattened view offset')
        else:need(t['offset']%a==0,'independent allocation alignment')
    bindings=next(e for e in events if e['event']=='BINDINGS')['nodes']
    expected=[i for i in walk_ids(desc) if ts[i]['executable']]
    need([b['node'] for b in bindings]==expected,'actual executable binding inventory')
    for b in bindings:
        t=ts[b['node']];need([o['tensor'] for o in b['operands']]==[t['id']]+t['src'],'all bound operands')
        for role,o in enumerate(b['operands']):
            pt=pts[o['tensor']];delta=pt['offset']%a;e=4 if pt['type']=='f32' else 2
            compensated=t['op'] in ('CONT','REPEAT','CONCAT')
            need(o['offset']==pt['offset'] and o['delta']==delta and o['device_matches'] and o['compensated_path']==compensated,'bound offset identity')
            if compensated:
                limit=255 if t['op']=='CONCAT' and role in (0,2) else 65535
                need(delta%e==0 and delta//e<=limit,'offset encoding range')
            else:need(delta==0,'strict bound start alignment')
    slabs=desc['slabs'];logical=sum(s['bytes'] for s in slabs)
    return dict(graph=desc,graph_calls=1,actual_alignment=a,all_physical_bounds=True,all_actual_bindings=True,
        PQ_extra_CPU_copy_bytes=logical,PQ_extra_API_upload_bytes=logical,PQ_extra_logical_storage_bytes=logical,
        PQ_extra_allocator_rounded_bytes=sum((s['bytes']+a-1)//a*a for s in slabs),
        original_mask_retained=True,unique_VRAM_allocation_or_DRAM_traffic=None)
