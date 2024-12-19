#!/usr/bin/env python
"""
Waveform Plot using the REST API
In this example waveform data is queried in the packed format using the default parameters ALL and V. 
Contrary to the SCPI-Raw example the metadata is stored in separate json fields.
"""

import matplotlib.pyplot as plt
import numpy as np
import requests
 
def main(url):
    # Query the packed data with a POST to the REST API and interpret the response as json
    data = requests.post(f"http://{url}:8080/scpi", json="CHAN1:DATA:PACK?").json()
    
    TimeDelta = data["TimeDelta"]
    StartTime = data["StartTime"]
    EndTime = data["EndTime"]
    SampleCount = data["SampleCount"]
    
    # Print metadata
    print(f"Metadata")
    print(f"  TimeDelta      = {TimeDelta}")
    print(f"  StartTime      = {StartTime}")
    print(f"  EndTime        = {EndTime}")
    print(f"  SampleCount    = {SampleCount}")
    
    # The waveform samples can be directly fetched from the response json object
    y = data["Samples"]
    
    # Create the timebase
    x = np.linspace(data["StartTime"], data["EndTime"], len(y), endpoint=True)
    
    plt.plot(x, y)
    plt.xlabel('Time in s')
    plt.ylabel('Amplitude in V')
    plt.title('Waveform')
    plt.show()

if __name__ == "__main__":
    main("[YOUR_INSTRUMENT_IP]")