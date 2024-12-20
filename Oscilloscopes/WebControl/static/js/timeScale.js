// Time scale handling
const timeScaleValues = [
    0.000001, 0.000002, 0.000005,  // 1, 2, 5 µs
    0.00001, 0.00002, 0.00005,     // 10, 20, 50 µs
    0.0001, 0.0002, 0.0005,        // 100, 200, 500 µs
    0.001, 0.002, 0.005,           // 1, 2, 5 ms
    0.01, 0.02, 0.05,              // 10, 20, 50 ms
    0.1, 0.2, 0.5,                 // 100, 200, 500 ms
    1.0                            // 1 s
];

function formatTimeScale(scale) {
    if (scale < 0.000001) return `${scale * 1e9} ns/div`;
    if (scale < 0.001) return `${scale * 1e6} µs/div`;
    if (scale < 1) return `${scale * 1e3} ms/div`;
    return `${scale} s/div`;
}

function getTimeScaleIndex(scale) {
    return timeScaleValues.findIndex(v => Math.abs(v - scale) < 1e-10);
}

async function updateTimeScale(scale) {
    try {
        // Set time scale through proxy
        const response = await fetch('/proxy_scpi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: `:TIMebase:SCALe ${scale}` })
        });
        const data = await response.json();
        
        // Always get the actual scale after setting it
        await getTimeScale();
    } catch (error) {
        console.error('Error setting time scale:', error);
        alert('Failed to set time scale: ' + error);
        await getTimeScale();
    }
}

async function getTimeScale() {
    try {
        const response = await fetch('/proxy_scpi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: ':TIMebase:SCALe?' })
        });
        const data = await response.json();
        
        // For query commands, the response is the value directly
        const scale = parseFloat(data);
        if (!isNaN(scale)) {
            const index = getTimeScaleIndex(scale);
            if (index !== -1) {
                $("#timeScaleSlider").roundSlider("setValue", index);
            }
            document.getElementById('timeScaleDisplay').textContent = formatTimeScale(scale);
        } else {
            console.error('Invalid time scale response:', data);
        }
    } catch (error) {
        console.error('Error getting time scale:', error);
    }
}

// Initialize time scale slider
function initTimeScaleSlider() {
    $("#timeScaleSlider").roundSlider({
        radius: 40,
        width: 8,
        handleSize: "+10",
        min: 0,
        max: timeScaleValues.length - 1,
        value: getTimeScaleIndex(0.0001), // Default to 100µs
        step: 1,
        sliderType: "min-range",
        circleShape: "full",
        showTooltip: false,
        change: async function (e) {
            const scale = timeScaleValues[e.value];
            document.getElementById('timeScaleDisplay').textContent = formatTimeScale(scale);
            await updateTimeScale(scale);
        }
    });
}
