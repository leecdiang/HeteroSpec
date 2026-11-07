"""Opt-in Q8 projection policy: retain F32 activations in the batched Vulkan path."""
from pathlib import Path
import argparse,hashlib
from dispatch_observer import apply as observe

def apply(source,diagnostic=False):
    source=Path(source)
    p=source/'ggml/src/ggml-vulkan/ggml-vulkan.cpp';s=p.read_text(encoding='utf-8')
    begin=s.index('static void ggml_vk_mul_mat_vec_q_f16(');end=s.index('    vk_pipeline to_fp16_vk_0',begin)
    region=s[begin:end]
    anchor='    bool quantize_y = ctx->device->integer_dot_product && '
    assert region.count(anchor)==1
    region=region.replace(anchor,'''    // An explicit F32 Q8 projection contract preserves the original F32
    // activation operand. The existing NUM_COLS batched shader remains batched.
    const bool reference_q8 = src0->type == GGML_TYPE_Q8_0 &&
        src1->type == GGML_TYPE_F32 && dst->op_params[0] == GGML_PREC_F32;
    bool quantize_y = !reference_q8 && ctx->device->integer_dot_product && ''')
    p.write_text(s[:begin]+region+s[end:],encoding='utf-8',newline='\n')
    p=source/'src/llama-graph.cpp';s=p.read_text(encoding='utf-8');anchor='    ggml_tensor * res = ggml_mul_mat(ctx0, w, cur);'
    assert s.count(anchor)==1
    s=s.replace(anchor,anchor+'''
    if (hs_b570::reference_q8 && hs_b570::mode != 0 && w->type == GGML_TYPE_Q8_0) {
        ggml_mul_mat_set_prec(res, GGML_PREC_F32);
    }
''')
    p.write_text(s,encoding='utf-8',newline='\n')
    if diagnostic:observe(source)
    print('reference_q8 explicit contract; legacy layout and R remain independently selectable')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--diagnostic',action='store_true');a=p.parse_args();apply(a.source,a.diagnostic)
