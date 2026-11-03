"""Extend the scalar p021 dispatch across query rows without changing its reduction."""
from paths import *
def apply(src):
    vk=src/'ggml/src/ggml-vulkan';p=vk/'ggml-vulkan.cpp';s=p.read_text(encoding='utf-8')
    k='struct vk_mat_vec_p021_push_constants {';a=s.index(k);b=s.index('};',a)
    hdr=s[a:b]+'    uint32_t query_stride_b;\n    uint32_t query_stride_d;\n'
    s=s[:a]+hdr+s[b:]
    a=s.index('static void ggml_vk_mul_mat_vec_p021_f16_f32(')
    b=s.index('static bool hs_head_geometry',a);body=s[a:b]
    body=once(body,'0, 0, fusion_flags','0, 0, fusion_flags, uint32_t(src1->nb[3]/sizeof(float)), uint32_t(dst->nb[3]/sizeof(float))')
    body=once(body,'{ 1, (uint32_t)ne01, workgroups_z }','{ (uint32_t)src1->ne[3], (uint32_t)ne01, workgroups_z }')
    s=s[:a]+body+s[b:]
    # Retain the ordinary permuted scalar predicate. The extended case has
    # interleaved K and per-query Q stride with a full contiguous head block.
    key='        src1->ne[3] == 1 &&\n        src0->ne[1] <= ctx->device->properties.limits.maxComputeWorkGroupCount[1]'
    s=once(s,key,'''        (src1->ne[3] == 1 ||
         (src0->ne[0]==64 && hs_qb_operand(src0,src1,false) &&
          src1->nb[2]==sizeof(float)*src1->ne[0] &&
          src1->nb[3]==src1->nb[2]*src1->ne[2])) &&
        src0->ne[1] <= ctx->device->properties.limits.maxComputeWorkGroupCount[1]''')
    p.write_text(s,encoding='utf-8',newline='\n')
    p=vk/'vulkan-shaders/mul_mat_vec_p021.comp';s=p.read_text(encoding='utf-8')
    s=once(s,'    uint fusion_flags;','    uint fusion_flags;\n    uint query_stride_b;\n    uint query_stride_d;')
    s=once(s,'    const uint row_x =','    const uint query = gl_WorkGroupID.x;\n    const uint row_x =')
    assert s.count('const uint iy = ')==2
    s=s.replace('const uint iy = ','const uint iy = query*p.query_stride_b + ')
    s=once(s,'const uint idst = ','const uint idst = query*p.query_stride_d + ')
    p.write_text(s,encoding='utf-8',newline='\n')

