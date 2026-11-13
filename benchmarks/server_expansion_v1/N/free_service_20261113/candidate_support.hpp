#pragma once
// Observer/accounting only. Arithmetic and planner come from frozen loop4 tree.
#include "hs_scope.h"
#include "hsc_counter.h"
using json=nlohmann::json;
static double since(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
inline bool phase_observe=false;
struct QualObserver {
 std::string phase="setup";int base=0,caller=0;bool bad=false;uint64_t gpu_nodes=0,loop4_nodes=0,projection_nodes=0;
 static bool callback(ggml_tensor*t,bool ask,void*p){auto&o=*static_cast<QualObserver*>(p);if(!phase_observe)return false;if(!ask){o.bad=true;return false;}std::string n=t->name;if(n.rfind("kq",0)&&n.rfind("hs_",0)&&t->op!=GGML_OP_MUL_MAT)return false;auto*d=t->buffer?ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer)):nullptr;if(!d||ggml_backend_dev_type(d)!=GGML_BACKEND_DEVICE_TYPE_GPU)o.bad=true;else++o.gpu_nodes;if(n.rfind("hs_backend_loop4_",0)==0)++o.loop4_nodes;if(n.rfind("tpds_projection_",0)==0)++o.projection_nodes;return false;}
};
static PJ physical_trace=PJ::array();
static int charged_decode(llama_context*c,llama_batch b){budget->rows(b.n_tokens);auto before=hsc::w.physical_rows;auto calls=hsc::w.physical_calls;int rc=::llama_decode(c,b);physical_trace.push_back({{"request",budget->active()},{"position",b.pos[0]},{"API_width",b.n_tokens},{"physical_rows",hsc::w.physical_rows-before},{"physical_calls",hsc::w.physical_calls-calls},{"returncode",rc}});need(rc!=0||(hsc::w.physical_rows-before==b.n_tokens&&hsc::w.physical_calls-calls==1),"actual physical width/accounting differs");return rc;}
#define llama_decode charged_decode
#include HS_LIVE_RESIDENT_HEADER
#undef llama_decode
struct QualOwner {llama_context*c=nullptr;llama_model*model=nullptr;bool capture=true;int calls=0;QualObserver obs;std::map<std::string,double>phases;PhaseContext plan;};
static QualOwner owner;
