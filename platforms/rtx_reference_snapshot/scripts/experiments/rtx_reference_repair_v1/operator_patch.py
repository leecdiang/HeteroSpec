"""Opt-in, source-bound Q8 matmul graph repair. Diagnose before selecting roles.
The wrapper is a candidate: its numerical path and actual cost require testing.
"""
import hashlib
from pathlib import Path
import re
import shutil

def apply_rows(source,code,roles,stable_norm_offload=False):
    if type(stable_norm_offload) is not bool:raise ValueError('stable norm offload flag')
    if stable_norm_offload:
        row_report=apply_rows(source,code,roles,False)
        p=Path(source)/'ggml/src/ggml-backend.cpp';text=p.read_text(encoding='utf-8')
        anchor='ggml_backend_offload_op(sched->backends[b], tensor)'
        if text.count(anchor)!=1:raise ValueError('scheduler offload anchor differs')
        before=hashlib.sha256(p.read_bytes()).hexdigest()
        includes='#include "ggml-backend-impl.h"'
        if text.count(includes)!=1:raise ValueError('backend include anchor differs')
        text=text.replace(includes,includes+'\n#include "../../src/hs_scope.h"\n#include "repair_offload.hpp"')
        text=text.replace(anchor,'hs_repair_offload::offload_op(sched->backends[b], tensor)')
        p.write_text(text,encoding='utf-8',newline='\n')
        shutil.copyfile(Path(code)/'repair_offload.hpp',p.parent/'repair_offload.hpp')
        return {'mode':'STABLE_HEAD_NORM_OFFLOAD','roles':roles,'rowwise':row_report,
                'file':'ggml/src/ggml-backend.cpp','before_sha256':before,
                'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                'header_sha256':hashlib.sha256((p.parent/'repair_offload.hpp').read_bytes()).hexdigest(),
                'scope':'Scoped target Q/K head normalization offload preference evaluated at one token; actual graph operands and operations unchanged. Native correspondence untested.'}
    if type(roles) is not int or not 0<=roles<=7:raise ValueError('role mask')
    if roles==0:return {'mode':'NO_ARITHMETIC_PATCH','roles':0}
    p=Path(source)/'src/llama-graph.cpp';text=p.read_text(encoding='utf-8')
    needle='llm_graph_context::build_lora_mm('
    if text.count(needle)!=1:raise ValueError('cannot identify unique native matmul helper; inspect frozen source')
    start=text.index(needle);brace=text.index('{',start);depth=1;end=brace+1
    while depth and end<len(text):
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    if depth:raise ValueError('unbalanced helper body')
    body=text[brace:end]
    # The main weight product, not the low-rank adapter products. Only this exact
    # source spelling is admitted automatically. An anchor repair is an engineering
    # change requiring a preserved diff, not a fallback to a global regex replacement.
    expression='ggml_mul_mat(ctx0, w, cur)'
    if body.count(expression)!=1:raise ValueError('native main weight product anchor differs; review and update exact site')
    updated=body.replace(expression,'hs_repair_mm::mul_mat(ctx0, w, cur)')
    before=hashlib.sha256(p.read_bytes()).hexdigest()
    text=text[:brace]+updated+text[end:]
    text='#include "repair_mm.hpp"\n'+text
    p.write_text(text,encoding='utf-8',newline='\n')
    shutil.copyfile(Path(code)/'repair_mm.hpp',p.parent/'repair_mm.hpp')
    return {'mode':'CANDIDATE_ROWWISE_MAIN_WEIGHT_PRODUCT','roles':roles,
      'file':'src/llama-graph.cpp','before_sha256':before,
      'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
      'bitwise_correspondence':'UNTESTED','performance':'UNTESTED',
      'note':'R/q1 and inactive draft calls take original branch; validate against historical R anyway.'}
