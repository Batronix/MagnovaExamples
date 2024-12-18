#!/usr/bin/env python
"""
Oscilloscope FFT Plotting Tool

This script connects to a Batronix oscilloscope via USB or network connection and plots
FFT data from a specified channel using matplotlib.
"""

import time
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pyvisa
import logging
import struct

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OscilloscopeFFT:
    def __init__(self, url: Optional[str] = None, protocol: str = "raw"):
        """
        Initialize the FFT analyzer with connection to oscilloscope.

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

    def get_fft_data(self, channel: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Capture FFT data from the specified channel.

        Args:
            channel: Oscilloscope channel number (1-4)

        Returns:
            Tuple of frequency and magnitude arrays
        """
        self.device.write("FFT1:STATe 1")
        # Select channel
        self.device.write(f"FFT1:SOURce CHANnel{channel}")
        # Ensure single acquisition mode
        self.device.write("RUN")
        time.sleep(0.5)  # Wait for acquisition

        # Get FFT data
        fft_data = self.device.query_binary_values("FFT1:DATA:PACKed?", datatype='B')
        # Define the struct format for the 12-byte metadata
        metadata_format = 'ffI' # Corresponds to BinFrequency, StopFrequency and BinCount
        metadata_size = struct.calcsize(metadata_format)
        # Extract the first 12 bytes of metadata from the data
        metadata_bytes = bytes(fft_data[:metadata_size]) # Convert the metadata part to a byte string
        metadata = struct.unpack(metadata_format, metadata_bytes)
        
        # Assign metadata to meaningful variable names
        BinFrequency, StopFrequency, BinCount = metadata
        
        # Print parsed metadata
        print(f"Metadata")
        print(f"  BinFrequency   = {BinFrequency}")
        print(f"  StopFrequency  = {StopFrequency}")
        print(f"  BinCount       = {BinCount}")
        
        # Extract bins starting from byte 13 onwards (after metadata) and convert into 32-bit floats
        bins_bytes = fft_data[metadata_size:]
        bins = np.frombuffer(bytes(bins_bytes), dtype=np.float32)
        
        # Create the frequency base
        frequency_base = np.linspace(0, StopFrequency, len(bins), endpoint=True)
        
        return frequency_base, bins

    def plot_fft(self, channel: int) -> None:
        """
        Configure, capture and plot FFT data from a channel.

        Args:
            channel: Oscilloscope channel number (1-4)
        """
        try:
            freq, magnitude = self.get_fft_data(channel)
            
            if len(freq) == 0:
                return

            # Plot FFT
            plt.figure(figsize=(12, 6))
            plt.plot(freq, magnitude)
            plt.grid(True)
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Amplitude (dB)')
            plt.title(f'Channel {channel} FFT')
            plt.show()

        except Exception as e:
            self.logger.error(f"Error plotting FFT: {e}")


def main():
    """Main function to demonstrate FFT plotting."""
    try:
        fft_analyzer = OscilloscopeFFT(url="192.168.10.121", protocol="raw")
        fft_analyzer.plot_fft(channel=1)
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main()