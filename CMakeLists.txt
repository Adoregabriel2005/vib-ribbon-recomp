cmake_minimum_required(VERSION 3.20)
set(PSXRECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/psxrecomp" CACHE PATH
    "Path to psxrecomp")
if(NOT EXISTS "${PSXRECOMP_ROOT}/runtime/runtime.cmake")
    message(FATAL_ERROR
        "PSXRecomp runtime is missing: ${PSXRECOMP_ROOT}/runtime/runtime.cmake\n"
        "This project expects the psxrecomp framework checkout at ${PSXRECOMP_ROOT}.\n"
        "Run: git submodule update --init --recursive\n"
        "If psxrecomp/ is not a submodule, set -DPSXRECOMP_ROOT=<path-to-psxrecomp>.")
endif()

project(VibRibbonRecomp LANGUAGES C CXX)

# Native menus use recomp-ui; the original game text remains a separate layer.
set(PSX_RECOMP_UI ON CACHE BOOL "Vib-Ribbon native settings interface" FORCE)
set(RECOMP_UI_LANGUAGE "pt-BR" CACHE STRING "Initial native interface language")
# Full netplay UI -- enable after adding recomp-ui + testing:
# if(EXISTS "${PSXRECOMP_ROOT}/lib/recomp-net/CMakeLists.txt")
#     set(PSX_NETPLAY ON CACHE BOOL "..." FORCE)
# endif()
# First-run setup wizard -- enable after testing:
# set(PSX_SETUP_WIZARD ON CACHE BOOL "..." FORCE)
# Fidelity baseline: keep the recompiled low-level implementations selected.
set(PSX_EXECUTION_PROFILE "REFERENCE" CACHE STRING "Vib-Ribbon fidelity baseline" FORCE)
set(PSX_GL_BATCH_IMPL "LLE" CACHE STRING "Baseline GPU batching" FORCE)
include("${PSXRECOMP_ROOT}/runtime/runtime.cmake")

# This project's own mod catalog. The FRAMEWORK stages it -- together with its
# builtin psx.* packages -- into <exe-dir>/mods/bundled, and refuses to
# configure if a catalog exists here but is not declared. Shared Internal
# Resolution is included even with a builtin allowlist, enabled at 4x on fresh
# profiles, with 1x..32x choices; do not supply a title-local copy of that id.
# Never copy the catalog by hand: five titles did, and framework 4cc04be3's rename of the staged
# directory broke all five silently (bead beads-eio.3.101).
set(PSX_PRELOADED_MODS "${CMAKE_CURRENT_SOURCE_DIR}/mods/preloaded")
if(NOT IS_DIRECTORY "${PSX_PRELOADED_MODS}")
    set(PSX_PRELOADED_MODS "NONE")
endif()

psxrecomp_add_game_runtime(psx-runtime
    PRELOADED_MODS_DIR "${PSX_PRELOADED_MODS}"
    # ENABLE_NETPLAY_IF_PRESENT
    # NETPLAY_LOBBY_URL "ws://netplay.retcomm.net:8765"
    # ENABLE_SETUP_WIZARD
    WINDOW_TITLE "VibRibbon Recompiled"
    DEFAULT_GAME_CONFIG_PATH "game.toml"
    MAX_PLAYERS 1
    # LAUNCHER_BOXART "${CMAKE_CURRENT_SOURCE_DIR}/launcher_assets/img/boxart.tga"
    APP_ICON "${CMAKE_CURRENT_SOURCE_DIR}/assets/psxrecomp.ico"
    # Committed game C (psxrecomp_cli.py generate; git add generated). Release
    # CI configures with -DPSXRECOMP_REQUIRE_GAME_C=ON so a checkout without
    # it fails instead of building a setup host.
    GAME_OVERLAY_STATIC_C "${CMAKE_CURRENT_SOURCE_DIR}/generated/overlays_static.c"
    GEN_MARKER "generated/SCES_028.73_dispatch.c"
    GEN_FULL_GLOB "generated/SCES_028.73_full_*.c"
    # CODEGEN_SETUP_SOURCES -- add with recomp-ui / wizard later
)

# Native music conversion and menu integration.
add_library(vib-music STATIC native/music_disc.cpp)
target_compile_features(vib-music PUBLIC cxx_std_17)
target_include_directories(vib-music PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/native")
target_link_libraries(vib-music PUBLIC SDL3::SDL3-static)
target_link_libraries(psx-runtime PRIVATE vib-music)
target_sources(psx-runtime PRIVATE native/vib_menu.cpp)
option(VIB_BUILD_TOOLS "Build standalone music/disc diagnostic tools" OFF)
if(VIB_BUILD_TOOLS)
add_executable(vib-music-tool native/music_tool.cpp)
target_link_libraries(vib-music-tool PRIVATE vib-music)
add_executable(vib-disc-check native/disc_check.cpp
    "${PSXRECOMP_ROOT}/runtime/src/iso_reader.cpp"
    "${PSXRECOMP_ROOT}/runtime/src/cue_sheet.cpp")
target_compile_features(vib-disc-check PRIVATE cxx_std_17)
target_include_directories(vib-disc-check PRIVATE "${PSXRECOMP_ROOT}/runtime/include"
    "${PSXRECOMP_ROOT}/recompiler/include")
target_link_libraries(vib-disc-check PRIVATE chdr-static)
endif()

# Seed native resolution; keep user choices once a state file exists.
if(NOT EXISTS "${CMAKE_CURRENT_BINARY_DIR}/mods/state.toml")
    file(MAKE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/mods")
    configure_file("config/native-mod-state.toml"
        "${CMAKE_CURRENT_BINARY_DIR}/mods/state.toml" COPYONLY)
endif()

# Stage runtime configs next to the exe for direct build/ launches. Only copy
# files that exist — never fail POST_BUILD when game_options.toml is absent.
foreach(_PSX_RUNTIME_CONFIG game.toml game_options.toml)
    set(_VIB_CONFIG_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/${_PSX_RUNTIME_CONFIG}")
    if(_PSX_RUNTIME_CONFIG STREQUAL "game.toml" AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/game.local.toml")
        set(_VIB_CONFIG_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/game.local.toml")
    endif()
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/${_PSX_RUNTIME_CONFIG}")
        add_custom_command(TARGET psx-runtime POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "${_VIB_CONFIG_SOURCE}"
                "$<TARGET_FILE_DIR:psx-runtime>/${_PSX_RUNTIME_CONFIG}"
            COMMENT "Staging ${_PSX_RUNTIME_CONFIG}"
            VERBATIM)
    endif()
endforeach()
