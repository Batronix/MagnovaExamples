#!/usr/bin/env python
"""
REST API version of the waveform test that uses HTTP POST requests instead of VISA commands.
Implements the same functionality as magnova_waveform_test.py but using the REST API interface.
"""

import time
import logging
import requests
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OscilloscopeWaveformREST:
    def __init__(self, url: str, port: int = 8080):
        """
        Initialize the waveform analyzer using REST API connection.

        Args:
            url: IP address of the oscilloscope
            port: Port number for REST API (default 8080)
        """
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.url = url
        self.port = port
        self.base_url = f"http://{url}:{port}/scpi"
        self._test_connection()

    def _test_connection(self):
        """Test connection to oscilloscope by querying identity."""
        try:
            response = requests.post(self.base_url, json="*IDN?")
            response.raise_for_status()
            device_id = response.json()
            self.logger.info(f"Connected to: {device_id}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to oscilloscope: {str(e)}")

    def _send_command(self, command: str) -> Any:
        """Send a SCPI command via REST API."""
        response = requests.post(self.base_url, json=command)
        response.raise_for_status()
        return response.json() if response.text else None

    def get_waveform_data(self, channel: int, data_length: str = "ALL", 
                         data_transfer_type: str = "RAW", 
                         number_of_sample_points: int = 1000000) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Acquire waveform data from specified channel using REST API.
        
        Args:
            channel: Oscilloscope channel number (1-4)
            data_length: Amount of data to acquire ('ALL' for complete waveform)
            data_transfer_type: Data format ('RAW' for binary or 'ASCII' for text)
            number_of_sample_points: Number of samples to acquire
        
        Returns:
            Tuple containing waveform data array and metadata dictionary
        """
        # Stop acquisition
        self._send_command("STOP")
        
        # Configure channel and trigger settings
        self._send_command(f"CHAN{channel}:STATe 1")
        self._send_command(f"TRIGger:EDGe:SOURce CHAN{channel}")
        
        # Disable other channels
        for i in range(1, 5):
            if i != channel:
                self._send_command(f"CHAN{i}:STATe 0")
        
        # Enable auto-trigger and configure acquisition
        self._send_command("AUTO 1")
        self._send_command(f"CHAN{channel}:DATa:TYPE {data_transfer_type}")
        self._send_command(f"ACQUire:MDEPth {number_of_sample_points*2}")
        
        memory_depth = self._send_command("ACQuire:MDEPth?")
        self.logger.info(f"Memory Depth: {memory_depth}")
        
        # Start acquisition and wait
        self._send_command("RUN")
        start_time = time.time()
        self._send_command("SEQUence:WAIT 10")
        self.logger.info(f"Sequence wait time: {time.time() - start_time:.5f} seconds.")
        
        # Request waveform data
        start_time = time.time()
        data = self._send_command(f"CHAN{channel}:DATa:PACK? {data_length}, {data_transfer_type}")
        self.logger.info(f"Data Transfer Time: {time.time() - start_time:.5f} seconds.")
        
        # Extract waveform data and metadata
        samples = np.array(data["Samples"])
        metadata = {
            "TimeDelta": data["TimeDelta"],
            "StartTime": data["StartTime"],
            "EndTime": data["EndTime"],
            "SampleCount": data["SampleCount"]
        }
        
        self.logger.info(f"Waveform data length: {len(samples)}")
        if len(samples) == number_of_sample_points:
            self.logger.info("Waveform data received correctly.")
        else:
            self.logger.info("Waveform data received incorrectly.")
            
        return samples, metadata

def main():
    # Example usage
    scope = OscilloscopeWaveformREST("192.168.10.121")
    samples, metadata = scope.get_waveform_data(channel=1)
    
    # Create time base and plot
    x = np.linspace(metadata["StartTime"], metadata["EndTime"], 
                    len(samples), endpoint=True)
    plt.plot(x, samples)
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude (V)')
    plt.title('Waveform Data')
    plt.show()
    

if __name__ == "__main__":
    main()
