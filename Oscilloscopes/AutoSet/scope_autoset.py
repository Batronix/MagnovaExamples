#!/usr/bin/env python

"""
Oscilloscope Auto Set Tool

This script connects to a Batronix oscilloscope via USB or network connection and 
runs an intelligent auto-setup process for all oscilloscope channels.
"""

import pyvisa
import struct
import time
import logging
from typing import Optional
from dataclasses import dataclass

import decimal

# create a new context for this task
ctx = decimal.Context()

# 20 digits should be enough for everyone :D
ctx.prec = 20

def float_to_str(f):
    """
    Convert the given float to a string,
    without resorting to scientific notation
    """
    d1 = ctx.create_decimal(repr(f))
    return format(d1, 'f')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ChannelMeasurements:
    vmid: float
    vpp: float
    freq: float
    scale: float

class OscilloscopeChannel:
    def __init__(self, number: int, device, vertical_divisions: int = 8):
        self.number = number
        self.device = device
        self.vertical_divisions = vertical_divisions
        self.logger = logging.getLogger(f"{self.__class__.__name__}.Channel{number}")
        
    def enable_channel(self, enable: bool = True):
        """Enable or disable the channel"""
        self.device.write(f"CHANnel{self.number}:STATe {1 if enable else 0}")

    def set_initial_settings(self):
        """Set initial scale and timebase"""
        self.set_scale_and_offset(6.0, 0)  # 6V/div, 0V offset
        
    def set_scale_and_offset(self, volts_per_div: float, offset: float):
        """Set vertical scale and offset for the channel"""
        self.device.write(f"CHANnel{self.number}:SCALe {volts_per_div}")
        self.device.write(f"CHANnel{self.number}:OFFSet {offset}")
        time.sleep(0.1)  # Give scope time to settle

    def _wait_for_measurements(self, mtype: str, min_count: int = 5, timeout: float = 4.0) -> bool:
        """Wait for enough measurement samples to be collected"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            self.device.write(f"MEASurement:{mtype}:COUNt? CHAN{self.number}")
            count = int(float(self.device.read().strip()))
            if count >= min_count:
                return True
            time.sleep(0.1)
        return False

    def _get_divisor(self) -> float:
        """Get the probe divisor for this channel"""
        self.device.write(f"CHANnel{self.number}:DIVisor?")
        divisor = float(self.device.read().strip())
        return divisor

    def get_measurements(self) -> tuple[float, float, float]:
        """Get Vmid, Vpp, and frequency measurements"""
        self.logger.debug(f"Getting measurements for channel {self.number}")
        try:
            # Get probe divisor
            divisor = self._get_divisor()
            
            # Setup measurements
            self.device.write(f"MEASurement:VMID:ADD CHAN{self.number}")
            self.device.write(f"MEASurement:VPP:ADD CHAN{self.number}")
            self.device.write(f"MEASurement:HFREQ:ADD CHAN{self.number}")
            
            # Wait for measurements to stabilize
            measurements_ready = all(
                self._wait_for_measurements(mtype) 
                for mtype in ["VMID", "VPP", "HFREQ"]
            )
            
            if not measurements_ready:
                self.logger.warning(f"Timeout waiting for measurements on channel {self.number}")
            
            # Read measurements and apply divisor to voltage measurements
            vmid = self._read_measurement("VMID") * divisor
            vpp = self._read_measurement("VPP") * divisor
            freq = self._read_measurement("HFREQ")
            
            self.logger.info(f"Channel {self.number} measurements - Vmid: {vmid}V, Vpp: {vpp}V, Freq: {freq}Hz")
            return vmid, vpp, freq
        finally:
            # Cleanup measurements
            self.device.write(f"MEASurement:VMID:REMove CHAN{self.number}")
            self.device.write(f"MEASurement:VPP:REMove CHAN{self.number}")
            self.device.write(f"MEASurement:HFREQ:REMove CHAN{self.number}")
    
    def _read_measurement(self, mtype: str) -> float:
        """Read a specific measurement value"""
        self.device.write(f"MEASurement:{mtype}:AVERage? CHAN{self.number}")
        value = self.device.read()
        return float(value)

class OscilloscopeAutoset:
    def __init__(self, device_url: Optional[str] = None):
        self.logger = logging.getLogger(f"{self.__class__.__name__}.Autoset")
        self.logger.info("Initializing OscilloscopeAutoset")
        self.device = self._connect(device_url)
        self.channels = [OscilloscopeChannel(i, self.device) for i in range(1, 5)]
        self.measurements = {}  # Store final measurements for each channel
        self.vertical_divisions = 8
        self.horizontal_divisions = 12
        self.vertical_scales = [6.0, 2.0, 1.0, 0.5, 0.2, 0.1, 0.05]
    
    def _connect(self, url: Optional[str]) -> pyvisa.Resource:
        """Connect to oscilloscope via USB or network"""
        self.logger.info("Connecting to oscilloscope...")
        rm = pyvisa.ResourceManager()
        self.logger.debug(f"Available resources: {rm.list_resources()}")
        
        if url:
            device = rm.open_resource(f"TCPIP::{url}::5025::SOCKET")
            device.read_termination = '\n'
        else:
            for resource in rm.list_resources():
                try:
                    device = rm.open_resource(resource)
                    idn = device.query("*IDN?")
                    if "Batronix" in idn:
                        self.logger.info(f"Connected to: {idn.strip()}")
                        break
                except Exception as e:
                    self.logger.debug(f"Failed to connect to {resource}: {str(e)}")
            else:
                raise ConnectionError("No oscilloscope found")
        
        device.timeout = 5000
        return device

    def _calculate_horizontal_scale(self, freq: float) -> float:
        """Calculate optimal horizontal scale to show 1.25 periods"""
        if freq <= 0:
            return 1e-3  # Default to 1ms/div
            
        # Calculate ideal time/div
        period = 1.0 / freq
        ideal_time_per_div = (period * 1.25) / self.horizontal_divisions
        
        # Standard oscilloscope time/div values (in seconds)
        standard_times = [
            1e-9, 2e-9, 5e-9,  # ns
            1e-8, 2e-8, 5e-8,
            1e-7, 2e-7, 5e-7,
            1e-6, 2e-6, 5e-6,  # µs
            1e-5, 2e-5, 5e-5,
            1e-4, 2e-4, 5e-4,
            1e-3, 2e-3, 5e-3,  # ms
            1e-2, 2e-2, 5e-2,
            1e-1, 2e-1, 5e-1,
            1, 2, 5,  # s
            10, 20, 50
        ]
        
        # Find the closest standard value that shows at least 1.25 periods
        for time_per_div in standard_times:
            total_time = time_per_div * self.horizontal_divisions
            periods_shown = total_time * freq
            if periods_shown >= 1.25:
                return time_per_div
                
        return standard_times[-1]  # Use maximum if frequency is very low

    def _get_signal_center(self, vmid: float, vpp: float) -> float:
        """Calculate appropriate center point based on Vmid and Vpp
        
        If Vmid is close to Vpp/2 (within 10% of Vpp), use Vmid.
        Otherwise use Vpp/2 as it's likely more appropriate for centering.
        """
        vpp_half = vpp / 2
        if abs(vmid - vpp_half) > (vpp * 0.1):  # If Vmid differs from Vpp/2 by more than 10% of Vpp
            return vpp_half
        return vmid

    def _align_channels_horizontally(self):
        """Align channels horizontally based on the main channel (highest Vpp)"""
        # Get list of enabled channels with measurements
        enabled_channels = [(i, m) for i, m in self.measurements.items() if m is not None]
        if not enabled_channels:
            self.logger.warning("No enabled channels with valid measurements found")
            return
            
        # Find the channel with highest Vpp
        main_channel_idx, main_measurements = max(enabled_channels, key=lambda x: x[1].vpp)
        
        # Calculate and set the horizontal scale
        time_per_div = self._calculate_horizontal_scale(main_measurements.freq)
        self.device.write(f"TIMe:SCALe {float_to_str(time_per_div)}")
        self.logger.info(f"Horizontal scale set to {time_per_div}s/div")
        self.logger.info(f"For Channel{main_channel_idx} - Vmid: {main_measurements.vmid}V, "
                        f"Vpp: {main_measurements.vpp}V, Freq: {main_measurements.freq}Hz")
        
        # Set trigger level and source
        trigger_level = self._get_signal_center(main_measurements.vmid, main_measurements.vpp)
        self.device.write(f"TRIGger:EDGe:SOURce CHAN{main_channel_idx}")
        self.device.write(f"TRIGger:EDGe:LEVel {float_to_str(trigger_level)}")
        self.logger.info(f"Trigger level set to {trigger_level}V, "
                        f"trigger source set to Channel{main_channel_idx}")

    def _align_channels_vertically(self):
        """Align channels vertically on screen"""
        # Get list of enabled channels with measurements
        enabled_channels = [(i, m) for i, m in self.measurements.items() if m is not None]
        if not enabled_channels:
            self.logger.warning("No enabled channels with valid measurements found")
            return
            
        available_divisions = self.vertical_divisions / len(enabled_channels)
        positions = [((i - (len(enabled_channels) - 1) / 2) / len(enabled_channels)) * self.vertical_divisions for i in range(len(enabled_channels)-1, -1, -1)]        
        
        # Set position and calculate optimal scale for each channel
        for (channel_num, measurements), position in zip(enabled_channels, positions):
            # Calculate ideal scale based on vpp and available divisions
            ideal_scale = measurements.vpp / available_divisions
            
            # Find the next larger standard scale
            scale = next(s for s in self.vertical_scales[::-1] if s >= ideal_scale)
            
            signal_center = self._get_signal_center(measurements.vmid, measurements.vpp)
            new_offset = (position * scale) - signal_center
            self.channels[channel_num-1].set_scale_and_offset(scale, new_offset)

    def _optimize_channel_scale(self, channel: OscilloscopeChannel) -> Optional[ChannelMeasurements]:
        """Get accurate measurements by using decreasing scales"""        
        # Initial settings
        channel.set_initial_settings()
        time.sleep(0.2)
        
        # Initial measurements
        vmid, vpp, freq = channel.get_measurements()
        
        # Disable channel if signal is negligible (less than 100mV peak-to-peak)
        if vpp < 0.1:
            self.logger.info(f"Channel {channel.number} disabled due to negligible signal (Vpp={vpp}V)")
            channel.enable_channel(False)
            return None
            
        # Center the signal with initial measurements
        channel.set_scale_and_offset(self.vertical_scales[0], -vmid)
        time.sleep(0.2)
        
        # Get measurements using decreasing scales for accuracy
        prev_vmid, prev_vpp, prev_freq = channel.get_measurements()
        current_scale = self.vertical_scales[0]
        
        # Check if initial centered measurement is too low
        if prev_vpp < 0.1:
            self.logger.info(f"Channel {channel.number} disabled due to negligible signal after centering (Vpp={prev_vpp}V)")
            channel.enable_channel(False)
            return None
        for i in range(1, len(self.vertical_scales)):
            next_scale = next(scale for scale in self.vertical_scales[::-1] if scale * self.vertical_divisions > prev_vpp)
            if next_scale == current_scale:
                break
            self.logger.info(f"Next Scale: {next_scale}V/div")
                
            # Try the next smaller scale
            channel.set_scale_and_offset(next_scale, -prev_vmid)
            time.sleep(0.2)
            
            # Get new measurements
            new_vmid, new_vpp, new_freq = channel.get_measurements()
            
            # Check if new measurement is too low
            if new_vpp < 0.1:
                self.logger.info(f"Channel {channel.number} disabled due to negligible signal at {next_scale}V/div (Vpp={new_vpp}V)")
                channel.enable_channel(False)
                return None
            
            # Update previous measurements and scale
            prev_vmid, prev_vpp, prev_freq = new_vmid, new_vpp, new_freq
            current_scale = next_scale
            
        return ChannelMeasurements(prev_vmid, prev_vpp, prev_freq, current_scale)

    def autoset(self):
        """Perform autoset on all channels"""
        self.logger.info("Starting autoset process")
        self.device.write("*RST")
        
        # Enable all channels
        for channel in self.channels:
            channel.enable_channel(True)
            time.sleep(0.1)
        
        # Set timebase
        self.device.write("TIMebase:SCALe 0.02")  # 20ms/div
        self.device.write("ACQuire:MODE PDETect")
        self.device.write("ACQuire:TEXPansion 0")
        
        # Optimize each channel
        for channel in self.channels:
            self.logger.info(f"Optimizing channel {channel.number}")
            measurements = self._optimize_channel_scale(channel)
            self.measurements[channel.number] = measurements
        
        # Align channels horizontally
        self._align_channels_horizontally()
        
        # Align channels vertically
        self._align_channels_vertically()
        self.logger.info("Autoset process completed")

def main():
    try:
        scope = OscilloscopeAutoset()
        scope.autoset()
    except Exception as e:
        logger.error(f"Autoset failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
