__declspec(dllimport) unsigned long __stdcall GetLastError(void); int chosen(void); int mainCRTStartup(void){return chosen()+(int)GetLastError();}
