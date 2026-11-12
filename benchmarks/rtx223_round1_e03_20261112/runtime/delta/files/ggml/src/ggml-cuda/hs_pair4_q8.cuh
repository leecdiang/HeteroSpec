#pragma once

// Q8_0/F32 q=8, g=2 only. Included after the bound original MMVQ source prefix.
__launch_bounds__(128, 1)
static __global__ void hs_two_group_q8(
        const block_q8_0 * __restrict__ weight,
        const block_q8_1 * __restrict__ activation,
        float * __restrict__ output, int k, int m, int padded_k) {
    constexpr int groups = 2, cols = 4, rows = 2, warps = 4, lanes = 32;
    const int tid = lanes * threadIdx.y + threadIdx.x;
    const int row0 = rows * blockIdx.x;
    const int blocks = k / QK8_0;
    const int stride_y = padded_k / QK8_1;
    const int kqs = VDR_Q8_0_Q8_1_MMVQ * (tid % (QI8_0 / VDR_Q8_0_Q8_1_MMVQ));
    float tmp[groups][cols][rows] = {};

    // Each output keeps the case-4 lane/K partition and its accumulation order.
    for (int kbx = tid / (QI8_0 / VDR_Q8_0_Q8_1_MMVQ);
            kbx < blocks; kbx += VDR_Q8_0_Q8_1_MMVQ * warps * lanes / QI8_0) {
#pragma unroll
        for (int i = 0; i < rows; ++i) {
            const block_q8_0 & w = weight[(row0 + i) * blocks + kbx];
            int v[VDR_Q8_0_Q8_1_MMVQ];
#pragma unroll
            for (int z = 0; z < VDR_Q8_0_Q8_1_MMVQ; ++z) {
                v[z] = get_int_b2(w.qs, kqs + z);
            }
            const float dw = w.d;
#pragma unroll
            for (int group = 0; group < groups; ++group) {
#pragma unroll
                for (int j = 0; j < cols; ++j) {
                    const block_q8_1 & a = activation[(group * cols + j) * stride_y + kbx];
                    int u[VDR_Q8_0_Q8_1_MMVQ];
#pragma unroll
                    for (int z = 0; z < VDR_Q8_0_Q8_1_MMVQ; ++z) {
                        u[z] = get_int_b4(a.qs, kqs + z);
                    }
                    const float da = __low2half(a.ds);
                    tmp[group][j][i] += vec_dot_q8_0_q8_1_impl<float, VDR_Q8_0_Q8_1_MMVQ>(v, u, dw, da);
                }
            }
        }
    }
    __shared__ float partial[groups][warps - 1][cols][rows][lanes];
    if (threadIdx.y > 0) {
#pragma unroll
        for (int group = 0; group < groups; ++group) {
#pragma unroll
            for (int j = 0; j < cols; ++j) {
#pragma unroll
                for (int i = 0; i < rows; ++i) {
                    partial[group][threadIdx.y - 1][j][i][threadIdx.x] = tmp[group][j][i];
                }
            }
        }
    }
    __syncthreads();
    if (threadIdx.y > 0) {
        return;
    }
#pragma unroll
    for (int group = 0; group < groups; ++group) {
#pragma unroll
        for (int j = 0; j < cols; ++j) {
#pragma unroll
            for (int i = 0; i < rows; ++i) {
#pragma unroll
                for (int l = 0; l < warps - 1; ++l) {
                    tmp[group][j][i] += partial[group][l][j][i][threadIdx.x];
                }
                tmp[group][j][i] = warp_reduce_sum<lanes>(tmp[group][j][i]);
                if (threadIdx.x == i) {
                    output[(group * cols + j) * m + row0 + i] = tmp[group][j][i];
                }
            }
        }
    }
}
