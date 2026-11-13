#include "active_kv.hpp"
#include "active_kv_host.hpp"
#include "llama.h"
#include "llama-io.h"
#include "llama-memory.h"
#include "llama-kv-cache.h"
#include "ggml.h"
#include "ggml-backend.h"
#include <algorithm>
#include <limits>
#include <memory>
#include <set>
#include <utility>
namespace hs::n1chain {
namespace {
constexpr std::uint32_t capacity=4096,heads=8,dimension=128,layers=36,width=heads*dimension;
constexpr std::size_t physical_layer_bytes=std::size_t(capacity)*width*2;
constexpr std::size_t metadata_limit=1024*1024;
static_assert(sizeof(llama_pos)==4&&sizeof(llama_seq_id)==4,"bound native sequence metadata ABI");
static_assert(physical_layer_bytes==8*1024*1024,"bounded Qwen3 F16 physical layer");
void need(bool x,const std::string&s){if(!x)throw Blocked("ACTIVE_KV_UNSUPPORTED: "+s);}
void checkpoint(ProductionGate&gate,BudgetHooks&account,const std::string&r,const std::string&action){gate.before_mutation(r,action);account.before_mutation(r,action);}
const ggml_tensor * storage_root(const ggml_tensor*t){std::vector<const ggml_tensor*>seen;std::size_t offset=0;while(t&&t->view_src){need(seen.size()<8&&std::find(seen.begin(),seen.end(),t)==seen.end(),"tensor view cycle/depth");seen.push_back(t);need(offset<=std::numeric_limits<std::size_t>::max()-t->view_offs,"view offset overflow");offset+=t->view_offs;t=t->view_src;}need(t&&offset==0,"one-stream zero-offset storage view required");return t;}
class ActiveIO final:public llama_io_write_i {
 KVMeta&meta_;ProductionGate&gate_;BudgetHooks&account_;const std::string&request_;const KVSink&sink_;const std::vector<ggml_tensor*>&keys_;std::vector<const ggml_tensor*>value_roots_;std::vector<hostkv::Range>ranges_;std::vector<std::int32_t>positions_;std::vector<std::uint8_t>scalars_;hostkv::Cursor cursor_{scalars_};std::size_t bytes_=0;bool header_=false,layer_started_=false,done_=false;int kind_=0;std::uint32_t layer_=0,column_=0;std::size_t range_=0,current_meta_=0;ggml_tensor*current_view_=nullptr;
 void parse_header(){if(header_)return;try{hostkv::validate_state_header(cursor_,positions_,layers);}catch(const std::runtime_error&e){throw Blocked(std::string("ACTIVE_KV_NATIVE_HEADER: ")+e.what());}header_=true;meta_.serialized_v_trans_present=!positions_.empty();if(positions_.empty())done_=true;}
 void parse_layer(){try{need(cursor_.i32()==static_cast<std::int32_t>(GGML_TYPE_F16),"serialized non-F16 KV type");if(kind_==0)need(cursor_.u64()==std::uint64_t(width)*2,"serialized K row size");else{need(cursor_.u32()==2,"serialized V element size");need(cursor_.u32()==width,"serialized V GQA embedding width");}}catch(const Blocked&){throw;}catch(const std::runtime_error&e){throw Blocked(std::string("ACTIVE_KV_LAYER_HEADER: ")+e.what());}}
 void begin_layer(ggml_tensor*t){parse_layer();need(t&&t->type==GGML_TYPE_F16,"actual tensor type");need(t->ne[0]==width&&t->ne[1]==capacity&&t->ne[2]==1&&t->ne[3]==1,"actual storage tensor dimensions");need(t->nb[0]==2&&t->nb[1]==width*2&&t->nb[2]==physical_layer_bytes&&t->nb[3]==physical_layer_bytes,"actual storage tensor strides");need(ggml_nbytes(t)==physical_layer_bytes&&t->data,"actual tensor allocation/byte count");const auto*buffer_owner=t->view_src?t->view_src:t;need(buffer_owner->buffer,"actual view/source backend buffer");const auto*root=storage_root(t);
  if(kind_==0)need(root==storage_root(keys_.at(layer_)),"K callback layer/storage identity");else{for(auto*k:keys_)need(root!=storage_root(k),"V storage aliases a K layer");need(std::find(value_roots_.begin(),value_roots_.end(),root)==value_roots_.end(),"shared V storage unsupported");value_roots_.push_back(root);}
  KVTensorMeta tensor;tensor.kind=kind_==0?"K":"V";tensor.layer=int(layer_);tensor.tensor_name=ggml_get_name(t);tensor.storage_name=ggml_get_name(root);for(int i=0;i<4;++i){tensor.dimensions[i]=t->ne[i];tensor.byte_strides[i]=t->nb[i];}tensor.physical_read_bytes=physical_layer_bytes;tensor.canonical_active_bytes=std::uint64_t(meta_.head)*width*2;meta_.tensors.push_back(std::move(tensor));current_meta_=meta_.tensors.size()-1;current_view_=t;layer_started_=true;
  // Exactly one bounded physical read for each actual K/V tensor. Only active,
  // logically ordered bytes are emitted; inactive physical bytes never reach Sink.
  std::vector<std::uint8_t>physical(physical_layer_bytes);checkpoint(gate_,account_,request_,"active_kv.captureREAD");ggml_backend_tensor_get(t,physical.data(),0,physical.size());meta_.physical_read_bytes+=physical.size();auto canonical=hostkv::canonical_f16(physical,{capacity,heads,dimension,kind_==1},meta_.physical_by_position);need(canonical.size()==tensor.canonical_active_bytes,"canonical active byte count");sink_(kind_==0?"K":"V",int(layer_),canonical.data(),canonical.size());meta_.canonical_active_bytes+=canonical.size();
 }
 void advance(){range_=0;column_=0;layer_started_=false;current_view_=nullptr;if(++layer_==layers){layer_=0;if(kind_==0)kind_=1;else done_=true;}}
 public:
 ActiveIO(KVMeta&m,ProductionGate&g,BudgetHooks&a,const std::string&r,const KVSink&s,const std::vector<ggml_tensor*>&keys):meta_(m),gate_(g),account_(a),request_(r),sink_(s),keys_(keys){std::vector<std::uint32_t>physical;for(const auto&c:m.cells_physical_order){physical.push_back(c.physical);positions_.push_back(c.position);}ranges_=hostkv::ranges_from_physical(physical);}
 void write(const void*source,std::size_t count)override{need(count<=metadata_limit-scalars_.size(),"scalar metadata exceeds1MiB");need(count==0||source,"null scalar metadata");const auto*p=static_cast<const std::uint8_t*>(source);if(count)scalars_.insert(scalars_.end(),p,p+count);need(bytes_<=std::numeric_limits<std::size_t>::max()-count,"serialized byte overflow");bytes_+=count;}
 void write_tensor(ggml_tensor*t,std::size_t offset,std::size_t count)override{parse_header();need(!done_&&!ranges_.empty(),"unexpected native tensor payload");const auto&r=ranges_.at(range_);const auto expected_offset=kind_==0?std::size_t(r.first)*width*2:(std::size_t(r.first)+std::size_t(column_)*capacity)*2;const auto expected_count=std::size_t(r.last-r.first)*(kind_==0?width*2:2);need(offset==expected_offset&&count==expected_count&&offset<=physical_layer_bytes&&count<=physical_layer_bytes-offset,"native tensor slice/layout mismatch");if(!layer_started_)begin_layer(t);need(t==current_view_,"native tensor identity changes inside layer");need(bytes_<=std::numeric_limits<std::size_t>::max()-count,"serialized tensor byte overflow");bytes_+=count;++meta_.native_tensor_callbacks;++meta_.tensors.at(current_meta_).native_tensor_callbacks;if(++range_==ranges_.size()){range_=0;if(kind_==0||++column_==width)advance();}}
 std::size_t n_bytes()override{return bytes_;}
 void finish(){parse_header();need(done_&&cursor_.offset==scalars_.size(),"incomplete native scalar/tensor stream");need(meta_.tensors.size()==(meta_.empty?0:layers*2),"captured K/V layer count");const auto expected_payload=std::uint64_t(meta_.head)*width*2*layers*2;need(meta_.canonical_active_bytes==expected_payload,"canonical full-active payload total");need(bytes_==scalars_.size()+expected_payload,"native serialized byte total");need(meta_.physical_read_bytes==(meta_.empty?0:std::uint64_t(physical_layer_bytes)*layers*2),"physical tensor read accounting");meta_.scalar_metadata_bytes=scalars_.size();meta_.serialized_memory_bytes=bytes_;}
};
}
KVMeta capture_active_kv(llama_context*ctx,ProductionGate&gate,BudgetHooks&account,const std::string&request,std::uint32_t expected_head,const KVSink&sink){
 // Permanent concrete deny precedes context inspection and every hardware API.
 checkpoint(gate,account,request,"active_kv.entry");
 try{need(ctx&&bool(sink)&&!request.empty(),"capture arguments");need(expected_head<=capacity,"head exceeds C4096");std::uint16_t endian=1;need(*reinterpret_cast<const std::uint8_t*>(&endian)==1,"F16LE requires little-endian host");checkpoint(gate,account,request,"active_kv.synchronizeREAD");llama_synchronize(ctx);need(llama_n_ctx(ctx)==capacity&&llama_n_seq_max(ctx)==1,"context must be C4096/one sequence");auto*cache=dynamic_cast<llama_kv_cache*>(llama_get_memory(ctx));need(cache,"non-dense cache");need(cache->get_size()==capacity&&cache->get_n_stream()==1,"cache capacity/stream profile");need(cache->type_k()==GGML_TYPE_F16&&cache->type_v()==GGML_TYPE_F16,"non-F16 cache");need(!cache->has_cell_ext(),"extended cell metadata unsupported");auto layer_ids=cache->get_layer_ids();need(layer_ids.size()==layers,"cache layer count");std::vector<ggml_tensor*>keys;std::set<const ggml_tensor*>key_roots;for(std::uint32_t i=0;i<layers;++i){need(layer_ids[i]==i,"cache layers must be0..35");auto*k=cache->get_k_storage(i);need(k,"missing K storage");need(key_roots.insert(storage_root(k)).second,"shared K storage unsupported");keys.push_back(k);}
  KVMeta meta;meta.head=expected_head;meta.empty=expected_head==0;const auto&cells=cache->get_cells(0);need(cells.size()==capacity&&cells.get_used()==expected_head,"active cell count");meta.physical_by_position.assign(expected_head,std::numeric_limits<std::uint32_t>::max());for(std::uint32_t physical=0;physical<cells.size();++physical){if(cells.is_empty(physical))continue;need(cells.seq_count(physical)==1&&cells.seq_has(physical,0),"cell must belong only to sequence0");const auto pos=cells.pos_get(physical);need(pos>=0&&std::uint32_t(pos)<expected_head,"active position outside declared head");need(meta.physical_by_position[pos]==std::numeric_limits<std::uint32_t>::max(),"duplicate active logical position");meta.physical_by_position[pos]=physical;meta.cells_physical_order.push_back({physical,pos,0});}for(auto physical:meta.physical_by_position)need(physical!=std::numeric_limits<std::uint32_t>::max(),"missing active logical position");need(cache->seq_pos_min(0)==(expected_head?0:-1)&&cache->seq_pos_max(0)==(expected_head?std::int32_t(expected_head)-1:-1),"active sequence frontier bounds");
  ActiveIO io(meta,gate,account,request,sink,keys);cache->state_write(io,0,0);io.finish();return meta;
 }catch(...){gate.poison("active_kv capture failed");account.poison("active_kv capture failed");throw;}
}
}
