#!/usr/bin/env sh
set -eu

echo "== vm_stat =="
vm_stat
echo "== swap =="
sysctl vm.swapusage
echo "== memory pressure =="
memory_pressure
