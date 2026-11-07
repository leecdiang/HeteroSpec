cmake_minimum_required(VERSION 3.20)
project(b570_boundary LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
foreach(var LLAMA_SOURCE QUALIFIED_BUILD)
  if(NOT DEFINED ${var})
    message(FATAL_ERROR "Set ${var} to the existing PR148/150 prepared tree/build")
  endif()
endforeach()
# Import the already qualified numerical libraries. This target builds drivers only.
add_executable(boundary native/boundary.cpp)
target_include_directories(boundary PRIVATE "${LLAMA_SOURCE}/include" "${LLAMA_SOURCE}/ggml/include" "${LLAMA_SOURCE}/vendor")
target_compile_options(boundary PRIVATE /O2 /W4 /fp:precise /utf-8)
target_link_libraries(boundary PRIVATE
  "${QUALIFIED_BUILD}/runtime/src/Release/llama.lib"
  "${QUALIFIED_BUILD}/runtime/ggml/src/Release/ggml.lib"
  "${QUALIFIED_BUILD}/runtime/ggml/src/Release/ggml-base.lib" bcrypt)
set_target_properties(boundary PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
