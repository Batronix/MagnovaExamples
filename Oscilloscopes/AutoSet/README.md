# Oscilloscope AutoSet Tool

This Python script provides an intelligent auto-setup functionality for oscilloscope channels. It automatically adjusts vertical and horizontal scales to optimize the display of waveforms across multiple channels.

## Features

- Automatic channel detection and setup
- Smart vertical scale optimization
- Horizontal alignment based on signal frequency
- Support for up to 4 channels
- Precise measurements (Vmid, Vpp, frequency)
- Logging system for debugging and monitoring

## Requirements

- Python 3.6+
- pyvisa
- decimal (standard library)
- logging (standard library)
- typing (standard library)
- dataclasses (standard library)

## Classes

### OscilloscopeChannel
Handles individual channel operations including:
- Channel enabling/disabling
- Scale and offset adjustment
- Measurement collection
- Signal optimization

### OscilloscopeAutoset
Main class that manages:
- Device connection (USB/Network)
- Multi-channel coordination
- Automatic signal optimization
- Horizontal and vertical alignment

## Usage

Basic usage:
```python
from scope_autoset import OscilloscopeAutoset

# Connect and autoset via USB
autoset = OscilloscopeAutoset()
autoset.autoset()

# Or connect via network
autoset = OscilloscopeAutoset("192.168.10.121")
autoset.autoset()
```

## Measurement Process

1. Connects to the oscilloscope
2. Enables and initializes channels
3. Collects initial measurements
4. Optimizes vertical scale for each channel
5. Aligns channels horizontally based on frequency
6. Fine-tunes vertical positioning

## Error Handling

The script includes comprehensive error handling and logging for:
- Connection issues
- Measurement failures
- Timeout conditions
- Invalid measurements

## Logging

The script uses Python's logging system with:
- Formatted timestamps
- Different log levels (INFO, DEBUG, WARNING, ERROR)
- Channel-specific logging
- Operation tracking
