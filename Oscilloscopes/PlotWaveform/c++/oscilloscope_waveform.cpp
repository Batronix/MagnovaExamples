#include "oscilloscope_waveform.hpp"
#include <iostream>
#include <cstring>
#include <algorithm>
#include <chrono>
#include <thread>
#include <iomanip>

OscilloscopeWaveform::OscilloscopeWaveform(const std::string& url, const std::string& protocol)
    : url_(url), protocol_(protocol), connected_(false) {
    connect();
}

OscilloscopeWaveform::~OscilloscopeWaveform() {
    if (connected_) {
        viClose(device_);
        viClose(defaultRM_);
    }
}

void OscilloscopeWaveform::connect() {
    ViStatus status = viOpenDefaultRM(&defaultRM_);
    if (status < VI_SUCCESS) {
        throw std::runtime_error("Failed to initialize VISA");
    }

    if (!url_.empty()) {
        // Network connection
        std::string resource_str;
        if (protocol_ == "hislip") {
            resource_str = "TCPIP::" + url_ + "::hislip0::INSTR";
        } else {
            resource_str = "TCPIP::" + url_ + "::5025::SOCKET";
        }
        status = viOpen(defaultRM_, resource_str.c_str(), VI_NULL, VI_NULL, &device_);
    } else {
        // USB connection - search for all VISA devices
        std::cout << "Searching for VISA devices..." << std::endl;
        
        ViFindList find_list;
        ViUInt32 ret_count;
        char desc[VI_FIND_BUFLEN];
        bool found_batronix = false;
        
        // Find all VISA instruments
        status = viFindRsrc(defaultRM_, "?*", &find_list, &ret_count, desc);
        
        if (status >= VI_SUCCESS) {
            std::cout << "Found " << ret_count << " VISA devices" << std::endl;
            
            // Iterate through all devices
            for (ViUInt32 i = 0; i < ret_count && !found_batronix; i++) {
                if (i > 0) {
                    status = viFindNext(find_list, desc);
                    if (status < VI_SUCCESS) continue;
                }
                
                std::cout << "\nDevice " << (i + 1) << ": " << desc << std::endl;
                queryDeviceInfo(defaultRM_, desc);
                
                if (std::string(desc).find("0x19B2::0x0030") != std::string::npos) {
                    status = viOpen(defaultRM_, desc, VI_NULL, VI_NULL, &device_);
                    if (status >= VI_SUCCESS) {
                        std::cout << "\nConnected to Batronix device: " << desc << std::endl;
                        found_batronix = true;
                    }
                }
            }
            
            viClose(find_list);
        } else {
            std::cout << "Failed to find any VISA devices: " << statusToString(status) << std::endl;
        }
    }

    if (!device_) {
        throw std::runtime_error("No oscilloscope found");
    }

    // Set timeout and verify connection
    viSetAttribute(device_, VI_ATTR_TMO_VALUE, 10000);
    unsigned char idn_response[256];
    ViUInt32 ret_count;
    viWrite(device_, (ViBuf)"*IDN?\n", 6, &ret_count);
    viRead(device_, (ViBuf)idn_response, sizeof(idn_response), &ret_count);
    std::cout << "Connected to: " << std::string(reinterpret_cast<char*>(idn_response), ret_count) << std::endl;
    
    connected_ = true;
}

std::pair<std::vector<double>, std::vector<double>> OscilloscopeWaveform::getWaveformData(
    int channel,
    const std::string& data_length,
    const std::string& data_transfer_type) {
    
    if (!connected_) {
        throw std::runtime_error("Not connected to oscilloscope");
    }

    // Enable only selected channel
    std::string cmd = "CHAN" + std::to_string(channel) + ":STATe 1\n";
    ViUInt32 ret_count;
    viWrite(device_, (ViBuf)cmd.c_str(), static_cast<ViUInt32>(cmd.length()), &ret_count);
    
    // Disable other channels
    for (int i = 1; i <= 4; i++) {
        if (i != channel) {
            cmd = "CHAN" + std::to_string(i) + ":STATe 0\n";
            viWrite(device_, (ViBuf)cmd.c_str(), static_cast<ViUInt32>(cmd.length()), &ret_count);
        }
    }

    // Set up socket connection parameters
    viSetAttribute(device_, VI_ATTR_TERMCHAR, '\n');
    viSetAttribute(device_, VI_ATTR_TERMCHAR_EN, VI_TRUE);
    viSetAttribute(device_, VI_ATTR_TMO_VALUE, 10000);  // 10 second timeout
    
    // Configure channel settings
    std::cout << "Setting up channel " << channel << std::endl;
    
    // Enable channel
    cmd = "CHAN" + std::to_string(channel) + ":DISP ON\n";
    viWrite(device_, (ViBuf)cmd.c_str(), static_cast<ViUInt32>(cmd.length()), &ret_count);
    
    // Set memory depth
    cmd = "ACQuire:MDEPth 100000\n";
    viWrite(device_, (ViBuf)cmd.c_str(), static_cast<ViUInt32>(cmd.length()), &ret_count);
    
    // Set acquisition type to normal
    cmd = "ACQuire:TYPE NORMal\n";
    viWrite(device_, (ViBuf)cmd.c_str(), static_cast<ViUInt32>(cmd.length()), &ret_count);
    
    // Set data type
    cmd = "CHAN" + std::to_string(channel) + ":DATa:TYPE " + data_transfer_type + "\n";
    viWrite(device_, (ViBuf)cmd.c_str(), static_cast<ViUInt32>(cmd.length()), &ret_count);
    
    // Wait for acquisition
    cmd = "SEQuence:WAIT? 1\n";
    viWrite(device_, (ViBuf)cmd.c_str(), static_cast<ViUInt32>(cmd.length()), &ret_count);
    char wait_response[10];
    viRead(device_, (ViBuf)wait_response, sizeof(wait_response), &ret_count);
    
    // Capture waveform data
    auto start_time = std::chrono::steady_clock::now();
    cmd = "CHAN" + std::to_string(channel) + ":DATa:PACK? " + data_length + ", " + data_transfer_type + "\n";
    
    // For binary transfer, disable termination character
    viSetAttribute(device_, VI_ATTR_TERMCHAR_EN, VI_FALSE);
    viSetAttribute(device_, VI_ATTR_TMO_VALUE, 30000);  // 30 second timeout for data transfer
    
    // Send the command
    ViStatus status = viWrite(device_, (ViBuf)cmd.c_str(), static_cast<ViUInt32>(cmd.length()), &ret_count);
    if (status < VI_SUCCESS) {
        throw std::runtime_error("Failed to send command: " + std::to_string(status));
    }

    // Read initial response
    unsigned char initial_buf[1024];
    status = viRead(device_, (ViBuf)initial_buf, sizeof(initial_buf), &ret_count);
    if (status < VI_SUCCESS) {
        throw std::runtime_error("Failed to read initial response");
    }

    // Find the '#' character in the response
    size_t header_pos = 0;
    while (header_pos < ret_count && initial_buf[header_pos] != '#') {
        ++header_pos;
    }

    if (header_pos >= ret_count) {
        throw std::runtime_error("Invalid response format: '#' not found");
    }

    // Parse the length digit
    if (header_pos + 1 >= ret_count) {
        throw std::runtime_error("Incomplete header");
    }

    int size_len = initial_buf[header_pos + 1] - '0';
    if (size_len <= 0 || size_len > 9) {
        throw std::runtime_error("Invalid size length in header: " + std::to_string(size_len));
    }

    // Extract the size string
    if (header_pos + 2 + size_len > ret_count) {
        throw std::runtime_error("Incomplete size digits");
    }

    char size_str[10];
    std::memcpy(size_str, initial_buf + header_pos + 2, size_len);
    size_str[size_len] = '\0';

    // Convert size string to number
    size_t data_size;
    try {
        data_size = std::stoul(size_str);
    } catch (const std::exception&) {
        throw std::runtime_error("Invalid size value: " + std::string(size_str));
    }

    // Calculate how many bytes we already have
    size_t header_size = header_pos + 2 + size_len;  // '#' + length digit + size digits
    size_t initial_data_size = ret_count - header_size;

    // Prepare the data vector with exactly the right size
    std::vector<uint8_t> data(data_size);
    
    // Copy the initial data
    if (initial_data_size > 0) {
        std::memcpy(data.data(), initial_buf + header_size, initial_data_size);
    }

    // Read the rest of the data
    size_t bytes_read = initial_data_size;
    const size_t chunk_size = 4096;

    while (bytes_read < data_size) {
        ViUInt32 to_read = static_cast<ViUInt32>(std::min(chunk_size, data_size - bytes_read));
        status = viRead(device_, (ViBuf)(data.data() + bytes_read), to_read, &ret_count);
        
        if (status < VI_SUCCESS) {
            throw std::runtime_error("VISA read error at position " + std::to_string(bytes_read));
        }
        
        if (ret_count == 0) {
            break;
        }
        
        bytes_read += ret_count;
    }

    if (bytes_read != data_size) {
        throw std::runtime_error("Incomplete data read: " + std::to_string(bytes_read) + " of " + std::to_string(data_size) + " bytes");
    }

    // Parse metadata and extract waveform
    auto metadata = parseMetadata(data, data_transfer_type);
    if (!metadata) {
        return std::make_pair(std::vector<double>(), std::vector<double>());
    }

    // Extract waveform data
    auto waveform = extractWaveform(data, *metadata, data_transfer_type);

    // Generate time values
    std::vector<double> time_values;
    time_values.reserve(metadata->sampleCount);
    double current_time = metadata->startTime;
    for (uint32_t i = 0; i < metadata->sampleCount; ++i) {
        time_values.push_back(current_time);
        current_time += metadata->timeDelta;
    }

    return std::make_pair(time_values, waveform);
}

void OscilloscopeWaveform::saveWaveformToCSV(
    int channel,
    const std::string& filename,
    const std::string& data_length,
    const std::string& data_transfer_type) {
    
    try {
        auto [time_values, waveform] = getWaveformData(channel, data_length, data_transfer_type);
        
        if (waveform.empty()) {
            throw std::runtime_error("No waveform data to save");
        }

        // Save to CSV
        std::ofstream file(filename);
        if (!file) {
            throw std::runtime_error("Failed to open file: " + filename);
        }

        // Write header
        file << "Time (s),Voltage (V)\n";

        // Write data with high precision
        file << std::scientific << std::setprecision(15);
        for (size_t i = 0; i < waveform.size(); ++i) {
            file << time_values[i] << "," << waveform[i] << "\n";
        }
    }
    catch (const std::exception& e) {
        throw std::runtime_error("Error saving waveform: " + std::string(e.what()));
    }
}

std::optional<OscilloscopeWaveform::Metadata> OscilloscopeWaveform::parseMetadata(
    const std::vector<uint8_t>& data,
    const std::string& data_transfer_type) {
    
    try {
        Metadata metadata;

        // Helper function to read little-endian float
        auto readFloat = [](const uint8_t* ptr) -> float {
            uint32_t value = static_cast<uint32_t>(ptr[0]) |
                           (static_cast<uint32_t>(ptr[1]) << 8) |
                           (static_cast<uint32_t>(ptr[2]) << 16) |
                           (static_cast<uint32_t>(ptr[3]) << 24);
            float result;
            std::memcpy(&result, &value, sizeof(float));
            return result;
        };

        // Helper function to read little-endian uint32
        auto readUint32 = [](const uint8_t* ptr) -> uint32_t {
            return static_cast<uint32_t>(ptr[0]) |
                   (static_cast<uint32_t>(ptr[1]) << 8) |
                   (static_cast<uint32_t>(ptr[2]) << 16) |
                   (static_cast<uint32_t>(ptr[3]) << 24);
        };

        // Read metadata in the correct order
        const uint8_t* ptr = data.data();

        if (data_transfer_type == "RAW") {
            // First three floats
            float time_delta = readFloat(ptr);
            ptr += sizeof(float);
            float start_time = readFloat(ptr);
            ptr += sizeof(float);
            float end_time = readFloat(ptr);
            ptr += sizeof(float);

            // Next two uint32s
            uint32_t sample_start = readUint32(ptr);
            ptr += sizeof(uint32_t);
            uint32_t sample_length = readUint32(ptr);
            ptr += sizeof(uint32_t);

            // Next two floats
            float vertical_start = readFloat(ptr);
            ptr += sizeof(float);
            float vertical_step = readFloat(ptr);
            ptr += sizeof(float);

            // Final uint32
            uint32_t sample_count = readUint32(ptr);

            // Assign all values
            metadata.timeDelta = time_delta;
            metadata.startTime = start_time;
            metadata.endTime = end_time;
            metadata.sampleStart = sample_start;
            metadata.sampleLength = sample_length;
            metadata.verticalStart = vertical_start;
            metadata.verticalStep = vertical_step;
            metadata.sampleCount = sample_count;
        } else {
            // V format: just 3 floats + uint32
            float time_delta = readFloat(ptr);
            ptr += sizeof(float);
            float start_time = readFloat(ptr);
            ptr += sizeof(float);
            float end_time = readFloat(ptr);
            ptr += sizeof(float);
            uint32_t sample_count = readUint32(ptr);

            // Assign values
            metadata.timeDelta = time_delta;
            metadata.startTime = start_time;
            metadata.endTime = end_time;
            metadata.sampleCount = sample_count;
            // Other fields not used in V format
        }

        return metadata;
    }
    catch (const std::exception& e) {
        throw std::runtime_error("Error parsing metadata: " + std::string(e.what()));
    }
}

std::vector<double> OscilloscopeWaveform::extractWaveform(
    const std::vector<uint8_t>& data,
    const Metadata& metadata,
    const std::string& data_transfer_type) {
    
    try {
        // Calculate metadata size based on format
        size_t metadata_size;
        if (data_transfer_type == "RAW") {
            metadata_size = 32;  // 3*float + 5*uint32 = 32 bytes
        } else {
            metadata_size = 16;  // 3*float + uint32 = 16 bytes
        }
        
        // Skip metadata
        const uint8_t* ptr = data.data() + metadata_size;

        std::vector<double> waveform;
        waveform.reserve(metadata.sampleCount);

        if (data_transfer_type == "RAW") {
            // Data is in uint16_t format
            for (uint32_t i = 0; i < metadata.sampleCount; ++i) {
                // Read uint16 in little-endian order
                uint16_t raw_value = static_cast<uint16_t>(ptr[i * 2]) |
                                   (static_cast<uint16_t>(ptr[i * 2 + 1]) << 8);
                
                // Convert raw value to voltage using the formula from Python code
                double value = metadata.verticalStart + raw_value * metadata.verticalStep;
                
                waveform.push_back(value);
            }
        } else {
            // Helper function to read little-endian float
            auto readFloat = [](const uint8_t* ptr) -> float {
                uint32_t value = static_cast<uint32_t>(ptr[0]) |
                               (static_cast<uint32_t>(ptr[1]) << 8) |
                               (static_cast<uint32_t>(ptr[2]) << 16) |
                               (static_cast<uint32_t>(ptr[3]) << 24);
                float result;
                std::memcpy(&result, &value, sizeof(float));
                return result;
            };

            // Read waveform data
            for (uint32_t i = 0; i < metadata.sampleCount; ++i) {
                float value = readFloat(ptr + i * 4);
                waveform.push_back(value);
            }
        }

        return waveform;
    }
    catch (const std::exception& e) {
        throw std::runtime_error("Error processing waveform data: " + std::string(e.what()));
    }
}

void OscilloscopeWaveform::saveRawData(const std::vector<uint8_t>& data, const std::string& filename) {
    std::ofstream file(filename, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Failed to open file: " + filename);
    }
    file.write(reinterpret_cast<const char*>(data.data()), data.size());
}

// status int to string
std::string OscilloscopeWaveform::statusToString(ViStatus status) {
    switch (status) {
        case VI_SUCCESS:
            return "VI_SUCCESS";
        case VI_ERROR_INV_OBJECT:
            return "VI_ERROR_INV_OBJECT";
        case VI_ERROR_NSUP_OPER:
            return "VI_ERROR_NSUP_OPER";
        case VI_ERROR_INV_EXPR:
            return "VI_ERROR_INV_EXPR";
        case VI_ERROR_RSRC_NFOUND:
            return "VI_ERROR_RSRC_NFOUND";
        default:
            return "Unknown status";
    }
}

void OscilloscopeWaveform::queryDeviceInfo(ViSession rm, const char* resource) {
    ViSession temp_device;
    ViStatus status = viOpen(rm, resource, VI_NULL, VI_NULL, &temp_device);
    
    if (status >= VI_SUCCESS) {
        // Query device identity
        unsigned char idn_response[256];
        ViUInt32 response_count;
        status = viWrite(temp_device, (ViBuf)"*IDN?\n", 6, &response_count);
        if (status >= VI_SUCCESS) {
            status = viRead(temp_device, (ViBuf)idn_response, sizeof(idn_response), &response_count);
            if (status >= VI_SUCCESS) {
                std::string idn_str(reinterpret_cast<char*>(idn_response), response_count);
                std::cout << "  ID: " << idn_str;
            } else {
                std::cout << "  Failed to read device ID: " << statusToString(status);
            }
        } else {
            std::cout << "  Failed to query device ID: " << statusToString(status);
        }
        viClose(temp_device);
    } else {
        std::cout << "  Failed to open device: " << statusToString(status);
    }
    std::cout << std::endl;
}