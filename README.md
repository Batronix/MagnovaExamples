# SCPI Examples for Test & Measurement Equipment

A collection of Python examples demonstrating how to control and interact with test and measurement equipment using SCPI (Standard Commands for Programmable Instruments) commands.

## Overview

This repository contains practical examples for automating and controlling various test and measurement instruments. Currently focused on oscilloscope control, the examples demonstrate common tasks and best practices for instrument automation.

## Project Structure

```
SCPIExamples/
├── Oscilloscopes/
│   ├── AutoSet/           # Intelligent auto-setup functionality
│   ├── PlotWaveform/      # Waveform capture and visualization
│   ├── PlotFFT/           # FFT analysis and visualization
│   ├── Simple/            # Basic PyVISA usage example
│   └── RESTAPI/          # Modern REST API control
```

## Examples

### Oscilloscopes

1. [**AutoSet Tool**](./Oscilloscopes/AutoSet/)
   - Intelligent auto-setup for oscilloscope channels
   - Automatic scale optimization
   - Multi-channel support
   - Precise measurements

2. [**Waveform Plotting Tool**](./Oscilloscopes/PlotWaveform/)
   - USB and network connection support
   - Raw and HiSLIP protocol compatibility
   - Waveform capture and visualization
   - Metadata extraction

3. [**FFT Analysis Tool**](./Oscilloscopes/PlotFFT/)
   - Frequency domain analysis
   - Real-time FFT capture
   - Frequency spectrum visualization
   - Bin frequency and magnitude data

4. [**Simple PyVISA Example**](./Oscilloscopes/Simple/)
   - Basic PyVISA usage demonstration
   - Simple SCPI command examples
   - Clear learning-focused implementation
   - Minimal error handling

5. [**REST API Control**](./Oscilloscopes/RESTAPI/)
   - Modern web-based control interface
   - No VISA drivers required
   - JSON-based command structure
   - Async operation support

## Requirements

- Python 3.6+
- PyVISA
- Additional requirements specified in individual example directories

## Getting Started

1. Clone this repository
2. Install the required dependencies for the example you want to run
3. Navigate to the specific example directory
4. Follow the README instructions in each example directory

## Contributing

Feel free to contribute additional examples or improvements to existing ones. Please follow the existing code structure and documentation patterns.

## License

This project is available for use and modification. Please check individual examples for specific licensing information.

## Last Updated

2024-12-16
