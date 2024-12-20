#include <stdio.h>
#include <string.h>
#include "visa.h"

int main() {
    ViStatus status;                        // Error checking
    ViSession defaultRM, instr;             // Communication channels
    ViByte buffer[256];                     // Buffer for response
    ViUInt32 retCount;                      // Return count from read

    // Initialize the VISA system
    status = viOpenDefaultRM(&defaultRM);
    if (status < VI_SUCCESS) {
        printf("Error initializing VISA system\n");
        return -1;
    }

    // Open connection to the device
    // Replace [YOUR_SERIAL_NUMBER] with your actual device serial number
    status = viOpen(defaultRM, "USB0::0x19B2::0x0030::[YOUR_SERIAL_NUMBER]::INSTR", 
                   VI_NULL, VI_NULL, &instr);
    if (status < VI_SUCCESS) {
        printf("Error opening device\n");
        viClose(defaultRM);
        return -1;
    }

    // Query device ID
    status = viWrite(instr, (ViBuf)"*IDN?\n", 6, &retCount);
    status = viRead(instr, buffer, sizeof(buffer), &retCount);
    if (status >= VI_SUCCESS) {
        buffer[retCount] = 0;    // Null terminate the string
        printf("Device ID: %s\n", buffer);
    }

    // Enable Channel 1
    status = viWrite(instr, (ViBuf)"CHAN1:STAT ON\n", 13, &retCount);
    if (status < VI_SUCCESS) {
        printf("Error enabling channel 1\n");
    }

    // Start acquisition
    status = viWrite(instr, (ViBuf)"RUN\n", 4, &retCount);
    if (status < VI_SUCCESS) {
        printf("Error starting acquisition\n");
    }

    // Clean up
    viClose(instr);
    viClose(defaultRM);

    return 0;
}
