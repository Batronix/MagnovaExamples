# Simple PyVISA Example

This example demonstrates the basic usage of PyVISA to communicate with an oscilloscope. It provides a simple, straightforward implementation for those getting started with instrument control.

## Features

- Basic PyVISA connection setup
- Simple SCPI command examples
- USB and network connection support
- Minimal error handling
- Clear code comments for learning

## Requirements

- Python 3.6+
- pyvisa

## Usage

Basic usage with USB connection:
```python
python simple_visa.py
```

## Learning Points

- How to establish a connection
- Basic SCPI command structure
- Reading and writing to instruments
- Query vs Write operations

This example serves as a starting point for those new to instrument control with Python and SCPI commands.

## C++ Example

A C++ version of the same example is also provided, demonstrating how to use the NI-VISA C/C++ library for instrument control.

### Features (C++)

- Uses industry-standard NI-VISA library
- CMake build system for easy compilation
- Same SCPI commands as Python example
- Proper resource management and error handling

### Requirements (C++)

- CMake 3.10 or later
- Visual Studio with C++ support (or another C++ compiler)
- NI-VISA library installed

### Building the C++ Example

1. Create a build directory:
```bash
mkdir build
cd build
```

2. Configure with CMake:
```bash
cmake ../ -G "Visual Studio 17 2022" -A x64
```

3. Build the project:
```bash
cmake --build . --config Release
```

The executable will be created in `build/Release/simple_visa.exe`

### Usage (C++)

Before running the program:
1. Replace `[YOUR_SERIAL_NUMBER]` in the code with your device's serial number
2. Ensure your SCPI device is connected via USB
3. Run the executable:
```bash
./build/Release/simple_visa.exe
```

### Learning Points (C++)

- NI-VISA library usage in C++
- VISA session management
- Error handling in instrument communication
- Resource cleanup in C++
