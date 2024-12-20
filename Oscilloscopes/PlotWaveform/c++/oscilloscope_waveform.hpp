#pragma once

#include <string>
#include <vector>
#include <memory>
#include <optional>
#include <fstream>
#include <stdexcept> // Added optional include
#include "visa.h"

/**
 * @brief Class for capturing and plotting waveform data from a Batronix oscilloscope
 */
class OscilloscopeWaveform {
public:
    /**
     * @brief Constructor for OscilloscopeWaveform
     * @param url Optional IP address for network connection
     * @param protocol Communication protocol ("raw" or "hislip")
     */
    explicit OscilloscopeWaveform(const std::string& url = "", const std::string& protocol = "raw");
    
    /**
     * @brief Destructor to clean up VISA resources
     */
    ~OscilloscopeWaveform();

    /**
     * @brief Capture waveform data and save to CSV
     * @param channel Oscilloscope channel number (1-4)
     * @param data_length Data length to capture ("ALL" or specific length)
     * @param data_transfer_type Data transfer type ("V" for voltage)
     * @param filename Output CSV filename
     */
    void saveWaveformToCSV(int channel, const std::string& filename,
                          const std::string& data_length = "ALL",
                          const std::string& data_transfer_type = "V");

    /**
     * @brief Get waveform data from the specified channel
     * @param channel Oscilloscope channel number (1-4)
     * @param data_length Data length to capture ("ALL" or specific length)
     * @param data_transfer_type Data transfer type ("V" for voltage)
     * @return Pair of time and voltage vectors
     */
    std::pair<std::vector<double>, std::vector<double>> getWaveformData(
        int channel,
        const std::string& data_length = "ALL",
        const std::string& data_transfer_type = "V");

private:
    struct Metadata {
        float timeDelta;
        float startTime;
        float endTime;
        uint32_t sampleCount;
        uint32_t sampleStart;
        uint32_t sampleLength;
        float verticalStart;
        float verticalStep;
    };

    /**
     * @brief Establish connection to the oscilloscope
     */
    void connect();

    /**
     * @brief Parse metadata from the oscilloscope data
     * @param data Raw data from oscilloscope
     * @param data_transfer_type Data transfer type
     * @return Parsed metadata
     */
    std::optional<Metadata> parseMetadata(const std::vector<uint8_t>& data,
                                        const std::string& data_transfer_type);

    /**
     * @brief Extract waveform data from raw data
     * @param data Raw data from oscilloscope
     * @param metadata Parsed metadata
     * @param data_transfer_type Data transfer type
     * @return Vector of voltage values
     */
    std::vector<double> extractWaveform(const std::vector<uint8_t>& data,
                                      const Metadata& metadata,
                                      const std::string& data_transfer_type);

    std::string url_;
    std::string protocol_;
    ViSession defaultRM_;
    ViSession device_;
    bool connected_;

    // Helper function to save raw data for debugging
    void saveRawData(const std::vector<uint8_t>& data, const std::string& filename);
};
