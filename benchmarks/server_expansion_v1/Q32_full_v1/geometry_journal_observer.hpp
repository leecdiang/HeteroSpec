#pragma once
// Exact PREFILL descriptors stream to a versioned binary journal. The same
// fields are reconstructed and checked offline, outside the native900s window.
// No arithmetic, state/value capture, callback decision or GPU wait is changed.
#ifdef Q32_OFFLINE_OPERANDS
#include "operand_observer.hpp"
#else
static bool q32_operand_wanted(ggml_tensor*,const std::string&){return false;}
static void q32_operand_copy(ggml_tensor*){throw std::runtime_error("offline operand capture disabled");}
#endif
struct Observer {
    std::string phase="setup";int base=0,caller=0;bool bad=false;
    std::map<std::string,json> signatures;fs::path journal_path;std::ofstream journal;uint64_t journal_records=0;
    std::map<ggml_backend_dev_t,bool> gpu_devices;
    static ggml_backend_dev_t device(ggml_tensor*t){return t->buffer?ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer)):nullptr;}
    bool gpu(ggml_tensor*t){auto*d=device(t);if(!d)return false;auto it=gpu_devices.find(d);if(it==gpu_devices.end())it=gpu_devices.emplace(d,ggml_backend_dev_type(d)==GGML_BACKEND_DEVICE_TYPE_GPU).first;return it->second;}
    static json meta(ggml_tensor*t){auto*d=device(t);return {{"name",t->name},{"type",ggml_type_name(t->type)},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},{"device",d?ggml_backend_dev_description(d):"UNALLOCATED"}};}
    template<class T>static void field(std::string&out,const T&x){out.append(reinterpret_cast<const char*>(&x),sizeof(x));}
    static void text(std::string&out,const char*x){const uint32_t n=uint32_t(std::strlen(x));field(out,n);out.append(x,n);}
    static void tensor_key(std::string&out,ggml_tensor*t){text(out,t->name);field(out,t->type);out.append(reinterpret_cast<const char*>(t->ne),sizeof(t->ne));out.append(reinterpret_cast<const char*>(t->nb),sizeof(t->nb));auto*d=device(t);field(out,d);}
    static void tensor_record(std::string&out,ggml_tensor*t){
        text(out,t->name);text(out,ggml_type_name(t->type));for(int i=0;i<4;++i){int64_t n=t->ne[i];field(out,n);}for(int i=0;i<4;++i){uint64_t n=t->nb[i];field(out,n);}auto*d=device(t);text(out,d?ggml_backend_dev_description(d):"UNALLOCATED");
    }
    void record(ggml_tensor*t){
        if(!journal.is_open()){need(!journal_path.empty()&&!fs::exists(journal_path),"Fresh descriptor journal");fs::create_directories(journal_path.parent_path());journal.open(journal_path,std::ios::binary);need(bool(journal),"Open descriptor journal");journal.write("HSOPV1LE",8);uint32_t endian=1;need(*reinterpret_cast<unsigned char*>(&endian)==1,"Journal requires registered little-endian ABI");}
        std::string bytes;bytes.reserve(768);int32_t p=base,n=caller;field(bytes,p);field(bytes,n);text(bytes,ggml_op_name(t->op));tensor_record(bytes,t);uint32_t sources=0;for(int i=0;i<GGML_MAX_SRC;++i)if(t->src[i])++sources;field(bytes,sources);for(int i=0;i<GGML_MAX_SRC;++i)if(t->src[i])tensor_record(bytes,t->src[i]);
        const uint32_t count=uint32_t(bytes.size());journal.write(reinterpret_cast<const char*>(&count),4);journal.write(bytes.data(),bytes.size());need(bool(journal),"Write full descriptor journal");++journal_records;
    }
    json journal_meta(){
        if(!journal_records)return nullptr;
        if(journal.is_open()){journal.flush();need(bool(journal),"Flush descriptor journal");journal.close();int fd=::open(journal_path.c_str(),O_RDONLY);need(fd>=0,"Journal sync open");int rc=::fsync(fd);::close(fd);need(rc==0,"Journal sync");}
        return {{"schema","heterospec.actual-prefill-operators.v1"},{"path",journal_path.string()},{"records",journal_records},{"bytes",fs::file_size(journal_path)},{"sha256",hash_file(journal_path)},{"fields","base:i32,caller:i32,op:utf8,tensor,source_count:u32,sources; tensor=name,type,ne[4]:i64,nb[4]:u64,device:utf8; little endian"}};
    }
    static bool callback(ggml_tensor*t,bool ask,void*opaque){
        auto&o=*static_cast<Observer*>(opaque);if(!phase_observe)return false;
        if(!ask){if(q32_operand_wanted(t,o.phase)){q32_operand_copy(t);return false;}o.bad=true;return false;}
        if(o.phase!="VERIFY"&&o.phase!="PREFILL"&&o.phase!="ORDINARY")return false;
        const std::string name=t->name;if(name.rfind("kq",0)!=0&&name.rfind("hs_",0)!=0&&t->op!=GGML_OP_MUL_MAT)return false;
        // Device type is immutable for a device identity during this request.
        // Resolve the actual buffer device on every invocation; query its type
        // once per distinct device, avoiding repeated CUDA property ioctls.
        if(!o.gpu(t))o.bad=true;
        if(o.phase=="PREFILL"){o.record(t);return false;}
        std::string key;key.reserve(1024);text(key,o.phase.c_str());field(key,o.caller);field(key,t->op);tensor_key(key,t);for(int i=0;i<GGML_MAX_SRC;++i){const bool present=t->src[i]!=nullptr;field(key,present);if(present)tensor_key(key,t->src[i]);}
        auto it=o.signatures.find(key);if(it!=o.signatures.end()){it->second["observed_occurrences"]=it->second["observed_occurrences"].get<int>()+1;return q32_operand_wanted(t,o.phase);}
        auto j=meta(t);j["phase"]=o.phase;j["op"]=ggml_op_name(t->op);j["sources"]=json::array();for(int i=0;i<GGML_MAX_SRC;++i)if(t->src[i])j["sources"].push_back(meta(t->src[i]));j["caller_rows"]=o.caller;j["first_position"]=o.base;j["observed_occurrences"]=1;j["visible_keys_by_causal_row"]=json::array();for(int i=0;i<o.caller;++i)j["visible_keys_by_causal_row"].push_back(o.base+i+1);j["visible_keys_basis"]="First descriptor instance, complete physical positions/widths in executions; exact PREFILL descriptors in separately bound binary journal";o.signatures.emplace(std::move(key),std::move(j));return q32_operand_wanted(t,o.phase);
    }
};
