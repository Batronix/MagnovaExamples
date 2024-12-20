// Connection handling
let isConnected = false;

document.addEventListener('DOMContentLoaded', function() {
    // Load saved connection details on page load
    loadSavedConnection();
    
    // Add event listener for connect button
    document.getElementById('connectBtn').addEventListener('click', toggleConnection);
});

function loadSavedConnection() {
    const savedIp = localStorage.getItem('oscilloscopeIp');
    const savedPort = localStorage.getItem('oscilloscopePort');
    const ipInput = document.getElementById('ipAddress');
    const portInput = document.getElementById('port');
    
    if (savedIp && ipInput) ipInput.value = savedIp;
    if (savedPort && portInput) portInput.value = savedPort;
}

function updateConnectionStatus(connected, message = null) {
    isConnected = connected;
    const btn = document.getElementById('connectBtn');
    const status = document.getElementById('connectionStatus');
    
    if (!btn || !status) {
        console.error('Connection UI elements not found');
        return;
    }
    
    if (connected) {
        btn.textContent = 'Disconnect';
        btn.classList.replace('btn-primary', 'btn-danger');
        status.textContent = 'Connected';
        status.className = 'text-success';
    } else {
        btn.textContent = 'Connect';
        btn.classList.replace('btn-danger', 'btn-primary');
        status.textContent = 'Disconnected';
        status.className = 'text-danger';
    }
    
    if (message) {
        console.log(message);
    }
}

async function connect() {
    const ipInput = document.getElementById('ipAddress');
    const portInput = document.getElementById('port');
    
    if (!ipInput || !portInput) {
        console.error('Connection input elements not found');
        return;
    }
    
    const ipAddress = ipInput.value;
    const port = portInput.value;
    
    // Save connection details
    localStorage.setItem('oscilloscopeIp', ipAddress);
    localStorage.setItem('oscilloscopePort', port);
    
    try {
        const response = await fetch('/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip: ipAddress, port: parseInt(port) })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            updateConnectionStatus(true, data.message);
            // Get initial settings
            if (typeof refreshSettings === 'function') {
                await refreshSettings();
            } else {
                console.warn('refreshSettings function not available');
            }
        } else {
            updateConnectionStatus(false, data.message);
            alert(data.message);
        }
    } catch (error) {
        console.error('Error connecting:', error);
        updateConnectionStatus(false);
        alert('Failed to connect: ' + error);
    }
}

async function disconnect() {
    try {
        const response = await fetch('/disconnect', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'success') {
            updateConnectionStatus(false, data.message);
        } else {
            alert('Failed to disconnect: ' + data.message);
        }
    } catch (error) {
        console.error('Error disconnecting:', error);
        alert('Failed to disconnect: ' + error);
    }
}

async function toggleConnection() {
    if (isConnected) {
        await disconnect();
    } else {
        await connect();
    }
}
