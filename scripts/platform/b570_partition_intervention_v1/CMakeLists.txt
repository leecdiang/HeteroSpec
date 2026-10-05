cmake_minimum_required(VERSION 3.20)
project(b570_partition_intervention LANGUAGES CXX)
set(PINNED_SOURCE "C:/hs/b570-direct-id-v1-src" CACHE PATH "Read-only pinned source")
set(PINNED_BUILD "C:/hs/b570-direct-id-v1-build" CACHE PATH "Read-only frozen libraries")
add_executable(heterospec-partition generated_speculative.cpp)
target_compile_features(heterospec-partition PRIVATE cxx_std_17)
target_compile_definitions(heterospec-partition PRIVATE _CRT_SECURE_NO_WARNINGS LLAMA_SUBPROCESS LLAMA_SHARED GGML_SHARED GGML_BACKEND_SHARED GGML_USE_CPU GGML_USE_VULKAN)
target_include_directories(heterospec-partition PRIVATE "${PINNED_SOURCE}/common" "${PINNED_SOURCE}/include" "${PINNED_SOURCE}/ggml/include" "${PINNED_SOURCE}/vendor" "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(heterospec-partition PRIVATE
 "${PINNED_BUILD}/common/Release/llama-common.lib"
 "${PINNED_BUILD}/common/Release/llama-common-base.lib"
 "${PINNED_BUILD}/src/Release/llama.lib"
 "${PINNED_BUILD}/ggml/src/Release/ggml.lib"
 "${PINNED_BUILD}/ggml/src/Release/ggml-cpu.lib"
 "${PINNED_BUILD}/ggml/src/ggml-vulkan/Release/ggml-vulkan.lib"
 "${PINNED_BUILD}/ggml/src/Release/ggml-base.lib")
