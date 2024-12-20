// Waveform handling
async function getWaveform() {
    try {
        const response = await fetch('/get_waveform', { method: 'POST' });
        const data = await response.json();
        if (data.status === 'success') {
            const trace = {
                x: data.time,
                y: data.voltage,
                type: 'scatter',
                mode: 'lines',
                name: 'Channel 1'
            };
            const layout = {
                title: 'Oscilloscope Waveform',
                xaxis: { title: 'Time (s)' },
                yaxis: { title: 'Voltage (V)' }
            };
            Plotly.newPlot('waveformPlot', [trace], layout);
        } else {
            alert('Failed to get waveform: ' + data.message);
        }
    } catch (error) {
        console.error('Error getting waveform:', error);
        alert('Failed to get waveform: ' + error);
    }
}
