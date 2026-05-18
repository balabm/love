document.addEventListener('DOMContentLoaded', () => {
    const wsStatus = document.getElementById('ws-status');
    const monologueFeed = document.getElementById('monologue-feed');
    const chatFeed = document.getElementById('chat-feed');
    const chatInput = document.getElementById('chat-input');
    const btnSend = document.getElementById('btn-send');
    const contextList = document.getElementById('context-list');
    
    // UI Elements
    const valMaturity = document.getElementById('val-maturity');
    const valEmotion = document.getElementById('val-emotion');
    const valBoots = document.getElementById('val-boots');
    
    // Connect to WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/agi/companion/ws`;
    
    let ws;
    
    function connect() {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            wsStatus.textContent = 'CONNECTED';
            wsStatus.classList.add('accent');
        };
        
        ws.onclose = () => {
            wsStatus.textContent = 'DISCONNECTED';
            wsStatus.classList.remove('accent');
            wsStatus.style.color = 'var(--accent-orange)';
            setTimeout(connect, 3000); // Reconnect
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleEvent(data);
            } catch (e) {
                console.error("Failed to parse WS message", e);
            }
        };
    }
    
    function handleEvent(data) {
        if (data.type === 'state_sync') {
            // Update stats
            if(data.consciousness) {
                valMaturity.textContent = data.consciousness.identity.maturity_level.toUpperCase();
                valEmotion.textContent = data.consciousness.emotional_state.primary_emotion.toUpperCase();
                valBoots.textContent = data.consciousness.identity.total_boots;
            }
            // Update context list
            if(data.context) {
                contextList.innerHTML = '';
                if(data.context.activity) addContextItem(`Activity: ${data.context.activity}`);
                if(data.context.active_window) addContextItem(`Focus: ${data.context.active_window}`);
                if(data.context.stress_score !== undefined) addContextItem(`User Stress: ${(data.context.stress_score*100).toFixed(0)}%`);
                addContextItem(`CPU Load: ${data.context.cpu_percent}%`);
            }
        } 
        else if (data.type === 'monologue') {
            const entry = document.createElement('div');
            entry.className = 'thought-entry';
            const time = new Date().toLocaleTimeString('en-US', { hour12: false });
            entry.innerHTML = `<span class="timestamp">[${time}]</span> <span class="text">${data.thought}</span>`;
            monologueFeed.appendChild(entry);
            monologueFeed.scrollTop = monologueFeed.scrollHeight;
        }
        else if (data.type === 'chat_response') {
            addChatMessage(data.message, 'love');
        }
    }
    
    function addContextItem(text) {
        const li = document.createElement('li');
        li.textContent = text;
        contextList.appendChild(li);
    }
    
    function addChatMessage(text, sender) {
        const msg = document.createElement('div');
        msg.className = `msg ${sender}`;
        msg.textContent = text;
        chatFeed.appendChild(msg);
        chatFeed.scrollTop = chatFeed.scrollHeight;
    }
    
    function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;
        
        addChatMessage(text, 'user');
        chatInput.value = '';
        
        // Send via REST for simplicity and robustness
        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, mode: 'general' })
        })
        .then(res => res.json())
        .then(data => {
            addChatMessage(data.response, 'love');
        })
        .catch(err => {
            addChatMessage('Error: Link severed.', 'love');
        });
    }
    
    btnSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    // Start connection
    connect();
});
