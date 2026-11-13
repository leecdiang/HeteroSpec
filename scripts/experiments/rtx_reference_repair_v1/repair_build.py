"""Patch only the fresh authenticated source extraction before its core build."""
from pathlib import Path
import hashlib, re, shutil, json

def patch_core(source,code):
    source,code=Path(source),Path(code)
    # Check pinned capsule APIs, never silently infer a compute device from buffers.
    context=(source/'src/llama-context.h').read_text()
    backend=(source/'ggml/include/ggml-backend.h').read_text()
    for token,text in [('get_sched()',context),('ggml_backend_sched_get_tensor_backend',backend),('ggml_backend_name',backend)]:
        if token not in text:raise ValueError('required source API absent: '+token)
    p=source/'src/llama-graph.cpp';s=p.read_text();before=hashlib.sha256(p.read_bytes()).hexdigest()
    start=s.find('llm_graph_context::build_lora_mm(')
    if start<0:raise ValueError('audited dense projection entry missing')
    begin=s.find('{',start);depth=1;i=begin+1
    while depth and i<len(s):
        depth+=(s[i]=='{')-(s[i]=='}');i+=1
    if depth:raise ValueError('unbalanced projection function')
    body=s[begin:i]
    pattern=r'ggml_mul_mat\(\s*ctx0\s*,\s*([A-Za-z_][A-Za-z_0-9]*)\s*,\s*([A-Za-z_][A-Za-z_0-9]*)\s*\)'
    found=list(re.finditer(pattern,body))
    if not found:raise ValueError('dense projection MUL_MAT anchor missing')
    # Only the first base projection; LoRA additions and other operations unchanged.
    m=found[0];body=body[:m.start()]+'hs_repair_rows::mul_mat(ctx0, '+m[1]+', '+m[2]+')'+body[m.end():]
    s=s[:begin]+body+s[i:]
    s='#include "reference_rows.h"\n'+s
    p.write_text(s,encoding='utf-8',newline='\n')
    precision_changes=[]
    for q in (source/'src').rglob('*.cpp'):
        original=q.read_text()
        if 'ggml_mul_mat_set_prec(' not in original:continue
        changed=original.replace('ggml_mul_mat_set_prec(', 'hs_repair_rows::set_prec(')
        if '#include "reference_rows.h"' not in changed:changed='#include "reference_rows.h"\n'+changed
        q.write_text(changed,encoding='utf-8',newline='\n')
        precision_changes.append({'path':q.relative_to(source).as_posix(),'before':hashlib.sha256(original.encode()).hexdigest(),'after':hashlib.sha256(q.read_bytes()).hexdigest()})
    shutil.copyfile(code/'reference_rows.h',source/'src/reference_rows.h')
    return {'file':'src/llama-graph.cpp','before':before,'after':hashlib.sha256(p.read_bytes()).hexdigest(),
            'kind':'process-fixed optional operator-family row lowering; off/R/draft use original call',
            'precision_forwarding':precision_changes,'native_validated':False}
