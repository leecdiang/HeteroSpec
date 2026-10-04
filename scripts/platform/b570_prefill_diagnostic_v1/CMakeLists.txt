cmake_minimum_required(VERSION 3.20)
project(heterospec_b570_mechanism_v08 LANGUAGES CXX)
set(PINNED_SOURCE "C:/hs/b570-direct-id-v1-src" CACHE PATH "Pinned b10839 source")
set(PINNED_BUILD "C:/hs/b570-direct-id-v1-build" CACHE PATH "Existing frozen library build")
add_executable(heterospec-mechanism target.cpp)
add_executable(heterospec-prefill-native native.cpp)
target_compile_features(heterospec-mechanism PRIVATE cxx_std_17)
target_compile_definitions(heterospec-mechanism PRIVATE _CRT_SECURE_NO_WARNINGS LLAMA_SUBPROCESS LLAMA_SHARED GGML_SHARED GGML_BACKEND_SHARED GGML_USE_CPU GGML_USE_VULKAN)
target_include_directories(heterospec-mechanism PRIVATE "${PINNED_SOURCE}/common" "${PINNED_SOURCE}/include" "${PINNED_SOURCE}/ggml/include" "${PINNED_SOURCE}/vendor")
target_link_libraries(heterospec-mechanism PRIVATE
    "${PINNED_BUILD}/common/Release/llama-common.lib"
    "${PINNED_BUILD}/common/Release/llama-common-base.lib"
    "${PINNED_BUILD}/src/Release/llama.lib"
    "${PINNED_BUILD}/ggml/src/Release/ggml.lib"
    "${PINNED_BUILD}/ggml/src/Release/ggml-cpu.lib"
    "${PINNED_BUILD}/ggml/src/ggml-vulkan/Release/ggml-vulkan.lib"
    "${PINNED_BUILD}/ggml/src/Release/ggml-base.lib")

target_compile_features(heterospec-prefill-native PRIVATE cxx_std_17)
get_target_property(shared_COMPILE_DEFINITIONS heterospec-mechanism COMPILE_DEFINITIONS)
set_target_properties(heterospec-prefill-native PROPERTIES COMPILE_DEFINITIONS "${shared_COMPILE_DEFINITIONS}")
get_target_property(shared_INCLUDE_DIRECTORIES heterospec-mechanism INCLUDE_DIRECTORIES)
set_target_properties(heterospec-prefill-native PROPERTIES INCLUDE_DIRECTORIES "${shared_INCLUDE_DIRECTORIES}")
get_target_property(shared_LINK_LIBRARIES heterospec-mechanism LINK_LIBRARIES)
set_target_properties(heterospec-prefill-native PROPERTIES LINK_LIBRARIES "${shared_LINK_LIBRARIES}")
