#include "modules.hpp"
#include "query_head.h"
#include <fstream>
#include <iostream>
#include <filesystem>
#include <chrono>
using Compute=int(*)(ggml_context*,ggml_cgraph*,int);
namespace fs=std::filesystem;
static const char*names[]={"MQ","PQ","QB4","QH_C","QH_D","REPEAT4"};
static size_t off(ggml_tensor*t,int a,int b=0,int c=0,int d=0){return a*t->nb[0]+b*t->nb[1]+c*t->nb[2]+d*t->nb[3];}
static double at(ggml_tensor*t,int a,int b=0,int c=0,int d=0){
 auto*p=static_cast<char*>(t->data)+off(t,a,b,c,d);
 return t->type==GGML_TYPE_F32?double(*reinterpret_cast<float*>(p)):half_value(*reinterpret_cast<uint16_t*>(p));
}
static bool samebits(float a,float b){uint32_t x,y;std::memcpy(&x,&a,4);std::memcpy(&y,&b,4);return x==y;}
static json meta(ggml_tensor*t){return {{"op",ggml_op_name(t->op)},{"type",ggml_type_name(t->type)},
 {"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},
 {"view_offset",t->view_offs},{"precision_parameter",t->op_params[0]},{"bytes",ggml_nbytes(t)}};}
static void walk(ggml_tensor*t,std::vector<ggml_tensor*>&v){if(!t||std::find(v.begin(),v.end(),t)!=v.end())return;for(auto*s:t->src)walk(s,v);v.push_back(t);}
struct Input{Logical l;int storage,mask,pattern;std::vector<float>q,m;std::vector<uint16_t>k,v;};
template<class T>static void readvec(std::ifstream&f,std::vector<T>&v,size_t n){v.resize(n);f.read((char*)v.data(),n*sizeof(T));require(bool(f),"truncated input");}
static Input read_input(std::string path){
 std::ifstream f(path,std::ios::binary);int a[7];f.read((char*)a,sizeof(a));require(bool(f),"input header");Input x;auto&l=x.l;
 l.nq=a[0];l.nk=a[1];l.nh=a[2];l.nv=a[3];x.storage=a[4];x.mask=a[5];x.pattern=a[6];
 require(l.nq>=1&&l.nq<=4&&(l.nk==63||l.nk==128||l.nk==257)&&l.nv>0&&l.nh%l.nv==0,"geometry");
 readvec(f,x.q,l.nq*l.nh*128);readvec(f,x.k,l.nv*l.nk*128);readvec(f,x.v,l.nv*128*l.nk);readvec(f,x.m,32*l.nk);require(f.peek()==EOF,"input trailing bytes");
 l.q.assign(x.q.begin(),x.q.end());for(auto v:x.k)l.k.push_back(half_value(v));for(auto v:x.v)l.v.push_back(half_value(v));l.mask.assign(x.m.begin(),x.m.begin()+l.nq*l.nk);l.solve();return x;
}
static hs_qh::Built original(ggml_context*c,ggml_tensor*q,ggml_tensor*k,ggml_tensor*v,ggml_tensor*m,float scale){
 hs_qh::Built b;b.common_original=true;auto*s=ggml_mul_mat(c,k,q);ggml_mul_mat_set_prec(s,GGML_PREC_F32);
 auto*p=ggml_soft_max_ext(c,s,m,scale,0);auto*a=ggml_mul_mat(c,v,p);auto*r=ggml_permute(c,a,0,2,1,3);
 b.scores={s};b.probs={p};b.values={a};b.out=ggml_cont_2d(c,r,128*q->ne[2],q->ne[1]);return b;
}
static json save_tensor(ggml_tensor*t,const fs::path&p){
 require(ggml_is_contiguous(t)&&t->type==GGML_TYPE_F32,"raw contiguous F32 stage");
 std::ofstream f(p,std::ios::binary);f.write((char*)t->data,ggml_nbytes(t));require(bool(f),"raw output write");
 return {{"file",p.filename().string()},{"tensor",meta(t)}};
}
static json execute(Input&x,Compute compute,const fs::path&dir){
 auto&l=x.l;int nq=l.nq,nk=l.nk,nh=l.nh,nv=l.nv;
 ggml_init_params init{128*1024*1024,nullptr,false};auto*c=ggml_init(init);require(c,"CPU context");
 auto*base=ggml_new_tensor_1d(c,GGML_TYPE_F32,8+128*nh*nq);
 auto*q=ggml_view_4d(c,base,128,nq,nh,1,x.storage?512*nh:512,x.storage?512:512*nq,512*nh*nq,32);
 auto*k=ggml_new_tensor_4d(c,GGML_TYPE_F16,128,nk,nv,1);auto*v=ggml_new_tensor_4d(c,GGML_TYPE_F16,nk,128,nv,1);auto*m=ggml_new_tensor_4d(c,GGML_TYPE_F32,nk,32,1,1);
 std::memset(base->data,0,ggml_nbytes(base));
 for(int j=0;j<nq;++j)for(int h=0;h<nh;++h)for(int d=0;d<128;++d)*reinterpret_cast<float*>(static_cast<char*>(q->data)+off(q,d,j,h))=x.q[l.qi(j,h,d)];
 std::memcpy(k->data,x.k.data(),x.k.size()*2);std::memcpy(v->data,x.v.data(),x.v.size()*2);std::memcpy(m->data,x.m.data(),x.m.size()*4);
 // Full input bytes are captured once and compared after every graph, including padding.
 std::vector<std::pair<ggml_tensor*,std::vector<char>>> originals;
 for(auto*t:{base,k,v,m})originals.push_back({t,std::vector<char>((char*)t->data,(char*)t->data+ggml_nbytes(t))});
 json record={{"inputs",{{"Q",meta(q)},{"K",meta(k)},{"V",meta(v)},{"mask",meta(m)}}},{"scale_f32",float(l.scale)}};
 uint64_t addresses=0;std::vector<float>mq_final;
 for(int mode=0;mode<6;++mode){
  auto start=std::chrono::steady_clock::now();auto b=hs_qh::build(c,hs_qh::Mode(mode),q,k,v,m,float(l.scale));
  if(b.common_original)b=original(c,q,k,v,m,float(l.scale));
  auto*g=ggml_new_graph(c);ggml_build_forward_expand(g,b.out);std::vector<ggml_tensor*>nodes;walk(b.out,nodes);
  json graph=json::array();size_t logical_dest=0;
  for(size_t i=0;i<nodes.size();++i){auto*t=nodes[i];json z=meta(t);z["id"]=i;z["sources"]=json::array();
   for(auto*s:t->src)if(s)z["sources"].push_back(std::find(nodes.begin(),nodes.end(),s)-nodes.begin());
   if(t->view_src){require(t->data==(char*)t->view_src->data+t->view_offs,"view data owner");require(t->view_offs+ggml_nbytes(t)<=ggml_nbytes(t->view_src),"view buffer bounds");}
   if(t->op==GGML_OP_CONT||t->op==GGML_OP_REPEAT||t->op==GGML_OP_CONCAT)logical_dest+=ggml_nbytes(t);
   graph.push_back(z);
  }
  require(b.scores.size()==size_t(mode==1&&nq>1?nq:1),"attention chain count");
  if(nq>1&&(mode==3||mode==4)){require(b.scores[0]->src[0]==k&&b.values[0]->src[0]==v,"QH shares original KV objects");
   require(b.packed_q==(x.storage!=0),"explicit Q pack flag");require(b.dense_mask==(mode==4),"dense mask flag");}
  if(nq>1&&mode==5)require(b.scores[0]->src[0]->op==GGML_OP_REPEAT&&b.values[0]->src[0]->op==GGML_OP_REPEAT,"actual KV repeat operators");
  require(compute(c,g,1)==0,"CPU graph compute");
  for(auto&entry:originals)require(std::memcmp(entry.first->data,entry.second.data(),entry.second.size())==0,"input bytes changed during compute");
  Metric sm,pm,am,fm;json stages=json::array();fs::path sub=dir/names[mode];fs::create_directories(sub);
  for(size_t part=0;part<b.scores.size();++part){auto*s=b.scores[part];auto*p=b.probs[part];auto*a=b.values[part];auto*qi=s->src[1];auto*ki=s->src[0];auto*vi=a->src[0];auto*mi=p->src[1];
   stages.push_back({{"QK",save_tensor(s,sub/("qk-"+std::to_string(part)+".f32"))},
                    {"softmax",save_tensor(p,sub/("sm-"+std::to_string(part)+".f32"))},
                    {"AV",save_tensor(a,sub/("av-"+std::to_string(part)+".f32"))}});
   for(int j=0;j<nq;++j){if(mode==1&&nq>1&&int(part)!=j)continue;
    bool packed=nq>1&&(mode==3||mode==4);int col=(mode==0||nq==1)?j:0,batch=nq>1&&(mode==2||mode==5)?j:0;
    for(int h=0;h<nh;++h){int head=packed?h*nq+j:h;
     int kh=int(head/(s->ne[2]/ki->ne[2])),kb=int(batch/(s->ne[3]/ki->ne[3]));
     require(kh==h/(nh/nv),"GQA group mapping");
     for(int d=0;d<128;++d){
      // Independent logical (j,h,d) labels, not floating labels or candidate helper.
      require(at(qi,d,col,head,batch)==l.q[l.qi(j,h,d)],"packed Q identity");
      size_t physical=32+4*(x.storage?((j*nh+h)*128+d):((h*nq+j)*128+d));
      require((char*)q->data-(char*)base->data+off(q,d,j,h)==physical&&physical+4<=ggml_nbytes(base),"original Q integer address");addresses+=2;
     }
     for(int key=0;key<nk;++key){
      double maskvalue=at(mi,key,col,head%int(mi->ne[2]),batch%int(mi->ne[3]));
      require(maskvalue==l.mask[j*nk+key],"mask logical column identity");++addresses;
      if(!(packed&&mode==4)){
       size_t addr=(char*)mi->data-(char*)m->data+off(mi,key,col,head%int(mi->ne[2]),batch%int(mi->ne[3]));
       require(addr==size_t(j*nk+key)*4,"mask integer source address");++addresses;
      }
      for(int d=0;d<128;++d){
       require(at(ki,d,key,kh,kb)==l.k[l.ki(h/(nh/nv),key,d)],"K repeat/broadcast identity");
       require(at(vi,key,d,kh,kb)==l.v[l.vi(h/(nh/nv),d,key)],"V repeat/broadcast identity");addresses+=2;
      }
      double se=l.score[l.si(j,h,key)],pe=l.prob[l.si(j,h,key)];
      sm.add(float(at(s,key,col,head,batch)),se,{j,h,key});pm.add(float(at(p,key,col,head,batch)),pe,{j,h,key});
      if(x.pattern)require(at(s,key,col,head,batch)==se,"structured one-hot QK exact");
      if(x.pattern&&x.mask==1)require(at(p,key,col,head,batch)==pe,"structured single-key softmax exact");
     }
     for(int d=0;d<128;++d){float av=float(at(a,d,col,head,batch)),out=float(at(b.out,h*128+d,j));double expected=l.value[l.qi(j,h,d)];
      am.add(av,expected,{j,h,d});require(samebits(av,out),"output restoration must preserve actual AV bits");++addresses;
      if(x.pattern&&x.mask==1)require(double(av)==expected,"structured single-key AV exact");
     }
    }
   }
  }
  require(b.out->ne[0]==128*nh&&b.out->ne[1]==nq&&ggml_is_contiguous(b.out),"ordinary final dimensions");
  for(int j=0;j<nq;++j)for(int h=0;h<nh;++h)for(int d=0;d<128;++d){float out=float(at(b.out,h*128+d,j));fm.add(out,l.value[l.qi(j,h,d)],{j,h,d});
   if(x.pattern&&x.mask==1)require(double(out)==l.value[l.qi(j,h,d)],"structured single-key final exact");
   if(mode==0)mq_final.push_back(out);else if(nq==1)require(samebits(out,mq_final[l.qi(j,h,d)]),"q1 common original bitwise control");
  }
  auto final=save_tensor(b.out,sub/"final.f32");auto elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
  record["modes"].push_back({{"mode",names[mode]},{"common_original",b.common_original},{"packed_q",b.packed_q},{"dense_mask",b.dense_mask},{"copied_kv",b.copied_kv},
   {"graph",graph},{"stages",stages},{"final",final},{"QK",sm.result()},{"softmax",pm.result()},{"AV",am.result()},{"output",fm.result()},
   {"materialization_logical_destination_bytes",logical_dest},{"CPU_build_compute_audit_write_wall_s",elapsed},{"input_bytes_unchanged",true}});
 }
 record["address_checks"]=addresses;ggml_free(c);return record;
}
int main(int argc,char**argv){
 try{require(argc==3,"usage: qh-real input-list.json output.jsonl");auto before=module_inventory();
  char exe[MAX_PATH];GetModuleFileNameA(nullptr,exe,MAX_PATH);fs::path dir=fs::path(exe).parent_path();
  auto lib=LoadLibraryExA((dir/"ggml-cpu.dll").string().c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);
  require(lib,"explicit frozen CPU load");auto compute=(Compute)GetProcAddress(lib,"ggml_graph_compute_with_ctx");require(compute,"CPU compute symbol");auto loaded=module_inventory();
  std::ifstream f(argv[1]);json cells;f>>cells;require(!fs::exists(argv[2]),"do not overwrite raw output");std::ofstream out(argv[2]);
  out<<json({{"event","MODULES"},{"entry",before},{"loaded",loaded}}).dump()<<std::endl;
  for(auto&cell:cells){require(module_inventory()==loaded,"modules before fixture");
   out<<json({{"event","FIXTURE_START"},{"id",cell["id"]},{"input_sha256",cell["input_sha256"]}}).dump()<<std::endl;
   auto input=read_input(cell["input"]);auto result=execute(input,compute,cell["raw_dir"]);
   require(module_inventory()==loaded,"modules after fixture");result["event"]="FIXTURE_COMPLETE";result["id"]=cell["id"];result["input_sha256"]=cell["input_sha256"];result["modules_unchanged"]=true;
   out<<result.dump()<<std::endl;
  }
  out<<json({{"event","CLOSE"},{"modules",module_inventory()},{"GPU_starts",0}}).dump()<<std::endl;
  FreeLibrary(lib);return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 50;}
}
