cmake_minimum_required(VERSION 3.10)
project(oscilloscope_waveform)

# Specify C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find NI-VISA
if(WIN32)
    # Typical installation paths for NI-VISA on Windows
    set(VISA_ROOT "C:/Program Files/IVI Foundation/VISA")
    set(VISA_INCLUDE_DIRS "${VISA_ROOT}/Win64/Include")
    set(VISA_LIBRARIES "${VISA_ROOT}/Win64/Lib_x64/msc/visa32.lib")
endif()

# Add the executable
add_executable(oscilloscope_waveform
    main.cpp
    oscilloscope_waveform.cpp
)

# Include directories
target_include_directories(oscilloscope_waveform PRIVATE
    ${VISA_INCLUDE_DIRS}
    ${CMAKE_SOURCE_DIR}
)

# Link libraries
target_link_libraries(oscilloscope_waveform PRIVATE
    ${VISA_LIBRARIES}
)
