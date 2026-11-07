#!/usr/bin/env sh
set -eu

if [ "$(uname -s)" != "Darwin" ]; then
  echo "FAIL: macOS is required" >&2
  exit 1
fi

sw_vers
uname -a
system_profiler SPHardwareDataType SPDisplaysDataType SPPowerDataType \
  | sed -E '/Serial Number|Hardware UUID|Provisioning UDID/d'
df -h /
sysctl vm.swapusage
pmset -g batt
pmset -g custom
