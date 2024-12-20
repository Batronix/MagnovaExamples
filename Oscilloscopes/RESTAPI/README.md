# REST API Oscilloscope Control

This example demonstrates how to control an oscilloscope using its REST API interface. It provides a modern web-based approach to instrument control without requiring VISA drivers.

## Features

- HTTP/HTTPS communication
- JSON-based command structure
- No VISA drivers required
- Async operation support
- Modern API design patterns

## Requirements

- Python 3.6+
- requests

## Usage

Basic usage:
```python
python rest_api.py
```

## Examples

### Basic REST API
```python
python rest_api.py
```

### Waveform Acquisition
```python
python rest_waveform_test.py
```
The waveform test example demonstrates how to:
- Acquire waveform data using REST API
- Configure oscilloscope settings (timebase, channels)
- Download and plot waveform data
- Process measurement data using numpy
- Visualize results with matplotlib

## Benefits

- Platform independent
- No driver installation needed
- Easy integration with web services
- Modern programming paradigms
- Suitable for remote operation

This example is ideal for modern applications requiring web-based instrument control or integration with cloud services.
