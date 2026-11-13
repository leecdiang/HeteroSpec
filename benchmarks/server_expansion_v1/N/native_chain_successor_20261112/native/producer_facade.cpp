// Operational parser/render path extracted from the frozen #226 bridge.
// Compile/link only in this CPU preparation. This file has no main/model load.
#include "producer_facade.hpp"
#include "../budget_writer/sha256.hpp"
#include "chat.h"
#include "server-task.h"
#include "common.h"
#include "llama.h"
#include "json.h"
#include <algorithm>
#include <set>
#include <utility>
namespace hs::n1chain {
namespace {
using J=common_json;
void need(bool b,const std::string&s){if(!b)throw Blocked(s);}
std::string bytes_hex(const std::string&s){static const char*h="0123456789abcdef";std::string o;for(unsigned char c:s){o+=h[c>>4];o+=h[c&15];}return o;}
void basic(const J&messages){
 need(messages.is_array(),"messages array required");
 for(const auto&m:messages){
  need(m.is_object()&&m.contains("role")&&m.contains("content"),"basic message object");
  const auto role=m.at("role").get<std::string>();
  need(role=="system"||role=="user"||role=="assistant","unsupported message role");
  need(m.at("content").is_string(),"typed/media content unsupported");
  for(auto it=m.begin();it!=m.end();++it)need(it.key()=="role"||it.key()=="content"||it.key()=="reasoning_content","unsupported message field");
 }
}
common_chat_params render(const common_chat_templates*t,const J&messages){
 basic(messages);common_chat_templates_inputs p;
 p.messages=common_chat_msgs_parse_oaicompat(messages);p.use_jinja=true;p.enable_thinking=false;
 p.reasoning_format=COMMON_REASONING_FORMAT_DEEPSEEK;p.add_generation_prompt=true;
 p.continue_final_message=COMMON_CHAT_CONTINUATION_NONE;p.parallel_tool_calls=false;p.force_pure_content=false;
 return common_chat_templates_apply(t,p);
}
J params(const common_chat_params&p){return{{"format",int(p.format)},{"format_name",common_chat_format_name(p.format)},
 {"generation_prompt",p.generation_prompt},{"generation_prompt_hex",bytes_hex(p.generation_prompt)},
 {"additional_stops",p.additional_stops},{"preserved_tokens",p.preserved_tokens},
 {"supports_thinking",p.supports_thinking},{"parser_serialized",p.parser},
 {"profile",{{"use_jinja",true},{"enable_thinking",false},{"reasoning_format","deepseek"},
 {"stream",false},{"explicit_stop_strings",J::array()},{"tools",J::array()},
 {"add_generation_prompt",true},{"parse_special",true},{"add_special",false}}}};}
}
struct NativeProducer::Impl {
 llama_model* model;const llama_vocab*vocab=nullptr;ProductionGate&gate;BudgetHooks&account;
 decltype(common_chat_templates_init(static_cast<llama_model*>(nullptr),"")) templates;
 J history=J::array();common_chat_params current;
 std::string last_request;bool started=false,poisoned=false;
 Impl(llama_model*m,ProductionGate&g,BudgetHooks&a):model(m),gate(g),account(a){
  // Concrete gate was checked before this object and before all model access.
  need(model!=nullptr,"existing model is required; facade cannot create one");
  vocab=llama_model_get_vocab(model);need(vocab&&llama_vocab_n_tokens(vocab)==151936,"exact model vocabulary required");
  const char*raw=llama_model_chat_template(model,nullptr);need(raw!=nullptr,"actual GGUF template absent");const std::string text(raw);
  need(text.size()==4100&&Sha256::of(text)=="57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361","exact frozen GGUF template mismatch");
  std::vector<int32_t>eog;for(int32_t i=0;i<151936;i++)if(llama_vocab_is_eog(vocab,i))eog.push_back(i);
  need(eog==std::vector<int32_t>({128247,151643,151645,151662,151663,151664}),"frozen six-token EOG predicate mismatch");
  templates=common_chat_templates_init(model,"");need(bool(templates),"actual template initialization failed");
 }
 void enter(const std::string&request,const std::string&action){
  need(!poisoned,"producer poisoned; no retry");
  gate.before_mutation(request,action);account.before_mutation(request,action);
 }
 void fail()noexcept{poisoned=true;account.poison("producer contract/parser/render failure");}
 ProducerPrompt prompt(){
  need(current.prompt.size()<=2*1024*1024,"canonical prompt byte envelope exceeded; do not truncate");
  ProducerPrompt out;out.prompt_utf8=current.prompt;out.canonical_ids=common_tokenize(vocab,current.prompt,false,true);
  out.history_json=safe_json_to_str(history);need(out.history_json.size()<=2*1024*1024,"history byte envelope exceeded; do not rewrite");out.runtime_parser_state_json=safe_json_to_str(params(current));
  need(!out.canonical_ids.empty(),"empty actual canonical prompt");return out;
 }
};
NativeProducer::NativeProducer(llama_model*model,ProductionGate&gate,BudgetHooks&account){
 // This is a pure frontend over the existing factory-owned model. There is no
 // second model reservation/load, context allocation or backend initialization.
 // The final concrete gate ALWAYS rejects here in the current CPU-only build.
 gate.before_mutation("producer-existing-model","producer_constructor_metadata_access");
 try{impl_=std::make_unique<Impl>(model,gate,account);}catch(...){account.poison("producer constructor identity failure");throw;}
}
NativeProducer::~NativeProducer()=default;
ProducerPrompt NativeProducer::initial(const std::string&messages_json,const std::string&request){
 auto&p=*impl_;
 try{p.enter(request,"producer_initial");need(!p.started,"producer already has a conversation");
  auto messages=J::parse(messages_json);basic(messages);need(!messages.empty()&&messages.back().at("role")=="user","initial next input must end in a user message");
  p.history=std::move(messages);p.current=render(p.templates.get(),p.history);p.last_request=request;p.started=true;return p.prompt();
 }catch(...){p.fail();throw;}
}
ProducerPrompt NativeProducer::advance(const std::vector<int32_t>&emitted,const std::string&stop,std::size_t cap,const std::string&next_user_json,const std::string&request){
 auto&p=*impl_;
 try{p.enter(request,"producer_advance");need(p.started&&request!=p.last_request,"producer advance requires a new already-reserved request");
  need(cap>0&&cap<=128&&!emitted.empty()&&emitted.size()<=cap,"terminal token count/cap");
  for(auto id:emitted)need(id>=0&&id<151936,"generated token outside vocabulary");
  for(std::size_t i=0;i+1<emitted.size();i++)need(!llama_vocab_is_eog(p.vocab,emitted[i]),"tokens after earlier EOG");
  const bool terminal_eog=llama_vocab_is_eog(p.vocab,emitted.back());
  need((stop=="EOG"&&terminal_eog)||(stop=="CAP"&&!terminal_eog&&emitted.size()==cap),"terminal/cap/EOG incompatible");
  std::set<int32_t>preserved;for(const auto&s:p.current.preserved_tokens){auto xs=common_tokenize(p.vocab,s,false,true);if(xs.size()==1)preserved.insert(xs[0]);}
  std::string text;
  for(auto id:emitted){const auto piece=common_token_to_piece(p.vocab,id,preserved.count(id)!=0);
   need(!llama_vocab_is_eog(p.vocab,id)||piece.empty(),"BLOCKED_VISIBLE_EOG: actual server stop filtering route not admitted");text+=piece;}
  for(const auto&s:p.current.additional_stops)need(s.empty()||text.find(s)==std::string::npos,"BLOCKED_ACTIVE_STOP_STRING: full actual server text-stop route required");
  common_chat_parser_params parser(p.current);parser.reasoning_format=COMMON_REASONING_FORMAT_DEEPSEEK;
  parser.reasoning_in_content=false;parser.parse_tool_calls=true;parser.is_continuation=false;parser.echo=false;
  if(!p.current.parser.empty())parser.parser.load(p.current.parser);
  task_result_state server_state(parser);server_task_result_cmpl_final server_final;
  server_final.content=text;server_final.stream=false;server_final.res_type=TASK_RESPONSE_TYPE_OAI_CHAT;
  server_final.stop=stop=="EOG"?STOP_TYPE_EOS:STOP_TYPE_LIMIT;server_final.n_decoded=emitted.size();server_final.update(server_state);
  const auto parsed=server_state.chat_msg;need(parsed.tool_calls.empty()&&!parsed.contains_media(),"BLOCKED_TOOL_MEDIA_ROUTE");
  const auto wire=safe_json_to_str(server_final.to_json_oaicompat_chat());
  const auto client=J::parse(wire).at("choices").at(0).at("message");
  J assistant={{"role","assistant"},{"content",client.value("content",std::string())}};
  const auto reasoning=client.value("reasoning_content",std::string());if(!reasoning.empty())assistant["reasoning_content"]=reasoning;
  auto next_user=J::parse(next_user_json);basic(J::array({next_user}));need(next_user.at("role")=="user","next message must be an actual user message");
  p.history.push_back(assistant);p.history.push_back(next_user);p.current=render(p.templates.get(),p.history);p.last_request=request;
  auto out=p.prompt();out.wire_response_json=wire;out.parser_input_hex=bytes_hex(text);return out;
 }catch(...){p.fail();throw;}
}
}
