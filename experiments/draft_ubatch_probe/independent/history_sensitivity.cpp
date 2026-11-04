#define main protocol_fixture_main
#include "fixture/test_native.cpp"
#undef main
int main(int argc,char**argv) {try {
 need(argc==2,"GGUF path required");llama_backend_init();auto p=llama_model_default_params();p.n_gpu_layers=0;
 std::unique_ptr<llama_model,decltype(&llama_model_free)> m(llama_model_load_from_file(argv[1],p),llama_model_free);need(bool(m),"model load");
 std::vector<std::vector<int>> prefixes={{1},{1,2,3,4,5,6,7,1},{7,6,5,4,3,2,1,1},{90,91,92,93,94,95,96,1},std::vector<int>(16,1),std::vector<int>(16,22)};
 prefixes.back().back()=1;auto reference=oracle(m.get(),prefixes[0]);J rows=J::array();
 for(auto& prefix:prefixes){auto x=oracle(m.get(),prefix);int different=0;float max_abs=0;for(size_t i=0;i<x.size();++i){different+=memcmp(&x[i],&reference[i],sizeof(float))!=0;max_abs=std::max(max_abs,std::fabs(x[i]-reference[i]));}rows.push_back({{"prefix",prefix},{"different_logit_elements",different},{"max_abs_difference",max_abs}});}
 std::cout<<J({{"scope","CPU synthetic history sensitivity; no GPU qualification"},{"cases",rows}}).dump(2)<<"\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
