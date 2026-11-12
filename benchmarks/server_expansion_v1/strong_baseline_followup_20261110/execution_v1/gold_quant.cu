// Glue only: the original quantizer and scalar dot objects remain untouched.
#include "quantize.cuh"
extern "C" size_t hs_gold_quantized_bytes(int64_t k) {
    return GGML_PAD(k,MATRIX_ROW_PADDING)/QK8_1*sizeof(block_q8_1);
}
extern "C" void hs_gold_quantize(const float* x,void* y,int64_t k,int type) {
    quantize_row_q8_1_cuda(x,nullptr,y,static_cast<ggml_type>(type),k,k,k,k,
                         GGML_PAD(k,MATRIX_ROW_PADDING),1,1,1,nullptr);
}
