#pragma once
#include "../budget_writer/hooks.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <string>
#include <vector>
struct llama_context;
namespace hs::n1chain {
struct KVCellMap{std::uint32_t physical;std::int32_t position;std::int32_t sequence;};
struct KVTensorMeta{std::string kind;int layer=0;std::string tensor_name,storage_name;std::array<std::int64_t,4> dimensions{};std::array<std::uint64_t,4> byte_strides{};std::uint64_t physical_read_bytes=0,canonical_active_bytes=0,native_tensor_callbacks=0;};
struct KVMeta{std::string format="active-kv-canonical-f16le-v1";std::uint32_t head=0,capacity=4096,kv_heads=8,head_dimension=128,layers=36,n_streams=1;bool empty=false,serialized_v_trans_present=false,v_trans=true,cell_ext=false;bool opaque_sequence_prefix_included=false;std::vector<std::uint32_t>physical_by_position;std::vector<KVCellMap>cells_physical_order;std::vector<KVTensorMeta>tensors;std::uint64_t scalar_metadata_bytes=0,serialized_memory_bytes=0,physical_read_bytes=0,canonical_active_bytes=0,native_tensor_callbacks=0;};
// One callback per actual K/V layer, exact F16LE bits in [8,head,128] order.
// Empty head returns metadata only. Sink must consume bytes before returning.
using KVSink=std::function<void(const std::string&,int,const std::uint8_t*,std::size_t)>;
// This is native-linked preparation only. Its concrete ProductionGate denies
// entry in this build before synchronize, tensor access, or any hardware API.
KVMeta capture_active_kv(llama_context*,ProductionGate&,BudgetHooks&,const std::string&request,std::uint32_t expected_head,const KVSink&);
}
