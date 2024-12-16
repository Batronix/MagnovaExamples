# Oscilloscope FFT Analysis Tool

This Python script provides functionality to capture and plot FFT (Fast Fourier Transform) data from a Batronix oscilloscope. It supports both USB and network connections and can analyze frequency components from any channel.

## Features

- Connect to oscilloscope via USB or network (TCP/IP)
- Support for both raw and HiSLIP protocols
- Automatic device detection for USB connections
- FFT data capture and visualization
- Metadata extraction (bin frequency, stop frequency, bin count)
- Frequency domain analysis

## Requirements

- Python 3.6+
- pyvisa
- numpy
- matplotlib
- struct (standard library)

## Usage

Basic usage with USB connection:
```python
from plot_fft import OscilloscopeFFT

# Connect and plot FFT for channel 1
fft_analyzer = OscilloscopeFFT()
fft_analyzer.plot_fft(channel=1)
```

Network connection:
```python
# Connect via network
fft_analyzer = OscilloscopeFFT(url="192.168.1.100", protocol="raw")
fft_analyzer.plot_fft(channel=1)
```

## Class Parameters

### OscilloscopeFFT

- `url`: IP address of the oscilloscope (optional, for network connection)
- `protocol`: Communication protocol ('raw' or 'hislip', default: 'raw')

### Methods

#### plot_fft(channel)
- `channel`: Oscilloscope channel number (1-4)

## Output

The script generates a plot showing:
- Frequency spectrum (X-axis in Hz)
- Amplitude in dB (Y-axis)
- Grid for easy reading
- Channel identification in title
