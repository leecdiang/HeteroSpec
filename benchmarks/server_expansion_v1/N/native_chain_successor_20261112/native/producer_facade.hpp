#pragma once
// Existing-model producer facade. Header is std-only; no model factory exists.
#include "../budget_writer/hooks.hpp"
#include <cstdint>
#include <memory>
#include <string>
#include <vector>
struct llama_model;
namespace hs::n1chain {
struct ProducerPrompt {
 std::vector<int32_t> canonical_ids;
 std::string prompt_utf8,history_json,runtime_parser_state_json;
 std::string wire_response_json,parser_input_hex;
};
class NativeProducer final {
 struct Impl;std::unique_ptr<Impl> impl_;
 public:
 // The caller owns an ALREADY-created exact model. This constructor never
 // initializes a backend, loads even a vocabulary-only model, or creates KV.
 NativeProducer(llama_model* existing_model,ProductionGate&,BudgetHooks& accounting);
 ~NativeProducer();
 NativeProducer(const NativeProducer&)=delete;NativeProducer&operator=(const NativeProducer&)=delete;
 ProducerPrompt initial(const std::string& messages_json,const std::string& request_id);
 ProducerPrompt advance(const std::vector<int32_t>& complete_generated_ids,const std::string& stop_reason,
                        std::size_t response_cap,const std::string& next_user_json,const std::string& request_id);
};
}
