"""Strict saved-byte checks. Passing CPU fixtures is never GPU qualification."""
import hashlib
from pathlib import Path
import numpy as np
from readers_legacy.active_kv import parse
from support import need,sha,safe_relative


def f32(path,rows,columns):
    raw=Path(path).read_bytes()
    need(len(raw)==rows*columns*4,'Complete requested F32 matrix')
    need(bool(np.isfinite(np.frombuffer(raw,dtype='<f4')).all()),'Nonfinite full output')
    return raw


def vectors(actual,expected,rows,columns):
    a=f32(actual,rows,columns);b=f32(expected,rows,columns)
    need(a==b,'Full output byte mismatch; tolerance is not adjustable')
    return dict(bytes=len(a),sha256=hashlib.sha256(a).hexdigest(),rows=rows,columns=columns)


def state(actual,expected,positions,profile):
    need(len(profile['layers'])==64 and [l['id']for l in profile['layers']]==list(range(64)),
         'All 64 layers required for this 32B model')
    a,am=parse(Path(actual).read_bytes(),list(range(positions)),profile)
    b,bm=parse(Path(expected).read_bytes(),list(range(positions)),profile)
    need(am['active_layout_sha256']==bm['active_layout_sha256'],'Active KV layout differs')
    need(bool(np.isfinite(np.frombuffer(a,dtype='<f2')).all() and
              np.isfinite(np.frombuffer(b,dtype='<f2')).all()),'Nonfinite active F16 KV')
    need(a==b,'Complete active K/V byte mismatch')
    return dict(layers=64,positions=positions,active_bytes=len(a),active_sha256=hashlib.sha256(a).hexdigest(),
                actual_raw_sha256=sha(actual),reference_raw_sha256=sha(expected),
                profile_sha256=am['profile_sha256'],layout_sha256=am['active_layout_sha256'])


def operand(actual,gold_files,operation,q,m):
    """All output rows, actual batch-quantizer bytes, padding, column order."""
    actual=Path(actual)
    need(len(gold_files)>=q,'Complete ordered independent gold columns')
    expected=b''.join(f32(p,1,m)for p in gold_files[:q])
    value=f32(actual/(operation+'.f32'),q,m)
    need(value==expected,'Independent original scalar output differs')
    return dict(output_sha256=hashlib.sha256(value).hexdigest(),rows=q,columns=m)


def quantized_chunks(directory,descriptors,gold_files,q):
    directory=Path(directory);parts=[];rows=0
    for d in descriptors:
        value=(directory/safe_relative(d['file'])).read_bytes();need(len(value)==d['bytes'] and
             hashlib.sha256(value).hexdigest()==d['sha256'],'Actual quantized activation payload')
        need(type(d['rows'])is int and d['rows']>0,'Quantized row count')
        rows+=d['rows'];parts.append(value)
    expected=b''.join(Path(p).read_bytes()for p in gold_files[:q])
    need(rows==q and b''.join(parts)==expected,'Complete quantized columns/padding differ from pristine gold')
    return dict(rows=rows,bytes=len(expected),sha256=hashlib.sha256(expected).hexdigest())


def physical(record,arm,q):
    c=record['work_counters']
    expected=dict(G=(q,q,0),B=(1,q,1 if q>1 else 0),C=(1,1,0))[arm]
    need(c['quant_calls']==expected[0] and c['scalar_dot_dispatches']==expected[1] and
         c['backend_loop_entries']==expected[2] and c['quant_rows']==q and
         c['scalar_dot_columns']==q,'Actual physical quantization/scalar dispatch differs')
    need(c['kernel_application_launch_calls']>=expected[0]+expected[1],'Missing actual kernel launch evidence')
    need(c['opaque_library_internal_launches']is None,'Opaque launches must not be invented')
    return dict(arm=arm,q=q,actual=c,instrumented_implementation=True)
