// Main initialization
document.addEventListener('DOMContentLoaded', function() {
    // Load saved connection details
    loadSavedConnection();
    
    // Initialize time scale slider
    initTimeScaleSlider();
    
    // Add event listeners
    document.getElementById('connectBtn').addEventListener('click', toggleConnection);
    document.getElementById('setMemoryDepthBtn').addEventListener('click', setMemoryDepth);
    document.getElementById('getWaveformBtn').addEventListener('click', () => {
        if (continuousAcquisitionEnabled) {
            stopContinuousAcquisition();
        }
        updateWaveform();
    });
    
    // Run/Single buttons
    document.getElementById('singleBtn').addEventListener('click', runSingle);
    document.getElementById('runBtn').addEventListener('click', runContinuous);
    
    // Continuous acquisition checkbox
    document.getElementById('continuousAcquisition').addEventListener('change', (event) => {
        console.log('Checkbox changed:', event.target.checked);
        if (event.target.checked) {
            startContinuousAcquisition();
        } else {
            stopContinuousAcquisition();
        }
    });
});
