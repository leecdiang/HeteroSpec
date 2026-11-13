#pragma once
// This header has no model/runtime/CUDA dependency and grants no admission.
#include <cstddef>
#include <stdexcept>
#include <string>
namespace hs::n1chain {
struct Blocked:std::runtime_error{using std::runtime_error::runtime_error;};
struct BudgetHooks {
 virtual ~BudgetHooks()=default;
 virtual void before_backend_init(const std::string&)=0;
 virtual void before_model_load(const std::string&)=0;
 virtual void before_context(const std::string&)=0;
 virtual void before_placement(const std::string&)=0;
 virtual void before_request(const std::string&)=0;
 virtual void before_decode(const std::string& request,std::size_t rows)=0;
 virtual void before_mutation(const std::string& request,const std::string& action)=0;
 virtual void finish_request(const std::string& request,const std::string& status)=0;
 virtual void poison(const std::string& reason)noexcept=0;
};
// This final concrete gate cannot be enabled by JSON/argv/env or a bool.
// Future admission needs a separate independently reviewed implementation.
class ProductionGate final:public BudgetHooks {
 bool poisoned_=false;
 [[noreturn]] void deny()const{throw Blocked(poisoned_?"CPU_ONLY_POISONED: native entry denied":"CPU_ONLY_NOT_ADMITTED: native entry denied");}
 public:
 void before_backend_init(const std::string&)override{deny();}
 void before_model_load(const std::string&)override{deny();}
 void before_context(const std::string&)override{deny();}
 void before_placement(const std::string&)override{deny();}
 void before_request(const std::string&)override{deny();}
 void before_decode(const std::string&,std::size_t)override{deny();}
 void before_mutation(const std::string&,const std::string&)override{deny();}
 void finish_request(const std::string&,const std::string&)override{deny();}
 void poison(const std::string&)noexcept override{poisoned_=true;}
};
}
