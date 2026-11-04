#!/usr/bin/env python3
"""Host model of an INT8-MMA remapping of frozen Q8_0 MMVQ.

This does not compile or execute CUDA. It checks operand indexing, exact bounded
integer dots, an ordered symbolic FP DAG, and host numerical witnesses for two
possible contraction modes. Quantized activation bytes are inputs, not generated.
"""
import ctypes
import argparse
import hashlib
import json
import pathlib
import platform
import subprocess
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
FP = np.float32


def make_update(output_dir):
    so = output_dir / "fp_update.so"
    subprocess.run(["g++", "-std=c++17", "-O2", "-shared", "-fPIC",
                    "-ffp-contract=off", str(HERE / "fp_update.cpp"),
                    "-o", str(so)], check=True)
    lib = ctypes.CDLL(str(so))
    fp = np.ctypeslib.ndpointer(dtype=np.float32, flags="C_CONTIGUOUS")
    ip = np.ctypeslib.ndpointer(dtype=np.int32, flags="C_CONTIGUOUS")
    lib.fp_update.argtypes = [fp, fp, ip, fp, ctypes.c_size_t, ctypes.c_int]

    def update(scale, dot, acc, fused):
        scale = np.ascontiguousarray(scale, dtype=np.float32)
        dot = np.ascontiguousarray(dot, dtype=np.int32)
        acc = np.ascontiguousarray(acc, dtype=np.float32)
        out = np.empty_like(acc)
        lib.fp_update(out, scale, dot, acc, out.size, fused)
        return out
    return update


UPDATE = None
P, Z = np.indices((32, 4))
G, T = P // 4, P % 4
MMA_ROW = G + 8 * (Z // 2)
R, J = MMA_ROW // 2, 2 * T + Z % 2
VPRIME = MMA_ROW % 2


def check_fragments():
    # Reconstruct the A/B tiles from the documented m16n8k16 INT8 fragments.
    seen_a, seen_b, seen_c = set(), set(), set()
    for p in range(32):
        g, t = divmod(p, 4)
        for i in range(8):
            seen_a.add((g + 8 * (i // 4), 4 * t + i % 4))
        for i in range(4):
            seen_b.add((4 * t + i, g))
            seen_c.add((g + 8 * (i // 2), 2 * t + i % 2))
    assert seen_a == {(r, k) for r in range(16) for k in range(16)}
    assert seen_b == {(k, j) for k in range(16) for j in range(8)}
    assert seen_c == {(r, j) for r in range(16) for j in range(8)}
    mapped = {(u, int(R[p,z]), int(J[p,z]), 2*h+int(VPRIME[p,z]))
              for p in range(32) for z in range(4)
              for u in range(8) for h in range(2)}
    expected = {(u,r,j,v) for u in range(8) for r in range(8)
                for j in range(8) for v in range(4)}
    assert len(mapped) == len(expected) == 2048 and mapped == expected
    return {"A_elements":len(seen_a),"B_elements":len(seen_b),
            "D_elements":len(seen_c),"per_warp_accumulator_bijection":len(mapped)}


def direct_dots(wq, yq):
    # [row, column, quant block, original eight-product subdot]
    return np.stack([np.einsum("rkb,jkb->rjk", wq[:,:,8*v:8*v+8].astype(np.int32),
                              yq[:,:,8*v:8*v+8].astype(np.int32))
                     for v in range(4)], axis=-1)


def masked_mma(wq, yq, k, h):
    # A expands each weight row into two rows, each keeping eight of 16 bytes.
    a = np.repeat(wq[:,k,16*h:16*h+16].astype(np.int32), 2, axis=0)
    a[np.arange(16)[:,None] % 2 != np.arange(16)[None,:] // 8] = 0
    b = yq[:,k,16*h:16*h+16].astype(np.int32).T
    d = a @ b
    return d[MMA_ROW, J]


def reference(dots, wd, yd, fused, nwarps=4, balanced_cross=False, reverse_xor=False):
    blocks = dots.shape[2]
    part = np.zeros((nwarps,32,8,8), dtype=np.float32)
    for w in range(nwarps):
        for lane in range(32):
            for k in range(8*w+lane//4, blocks, 8*nwarps):
                scale = wd[:,k,None] * yd[None,:,k]
                part[w,lane] = UPDATE(scale, dots[:,:,k,lane%4], part[w,lane], fused)
    if balanced_cross:
        assert nwarps == 4
        values = (part[0]+part[1])+(part[2]+part[3])
    else:
        values = part[0].copy()
        for w in range(1,nwarps):
            values = values + part[w]
    for off in ((1,2,4,8,16) if reverse_xor else (16,8,4,2,1)):
        values = values + values[np.arange(32)^off]
    # The frozen width-four kernel writes row i from logical lane i, i in {0,1}.
    return np.stack([values[r%2,r,:] for r in range(8)])


def candidate(wq, yq, wd, yd, fused, expected_dots):
    blocks = wq.shape[1]
    part = np.zeros((4,32,8,2,4), dtype=np.float32)
    checked = 0
    for s in range((blocks+31)//32):
        for w in range(4):
            for u in range(8):
                k = 32*s+8*w+u
                if k >= blocks:
                    continue  # A missing reference update must not become FMA(0,acc).
                for h in range(2):
                    ints = masked_mma(wq,yq,k,h)
                    assert np.array_equal(ints,expected_dots[R,J,k,2*h+VPRIME])
                    checked += ints.size
                    scale = wd[R,k] * yd[J,k]
                    part[w,:,u,h,:] = UPDATE(scale,ints,part[w,:,u,h,:],fused)
    a = part[0].copy()
    for w in range(1,4):
        a = a + part[w]
    # Reference XOR16,8,4 are register permutations on u; XOR2 permutes h.
    for off in (4,2,1):
        a = a + a[:,np.arange(8)^off,:,:]
    a = a + a[:,:,np.arange(2)^1,:]
    # Reference XOR1 (v'=0/1) changes the physical MMA lane by XOR4.
    a = a + a[np.arange(32)^4,:,:,:]
    out = np.empty((8,8),dtype=np.float32)
    for r in range(8):
        for j in range(8):
            p = 4*(2*(r%4)+(r%2))+j//2
            z = 2*(r//4)+j%2
            out[r,j] = a[p,0,0,z]
    return out, checked


class DAG:
    def __init__(self, fused):
        self.nodes = {}
        self.fused = fused
        self.zero = self.node("f32+0")
    def node(self,*parts):
        return self.nodes.setdefault(parts,len(self.nodes))
    def add(self,a,b):
        return self.node("add.rn.f32",a,b)
    def update(self,r,j,k,v,a):
        scale = self.node("mul.rn.f32",self.node("W_half_to_float",r,k),
                          self.node("Y_half_to_float",j,k))
        dot = self.node("exact_i32_to_f32",self.node("exact_dot8",r,j,k,v))
        if self.fused:
            return self.node("fma.rn.f32",scale,dot,a)
        return self.add(a,self.node("mul.rn.f32",scale,dot))


def symbolic(blocks,fused):
    d = DAG(fused)
    # [warp, original lane, row, column]
    ref = np.full((4,32,8,8),d.zero,dtype=np.int64)
    for w in range(4):
        for l in range(32):
            for r in range(8):
                for j in range(8):
                    for k in range(8*w+l//4,blocks,32):
                        ref[w,l,r,j] = d.update(r,j,k,l%4,int(ref[w,l,r,j]))
    cand = np.full((4,32,8,2,4),d.zero,dtype=np.int64)
    for s in range((blocks+31)//32):
        for w in range(4):
            for u in range(8):
                k = 32*s+8*w+u
                if k >= blocks: continue
                for p in range(32):
                    for h in range(2):
                        for z in range(4):
                            cand[w,p,u,h,z] = d.update(int(R[p,z]),int(J[p,z]),k,
                                2*h+int(VPRIME[p,z]),int(cand[w,p,u,h,z]))
    add = np.vectorize(lambda a,b:d.add(int(a),int(b)),otypes=[np.int64])
    ra,ca = ref[0],cand[0]
    for w in range(1,4):
        ra,ca = add(ra,ref[w]),add(ca,cand[w])
    for off in (16,8,4,2,1): ra = add(ra,ra[np.arange(32)^off])
    for off in (4,2,1): ca = add(ca,ca[:,np.arange(8)^off,:,:])
    ca = add(ca,ca[:,:,np.arange(2)^1,:])
    ca = add(ca,ca[np.arange(32)^4,:,:,:])
    for r in range(8):
        for j in range(8):
            p,z = 4*(2*(r%4)+r%2)+j//2,2*(r//4)+j%2
            assert ra[r%2,r,j] == ca[p,0,0,z]
    return {"blocks":blocks,"fused":bool(fused),"ordered_output_DAGs":64,
            "interned_nodes":len(d.nodes)}


def tail_plans():
    tests = 0
    for m in (1,2,7,8,9,16,17):
        for n in range(1,33):
            for k in (32,256,1024,4096,12288):
                coverage = np.zeros((m,n),np.int32)
                mf,nf = m//8*8,n//8*8
                for r in range(0,mf,8):
                    for j in range(0,nf,8): coverage[r:r+8,j:j+8] += 1
                # Columns and rows outside the fast rectangle use existing loop4.
                for j in range(nf,n,4): coverage[:mf,j:min(n,j+4)] += 1
                for j in range(0,n,4): coverage[mf:,j:min(n,j+4)] += 1
                assert np.all(coverage == 1)
                tests += 1
    return tests


def bits(x): return np.asarray(x,dtype=np.float32).view(np.uint32)


def main():
    global UPDATE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",type=pathlib.Path,default=HERE/"reproduced")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True,exist_ok=True)
    UPDATE = make_update(output_dir)
    result = {"status":"CPU_MODEL_ONLY_NOT_CUDA_COMPILED_NOT_GPU_RUN",
              "environment":{"python":platform.python_version(),"numpy":np.__version__,
                             "platform":platform.platform(),
                             "g++":subprocess.check_output(["g++","--version"],text=True).splitlines()[0]},
              "fragments":check_fragments(),"tail_plan_cases":tail_plans(),
              "symbolic":[],"numeric":[],"edge_cases":[],"negative_controls":{}}
    for blocks in (1,17,33,128,384):
        for fused in (0,1): result["symbolic"].append(symbolic(blocks,fused))
    total_ints,total_outputs = 0,0
    for blocks in (1,2,7,8,15,16,17,31,32,33,64,128,384):
        for seed in (0,1,2):
            rng = np.random.default_rng(20261104+seed+1000*blocks)
            wq = rng.integers(-128,128,(8,blocks,32),dtype=np.int16).astype(np.int8)
            yq = rng.integers(-128,128,(8,blocks,32),dtype=np.int16).astype(np.int8)
            # Half encodings cover signed finite normals and finite subnormals.
            wh = rng.integers(0,0x7c00,(8,blocks),dtype=np.uint16)
            wh |= rng.integers(0,2,(8,blocks),dtype=np.uint16)<<15
            yh = rng.integers(0,0x7c00,(8,blocks),dtype=np.uint16)
            wd,yd = wh.view(np.float16).astype(FP),yh.view(np.float16).astype(FP)
            dots = direct_dots(wq,yq)
            for fused in (0,1):
                ref = reference(dots,wd,yd,fused)
                got,count = candidate(wq,yq,wd,yd,fused,dots)
                assert np.array_equal(bits(ref),bits(got)),(blocks,seed,fused)
                total_ints += count
                total_outputs += ref.size
                if blocks == 128 and seed == 0:
                    for name,bad in (("two_reduction_warps",reference(dots,wd,yd,fused,2)),
                                     ("balanced_cross_warp",reference(dots,wd,yd,fused,4,True)),
                                     ("reverse_xor_order",reference(dots,wd,yd,fused,4,False,True)),
                                     ("changed_fma_contract",reference(dots,wd,yd,1-fused))):
                        different = np.argwhere(bits(ref)!=bits(bad))
                        assert len(different)>0,name
                        r,j = different[0]
                        result["negative_controls"][name+"_mode"+str(fused)] = {
                            "mismatching_outputs":len(different),"of":64,
                            "row":int(r),"column":int(j),
                            "reference_hex":hex(int(bits(ref)[r,j])),
                            "wrong_hex":hex(int(bits(bad)[r,j]))}
            result["numeric"].append({"K":blocks*32,"seed":seed,"modes":2,"outputs":128})
    for name, wvalue, yvalue, wh, yh in (
            ("maximum_integer_dot",-128,-128,0x3c00,0x3c00),
            ("signed_zero_scale",-128,127,0x8000,0x3c00),
            ("minimum_half_scales",-128,-128,0x0001,0x0001),
            ("maximum_finite_half_scales",-128,127,0x7bff,0x7bff),
            ("zero_quants_negative_scale",0,0,0xbc00,0x3c00)):
        blocks = 33
        wq = np.full((8,blocks,32),wvalue,dtype=np.int8)
        yq = np.full((8,blocks,32),yvalue,dtype=np.int8)
        wd = np.full((8,blocks),wh,dtype=np.uint16).view(np.float16).astype(FP)
        yd = np.full((8,blocks),yh,dtype=np.uint16).view(np.float16).astype(FP)
        dots = direct_dots(wq,yq)
        if name == "maximum_integer_dot": assert np.all(dots == 131072)
        for fused in (0,1):
            ref = reference(dots,wd,yd,fused)
            got,count = candidate(wq,yq,wd,yd,fused,dots)
            assert np.array_equal(bits(ref),bits(got)),name
            total_ints += count
            total_outputs += ref.size
        result["edge_cases"].append({"name":name,"outputs":128,"modes":2,"K":1056})
    # A counterexample to replacing four rounded dot8 leaves by one dot32 leaf.
    rng = np.random.default_rng(1701)
    for attempt in range(10000):
        w = rng.integers(-128,128,32,dtype=np.int16).astype(np.int32)
        y = rng.integers(-128,128,32,dtype=np.int16).astype(np.int32)
        wh = np.uint16(rng.integers(1,0x7c00))
        yh = np.uint16(rng.integers(1,0x7c00))
        scale = wh.view(np.float16).astype(FP)*yh.view(np.float16).astype(FP)
        ints = (w*y).reshape(4,8).sum(axis=1).astype(np.int32)
        a = scale*ints.astype(FP)
        ref = FP(FP(a[0]+a[2])+FP(a[1]+a[3]))
        bad = FP(scale*FP(ints.sum()))
        if bits(ref) != bits(bad):
            result["negative_controls"]["collapse_dot8_to_dot32"] = {
                "weight_q":w.tolist(),"activation_q":y.tolist(),
                "weight_half_hex":hex(int(wh)),"activation_half_hex":hex(int(yh)),
                "dot8":ints.tolist(),"reference_hex":hex(int(bits(ref))),
                "wrong_hex":hex(int(bits(bad))),"attempt":attempt}
            break
    else: raise AssertionError("negative control failed to distinguish dot32")
    # Even with the same fused/split choice, a compiler must retain scale-first grouping.
    a,b,i = FP(0.91748046875),FP(1.5615234375),FP(12209)
    scale_first,wrong_group = FP(FP(a*b)*i),FP(a*FP(b*i))
    assert bits(scale_first) != bits(wrong_group)
    result["negative_controls"]["reassociated_scales"] = {
        "weight_half_hex":"0x3b57","activation_half_hex":"0x3e3f","dot8":12209,
        "weight_q8":[127,17,0,0,0,0,0,0],"activation_q8":[96,1,0,0,0,0,0,0],
        "reference_hex":hex(int(bits(scale_first))),"wrong_hex":hex(int(bits(wrong_group)))}
    result["counts"] = {"numeric_exact_integer_comparisons":total_ints,
                        "numeric_output_bit_comparisons":total_outputs,
                        "symbolic_output_DAGs":sum(x["ordered_output_DAGs"] for x in result["symbolic"])}
    result["source_sha256"] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (HERE/"check_mapping.py",HERE/"fp_update.cpp")}
    (output_dir/"results.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("status","counts","tail_plan_cases","negative_controls")},indent=2))


if __name__ == "__main__": main()
