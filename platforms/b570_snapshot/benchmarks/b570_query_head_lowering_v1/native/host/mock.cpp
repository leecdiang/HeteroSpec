#include "modules.hpp"
#include <iostream>
#define main descriptor_main
#include "../../tests/test_graph.cpp"
#undef main
int main(){
 auto before=module_inventory();descriptor_main();auto after=module_inventory();
 require(before==after,"descriptor modules changed");
 std::cout<<json({{"scope","DESCRIPTOR_MOCK_ONLY"},{"modules",after},{"numerical_compute",0},{"gpu",0}}).dump()<<std::endl;
}
