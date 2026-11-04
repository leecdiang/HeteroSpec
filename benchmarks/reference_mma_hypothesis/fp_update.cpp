#include <cmath>
#include <cstddef>
#include <cstdint>

// Host-only IEEE arithmetic helper. This is not CUDA or a GPU oracle.
extern "C" void fp_update(float * out, const float * scale, const int32_t * dot,
                          const float * acc, size_t count, int fused) {
    for (size_t i = 0; i < count; ++i) {
        const float value = static_cast<float>(dot[i]);
        if (fused) {
            out[i] = std::fma(scale[i], value, acc[i]);
        } else {
            const float product = scale[i] * value;
            out[i] = acc[i] + product;
        }
    }
}
