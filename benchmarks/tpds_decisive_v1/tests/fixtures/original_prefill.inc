 void prefill(const std::vector<int>&ids,const std::vector<int>&schedule){
  size_t pos=0;for(int n:schedule){need((n==1||n==2||n==4)&&pos+n<=ids.size(),"prefill schedule");
   decode(std::vector<int>(ids.begin()+pos,ids.begin()+pos+n),int(pos),false,"PREFILL",pos+n==ids.size());pos+=n;}
  need(pos==ids.size(),"prefill incomplete");
 }
