#include "llama.h"
int main(int n,char**v){if(n!=3)return 2;auto p=llama_model_quantize_default_params();p.ftype=LLAMA_FTYPE_MOSTLY_Q8_0;return llama_model_quantize(v[1],v[2],&p);}
