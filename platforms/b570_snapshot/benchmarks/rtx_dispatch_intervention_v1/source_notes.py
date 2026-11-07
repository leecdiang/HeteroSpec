"""CPU-only build provenance and inspected source candidates, never binary causality."""
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
r=root();base=Path('D:/hs104-e1-v1/native');paths=['build/CMakeCache.txt','build/build.ninja','source/ggml/src/ggml-cuda/ggml-cuda.cu','source/ggml/src/ggml-cuda/mmvf.cu','source/ggml/src/ggml-cuda/softmax.cu']
rows=[]
for rel in paths:
    p=base/rel;dest=r/'SOURCE_PROVENANCE'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());rows.append(dict(path=str(p),sha256=sha(p),retained=dest.relative_to(r).as_posix()))
s=load(r/'RUN_SPEC.json');save(r/'SOURCE_LINK.json',dict(status='SOURCE_LINK_UNKNOWN',files=rows,reason='local E1 build CMakeCache reports GGML_CUDA=OFF while the frozen staged CUDA DLL is present. No authenticated compile/link receipt connects this candidate CUDA source to that exact DLL; no forced-dispatch or numerical rebuild.',inspected_predicates=[dict(file='ggml-cuda.cu',lines='1839-1854',detail='matmul delegates to should_use_mmvf, then cuBLAS/fallback candidates'),dict(file='mmvf.cu',lines='792-808',detail='requires even reduction dimension, native inner stride, higher strides divisible by 2*type_size'),dict(file='softmax.cu',lines='287,342-350',detail='specialized ncols launch list includes1024 with dynamic fallback')],empirical_causality='must use actual retained CUPTI signatures; source predicates are hypotheses, not matched-binary proof',numerical_DLLs=s['numerical_DLLs'],GPU_calls=0))
print('SOURCE_LINK_UNKNOWN: candidate source retained and hashed')
