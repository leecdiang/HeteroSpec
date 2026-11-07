#pragma once
#include <dxgi1_4.h>
// Request only a reservation offered to this process by Windows. Never replace
// the actual Vulkan budget with the requested amount or relax the reserve.
static void hs_dxgi_budget(VkPhysicalDevice physical) {
 struct State {
  IDXGIFactory1* factory=nullptr;IDXGIAdapter3* adapter=nullptr;bool attempted=false;
  State(VkPhysicalDevice physical){
   VkPhysicalDeviceIDProperties id{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ID_PROPERTIES};
   VkPhysicalDeviceProperties2 properties{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2};properties.pNext=&id;
   vkGetPhysicalDeviceProperties2(physical,&properties);need(id.deviceLUIDValid,"Vulkan device LUID unavailable");
   need(SUCCEEDED(CreateDXGIFactory1(__uuidof(IDXGIFactory1),(void**)&factory)),"DXGI factory");
   for(UINT i=0;;i++){
    IDXGIAdapter1* a=nullptr;if(factory->EnumAdapters1(i,&a)==DXGI_ERROR_NOT_FOUND)break;
    DXGI_ADAPTER_DESC1 d{};a->GetDesc1(&d);
    if(std::wstring(d.Description).find(L"B570")!=std::wstring::npos)
     std::fprintf(stderr,"HS_DXGI_ENUM vendor=%u device=%u luid_high=%ld luid_low=%lu\n",d.VendorId,d.DeviceId,d.AdapterLuid.HighPart,d.AdapterLuid.LowPart);
    if(std::memcmp(&d.AdapterLuid,id.deviceLUID,8)==0){
     need(!adapter,"ambiguous DXGI B570");need(SUCCEEDED(a->QueryInterface(__uuidof(IDXGIAdapter3),(void**)&adapter)),"DXGI3 adapter");
     std::fprintf(stderr,"HS_DXGI_DEVICE vendor=%u device=%u luid_high=%ld luid_low=%lu\n",d.VendorId,d.DeviceId,d.AdapterLuid.HighPart,d.AdapterLuid.LowPart);
    }a->Release();
   }need(adapter,"DXGI B570 absent");
  }
  ~State(){if(adapter)adapter->Release();if(factory)factory->Release();}
 };
 static State s(physical);
 auto query=[&](const char* phase){
  DXGI_QUERY_VIDEO_MEMORY_INFO x{};need(SUCCEEDED(s.adapter->QueryVideoMemoryInfo(0,DXGI_MEMORY_SEGMENT_GROUP_LOCAL,&x)),"DXGI memory query");
  std::fprintf(stderr,"HS_DXGI phase=%s budget=%llu usage=%llu available_reservation=%llu reservation=%llu\n",phase,(unsigned long long)x.Budget,(unsigned long long)x.CurrentUsage,(unsigned long long)x.AvailableForReservation,(unsigned long long)x.CurrentReservation);return x;
 };
 auto x=query("before");
 if(!s.attempted){
  s.attempted=true;auto requested=std::min<UINT64>(x.AvailableForReservation,9ULL*1024*1024*1024);
  HRESULT rc=s.adapter->SetVideoMemoryReservation(0,DXGI_MEMORY_SEGMENT_GROUP_LOCAL,requested);
  std::fprintf(stderr,"HS_DXGI_RESERVATION requested=%llu hresult=%ld\n",(unsigned long long)requested,(long)rc);
  query("after_request");
 }
}
