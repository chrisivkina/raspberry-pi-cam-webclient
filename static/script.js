// Socket.IO connection
let socket = null;
let connectedToSocket = false;

// Initialize Socket.IO connection
function initSocketConnection() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server via Socket.IO');
        connectedToSocket = true;
        document.querySelectorAll('.connection-indicator').forEach(el => {
            el.style.color = 'green';
            el.textContent = 'Connected';
        });
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        connectedToSocket = false;
        document.querySelectorAll('.connection-indicator').forEach(el => {
            el.style.color = 'red';
            el.textContent = 'Disconnected';
        });
    });
    
    // Handle config updates from server
    socket.on('config_updated', function(data) {
        console.log('Config updated:', data);
        getConfig(); // Refresh config display
    });
    
    // Handle status updates
    socket.on('pi_status_update', function(data) {
        updateStatusDisplay(data);
    });
}

// Update status display with data from Socket.IO
function updateStatusDisplay(data) {
    let device_status = document.getElementById('device_status');
    let cpu_p = document.getElementById('cpu_temp');
    let battery_low = document.getElementById('battery_low');
    let uptime = document.getElementById('uptime');
    let disk_space = document.getElementById('disk_space');
    let disk_space_used = document.getElementById('disk_space_used');
    let record_status = document.getElementById('record_status');
    let humidity = document.getElementById('humidity');
    
    device_status.innerHTML = 'Active and connected';
    device_status.style.color = 'green';
    cpu_p.innerHTML = data.cpu_temp;
    battery_low.innerHTML = data.battery_low;
    uptime.innerHTML = data.uptime;
    disk_space.innerHTML = data.disk_space;
    disk_space_used.innerHTML = data.disk_space_used;
    record_status.innerHTML = data.record_status;
    humidity.innerHTML = data.humidity;
    
    if (data.battery_low === 'Low') {
        battery_low.style.color = 'red';
    } else {
        battery_low.style.color = 'var(--paragraph)';
    }
    
    if (data.humidity > 40) {
        humidity.style.color = 'red';
    } else {
        humidity.style.color = 'var(--paragraph)';
    }
    
    if (parseInt(data.cpu_temp[0]) >= 8) {
        cpu_p.style.color = 'red';
    } else {
        cpu_p.style.color = 'var(--paragraph)';
    }
    
    if (data.disk_space_used[6] === '1' || data.disk_space_used[15] === '1') {
        disk_space_used.style.color = 'red';
    } else {
        disk_space_used.style.color = 'var(--paragraph)';
    }
}

// Request Pi status via Socket.IO
function fetchPiStatus() {
    if (connectedToSocket) {
        socket.emit('get_pi_status');
    } else {
        // Fallback to HTTP if socket not connected
        fetch('/api/get_pi_data', {signal: AbortSignal.timeout(1000)})
            .then(response => response.json())
            .then(json => {
                updateStatusDisplay(json);
            })
            .catch(error => {
                console.log('Error fetching Pi data', error);
                let device_status = document.getElementById('device_status');
                device_status.innerHTML = 'Inactive / Disconnected';
                device_status.style.color = 'red';
                
                ['cpu_temp', 'battery_low', 'uptime', 'disk_space', 
                 'disk_space_used', 'record_status', 'humidity'].forEach(id => {
                    document.getElementById(id).innerHTML = 'N/A';
                });
            });
    }
    
    setTimeout(fetchPiStatus, 2000);
}

// Toggle configuration setting via Socket.IO
function toggleConfig(key) {
    if (connectedToSocket) {
        socket.emit('toggle_config', {key: key});
    } else {
        // Fallback to HTTP
        fetch('api/toggle_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({key: key})
        });
    }
    getConfig();
}

// Get configuration
function getConfig() {
    fetch('api/get_config')
        .then(response => response.json())
        .then(data => {
            let config_ul = document.getElementById('config-items');
            config_ul.innerHTML = '';
            
            for (let key in data) {
                let li = document.createElement('li');
                li.innerHTML = key + ': ' + data[key];
                
                if (key !== 'CONFIG_LOCAL_MODE' && typeof data[key] === 'boolean') {
                    let toggleBtn = document.createElement('button');
                    toggleBtn.innerHTML = 'Toggle';
                    toggleBtn.onclick = () => toggleConfig(key);
                    toggleBtn.classList.add('config-toggle-button');
                    li.appendChild(toggleBtn);
                }
                
                config_ul.appendChild(li);
            }
        })
        .catch(error => {
            console.error('Error fetching config:', error);
        });
}

// Toggle collapsible sections
function toggleTargetConfigCollapse(number, do_opposite) {
    let targetConfig = document.getElementById('config-collapsible-target-' + number);
    let button = document.getElementById('config-collapsible-button-' + number);
    let target_arrow = document.getElementById('collapse-arrow-' + number);
    
    button.classList.toggle('active');
    
    if (do_opposite) {
        if (targetConfig.style.display === 'block') {
            targetConfig.style.display = 'none';
            target_arrow.innerHTML = 'keyboard_arrow_up';
        } else {
            targetConfig.style.display = 'block';
            target_arrow.innerHTML = 'keyboard_arrow_down';
        }
    } else {
        if (targetConfig.style.display === 'none') {
            targetConfig.style.display = 'block';
            target_arrow.innerHTML = 'keyboard_arrow_up';
        } else {
            targetConfig.style.display = 'none';
            target_arrow.innerHTML = 'keyboard_arrow_down';
        }
    }
}

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Socket.IO connection
    initSocketConnection();
    
    // Get initial data
    getConfig();
    
    // Start status updates
    fetchPiStatus();
    
    // Connection status indicators
    const statusDiv = document.querySelector('.status_data');
    if (statusDiv) {
        const connIndicator = document.createElement('p');
        connIndicator.id = 'socket_connection';
        connIndicator.className = 'connection-indicator';
        connIndicator.textContent = 'Connecting...';
        statusDiv.appendChild(connIndicator);
    }
    
    // Page visibility detection
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            // Page not visible, emit event if needed
            console.log('Page hidden, conserving resources');
        } else {
            // Page visible again
            console.log('Page visible, resuming updates');
            fetchPiStatus();
        }
    });
});