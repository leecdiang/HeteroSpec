#pragma once
#include "ggml.h"
#include "ggml-backend.h"
#include <array>
#include <string>
#include <tuple>
namespace hs_reference_batching {
struct TensorObservation {
    std::array<int64_t,4> shape{};
    std::array<size_t,4> strides{};
    int type=-1, device_type=-1;
    std::string buffer_type, device_name;
    bool allocated=false, host=false, contiguous=false, view=false;
    auto key() const {return std::tie(shape,strides,type,device_type,buffer_type,device_name,allocated,host,contiguous,view);}
    bool operator==(const TensorObservation & b) const {return key()==b.key();}
};
// Observe real scheduler-assigned buffers, not graph-build guesses. The
// returned names are descriptive, not globally unique device/binary identity.
inline TensorObservation observe_tensor(const ggml_tensor * tensor) {
    TensorObservation result;if(!tensor)return result;
    result.type=int(tensor->type);result.contiguous=ggml_is_contiguous(tensor);result.view=tensor->view_src!=nullptr;
    for(int i=0;i<4;++i){result.shape[i]=tensor->ne[i];result.strides[i]=tensor->nb[i];}
    auto buffer=tensor->buffer;
    if(!buffer && tensor->view_src)buffer=tensor->view_src->buffer;
    if(!buffer || !tensor->data)return result;
    auto type=ggml_backend_buffer_get_type(buffer);
    if(!type)return result;
    result.allocated=true;result.host=ggml_backend_buft_is_host(type);
    const auto * name=ggml_backend_buft_name(type);if(name)result.buffer_type=name;
    auto device=ggml_backend_buft_get_device(type);
    if(device){result.device_type=int(ggml_backend_dev_type(device));const auto * n=ggml_backend_dev_name(device);if(n)result.device_name=n;}
    return result;
}
// Names alone do not establish same physical device. Require exact runtime
// buffer-type object identity, supplied by the backend for its current device.
inline bool resident_on(const ggml_tensor * tensor,ggml_backend_buffer_type_t expected) {
    if(!tensor || !tensor->data || !expected || ggml_backend_buft_is_host(expected))return false;
    auto buffer=tensor->buffer;
    if(!buffer && tensor->view_src)buffer=tensor->view_src->buffer;
    return buffer && ggml_backend_buffer_get_type(buffer)==expected;
}
} // namespace hs_reference_batching
