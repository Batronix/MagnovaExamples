use std::ffi::CString;
use std::io::{BufRead, BufReader, Read, Write};
use std::time::{Duration, Instant};
use anyhow::{Result, anyhow};
use byteorder::{ByteOrder, LittleEndian};
use log::{info, error};
use plotters::prelude::*;
use visa_rs::prelude::*;

#[derive(Debug)]
struct WaveformMetadata {
    time_delta: f32,
    start_time: f32,
    end_time: f32,
    sample_start: u32,
    sample_length: u32,
    vertical_start: f32,
    vertical_step: f32,
    sample_count: u32,
}

struct OscilloscopeWaveform {
    device: Instrument,
    #[allow(dead_code)]
    rm: DefaultRM,  // Keep the resource manager alive
}

impl OscilloscopeWaveform {
    fn find_batronix_device(rm: &DefaultRM) -> Result<Instrument> {
        info!("Searching for VISA devices");
        
        // Try different resource patterns
        let patterns = ["?*::INSTR", "USB?*INSTR", "TCPIP?*INSTR"];
        
        for pattern in patterns {
            info!("Trying pattern: {}", pattern);
            let expr = CString::new(pattern)?.into();
            
            match rm.find_res_list(&expr) {
                Ok(resources) => {
                    for res in resources {
                        if let Ok(resource) = res {
                            info!("Found resource: {:?}", resource);
                            // Try to open this device
                            if let Ok(device) = rm.open(&resource, AccessMode::NO_LOCK, Duration::from_secs(1)) {
                                // Query device identification
                                if let Ok(_) = (&device).write_all(b"*IDN?\n") {
                                    let mut buf_reader = BufReader::new(&device);
                                    let mut idn = String::new();
                                    if buf_reader.read_line(&mut idn).is_ok() {
                                        info!("Device responded: {}", idn.trim());
                                        if idn.contains("Batronix") {
                                            info!("Found Batronix device!");
                                            // Reopen with longer timeout
                                            if let Ok(device) = rm.open(&resource, AccessMode::NO_LOCK, Duration::from_secs(10)) {
                                                return Ok(device);
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                Err(e) => error!("Error listing resources for pattern {}: {}", pattern, e),
            }
        }
        
        Err(anyhow!("No Batronix device found"))
    }

    fn new(url: Option<&str>, _protocol: &str) -> Result<Self> {
        info!("Initializing VISA");
        let rm = DefaultRM::new()?;
        
        let device = if let Some(url) = url {
            // Use specified network connection
            info!("Trying network connection to {}", url);
            let resource_str = CString::new(format!("TCPIP::{}::INSTR", url))?.into();
            rm.open(&resource_str, AccessMode::NO_LOCK, Duration::from_secs(10))?
        } else {
            // Search for Batronix device
            Self::find_batronix_device(&rm)?
        };
        
        info!("Successfully opened connection");
        Ok(Self { device, rm })
    }
    
    fn get_waveform_data(&self, channel: u8, data_length: &str, data_transfer_type: &str) 
        -> Result<(Vec<f32>, Vec<f32>)> {
        // Enable only selected channel
        info!("Configuring channels");
        (&self.device).write_all(format!("CHAN{}:STATe 1\n", channel).as_bytes())?;
        for i in 1..=4 {
            if i != channel {
                (&self.device).write_all(format!("CHAN{}:STATe 0\n", i).as_bytes())?;
            }
        }
        
        // Run acquisition with 1M memory depth
        info!("Starting acquisition");
        (&self.device).write_all(b"RUN\n")?;
        (&self.device).write_all(b"ACQUire:MDEPth 1000000\n")?;
        
        // Query memory depth
        (&self.device).write_all(b"ACQuire:MDEPth?\n")?;
        let mut buf_reader = BufReader::new(&self.device);
        let mut memory_depth = String::new();
        buf_reader.read_line(&mut memory_depth)?;
        info!("Memory Depth: {}", memory_depth.trim());
        
        // Configure channel settings
        (&self.device).write_all(
            format!("CHAN{}:DATa:TYPE {}\n", channel, data_transfer_type).as_bytes()
        )?;
        
        // Wait for acquisition
        (&self.device).write_all(b"SEQuence:WAIT? 1\n")?;
        let mut wait_response = String::new();
        buf_reader.read_line(&mut wait_response)?;
        
        // Capture waveform data
        info!("Capturing waveform data");
        let start_time = Instant::now();
        
        // First query the data size
        let data_cmd = format!("CHAN{}:DATa:PACK? {}, {}\n", channel, data_length, data_transfer_type);
        (&self.device).write_all(data_cmd.as_bytes())?;
        
        // Read the header first
        let mut header = [0u8; 2];
        (&self.device).read_exact(&mut header)?;
        if header[0] != b'#' {
            return Err(anyhow!("Invalid header start"));
        }
        
        let size_len = (header[1] - b'0') as usize;
        let mut size_str = vec![0u8; size_len];
        (&self.device).read_exact(&mut size_str)?;
        let data_size = std::str::from_utf8(&size_str)?.parse::<usize>()?;
        
        // Now read the actual data
        let mut data = vec![0u8; data_size];
        (&self.device).read_exact(&mut data)?;
        
        // Read the trailing newline
        let mut newline = [0u8; 1];
        (&self.device).read_exact(&mut newline)?;
        
        info!("Data capture time: {:.3} seconds", start_time.elapsed().as_secs_f32());
        
        if data.is_empty() {
            error!("No data received");
            return Ok((vec![], vec![]));
        }
        
        // Parse metadata
        let metadata = self.parse_metadata(&data, data_transfer_type)?;
        let waveform = self.extract_waveform(&data, &metadata, data_transfer_type)?;
        
        // Create time base
        let time_values: Vec<f32> = (0..waveform.len())
            .map(|i| metadata.start_time + (i as f32) * metadata.time_delta)
            .collect();
            
        Ok((time_values, waveform))
    }
    
    fn parse_metadata(&self, data: &[u8], data_transfer_type: &str) -> Result<WaveformMetadata> {
        let metadata_size = if data_transfer_type == "RAW" { 32 } else { 16 };
        if data.len() < metadata_size {
            return Err(anyhow!("Data too short for metadata"));
        }
        
        let metadata = WaveformMetadata {
            time_delta: LittleEndian::read_f32(&data[0..4]),
            start_time: LittleEndian::read_f32(&data[4..8]),
            end_time: LittleEndian::read_f32(&data[8..12]),
            sample_start: if data_transfer_type == "RAW" { 
                LittleEndian::read_u32(&data[12..16]) 
            } else { 0 },
            sample_length: if data_transfer_type == "RAW" { 
                LittleEndian::read_u32(&data[16..20]) 
            } else { 0 },
            vertical_start: if data_transfer_type == "RAW" { 
                LittleEndian::read_f32(&data[20..24]) 
            } else { 0.0 },
            vertical_step: if data_transfer_type == "RAW" { 
                LittleEndian::read_f32(&data[24..28]) 
            } else { 0.0 },
            sample_count: if data_transfer_type == "RAW" { 
                LittleEndian::read_u32(&data[28..32]) 
            } else { 
                LittleEndian::read_u32(&data[12..16]) 
            },
        };
        
        info!("Metadata:");
        info!("  TimeDelta = {}", metadata.time_delta);
        info!("  StartTime = {}", metadata.start_time);
        info!("  EndTime = {}", metadata.end_time);
        if data_transfer_type == "RAW" {
            info!("  SampleStart = {}", metadata.sample_start);
            info!("  SampleLength = {}", metadata.sample_length);
            info!("  VerticalStart = {}", metadata.vertical_start);
            info!("  VerticalStep = {}", metadata.vertical_step);
        }
        info!("  SampleCount = {}", metadata.sample_count);
        
        Ok(metadata)
    }
    
    fn extract_waveform(&self, data: &[u8], metadata: &WaveformMetadata, data_transfer_type: &str) 
        -> Result<Vec<f32>> {
        let metadata_size = if data_transfer_type == "RAW" {
            std::mem::size_of::<f32>() * 3 + std::mem::size_of::<u32>() * 5
        } else {
            std::mem::size_of::<f32>() * 3 + std::mem::size_of::<u32>()
        };
        
        if data.len() < metadata_size {
            error!("Data too short for metadata");
            return Ok(vec![]);
        }
        
        let waveform_data = &data[metadata_size..];
        
        if data_transfer_type == "RAW" {
            // Convert bytes to u16 values and scale them to voltage
            let mut values = Vec::with_capacity(waveform_data.len() / 2);
            for chunk in waveform_data.chunks_exact(2) {
                let raw_value = LittleEndian::read_u16(chunk);
                // The vertical step is already scaled for 16-bit range
                let voltage = metadata.vertical_start + (raw_value as f32) * metadata.vertical_step / 65536.0;
                values.push(voltage);
            }
            Ok(values)
        } else {
            // For non-RAW data, just interpret as f32
            let mut values = Vec::with_capacity(waveform_data.len() / 4);
            for chunk in waveform_data.chunks_exact(4) {
                let value = LittleEndian::read_f32(chunk);
                values.push(value);
            }
            Ok(values)
        }
    }
    
    fn plot_waveform(&self, time_values: &[f32], waveform: &[f32]) -> Result<()> {
        info!("Creating plot");
        let root = BitMapBackend::new("waveform.png", (1200, 600))
            .into_drawing_area();
        root.fill(&WHITE)?;

        let min_time = time_values.first().unwrap_or(&0.0);
        let max_time = time_values.last().unwrap_or(&1.0);
        let min_voltage = waveform.iter().fold(f32::INFINITY, |a, &b| a.min(b));
        let max_voltage = waveform.iter().fold(f32::NEG_INFINITY, |a, &b| a.max(b));
        
        // Add some padding to the voltage range
        let voltage_padding = (max_voltage - min_voltage) * 0.1;
        let min_voltage = min_voltage - voltage_padding;
        let max_voltage = max_voltage + voltage_padding;

        let mut chart = ChartBuilder::on(&root)
            .caption("Oscilloscope Waveform", ("sans-serif", 40))
            .margin(10)
            .x_label_area_size(40)
            .y_label_area_size(60)
            .build_cartesian_2d(
                *min_time..*max_time,
                min_voltage..max_voltage,
            )?;

        chart
            .configure_mesh()
            .x_desc("Time (s)")
            .y_desc("Voltage (V)")
            .draw()?;

        chart.draw_series(LineSeries::new(
            time_values.iter().zip(waveform.iter()).map(|(&x, &y)| (x, y)),
            &BLUE,
        ))?;

        info!("Plot saved as waveform.png");
        Ok(())
    }
}

fn main() -> Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info"))
        .init();
    
    let scope = OscilloscopeWaveform::new(None, "raw")?;
    let (time_values, waveform) = scope.get_waveform_data(1, "ALL", "RAW")?;
    scope.plot_waveform(&time_values, &waveform)?;
    
    Ok(())
}
