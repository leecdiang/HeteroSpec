// Preparation-only allocator exercise. Never serialize this uncomputed KV state
// or use this context for inference. It is reset before and after every probe.
#include "llama-context.h"
#include "llama-kv-cache.h"
extern "C" LLAMA_API int hs_prefix_allocator_census(llama_context *ctx,uint32_t count,uint32_t *head,uint32_t *padding){
 auto *kv=dynamic_cast<llama_kv_cache *>(llama_get_memory(ctx));
 if(!kv || count>=kv->get_size() || kv->get_n_stream()!=1)return -1;
 kv->clear(false);
 llama_pos pos=0;llama_seq_id seq=0,*seqs=&seq;int32_t nseq=1,idx=0;int8_t output=0;
 llama_ubatch b{};b.b_equal_seqs=1;b.n_tokens=b.n_seq_tokens=b.n_seqs=b.n_seqs_unq=b.n_pos=1;
 b.pos=&pos;b.n_seq_id=&nseq;b.seq_id=&seqs;b.seq_id_unq=&seq;b.seq_idx=&idx;b.output=&output;
 for(uint32_t i=0;i<count;++i){pos=i;auto slot=kv->find_slot(b,true);if(slot.empty()||!slot.is_contiguous()||slot.head()!=i){kv->clear(false);return -2;}kv->apply_ubatch(slot,b);}
 uint32_t groups[32];int n=kv->hs_next_groups(1,groups,head);
 pos=count;auto next=kv->find_slot(b,true);if(next.empty()||next.head()!=*head){kv->clear(false);return -3;}
 *padding=kv->get_n_kv(next); // scalar requirement, first probe reports effective padding
 kv->clear(false);return n==1?0:-4;
}
