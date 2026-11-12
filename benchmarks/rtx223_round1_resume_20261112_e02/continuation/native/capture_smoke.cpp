#include "capture_operand.hpp"
// Compile-only. It instantiates no model, backend or CUDA context.
int main() {
    hs_q8_capture::Capture capture;
    return capture.armed ? 1 : 0;
}
