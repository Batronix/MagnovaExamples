#include "oscilloscope_waveform.hpp"
#include <iostream>

int main() {
    try {
        // Create waveform analyzer instance
        // Replace [YOUR_INSTRUMENT_IP] with your oscilloscope's IP address
        // or leave empty for USB connection
        OscilloscopeWaveform waveform_analyzer("192.168.10.121", "raw");
        
        // Capture waveform from channel 1 and save to CSV
        waveform_analyzer.saveWaveformToCSV(1, "waveform_data.csv", "ALL", "RAW");
        
        std::cout << "Waveform data has been saved to waveform_data.csv\n";
        std::cout << "You can plot this data using your preferred plotting tool (Excel, Python, MATLAB, etc.)\n";
        
        return 0;
    }
    catch (const std::exception& e) {
        std::cerr << "Error in main: " << e.what() << std::endl;
        return 1;
    }
}
