// Acquisition control
let continuousAcquisitionEnabled = false;
let acquisitionInterval = null;
let currentAbortController = null;
let isRequestInProgress = false;

// Initialize empty plot
document.addEventListener('DOMContentLoaded', function() {
    const layout = {
        title: 'Oscilloscope Waveform',
        xaxis: { title: 'Time (s)' },
        yaxis: { title: 'Voltage (V)' },
        margin: { t: 30 },  // Reduce top margin
        autosize: true,     // Enable auto-sizing
    };

    const config = {
        responsive: true,   // Make the plot responsive
        displayModeBar: true,  // Show the plotly toolbar
        scrollZoom: true,      // Enable scroll to zoom
    };

    Plotly.newPlot('waveformPlot', [{
        x: [],
        y: [],
        type: 'scatter'
    }], layout, config);

    // Add continuous acquisition checkbox handler
    document.getElementById('continuousAcquisition').addEventListener('change', function(e) {
        continuousAcquisitionEnabled = e.target.checked;
        if (continuousAcquisitionEnabled) {
            runContinuous();
            startContinuousAcquisition();
        } else {
            stopContinuousAcquisition();
        }
    });

    // Handle window resize
    window.addEventListener('resize', function() {
        Plotly.Plots.resize('waveformPlot');
    });
});

// Get the currently selected channel number
function getSelectedChannel() {
    return document.querySelector('input[name="channelSelect"]:checked').value;
}

async function waitForAcquisition() {
    try {
        const response = await fetch('/proxy_scpi', {
            method: 'POST',
            signal: currentAbortController?.signal,
            body: JSON.stringify({ command: 'SEQUence:WAIT? 1' }),
            headers: {
                'Content-Type': 'application/json'
            }
        });
        await response.json(); // Wait for the command to complete
        return true;
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('Acquisition wait aborted');
            return false;
        }
        console.error('Error waiting for acquisition:', error);
        return false;
    }
}

async function updateWaveform(isPartOfContinuous = false) {
    if (isRequestInProgress) {
        console.log('Request already in progress, skipping');
        return;
    }
    
    isRequestInProgress = true;
    
    try {
        currentAbortController = new AbortController();
        
        // Wait for acquisition to complete
        const acquisitionComplete = await waitForAcquisition();
        if (!acquisitionComplete) {
            isRequestInProgress = false;
            return;
        }
        
        // Get waveform data through our proxy
        const channel = getSelectedChannel();
        const response = await fetch('/proxy_scpi', { 
            method: 'POST',
            signal: currentAbortController.signal,
            body: JSON.stringify({ command: `CHAN${channel}:DATA:PACK?` }),
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        
        if (data && data.Samples) {
            if (!isPartOfContinuous || continuousAcquisitionEnabled) {
                // Create time points array based on SampleCount and TimeDelta
                const timePoints = Array.from({length: data.SampleCount}, 
                    (_, i) => data.StartTime + i * data.TimeDelta);
                
                // Update the plot
                await Plotly.update('waveformPlot', {
                    x: [timePoints],
                    y: [data.Samples]
                });
                
                document.getElementById('acquisitionStatus').textContent = 
                    `Updated waveform for Channel ${channel}`;
            }
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('Waveform update aborted');
        } else {
            console.error('Error updating waveform:', error);
            document.getElementById('acquisitionStatus').textContent = 
                'Error updating waveform: ' + error.message;
        }
    } finally {
        isRequestInProgress = false;
        currentAbortController = null;
    }
}

function startContinuousAcquisition() {
    if (!acquisitionInterval) {
        acquisitionInterval = setInterval(async () => {
            if (continuousAcquisitionEnabled) {
                await updateWaveform(true);
            } else {
                stopContinuousAcquisition();
            }
        }, 10); // Small delay to prevent overwhelming the system
    }
}

function stopContinuousAcquisition() {
    if (acquisitionInterval) {
        clearInterval(acquisitionInterval);
        acquisitionInterval = null;
    }
    if (currentAbortController) {
        currentAbortController.abort();
        currentAbortController = null;
    }
    isRequestInProgress = false;
    document.getElementById('acquisitionStatus').textContent = 
        'Continuous acquisition stopped';
}

async function runSingle() {
    // Stop continuous acquisition if running
    continuousAcquisitionEnabled = false;
    document.getElementById('continuousAcquisition').checked = false;
    stopContinuousAcquisition();
    
    try {
        // Send single trigger command
        const response = await fetch('/proxy_scpi', {
            method: 'POST',
            body: JSON.stringify({ command: ':SINGle' }),
            headers: {
                'Content-Type': 'application/json'
            }
        });
        await response.json();
        
        document.getElementById('acquisitionStatus').textContent = 
            'Single acquisition completed';
    } catch (error) {
        console.error('Error in single acquisition:', error);
        document.getElementById('acquisitionStatus').textContent = 
            'Error in single acquisition: ' + error.message;
    }
}

async function runContinuous() {
    try {
        // Send run command
        const response = await fetch('/proxy_scpi', {
            method: 'POST',
            body: JSON.stringify({ command: 'RUN' }),
            headers: {
                'Content-Type': 'application/json'
            }
        });
        await response.json();
        
        document.getElementById('acquisitionStatus').textContent = 
            'Running continuous acquisition';
    } catch (error) {
        console.error('Error starting continuous run:', error);
        document.getElementById('acquisitionStatus').textContent = 
            'Error starting continuous run: ' + error.message;
    }
}
