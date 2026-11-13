#pragma once
#include "live_gate.hpp"
#include <memory>
struct llama_model;
namespace hs::n1chain {
struct LivePrompt{std::vector<int>ids;PJ receipt;};
class LiveProducer final{
 struct Impl;std::unique_ptr<Impl>p_;
 public:
 LiveProducer(llama_model*,BudgetHooks&);~LiveProducer();
 LivePrompt initial(const PJ&messages);LivePrompt next(const PJ&user);
 PJ consume(const std::vector<int>&emitted,const std::string&stop,int cap,int cached);
};
}
