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
