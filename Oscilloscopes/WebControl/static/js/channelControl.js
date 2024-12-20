// Base memory depth limits for single channel
const BASE_MIN_MEMORY = 20000;
const BASE_MAX_MEMORY = 200000000;

// Function to count active channels and update memory depth limits
function updateMemoryDepthLimits() {
    const activeChannels = Array.from(document.querySelectorAll('input[name="channelState"]'))
        .filter(checkbox => checkbox.checked).length;
    
    // Calculate divisor: 1 for single channel, 2 for two channels, 4 for three or four channels
    const divisor = activeChannels <= 1 ? 1 : (activeChannels === 2 ? 2 : 4);
    
    const minMemory = Math.floor(BASE_MIN_MEMORY / divisor);
    const maxMemory = Math.floor(BASE_MAX_MEMORY / divisor);
    
    const memoryInput = document.getElementById('memoryDepth');
    memoryInput.min = minMemory;
    memoryInput.max = maxMemory;
    
    // Update the help text - now targeting specific element
    const helpText = document.getElementById('memoryDepthRange');
    if (helpText) {
        helpText.textContent = `Range: ${minMemory.toLocaleString()} - ${maxMemory.toLocaleString()} points`;
    }
    
    // Adjust current value if it's outside the new limits
    const currentValue = parseInt(memoryInput.value);
    if (currentValue < minMemory) {
        memoryInput.value = minMemory;
    } else if (currentValue > maxMemory) {
        memoryInput.value = maxMemory;
    }
}

// Function to query a channel's state
async function queryChannelState(channel) {
    try {
        const response = await fetch('/proxy_scpi', {
            method: 'POST',
            body: JSON.stringify({ command: `:CHANnel${channel}:STATe?` }),
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            // Handle both direct string response and Response property
            const state = typeof data === 'string' ? data.trim() : data.Response?.trim();
            const checkbox = document.getElementById(`state${channel}`);
            const radioBtn = document.getElementById(`channel${channel}`);
            if (checkbox && state) {
                const isEnabled = state === "ON";
                checkbox.checked = isEnabled;
                // Enable/disable the radio button based on channel state
                if (radioBtn) {
                    radioBtn.disabled = !isEnabled;
                    // If this channel is selected but now disabled, select the first enabled channel
                    if (!isEnabled && radioBtn.checked) {
                        selectFirstEnabledChannel();
                    }
                }
                // Update memory depth limits after changing channel state
                updateMemoryDepthLimits();
            }
        }
    } catch (error) {
        console.error(`Error querying channel ${channel} state:`, error);
    }
}

// Function to find and select the first enabled channel
function selectFirstEnabledChannel() {
    for (let i = 1; i <= 4; i++) {
        const radio = document.getElementById(`channel${i}`);
        if (radio && !radio.disabled) {
            radio.checked = true;
            return;
        }
    }
}

// Function to query all channel states
async function queryAllChannelStates() {
    for (let i = 1; i <= 4; i++) {
        await queryChannelState(i);
    }
}

// Function to refresh time scale and memory depth settings
window.refreshSettings = async function() {
    try {
        // Query all channel states
        await queryAllChannelStates();
        
        // Get current time scale
        const timeScaleResponse = await fetch('/proxy_scpi', {
            method: 'POST',
            body: JSON.stringify({ command: 'TIMebase:SCALe?' }),
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (timeScaleResponse.ok) {
            const timeData = await timeScaleResponse.json();
            const timeScale = typeof timeData === 'string' ? parseFloat(timeData) : 
                            timeData.Response ? parseFloat(timeData.Response) : null;
            if (timeScale !== null) {
                updateTimeScaleSlider(timeScale);
            }
        }
        
        // Get current memory depth
        const memoryResponse = await fetch('/proxy_scpi', {
            method: 'POST',
            body: JSON.stringify({ command: 'ACQuire:MDEPth?' }),
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (memoryResponse.ok) {
            const memoryData = await memoryResponse.json();
            const memoryDepth = typeof memoryData === 'string' ? parseInt(memoryData) :
                              memoryData.Response ? parseInt(memoryData.Response) : null;
            if (memoryDepth !== null) {
                document.getElementById('memoryDepth').value = memoryDepth;
            }
        }
        
        document.getElementById('acquisitionStatus').textContent = 'Settings refreshed';
    } catch (error) {
        console.error('Error refreshing settings:', error);
        document.getElementById('acquisitionStatus').textContent = 
            `Error refreshing settings: ${error.message}`;
    }
}

// Handle channel state changes and refresh functionality
document.addEventListener('DOMContentLoaded', function() {
    // Handle channel state changes
    document.querySelectorAll('input[name="channelState"]').forEach(checkbox => {
        checkbox.addEventListener('change', async function() {
            const channel = this.value;
            const state = this.checked ? 1 : 0;
            
            try {
                const response = await fetch('/proxy_scpi', {
                    method: 'POST',
                    body: JSON.stringify({ command: `CHAN${channel}:STATe ${state}` }),
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`Failed to set channel ${channel} state`);
                }
                
                // Query the actual state to confirm
                const stateResponse = await fetch('/proxy_scpi', {
                    method: 'POST',
                    body: JSON.stringify({ command: `:CHANnel${channel}:STATe?` }),
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (stateResponse.ok) {
                    const stateData = await stateResponse.json();
                    const actualState = typeof stateData === 'string' ? stateData.trim() : stateData.Response?.trim();
                    const isEnabled = actualState === "ON";
                    this.checked = isEnabled;
                    
                    // Enable/disable the radio button
                    const radioBtn = document.getElementById(`channel${channel}`);
                    if (radioBtn) {
                        radioBtn.disabled = !isEnabled;
                        // If this channel is selected but now disabled, select the first enabled channel
                        if (!isEnabled && radioBtn.checked) {
                            selectFirstEnabledChannel();
                        }
                    }
                    
                    document.getElementById('acquisitionStatus').textContent = 
                        `Channel ${channel} is ${actualState}`;
                    
                    // Refresh all settings after channel state change
                    await refreshSettings();
                }
            } catch (error) {
                console.error('Error setting channel state:', error);
                document.getElementById('acquisitionStatus').textContent = 
                    `Error setting channel ${channel} state: ${error.message}`;
                // Query current state to update checkbox correctly
                queryChannelState(channel);
            }
        });
    });

    // Add refresh button event listener
    document.getElementById('refreshBtn').addEventListener('click', refreshSettings);
    
    // Initialize memory depth limits
    updateMemoryDepthLimits();
});
