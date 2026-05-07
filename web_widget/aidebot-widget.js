// ==================== aidebot-widget.js ====================
// A single‑file embeddable widget for AideBot.
// Include with:
// <script src="aidebot-widget.js" data-api-base="..." data-auto-open-delay="..." data-health-check-interval="..."></script>

(function() {
    // ========== CONFIGURATION ==========
    const DEFAULT_CONFIG = {
        apiBase: 'https://your-domain.com/api',
        autoOpenDelay: 5000,           // ms before popup appears
        healthCheckInterval: 30000,     // ms between server health checks
    };

    const scripts = document.getElementsByTagName('script');
    const currentScript = scripts[scripts.length - 1];
    const config = {
        apiBase: currentScript.dataset.apiBase || DEFAULT_CONFIG.apiBase,
        autoOpenDelay: parseInt(currentScript.dataset.autoOpenDelay) || DEFAULT_CONFIG.autoOpenDelay,
        healthCheckInterval: parseInt(currentScript.dataset.healthCheckInterval) || DEFAULT_CONFIG.healthCheckInterval,
    };

    // ========== TEXT CONSTANTS (English, persona‑aligned) ==========
    const TEXTS = {
        popupMessage: 'Hi! I am AideBot, an AI assistant created by Evgenii Bykov, a full‑stack developer. Ask me anything!',
        greetingTitle: 'Hi, I am AideBot',
        greetingParagraph1: 'an AI assistant created by Evgenii Bykov, a full‑stack developer with extensive experience in web development, PHP, JavaScript, Python, Laravel, React, Angular, and more.',
        greetingParagraph2: 'I can answer your questions about my creator, his skills, projects, and experience. Feel free to start a conversation!',
        startFormNamePlaceholder: 'Your name',
        startFormPhonePlaceholder: 'Your phone (optional)',
        startFormButton: 'Start Chat',
        chatHeader: 'AideBot – Evgenii Bykov',
        messageInputPlaceholder: 'Type your message...',
        botWelcome: 'Hello! Ask me anything about Evgenii Bykov\'s experience, skills, or projects. I\'ll do my best to help!',
        sessionInactive: 'Session is not active. Please start a new session.',
        sessionExpired: 'Session expired. Please start a new session.',
        invalidNameAlert: 'Please enter a valid name (letters, spaces, hyphens only).',
        invalidPhoneAlert: 'Please enter a valid phone number (digits only, 10–11 digits).',
        serverError: 'Error: ',
        connectionError: 'Connection error: ',
    };

    // ========== STYLES (embedded, no changes needed) ==========
    const styles = `
        @import url('https://fonts.googleapis.com/css2?family=Roboto&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;900&display=swap');
        .ab-widget-container,
        .ab-widget-container * {
            font-family: 'Roboto', sans-serif;
            padding: 0;
        }
        .ab-widget-container {
            position: fixed;
            top: 50%;
            right: 20px;
            transform: translateY(-50%);
            display: flex;
            flex-direction: row;
            align-items: center;
            z-index: 10000;
        }
        .ab-open-panel {
            position: relative;
            background: url('avatar.png') center / cover no-repeat;
            width: 20vw;
            height: 20vw;
            max-width: 100px;
            max-height: 100px;
            border-radius: 54px;
            cursor: pointer;
            user-select: none;
            border: 4px solid #eee;
            transition: opacity 0.3s ease;
        }
        @media (max-width: 800px) {
            .ab-open-panel {
                top: 20vh;
            }
        }
        .ab-open-panel::before {
            content: '';
            position: absolute;
            top: -8px;
            left: -8px;
            right: -8px;
            bottom: -8px;
            border-radius: 60px;
            background: linear-gradient(45deg, #009fff, #ec2f4b, #009fff, #ec2f4b);
            background-size: 300% 300%;
            z-index: -1;
            filter: blur(12px);
            animation: gradientShift 3s ease infinite;
            transition: opacity 0.3s ease;
        }
        .ab-open-panel:hover {
            border: 4px solid #fff;
        }
        .ab-open-panel.ab-server-unavailable {
            opacity: 0.5;
            pointer-events: none;
            border-color: #ccc;
        }
        .ab-open-panel.ab-server-unavailable::before {
            opacity: 0;
            animation: none;
        }
        .ab-chat-window {
            width: calc(50vw - 28px);
            right: 20px;
            overflow: hidden;
            display: none;
            flex-direction: column;
            height: 70vh;
            border: 4px solid transparent;
            background: linear-gradient(white, white) padding-box,
                        linear-gradient(270deg, #009fff, #ec2f4b) border-box;
        }
        .ab-chat-window::before {
            content: '';
            position: absolute;
            top: 0px;
            left: 0px;
            right: 0px;
            bottom: 0px;
            border-radius: 0px;
            background: linear-gradient(45deg, #009fff, #ec2f4b, #009fff, #ec2f4b);
            background-size: 300% 300%;
            z-index: -1;
            filter: blur(12px);
            opacity: 0.7;
            animation: gradientShift 3s ease infinite;
        }
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }        
        .ab-chat-header {
            color: #aaa;
            padding: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-weight: 300;
            font-size: 1.2rem;
        }
        .ab-chat-header .ab-close-chat {
            cursor: pointer;
            font-size: 1.4rem;
            line-height: 1;
            opacity: 0.8;
            transition: opacity 0.2s;
        }
        .ab-chat-header .ab-close-chat:hover {
            opacity: 1;
        }
        .ab-chat-body {
            padding: 10px 10px;
            flex: 1;
            overflow-y: auto;
        }
        .ab-greeting-area {
            text-align: left;
        }
        .ab-greeting-area h3 {
            margin-bottom: 10px;
            color: #818181;
        }
        .ab-greeting-area p {
            color: #818181;
            margin-bottom: 10px;
            font-size: 1rem;
            line-height: 1.2;
        }
        .ab-start-form {
            margin-top: 30px;
        }
        .ab-start-form input {
            width: 100%;
            box-sizing: border-box;
            padding: 12px 16px;
            margin-bottom: 12px;
            border: 1px solid #aaa;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.2s;
        }
        .ab-start-form input:focus {
            border-color: #ec2f4b;
        }
        .ab-start-form button {
            width: 100%;
            background: linear-gradient(270deg, #009fff, #ec2f4b);
            color: white;
            border: none;
            padding: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
            margin-top: 4px;
        }
        .ab-messages-area {
            height: calc(100% - 54px);
            display: none;
        }
        .ab-messages {
            height: 100%;
            overflow-y: auto;
            margin-bottom: 12px;
            padding: 0;
        }
        .ab-message {
            margin: 8px 0;
            padding: 8px 12px;
            border-radius: 18px;
            max-width: 75%;
            word-wrap: break-word;
            clear: both;
        }
        .ab-message.user {
            background: #abdfff;
            float: right;
        }
        .ab-message.bot {
            background: #efefef;
            float: left;
        }
        .ab-input-row {
            display: flex;
            gap: 8px;
            align-items: center;
            margin-top: 8px;
        }
        .ab-input-row input {
            flex: 1;
            padding: 10px 16px;
            border: 1px solid #ccc;
            border-radius: 40px;
            outline: none;
            font-size: 1rem;
        }
        .ab-circle-btn {
            width: 42px;
            height: 42px;
            border-radius: 50%;
            border: none;
            background: #009fff;
            color: white;
            font-size: 1.4rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }
        .ab-circle-btn:hover {
            background: #0082d0;
        }
        .ab-circle-btn.danger {
            background: #ec2f4b;
            display: none;
        }
        .ab-circle-btn.danger:hover {
            background: #c30824;
        }
        @media (max-width: 800px) {
            .ab-chat-window {
                width: calc(100vw - 48px);
                right: 20px;
                height: calc(100vh - 148px);
            }
        }
        .ab-popup {
            right: 20px;
            position: fixed;
            width: 280px;
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            z-index: 1002;
            font-family: 'Roboto', sans-serif;
            display: none;
        }
        .ab-popup .ab-popup-content {
            position: relative;
        }
        .ab-popup .ab-popup-close {
            position: absolute;
            top: -8px;
            right: -8px;
            cursor: pointer;
            font-size: 20px;
            line-height: 1;
            width: 24px;
            height: 24px;
            background: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: black;
        }
        .ab-popup p {
            margin: 0;
            font-size: 14px;
            line-height: 1.4;
            padding: 0;
            color: black;
        }
    `;

    // ========== HTML TEMPLATE ==========
    const widgetHTML = `
        <div class="ab-widget-container" id="ab-widget-container">
            <div class="ab-open-panel" id="ab-open-panel"></div>
            <div class="ab-chat-window" id="ab-chat-window">
                <div class="ab-chat-header">
                    ${TEXTS.chatHeader}
                    <span class="ab-close-chat" id="ab-close-chat">&times;</span>
                </div>
                <div class="ab-chat-body">
                    <div class="ab-greeting-area" id="ab-greeting-area">
                        <h3>${TEXTS.greetingTitle}</h3>
                        <p>${TEXTS.greetingParagraph1}</p>
                        <p>${TEXTS.greetingParagraph2}</p>
                        <div class="ab-start-form" id="ab-start-form">
                            <input type="text" id="ab-name" placeholder="${TEXTS.startFormNamePlaceholder}" required>
                            <input type="tel" id="ab-phone" placeholder="${TEXTS.startFormPhonePlaceholder}">
                            <button id="ab-start-chat">${TEXTS.startFormButton}</button>
                        </div>
                    </div>
                    <div class="ab-messages-area" id="ab-messages-area">
                        <div class="ab-messages" id="ab-messages"></div>
                        <div class="ab-input-row">
                            <input type="text" id="ab-message-input" placeholder="${TEXTS.messageInputPlaceholder}">
                            <button class="ab-circle-btn" id="ab-send-message">➤</button>
                            <button class="ab-circle-btn danger" id="ab-end-session">✕</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="ab-popup" id="ab-popup">
            <div class="ab-popup-content">
                <span class="ab-popup-close" id="ab-popup-close">&times;</span>
                <p>${TEXTS.popupMessage}</p>
            </div>
        </div>
    `;

    // ========== DOM ELEMENTS ==========
    const styleEl = document.createElement('style');
    styleEl.textContent = styles;
    document.head.appendChild(styleEl);
    document.body.insertAdjacentHTML('beforeend', widgetHTML);

    const panel = document.getElementById('ab-open-panel');
    const chatWindow = document.getElementById('ab-chat-window');
    const closeBtn = document.getElementById('ab-close-chat');
    const greetingArea = document.getElementById('ab-greeting-area');
    const messagesArea = document.getElementById('ab-messages-area');
    const startBtn = document.getElementById('ab-start-chat');
    const nameInput = document.getElementById('ab-name');
    const phoneInput = document.getElementById('ab-phone');
    const messagesDiv = document.getElementById('ab-messages');
    const messageInput = document.getElementById('ab-message-input');
    const sendBtn = document.getElementById('ab-send-message');
    const endBtn = document.getElementById('ab-end-session');
    const popup = document.getElementById('ab-popup');
    const popupClose = document.getElementById('ab-popup-close');

    // ========== STATE ==========
    let currentSessionId = localStorage.getItem('aidebot_session_id');
    let popupTimer = null;
    let popupClosed = false;
    let popupShown = false;
    let healthCheckTimer = null;

    // ========== LOCAL STORAGE HELPERS ==========
    function getStorageKey(sessionId) {
        return `aidebot_messages_${sessionId}`;
    }

    function loadMessages(sessionId) {
        if (!sessionId) return [];
        const stored = localStorage.getItem(getStorageKey(sessionId));
        return stored ? JSON.parse(stored) : [];
    }

    function saveMessage(sessionId, role, text) {
        if (!sessionId) return;
        const messages = loadMessages(sessionId);
        messages.push({ role, text });
        localStorage.setItem(getStorageKey(sessionId), JSON.stringify(messages));
    }

    function clearMessages(sessionId) {
        if (!sessionId) return;
        localStorage.removeItem(getStorageKey(sessionId));
    }

    function displayStoredMessages(sessionId) {
        const messages = loadMessages(sessionId);
        messagesDiv.innerHTML = '';
        messages.forEach(msg => {
            const msgDiv = document.createElement('div');
            msgDiv.className = `ab-message ${msg.role}`;
            msgDiv.textContent = msg.text;
            messagesDiv.appendChild(msgDiv);
        });
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    // ========== UI HELPERS ==========
    function addMessage(role, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `ab-message ${role}`;
        msgDiv.textContent = text;
        messagesDiv.appendChild(msgDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        saveMessage(currentSessionId, role, text);
    }

    function positionPopupUnderIcon() {
        const iconRect = panel.getBoundingClientRect();
        popup.style.right = '20px';
        popup.style.top = iconRect.bottom + 20 + 'px';
        popup.style.left = 'auto';
    }

    function openChat() {
        if (popup.style.display === 'block') {
            popup.style.display = 'none';
            popupClosed = true;
        }
        if (popupTimer) {
            clearTimeout(popupTimer);
            popupTimer = null;
        }

        panel.style.display = 'none';
        chatWindow.style.display = 'flex';

        if (currentSessionId) {
            greetingArea.style.display = 'none';
            messagesArea.style.display = 'block';
            displayStoredMessages(currentSessionId);
        } else {
            greetingArea.style.display = 'block';
            messagesArea.style.display = 'none';
            const savedName = localStorage.getItem('aidebot_user_name');
            const savedPhone = localStorage.getItem('aidebot_user_phone');
            if (savedName) nameInput.value = savedName;
            if (savedPhone) phoneInput.value = savedPhone;
        }
    }

    function closeChat() {
        panel.style.display = 'block';
        chatWindow.style.display = 'none';
    }

    async function endSession() {
        if (!currentSessionId) return;
        try {
            await fetch(config.apiBase + '/end', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: currentSessionId })
            });
        } catch (e) {
            console.warn('Error ending session:', e);
        }
        clearMessages(currentSessionId);
        localStorage.removeItem('aidebot_session_id');
        currentSessionId = null;
        greetingArea.style.display = 'block';
        messagesArea.style.display = 'none';
        messagesDiv.innerHTML = '';
    }

    function resetSession() {
        if (currentSessionId) {
            clearMessages(currentSessionId);
            localStorage.removeItem('aidebot_session_id');
            currentSessionId = null;
        }
        greetingArea.style.display = 'block';
        messagesArea.style.display = 'none';
        messagesDiv.innerHTML = '';
    }

    // ========== VALIDATION ==========
    function validateName(name) {
        const re = /^[a-zA-Zа-яА-ЯёЁ\s\-]+$/;
        return name.trim() !== '' && re.test(name);
    }

    function validatePhone(phone) {
        const digits = phone.replace(/\D/g, '');
        if (digits.length === 0) return true; // phone is optional
        return digits.length === 10 || (digits.length === 11 && (digits[0] === '7' || digits[0] === '8'));
    }

    function fillStoredUserData() {
        const savedName = localStorage.getItem('aidebot_user_name');
        const savedPhone = localStorage.getItem('aidebot_user_phone');
        if (savedName) nameInput.value = savedName;
        if (savedPhone) phoneInput.value = savedPhone;
    }

    // ========== POPUP DISPLAY ==========
    function showPopup() {
        if (popupShown) return;
        if (popupClosed) return;
        if (currentSessionId) return;
        if (chatWindow.style.display === 'flex') return;
        if (panel.classList.contains('ab-server-unavailable')) return;

        positionPopupUnderIcon();
        popup.style.display = 'block';
        popupShown = true;
    }

    // ========== HEALTH CHECK ==========
    function checkServerHealth() {
        fetch(config.apiBase + '/start', {
            method: 'OPTIONS',
            mode: 'cors',
            cache: 'no-cache',
        })
        .then(() => {
            panel.classList.remove('ab-server-unavailable');
        })
        .catch(() => {
            panel.classList.add('ab-server-unavailable');
        });
    }

    // ========== INITIALIZATION ==========
    if (!currentSessionId) {
        popupTimer = setTimeout(showPopup, config.autoOpenDelay);
    }

    checkServerHealth();
    if (config.healthCheckInterval > 0) {
        healthCheckTimer = setInterval(checkServerHealth, config.healthCheckInterval);
    }

    // ========== EVENT LISTENERS ==========
    popupClose.addEventListener('click', (e) => {
        e.stopPropagation();
        popup.style.display = 'none';
        popupClosed = true;
        if (popupTimer) {
            clearTimeout(popupTimer);
            popupTimer = null;
        }
    });

    window.addEventListener('resize', () => {
        if (popup.style.display === 'block') {
            positionPopupUnderIcon();
        }
    });

    panel.addEventListener('click', openChat);
    closeBtn.addEventListener('click', closeChat);

    startBtn.addEventListener('click', async () => {
        const name = nameInput.value.trim();
        const phone = phoneInput.value.trim();

        if (!validateName(name)) {
            alert(TEXTS.invalidNameAlert);
            return;
        }
        if (!validatePhone(phone)) {
            alert(TEXTS.invalidPhoneAlert);
            return;
        }

        try {
            const response = await fetch(config.apiBase + '/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, phone })
            });
            if (response.ok) {
                const data = await response.json();
                currentSessionId = data.session_id;
                localStorage.setItem('aidebot_session_id', currentSessionId);
                localStorage.setItem('aidebot_user_name', name);
                localStorage.setItem('aidebot_user_phone', phone);

                greetingArea.style.display = 'none';
                messagesArea.style.display = 'block';
                messagesDiv.innerHTML = '';
                addMessage('bot', TEXTS.botWelcome);
            } else {
                const err = await response.json();
                alert(TEXTS.serverError + (err.error || 'Unknown error'));
            }
        } catch (e) {
            alert(TEXTS.connectionError + e.message);
        }
    });

    async function sendMessage() {
        if (!currentSessionId) {
            addMessage('bot', TEXTS.sessionInactive);
            return;
        }
        const text = messageInput.value.trim();
        if (!text) return;
        messageInput.value = '';
        addMessage('user', text);

        try {
            const response = await fetch(config.apiBase + '/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, session_id: currentSessionId })
            });

            if (response.ok) {
                const data = await response.json();
                addMessage('bot', data.reply);
            } else {
                const err = await response.json();
                if (response.status === 401) {
                    resetSession();
                    addMessage('bot', TEXTS.sessionExpired);
                } else {
                    addMessage('bot', TEXTS.serverError + (err.error || 'Unknown error'));
                }
            }
        } catch (e) {
            addMessage('bot', TEXTS.connectionError + e.message);
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    endBtn.addEventListener('click', endSession);

    fillStoredUserData();

    window.addEventListener('beforeunload', () => {
        if (healthCheckTimer) clearInterval(healthCheckTimer);
        if (popupTimer) clearTimeout(popupTimer);
    });
})();