#pragma once
// Gate before process creation: linked GPU initializers can run before main.
// This current gate ALWAYS denies before IPC, fork or caller exec callback.
#include "accounting_ipc.hpp"
namespace hs::n1chain {
struct LaunchAccountingSpec{std::string socket_path,run_id,manifest_sha256,launch_client_id;unsigned command_timeout_ms=0;};
template<class Exec>
decltype(auto) guarded_native_launch(ProductionGate&gate,const LaunchAccountingSpec&spec,const std::string&placement_id,Exec&&exec){
 gate.before_placement(placement_id);
 NativeAccountingClient client(spec.socket_path,spec.run_id,spec.manifest_sha256,spec.launch_client_id,spec.command_timeout_ms);
 client.before_placement(placement_id); // durable ACK BEFORE any native ELF exec
 client.close_worker();               // LAUNCH_ONLY completes before WORKER hello
 return std::forward<Exec>(exec)();    // unreachable under current ProductionGate
}
}
