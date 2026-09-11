cmake_minimum_required(VERSION 3.24)
project(b570_presentmon_telemetry LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(PRESENTMON_SDK "C:/Program Files/Intel/PresentMon/SDK" CACHE PATH "Official PresentMon SDK directory")
add_executable(b570_presentmon_telemetry collector.cpp)
target_include_directories(b570_presentmon_telemetry PRIVATE "${PRESENTMON_SDK}")
target_link_libraries(b570_presentmon_telemetry PRIVATE "${PRESENTMON_SDK}/PresentMonAPI2Loader.lib" setupapi)
add_custom_command(TARGET b570_presentmon_telemetry POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${PRESENTMON_SDK}/PresentMonAPI2Loader.dll"
    "$<TARGET_FILE_DIR:b570_presentmon_telemetry>")

set(LEVEL_ZERO_SDK "C:/Program Files/LevelZeroSDK/1.32.0" CACHE PATH "Official Level Zero SDK directory")
if(EXISTS "${LEVEL_ZERO_SDK}/include/level_zero/zes_api.h")
  add_executable(b570_sysman_probe sysman_probe.cpp)
  target_include_directories(b570_sysman_probe PRIVATE "${LEVEL_ZERO_SDK}/include")
  target_link_libraries(b570_sysman_probe PRIVATE "${LEVEL_ZERO_SDK}/lib/ze_loader.lib")
endif()
