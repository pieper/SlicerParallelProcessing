cmake_minimum_required(VERSION 3.13.4)

project(ParallelProcessing)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/pieper/SlicerParallelProcessing")
set(EXTENSION_CATEGORY "Utilities")
set(EXTENSION_CONTRIBUTORS "Steve Pieper (Isomics, Inc.)")
set(EXTENSION_DESCRIPTION "Manage helper processes to perform background tasks in parallel.")
set(EXTENSION_ICONURL "https://github.com/pieper/SlicerParallelProcessing/raw/master/ParallelProcessing.png")
set(EXTENSION_SCREENSHOTURLS "https://camo.githubusercontent.com/f32d3911615ff1ff73af2e453fb8d1233f43a831339317618229a6e622859a01/687474703a2f2f696d672e796f75747562652e636f6d2f76692f6c6f3830346352446d70512f302e6a7067")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(Processes)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
