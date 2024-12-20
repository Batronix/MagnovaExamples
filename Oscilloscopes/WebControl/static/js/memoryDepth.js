// Memory depth handling
async function setMemoryDepth() {
    const memoryDepth = document.getElementById('memoryDepth').value;
    try {
        const response = await fetch('/proxy_scpi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: `:ACQuire:MDEPth ${memoryDepth}` })
        });
        await response.json(); // Consume response but don't check status
        
        // Always verify the actual value after setting
        await getMemoryDepth();
    } catch (error) {
        console.error('Error setting memory depth:', error);
        alert('Failed to set memory depth: ' + error);
    }
}

async function getMemoryDepth() {
    try {
        const response = await fetch('/proxy_scpi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: ':ACQuire:MDEPth?' })
        });
        const data = await response.json();
        
        // For query commands, the response is the value directly
        const depth = parseInt(data);
        if (!isNaN(depth)) {
            document.getElementById('memoryDepth').value = depth;
        } else {
            console.error('Invalid memory depth response:', data);
        }
    } catch (error) {
        console.error('Error getting memory depth:', error);
    }
}
