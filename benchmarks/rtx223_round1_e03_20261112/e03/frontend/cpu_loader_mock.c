#include <windows.h>
__declspec(dllexport) int hs_e03_cpu_mock_marker(void){return 0x0303;}
__declspec(dllexport) const char* hs_e03_runtime_metadata(void){return "{\"schema\":\"heterospec.e03.cpu-loader-mock.v1\",\"scope\":\"CPU_STANDIN_NOT_NUMERICAL_RUNTIME\"}";}
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,LPVOID reserved){(void)instance;(void)reason;(void)reserved;return TRUE;}
