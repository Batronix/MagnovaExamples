#!/usr/bin/env python
"""
Simple instrument commands and queries using USBTMC
In this example the instruments unique identifier is queried, the first analog channel is enabled and the acquisition is started.
"""

import pyvisa
 
# Open the instrument using a USBTMC connection
rm = pyvisa.ResourceManager()
instr = rm.open_resource('USB0::0x19B2::0x0030::[YOUR_SERIAL_NUMBER]::INSTR')
 
# Query the unique identifier
print(instr.query('*IDN?'))
 
# Enable the first analog channel
instr.write("CHAN1:STAT ON")
 
# Start the acquisition
instr.write("RUN")