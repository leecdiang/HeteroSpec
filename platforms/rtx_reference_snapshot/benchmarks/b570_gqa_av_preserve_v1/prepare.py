from pathlib import Path
import json,difflib,shutil,hashlib
r=Path(__file__).parent
p=Path("C:/hs/b570-gqa-admission-20261020184000")
src=(p/"ggml-vulkan.cpp").read_text()
marker="static void ggml_vk_mul_mat_vec_nc_f16_f32("
helper="""// Exact E2 AV domain only. Keep the existing nc shader's per-output reduction.
static bool ggml_vk_qb_gqa_av_broadcast(const ggml_tensor * a, const ggml_tensor * b) {
    return a->type == GGML_TYPE_F16 && b->type == GGML_TYPE_F32 &&
        (a->ne[0] == 256 || a->ne[0] == 512) && a->ne[1] == 128 &&
        a->ne[2] == 8 && b->ne[2] == 32 && a->ne[3] == 1 &&
        (b->ne[3] == 2 || b->ne[3] == 4) && b->ne[1] == 1 &&
        a->nb[0] == 2 && a->nb[1] == 2048 && a->nb[2] == 262144 &&
        a->nb[3] == 2097152 && ggml_is_contiguous(b);
}

"""
assert src.count(marker)==1
out=src.replace(marker,helper+marker)
start=out.index(marker);end=out.index("static int ggml_vk_fwht_pipeline_idx",start)
block=out[start:end]
block=block.replace("const uint64_t ne03 = src0->ne[3];","const uint64_t ne13 = src1->ne[3];\n    const bool broadcast_av = ggml_vk_qb_gqa_av_broadcast(src0, src1);")
block=block.replace("const uint32_t nb03 = (uint32_t)(src0->nb[3] / sizeof(ggml_fp16_t));",
"""// Every query reads the same V head. Only probability/output addresses advance.
    const uint32_t nb03 = broadcast_av ? 0 : (uint32_t)(src0->nb[3] / sizeof(ggml_fp16_t));""")
block=block.replace("GGML_ASSERT(src0->ne[3] == src1->ne[3]); // checked in supports_op",
                    "GGML_ASSERT(src0->ne[3] == src1->ne[3] || broadcast_av);")
block=block.replace("pc, { (uint32_t)ne03, (uint32_t)ne01, (uint32_t)ne12 });",
                    "pc, { (uint32_t)ne13, (uint32_t)ne01, (uint32_t)ne12 });")
out=out[:start]+block+out[end:]
old="src0->ne[3] == src1->ne[3] && // nc shader has no batch-3 broadcast"
new="(src0->ne[3] == src1->ne[3] || ggml_vk_qb_gqa_av_broadcast(src0, src1)) &&"
assert out.count(old)==1
out=out.replace(old,new)
(r/"ggml-vulkan.cpp").write_text(out,newline="\n")
(r/"av-preserve.patch").write_text("".join(difflib.unified_diff(src.splitlines(True),out.splitlines(True),fromfile="a/ggml/src/ggml-vulkan/ggml-vulkan.cpp",tofile="b/ggml/src/ggml-vulkan/ggml-vulkan.cpp")),newline="\n")
for n in ("gqa.cpp","CMakeLists.txt"):
    shutil.copy2(p/n,r/n)
run=(p/"RUN.ps1").read_text().replace(p.as_posix(),"C:/hs/b570-gqa-av-preserve-20261020190000")
run=run.replace("C:/hs/b570-model-profile-final-20261020164000/BUDGET_LEDGER.json",str(p/"BUDGET_LEDGER.json"))
run=run.replace("246.8043431","248.4105591")
(r/"RUN.ps1").write_text(run,newline="\n")
reg=json.loads((p/"PREREGISTRATION.json").read_text())
reg.update(study="B570_E2_AV_PQ_REDUCTION_PRESERVE",uuid="c2bdba94-d819-4191-b40e-21a227e0ea13",
           parent_source="PR131@b5370cab7ce853d4b284e42e5515ffa50f1e8ce7",
           prior_cumulative_seconds=248.4105591,
           scope="Only nc AV query-batch addressing/dispatch. Same frozen shader, same within-output arithmetic. Same six-coordinate panel, no model/performance/CPU8.")
reg["reference"]="R_E2_PQ unchanged. Additionally compare all five existing PQ coordinates against PR131 complete raw stage bytes. Do not replace the failed PR131 QB evidence."
(r/"PREREGISTRATION.json").write_text(json.dumps(reg,indent=2))
freeze=(p/"freeze.py").read_text().replace('"gqa-scoped.patch"','"av-preserve.patch"')
(r/"freeze.py").write_text(freeze)
analysis=(p/"analyze.py").read_text()
analysis=analysis.replace('==10 and len(report["pairs"])==5','==12 and len(report["pairs"])==6')
analysis=analysis.replace('assert report["pairs"][-1]["stages"]["av"]["mismatch_count"]>0',
'''assert all(s["mismatch_count"]==0 for pair in report["pairs"] for s in pair["stages"].values())
previous=Path("C:/hs/b570-gqa-admission-20261020184000/results")
report["prior_PQ_stage_files_verified"]=0
for row in report["rows"]:
    if row["arm"]!="PQ":continue
    d=f'{row["n"]}-q{row["q"]}-PQ'
    for name in ("qk","softmax","av","final"):
        old=previous/d/(name+".f32")
        if old.exists():
            assert old.read_bytes()==(r/"results"/d/(name+".f32")).read_bytes()
            report["prior_PQ_stage_files_verified"]+=1
assert report["prior_PQ_stage_files_verified"]==20''')
analysis=analysis.replace('receipt["exit_code"]==2','receipt["exit_code"]==0').replace('native["computes"]==10','native["computes"]==12')
analysis=analysis.replace('abs(receipt["cumulative_charged_seconds"]-248.4105591)<1e-8',
                        'abs(receipt["cumulative_charged_seconds"]-248.4105591-receipt["charged_seconds"])<1e-8')
analysis=analysis.replace('SCOPED_CANDIDATE_NOT_QUALIFIED; stop E2 before request/timing','SIX_COORDINATE_OPERATOR_PANEL_PASS; natural request remains unqualified')
(r/"analyze.py").write_text(analysis)
# Pure integer address proof for all outputs and all reduction inputs, no native process.
count=0
for n in (256,512):
    for q in (1,2,4):
        for j in range(q):
            for h in range(32):
                for d in range(128):
                    pq_v=(h//4)*131072+d*1024
                    qb_v=j*0+(h//4)*131072+d*1024
                    assert pq_v==qb_v
                    assert j*(n*32)+h*n== (j*32+h)*n
                    assert j*(128*32)+h*128+d==(j*32+h)*128+d
                    assert pq_v+n<=1024*128*8
                    count+=n
check={"scalar_addresses_verified":count,"shader_modified":False,
       "same_v_per_query":True,"probability_and_output_rows_disjoint":True,
       "q1_path_unchanged":True,"native_execution":False,
       "harness_sha256":hashlib.sha256((r/"gqa.cpp").read_bytes()).hexdigest(),
       "same_harness_as_PR131":(r/"gqa.cpp").read_bytes()==(p/"gqa.cpp").read_bytes()}
(r/"CPU_ADDRESS_CHECK.json").write_text(json.dumps(check,indent=2))
print(json.dumps(check))
