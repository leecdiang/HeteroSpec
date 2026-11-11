#pragma once
#include <vulkan/vulkan.h>
// Independent metadata query; historical numerical DLLs remain byte-identical.
// Query within the same process so VK_EXT_memory_budget observes its allocations.
static size_t bounded_vulkan_free() {
 struct Query {
  VkInstance instance{};VkPhysicalDevice device{};
  Query(){
   VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};app.apiVersion=VK_API_VERSION_1_1;
   VkInstanceCreateInfo ci{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};ci.pApplicationInfo=&app;
   need(vkCreateInstance(&ci,nullptr,&instance)==VK_SUCCESS,"resource instance");
   uint32_t n=0;need(vkEnumeratePhysicalDevices(instance,&n,nullptr)==VK_SUCCESS,"resource devices");
   std::vector<VkPhysicalDevice> devices(n);vkEnumeratePhysicalDevices(instance,&n,devices.data());
   for(auto d:devices){VkPhysicalDeviceProperties p{};vkGetPhysicalDeviceProperties(d,&p);
    if(std::string(p.deviceName).find("B570")!=std::string::npos){need(!device,"ambiguous resource device");device=d;}}
   need(device,"resource B570 missing");
   uint32_t k=0;vkEnumerateDeviceExtensionProperties(device,nullptr,&k,nullptr);
   std::vector<VkExtensionProperties> extensions(k);vkEnumerateDeviceExtensionProperties(device,nullptr,&k,extensions.data());
   bool supported=false;for(auto&e:extensions)supported|=std::string(e.extensionName)==VK_EXT_MEMORY_BUDGET_EXTENSION_NAME;
   need(supported,"resource budget extension required");
  }
  ~Query(){if(instance)vkDestroyInstance(instance,nullptr);}
 };
 static Query q;
 VkPhysicalDeviceMemoryBudgetPropertiesEXT b{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_BUDGET_PROPERTIES_EXT};
 VkPhysicalDeviceMemoryProperties2 p{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_PROPERTIES_2};p.pNext=&b;
 vkGetPhysicalDeviceMemoryProperties2(q.device,&p);
 uint64_t available=0;
 for(uint32_t i=0;i<p.memoryProperties.memoryHeapCount;i++){
  auto h=p.memoryProperties.memoryHeaps[i];if(!(h.flags&VK_MEMORY_HEAP_DEVICE_LOCAL_BIT))continue;
  auto budget=std::min<uint64_t>(h.size,b.heapBudget[i]);auto usage=uint64_t(b.heapUsage[i]);
  int64_t remaining=int64_t(budget)-int64_t(usage);
  std::fprintf(stderr,"HS_BUDGET heap=%u physical=%llu budget=%llu usage=%llu signed_remaining=%lld\n",i,(unsigned long long)h.size,(unsigned long long)budget,(unsigned long long)usage,(long long)remaining);
  if(remaining>0)available+=uint64_t(remaining);
 }
 return size_t(available);
}
