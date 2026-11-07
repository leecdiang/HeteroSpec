#pragma once
// Diagnostic frontend only; no extra drain, mutation or model invocation.
static bool economics_trim(llama_memory_t mem,llama_seq_id seq,llama_pos p0,llama_pos p1){
 static const bool trace=std::getenv("HS_ECON_MICROTRACE")!=nullptr;
 if(!trace)return llama_memory_seq_rm(mem,seq,p0,p1);
 const auto before=seq==0?llama_memory_seq_pos_max(mem,seq):-1;
 const auto result=llama_memory_seq_rm(mem,seq,p0,p1);
 const auto after=seq==0?llama_memory_seq_pos_max(mem,seq):-1;
 std::fprintf(stderr,"ECON_TRIM kv=%p seq=%d p0=%d p1=%d before_max=%d after_max=%d result=%d\n",(void*)mem,seq,p0,p1,before,after,int(result));
 return result;
}
