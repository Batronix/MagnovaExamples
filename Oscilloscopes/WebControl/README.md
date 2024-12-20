# Web-Based Oscilloscope Control Interface

A modern web application for controlling oscilloscopes using their REST API interface. This implementation provides a user-friendly way to control and visualize oscilloscope data directly from your web browser.

## Features

- **Real-time Waveform Display**
  - Live waveform visualization using Plotly.js
  - Support for continuous acquisition mode
  - Single-shot acquisition capability

- **Interactive Controls**
  - Time scale adjustment with intuitive round slider
  - Memory depth configuration
  - Run/Stop/Single acquisition modes
  - Connection management

- **Modern UI**
  - Responsive design using Bootstrap
  - Clean and intuitive interface
  - Real-time status updates
  - Error handling and user feedback

## Architecture

- **Frontend**
  - HTML5 with Bootstrap 5 for responsive layout
  - JavaScript modules for different functionalities:
    - `acquisition.js`: Handles waveform acquisition and display
    - `connection.js`: Manages oscilloscope connection
    - `timeScale.js`: Controls time base settings
    - `memoryDepth.js`: Handles memory depth configuration
    - `main.js`: Initializes and coordinates all components

- **Backend**
  - FastAPI Python server
  - RESTful API endpoints
  - SCPI command proxy for direct oscilloscope communication

## Requirements

- Python 3.6+
- FastAPI
- Uvicorn
- Requests
- Modern web browser with JavaScript enabled

## Installation

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the web server:
   ```bash
   python main.py
   ```

3. Open your web browser and navigate to:
   ```
   http://localhost:8000
   ```

## Usage

1. **Connect to Oscilloscope**
   - Enter the oscilloscope's IP address
   - Default port is 8080 for REST API
   - Click "Connect" to establish connection

2. **View Waveforms**
   - Use "Single" for one-shot acquisition
   - Use "Run" for continuous acquisition
   - Adjust time scale using the round slider
   - Configure memory depth as needed

3. **Adjust Settings**
   - Time scale: 1µs/div to 1s/div
   - Memory depth: Various options based on oscilloscope model
   - Enable/disable continuous acquisition mode

## Implementation Details

- Direct SCPI command communication via REST API
- Proxy server to handle CORS and provide unified interface
- Modular JavaScript code for maintainability
- Error handling for both frontend and backend
- Real-time updates without page reload

## Notes

- Network connection required between server and oscilloscope
- Modern browser recommended for best experience
