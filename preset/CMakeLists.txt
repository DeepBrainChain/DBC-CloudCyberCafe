cmake_minimum_required (VERSION 3.2)
# 使用新策略设置静态运行时：https://cmake.org/cmake/help/latest/policy/CMP0091.html
if (POLICY CMP0091)
  cmake_policy(SET CMP0091 NEW)
endif (POLICY CMP0091)
project("preset")

set(CMAKE_CXX_STANDARD 11)

message("CMAKE_HOST_SYSTEM_NAME: ${CMAKE_HOST_SYSTEM_NAME}")
message("CMAKE_HOST_SYSTEM: ${CMAKE_HOST_SYSTEM}")
message("CMAKE_SYSTEM_NAME: ${CMAKE_SYSTEM_NAME}")
message("CMAKE_SYSTEM: ${CMAKE_SYSTEM}")
message("CMAKE_HOST_UNIX: ${CMAKE_HOST_UNIX}")
message("CMAKE_HOST_WIN32: ${CMAKE_HOST_WIN32}")

if (MSVC)
  add_definitions(-DUNICODE -D_UNICODE)
  message("CMAKE_MSVC_RUNTIME_LIBRARY: ${CMAKE_MSVC_RUNTIME_LIBRARY}")
  set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
  message("CMAKE_MSVC_RUNTIME_LIBRARY: ${CMAKE_MSVC_RUNTIME_LIBRARY}")
endif()

if (CMAKE_HOST_SYSTEM_NAME MATCHES "Windows" AND WIN32)
  message("current win32")

  # set(Boost_DEBUG ON)
  # set(Boost_THREADAPI win32)
  # set(Boost_COMPILER "-vc142")

  set(BOOST_ROOT "D:\\Code\\boost_1_71_0")
  set(BOOST_INCLUDEDIR "D:\\Code\\boost_1_71_0\\boost")
  set(BOOST_LIBRARYDIR "D:\\Code\\boost_1_71_0\\stage\\lib")

  set(Boost_USE_STATIC_LIBS     ON)
  set(Boost_USE_STATIC_RUNTIME  ON)
  set(Boost_USE_MULTITHREADED   ON)

  find_package(Boost 1.71.0 REQUIRED COMPONENTS atomic chrono container context
    contract coroutine date_time exception fiber filesystem graph iostreams
    locale log log_setup program_options python27 random regex serialization
    system thread timer unit_test_framework)

  if (Boost_FOUND)
    message(STATUS "Boost_VERSION: ${Boost_VERSION} ${Boost_LIBRARIES}")
    include_directories(${Boost_INCLUDE_DIRS})
    link_directories(${Boost_LIBRARY_DIR})
  else ()
    message(FATAL_ERROR " fail to find boost library")
  endif()

  # thrift
  set(THRIFT_CPP_ROOT "D:\\Code\\thrift-0.13.0\\lib\\cpp")
  include_directories(SYSTEM ${THRIFT_CPP_ROOT}\\src)
  # link_directories(${THRIFT_CPP_ROOT}\\Release-mt)
  find_library(THRIFT_CPP_LIB libthrift.lib ${THRIFT_CPP_ROOT}\\Release-mt)
  if (NOT THRIFT_CPP_LIB)
    message(FATAL_ERROR "libthrift.lib not found")
  endif()

  get_property(dirs DIRECTORY ${CMAKE_SOURCE_DIR} PROPERTY INCLUDE_DIRECTORIES)
  message(">>> include_dirs=${dirs}") #打印一下目录情况
elseif(APPLE)
  message("current apple")
elseif(UNIX)
  message("current linux")

  # GLIB2
  find_package(PkgConfig REQUIRED)
  pkg_search_module(GLIB REQUIRED glib-2.0)

  include_directories(${GLIB_INCLUDE_DIRS})
  link_directories(${GLIB_LIBRARY_DIRS})
  message("GLIB_INCLUDE_DIRS: ${GLIB_INCLUDE_DIRS}")
  message("GLIB_LIBRARY_DIRS: ${GLIB_LIBRARY_DIRS}")
  message("GLIB_CFLAGS_OTHER: ${GLIB_CFLAGS_OTHER}")
  message("GLIB_LIBRARIES: ${GLIB_LIBRARIES}")
  message("GLIB_LDFLAGS: ${GLIB_LDFLAGS}")

  # 仅查找静态库，强制后缀为 .a
  message("CMAKE_FIND_LIBRARY_SUFFIXES: ${CMAKE_FIND_LIBRARY_SUFFIXES}")
  set(CMAKE_FIND_LIBRARY_SUFFIXES ".a" ".so")
  message("CMAKE_FIND_LIBRARY_SUFFIXES: ${CMAKE_FIND_LIBRARY_SUFFIXES}")

  set(Boost_USE_STATIC_LIBS     ON)
  set(Boost_USE_STATIC_RUNTIME  ON)
  set(Boost_USE_MULTITHREADED   ON)

  find_library(Boost_LIBRARIES boost_program_options)

  if (NOT Boost_LIBRARIES)
    message(FATAL_ERROR " fail to find boost library")
  else ()
    set(Boost_LIBRARIES libboost_program_options.a)
    message(STATUS "find boost library: ${Boost_LIBRARIES}")
  endif()

  find_library(THRIFT_CPP_LIB libthrift.a)
  if (NOT THRIFT_CPP_LIB)
    message(FATAL_ERROR "libthrift.a not found")
  endif()
else()
  message("unknown system")
endif()

set(presetgencpp_SOURCES
  gen-cpp/Preset.cpp
  gen-cpp/preset_constants.cpp
  gen-cpp/preset_types.cpp
)
add_library(presetgencpp STATIC ${presetgencpp_SOURCES})
target_link_libraries(presetgencpp ${THRIFT_CPP_LIB})

if (WIN32)
  set(CROSS_FILES cross_func_win32.cpp)
else ()
  set(CROSS_FILES cross_func_posix.cpp)
endif ()

add_executable(Preset main.cpp preset_handler.cpp cross_util.cpp ${CROSS_FILES})
target_include_directories(Preset PRIVATE gen-cpp)
target_link_libraries(Preset presetgencpp)
target_link_libraries(Preset ${Boost_LIBRARIES})
target_link_libraries(Preset ${THRIFT_CPP_LIB})
if (UNIX AND NOT APPLE)
  target_link_libraries(Preset ${GLIB_LIBRARIES})
  # target_link_libraries(Preset -static-libgcc -static-libstdc++ -pthread -lrt -ldl)
  # target_link_libraries(Preset -Wl,-static ${GLIB_LIBRARIES})
endif ()

add_executable(testClient test_client.cpp)
target_include_directories(testClient PRIVATE gen-cpp)
target_link_libraries(testClient presetgencpp ${Boost_LIBRARIES} ${THRIFT_CPP_LIB})
