#pragma once
#include "session.hpp"
#include <memory>
#include <string>
struct llama_model;
struct llama_context;
namespace hs::n1chain {
struct RuntimeConfig {
 std::string run_id,model_path,model_sha256,placement_id,gpu_uuid;
 int threads=2;
};
struct NativeCore:Core {
 virtual llama_context* existing_context()const=0;
 virtual llama_model* existing_model()const=0; // never loads an additional model
 virtual std::string context_id()const=0;
 virtual std::string actual_work_json()const=0;
 virtual void set_control_fault(const std::string&)=0;
};
// Concrete, final gate is mandatory: a DurableMockBudget cannot be injected to
// unlock the real backend. This CPU-preparation build has no admitting gate.
std::unique_ptr<NativeCore> make_native_core(ProductionGate&,BudgetHooks&,const RuntimeConfig&);
}
