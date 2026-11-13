#include "u_oracle.hpp"
#include <cfenv>
#include <cstdio>
#include <limits>
static void need(bool c,const char*m){if(!c){std::printf("FAIL %s\n",m);std::exit(2);}}
int main(){
 using namespace e11_oracle;need(std::fegetround()==FE_TONEAREST,"host RN");
 float x[32];int q[32];for(int k=0;k<32;++k)x[k]=(k%2?-1.0f:1.0f)*float(k+1)*0.003f;
 float inverse=rn_div(127.0f,std::fabs(x[31])),scale=rn_div(1.0f,inverse);
 for(int k=0;k<32;++k)q[k]=quant(x[k],inverse);
 need(block(x,q,scale).pass,"RN witness");
 inverse=value(bits(inverse)+2);scale=rn_div(1.0f,inverse);
 for(int k=0;k<32;++k)q[k]=quant(x[k],inverse);
 need(block(x,q,scale).pass,"allowed approximate witness");
 q[3]+=4;need(!block(x,q,scale).pass,"reject corrupted q");q[3]-=4;
 need(!block(x,q,value(bits(scale)+64)).pass,"reject corrupted scale");
 x[0]=1.0f;for(int k=1;k<32;++k)x[k]=0;
 x[1]=rn_div(0.5f,127.0f);x[2]=-x[1];inverse=127.0f;scale=rn_div(1.0f,inverse);
 for(int k=0;k<32;++k)q[k]=quant(x[k],inverse);
 q[1]=0;q[2]=-1;need(!block(x,q,scale).pass,"reject independently chosen incompatible witnesses");
 x[0]=std::numeric_limits<float>::quiet_NaN();need(!block(x,q,scale).pass,"reject NaN input");
 for(int k=0;k<32;++k)x[k]=0;need(!block(x,q,scale).pass,"reject excluded zero block");
 need(output(0.125f,0.125,0.25),"exact mathematical output");
 need(!output(1.0f,0.125,0.25),"reject out-of-bound output");
 need(!output(std::numeric_limits<float>::infinity(),0.125,0.25),"reject nonfinite output");
 std::puts("PASS RN,approximate,joint-witness,q-corruption,scale-corruption,NaN,zero-block,output-corruption,nonfinite-output;CUDA0");
}
