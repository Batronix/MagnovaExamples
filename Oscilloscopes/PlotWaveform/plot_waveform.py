#!/usr/bin/env python
"""
Oscilloscope Waveform Plotting Tool

This script connects to a Batronix oscilloscope via USB or network connection and plots
waveform data from a specified channel using matplotlib.
"""

import struct
import time
from typing import Optional, Dict, Any, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pyvisa
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OscilloscopeWaveform:
    def __init__(self, url: Optional[str] = None, protocol: str = "raw"):
        """
        Initialize the waveform analyzer with connection to oscilloscope.

        Args:
            url: IP address of the oscilloscope (for network connection)
            protocol: Communication protocol ('raw' or 'hislip')
        """
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.url = url
        self.protocol = protocol
        self.device = self._connect()

    def _connect(self) -> pyvisa.Resource:
        """Establish connection to the oscilloscope."""
        rm = pyvisa.ResourceManager()
        device = None
        connection = "eth" if self.url else "usb"

        # Establish connection based on connection type
        if self.url:
            if self.protocol == "hislip":
                device = rm.open_resource(f"TCPIP::{self.url}::hislip0::INSTR")
            elif self.protocol == "raw":
                device = rm.open_resource(f"TCPIP::{self.url}::5025::SOCKET")
                device.read_termination = '\n'
        else:
            # Search for Batronix device on USB
            devices = rm.list_resources()
            for d in devices:
                temp_device = rm.open_resource(d)
                d_idn = temp_device.query("*IDN?")
                if "Batronix" in d_idn:
                    device = temp_device
                    break

        if not device:
            raise ConnectionError("No oscilloscope found")

        device.timeout = 50000
        device_id = device.query("*IDN?")
        self.logger.info(f"Connected to: {device_id}")
        return device

    def get_waveform_data(self, channel: int, data_length: str = "ALL", 
                         data_transfer_type: str = "V") -> Tuple[np.ndarray, np.ndarray]:
        """
        Capture waveform data from the specified channel.

        Args:
            channel: Oscilloscope channel number (1-4)
            data_length: Data length to capture ("ALL" or specific length)
            data_transfer_type: Data transfer type ("V" for voltage)

        Returns:
            Tuple of time and voltage arrays
        """
        # Enable only selected channel
        self.device.write(f"CHAN{channel}:STATe 1")
        disabled_channels = [i for i in range(1, 5) if i != channel]
        for i in disabled_channels:
            self.device.write(f"CHAN{i}:STATe 0")

        self.device.write("RUN")
        # If the Memory Depth is too high this will take a long time so set it to 1M
        self.device.write("ACQUire:MDEPth 100000")
        memory_depth = self.device.query("ACQuire:MDEPth?")
        self.logger.info(f"Memory Depth: {memory_depth}")

        # Configure channel settings
        self.device.write(f"CHAN{channel}:DATa:TYPE {data_transfer_type}")
        data_cmd = f"CHAN{channel}:DATa:PACK? {data_length}, {data_transfer_type}"
        self.device.query("SEQUence:WAIT? 1")
        self.device.write("SINGLE")  # Single acquisition mode
        

        # Capture waveform data
        start_time = time.time()
        try:
            
            data = self.device.query_binary_values(data_cmd, datatype='B')
        except pyvisa.errors.VisaIOError:
            self.logger.error("Failed to capture waveform data")
            return np.array([]), np.array([])

        self.logger.info(f"Data capture time: {time.time() - start_time:.3f} seconds")

        if not data:
            self.logger.error("No data received")
            return np.array([]), np.array([])

        # Parse metadata and waveform data
        metadata = self._parse_metadata(data, data_transfer_type)
        if not metadata:
            return np.array([]), np.array([])

        waveform = self._extract_waveform(data, metadata, data_transfer_type)
        if len(waveform) == 0:
            return np.array([]), np.array([])

        # Create time base for x-axis
        time_values = np.linspace(metadata["StartTime"], metadata["EndTime"], 
                                len(waveform))

        return time_values, waveform

    def _parse_metadata(self, data: list, data_transfer_type: str) -> Optional[Dict[str, Any]]:
        """Parse the metadata header from the oscilloscope data."""
        metadata_format = 'fffIIffI' if data_transfer_type == "RAW" else 'fffI'
        metadata_size = struct.calcsize(metadata_format)
        
        try:
            metadata_bytes = bytes(data[:metadata_size])
            metadata_values = struct.unpack(metadata_format, metadata_bytes)
            
            metadata = {
                "TimeDelta": metadata_values[0],
                "StartTime": metadata_values[1],
                "EndTime": metadata_values[2],
            }
            
            if data_transfer_type == "RAW":
                metadata.update({
                    "SampleStart": metadata_values[3],
                    "SampleLength": metadata_values[4],
                    "VerticalStart": metadata_values[5],
                    "VerticalStep": metadata_values[6],
                    "SampleCount": metadata_values[7],
                })
            else:
                metadata["SampleCount"] = metadata_values[3]
            
            self.logger.info("\nMetadata:")
            for key, value in metadata.items():
                self.logger.info(f"  {key} = {value}")
                
            return metadata
        except Exception as e:
            self.logger.error(f"Error parsing metadata: {e}")
            return None

    def _extract_waveform(self, data: list, metadata: Dict[str, Any], 
                         data_transfer_type: str) -> np.ndarray:
        """Extract and process the waveform data."""
        metadata_format = 'fffIIffI' if data_transfer_type == "RAW" else 'fffI'
        metadata_size = struct.calcsize(metadata_format)
        
        try:
            waveform_data_bytes = data[metadata_size:]
            if data_transfer_type == "RAW":
                waveform_data = np.frombuffer(bytes(waveform_data_bytes), dtype=np.uint16)
                return metadata["VerticalStart"] + waveform_data * metadata["VerticalStep"]
            else:
                return np.frombuffer(bytes(waveform_data_bytes), dtype=np.float32)
        except Exception as e:
            self.logger.error(f"Error processing waveform data: {e}")
            return np.array([])

    def plot_waveform(self, channel: int, data_length: str = "ALL", 
                     data_transfer_type: str = "V") -> None:
        """
        Capture and plot waveform data from a channel.

        Args:
            channel: Oscilloscope channel number (1-4)
            data_length: Data length to capture ("ALL" or specific length)
            data_transfer_type: Data transfer type ("V" for voltage)
        """
        try:
            time_values, waveform = self.get_waveform_data(channel, data_length, data_transfer_type)
            
            if len(waveform) == 0:
                return

            # Plot the waveform
            plt.figure(figsize=(12, 6))
            plt.plot(time_values, waveform)
            plt.grid(True)
            plt.xlabel('Time (s)')
            plt.ylabel('Voltage (V)')
            plt.title(f'Channel {channel} Waveform')
            plt.show()

        except Exception as e:
            self.logger.error(f"Error plotting waveform: {e}")


def main():
    """Main function to demonstrate waveform plotting."""
    try:
        waveform_analyzer = OscilloscopeWaveform(url="192.168.10.121", protocol="raw")
        waveform_analyzer.plot_waveform(channel=1, data_transfer_type="RAW")
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main()