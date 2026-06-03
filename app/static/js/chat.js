/**
 * SkillConnect – AI Chat Widget (SkillBot)
 * ==========================================
 * Floating chat bubble that connects to the /chat/message backend,
 * which proxies to the Google Gemini API.
 */

(function () {
    'use strict';

    // ── State ──────────────────────────────────────────────────────────
    let isOpen = false;
    let isLoading = false;
    let conversationHistory = []; // { role: 'user'|'model', text: '...' }

    const SUGGESTIONS = [
        '🗓️ Browse events',
        '📋 How to register?',
        '🔗 Networking tips',
        '📊 What\'s SkillConnect?',
    ];

    // ── DOM refs ──────────────────────────────────────────────────────
    let toggleBtn, panel, messagesEl, inputEl, sendBtn, suggestionsEl;

    // ── Init ──────────────────────────────────────────────────────────
    function init() {
        injectHTML();
        cacheRefs();
        bindEvents();
        renderSuggestions();
        // Show welcome message after short delay
        setTimeout(showWelcome, 600);
    }

    function injectHTML() {
        const html = `
        <!-- AI Chat Toggle Button -->
        <button id="scChatToggle" aria-label="Open AI Assistant">
            <i class="bi bi-stars" id="scChatIcon"></i>
            <span class="sc-chat-notif" id="scChatNotif"></span>
        </button>

        <!-- AI Chat Panel -->
        <div id="scChatPanel" role="dialog" aria-label="SkillBot AI Assistant">
            <!-- Header -->
            <div class="sc-chat-header">
                <div class="sc-chat-avatar">
                    <i class="bi bi-stars"></i>
                </div>
                <div class="sc-chat-header-info">
                    <strong>SkillBot</strong>
                    <span>● Online · AI Assistant</span>
                </div>
                <button id="scChatClose" aria-label="Close chat">
                    <i class="bi bi-x-lg"></i>
                </button>
            </div>

            <!-- Messages -->
            <div id="scChatMessages" aria-live="polite"></div>

            <!-- Quick suggestions -->
            <div class="sc-chat-suggestions" id="scChatSuggestions"></div>

            <!-- Input -->
            <div class="sc-chat-input-area">
                <textarea
                    id="scChatInput"
                    placeholder="Ask me anything about SkillConnect…"
                    rows="1"
                    aria-label="Chat message"
                    maxlength="500"
                ></textarea>
                <button id="scChatSend" aria-label="Send message">
                    <i class="bi bi-send-fill"></i>
                </button>
            </div>
        </div>`;

        const wrapper = document.createElement('div');
        wrapper.innerHTML = html;
        document.body.appendChild(wrapper);
    }

    function cacheRefs() {
        toggleBtn    = document.getElementById('scChatToggle');
        panel        = document.getElementById('scChatPanel');
        messagesEl   = document.getElementById('scChatMessages');
        inputEl      = document.getElementById('scChatInput');
        sendBtn      = document.getElementById('scChatSend');
        suggestionsEl= document.getElementById('scChatSuggestions');
    }

    function bindEvents() {
        toggleBtn.addEventListener('click', togglePanel);
        document.getElementById('scChatClose').addEventListener('click', closePanel);

        sendBtn.addEventListener('click', handleSend);

        inputEl.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        });

        // Auto-resize textarea
        inputEl.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 100) + 'px';
        });

        // Close on outside click
        document.addEventListener('click', function (e) {
            if (isOpen && !panel.contains(e.target) && e.target !== toggleBtn && !toggleBtn.contains(e.target)) {
                closePanel();
            }
        });
    }

    function renderSuggestions() {
        suggestionsEl.innerHTML = SUGGESTIONS.map(s =>
            `<button class="sc-suggestion-chip" data-text="${s.replace(/^.*?\s/, '')}">${s}</button>`
        ).join('');

        suggestionsEl.querySelectorAll('.sc-suggestion-chip').forEach(chip => {
            chip.addEventListener('click', function () {
                const text = this.textContent.replace(/^[^\w]+ ?/, '').trim();
                sendMessage(this.textContent.trim());
                hideSuggestions();
            });
        });
    }

    function hideSuggestions() {
        suggestionsEl.style.display = 'none';
    }

    // ── Panel toggle ──────────────────────────────────────────────────
    function togglePanel() {
        isOpen ? closePanel() : openPanel();
    }

    function openPanel() {
        isOpen = true;
        panel.classList.add('sc-chat-open');
        document.getElementById('scChatIcon').className = 'bi bi-x-lg';
        document.getElementById('scChatNotif').style.display = 'none';
        setTimeout(() => inputEl.focus(), 350);
    }

    function closePanel() {
        isOpen = false;
        panel.classList.remove('sc-chat-open');
        document.getElementById('scChatIcon').className = 'bi bi-stars';
    }

    // ── Messages ──────────────────────────────────────────────────────
    function showWelcome() {
        appendBotMessage("👋 Hi! I'm **SkillBot**, your AI assistant for SkillConnect.\n\nI can help you discover events, understand platform features, and get networking tips. What would you like to know?");
        // Show notif dot only if panel is closed
        if (!isOpen) {
            document.getElementById('scChatNotif').style.display = '';
        }
    }

    function appendBotMessage(text) {
        const msg = document.createElement('div');
        msg.className = 'sc-chat-msg sc-msg-bot';
        msg.innerHTML = `
            <div class="sc-msg-icon bot-icon"><i class="bi bi-stars"></i></div>
            <div class="sc-msg-bubble bot-bubble">${formatMessage(text)}</div>
        `;
        messagesEl.appendChild(msg);
        scrollBottom();
    }

    function appendUserMessage(text) {
        const msg = document.createElement('div');
        msg.className = 'sc-chat-msg sc-msg-user';
        msg.innerHTML = `
            <div class="sc-msg-icon user-icon"><i class="bi bi-person-fill"></i></div>
            <div class="sc-msg-bubble user-bubble">${escapeHtml(text)}</div>
        `;
        messagesEl.appendChild(msg);
        scrollBottom();
    }

    function showTyping() {
        const typing = document.createElement('div');
        typing.className = 'sc-chat-msg sc-msg-bot';
        typing.id = 'scChatTyping';
        typing.innerHTML = `
            <div class="sc-msg-icon bot-icon"><i class="bi bi-stars"></i></div>
            <div class="sc-chat-typing">
                <span></span><span></span><span></span>
            </div>
        `;
        messagesEl.appendChild(typing);
        scrollBottom();
    }

    function hideTyping() {
        const el = document.getElementById('scChatTyping');
        if (el) el.remove();
    }

    function scrollBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    // ── Send flow ─────────────────────────────────────────────────────
    function handleSend() {
        const text = inputEl.value.trim();
        if (!text || isLoading) return;
        sendMessage(text);
        inputEl.value = '';
        inputEl.style.height = 'auto';
    }

    async function sendMessage(text) {
        if (isLoading) return;

        hideSuggestions();
        appendUserMessage(text);
        conversationHistory.push({ role: 'user', text });

        setLoading(true);
        showTyping();

        try {
            const response = await fetch('/chat/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    history: conversationHistory.slice(0, -1) // exclude latest user msg (already sent)
                })
            });

            const data = await response.json();
            hideTyping();

            if (!response.ok) {
                const errMsg = data.error || 'Something went wrong. Please try again.';
                appendBotMessage(`⚠️ ${errMsg}`);
                return;
            }

            const reply = data.reply || 'I didn\'t get a response. Please try again.';
            appendBotMessage(reply);
            conversationHistory.push({ role: 'model', text: reply });

        } catch (err) {
            hideTyping();
            appendBotMessage('⚠️ Network error. Please check your connection and try again.');
            console.error('[SkillBot]', err);
        } finally {
            setLoading(false);
        }
    }

    function setLoading(state) {
        isLoading = state;
        sendBtn.disabled = state;
        inputEl.disabled = state;
    }

    // ── Formatting helpers ────────────────────────────────────────────
    function escapeHtml(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function formatMessage(text) {
        // Escape HTML first
        let safe = escapeHtml(text);
        // Bold: **text**
        safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Italic: *text*
        safe = safe.replace(/\*(.*?)\*/g, '<em>$1</em>');
        // Bullet lists
        safe = safe.replace(/^[-•] (.+)$/gm, '<li>$1</li>');
        safe = safe.replace(/(<li>.*<\/li>)/s, '<ul style="padding-left:1.2rem;margin:0.25rem 0">$1</ul>');
        // Line breaks
        safe = safe.replace(/\n/g, '<br>');
        return safe;
    }

    // ── Kick off on DOM ready ─────────────────────────────────────────
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
