# Oscilloscope Waveform Plotting Tool

This Python script provides functionality to capture and plot waveform data from a Batronix oscilloscope. It supports both USB and network connections and can visualize waveform data from any channel.

## Features

- Connect to oscilloscope via USB or network (TCP/IP)
- Support for both raw and HiSLIP protocols
- Automatic device detection for USB connections
- Waveform data capture and visualization
- Metadata extraction and display
- Configurable vertical scale and offset

## Requirements

- Python 3.6+
- pyvisa
- numpy
- matplotlib

## Usage

Basic usage with USB connection:
```python
python plot_waveform.py
```

## Function Parameters

- `url`: IP address of the oscilloscope (optional, for network connection)
- `channel`: Oscilloscope channel number (1-4, default: 1)
- `protocol`: Communication protocol ('raw' or 'hislip', default: 'raw')

## Output

The script will:
1. Connect to the oscilloscope
2. Capture waveform data
3. Display metadata information
4. Plot the waveform with time on x-axis and voltage on y-axis

## Error Handling

The script includes error handling for:
- Connection failures
- Data capture errors
- Metadata parsing issues
- Waveform processing errors

## C++ Implementation

A C++ version of the waveform plotting tool is also provided, offering the same functionality with native C++ performance.

### Additional Requirements for C++

- CMake 3.10 or later
- C++17 compatible compiler
- NI-VISA library
- Python 3.x with NumPy (for matplotlib-cpp)
- matplotlib-cpp (header-only library)

### Building the C++ Version

1. Install the NI-VISA library from National Instruments
2. Create a build directory:
```bash
mkdir build
cd build
```

3. Configure with CMake:
```bash
cmake ../ -G "Visual Studio 17 2022" -A x64
```

4. Build the project:
```bash
cmake --build . --config Release
```

The executable will be created in `build/Release/oscilloscope_waveform.exe`

### Using the C++ Version

The C++ implementation provides the same features as the Python version:
- USB and network connection support
- Raw and HiSLIP protocol support
- Automatic device detection for USB
- Waveform capture and visualization
- Metadata parsing and display

Basic usage:
```cpp
// Using network connection
OscilloscopeWaveform waveform_analyzer("192.168.1.100", "raw");
waveform_analyzer.plotWaveform(1, "ALL", "RAW");

// Using USB connection (auto-detect)
OscilloscopeWaveform waveform_analyzer;
waveform_analyzer.plotWaveform(1);
```

### Code Organization

- `oscilloscope_waveform.hpp`: Class declaration and interface
- `oscilloscope_waveform.cpp`: Implementation of the waveform analyzer
- `main.cpp`: Example usage
- `CMakeLists.txt`: Build configuration

The C++ implementation follows modern C++ practices with RAII for resource management, exception handling for error cases, and strong type safety.
