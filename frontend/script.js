/**
 * Green AI – ChatGPT-style chat UI
 * Uses /ask and /ingest endpoints; shows typing indicator and risk badge.
 */

(function () {
    const hero = document.getElementById('hero');
    const app = document.getElementById('app');
    const btnAnalyze = document.getElementById('btnAnalyze');
    const btnDemo = document.getElementById('btnDemo');
    const chatArea = document.getElementById('chatArea');
    const chatWelcome = document.getElementById('chatWelcome');
    const messagesEl = document.getElementById('messages');
    const typingIndicator = document.getElementById('typingIndicator');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const suggestions = document.getElementById('suggestions');
    const btnNewChat = document.getElementById('btnNewChat');
    const heroPptInput = document.getElementById('heroPptInput');
    const chatPptInput = document.getElementById('chatPptInput');
    const heroPdfInput = document.getElementById('heroPdfInput');
    const chatPdfInput = document.getElementById('chatPdfInput');
    const heroImageInput = document.getElementById('heroImageInput');
    const chatImageInput = document.getElementById('chatImageInput');
    const settingsPanel = document.getElementById('settingsPanel');
    const inputArea = document.querySelector('.input-area');
    const historyListEl = document.getElementById('historyList');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    const btnAuth = document.getElementById('btnAuth');
    const btnLogout = document.getElementById('btnLogout');
    const authUser = document.getElementById('authUser');
    const authModal = document.getElementById('authModal');
    const authClose = document.getElementById('authClose');
    const authTabs = document.querySelectorAll('.auth-tab');
    const loginEmail = document.getElementById('loginEmail');
    const loginPassword = document.getElementById('loginPassword');
    const doLogin = document.getElementById('doLogin');
    const regName = document.getElementById('regName');
    const regEmail = document.getElementById('regEmail');
    const regPassword = document.getElementById('regPassword');
    const doRegister = document.getElementById('doRegister');
    const authError = document.getElementById('authError');

    const SESS_KEY_PREFIX = 'green_ai_chats_v1:';
    let sessions = [];
    let currentSessionId = null;
    let authState = { authenticated: false, id: null, name: '', email: '' };

    function getSessKey() {
        if (!authState || !authState.authenticated || !authState.email) return null;
        return SESS_KEY_PREFIX + authState.email.toLowerCase();
    }

    const API_BASE = (function () {
        if (typeof location !== 'undefined' && location.port !== '8000') {
            return 'http://127.0.0.1:8000';
        }
        return '';
    })();

    function uid() {
        return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    }

    function createSession() {
        return { id: uid(), title: 'New chat', createdAt: Date.now(), updatedAt: Date.now(), messages: [] };
    }

    function loadSessions() {
        const key = getSessKey();
        if (!key) {
            sessions = [];
            renderHistory();
            renderCurrentSession();
            return;
        }
        try {
            const raw = localStorage.getItem(key) || '[]';
            sessions = JSON.parse(raw);
            if (!Array.isArray(sessions)) sessions = [];
        } catch (e) {
            sessions = [];
        }
        if (sessions.length === 0) {
            const s = createSession();
            sessions.push(s);
            currentSessionId = s.id;
            saveSessions();
        }
        if (!currentSessionId) currentSessionId = sessions[0].id;
        renderHistory();
        renderCurrentSession();
    }

    function saveSessions() {
        const key = getSessKey();
        if (!key) return;
        try {
            localStorage.setItem(key, JSON.stringify(sessions));
        } catch (e) {}
    }

    function getCurrentSession() {
        return sessions.find(s => s.id === currentSessionId);
    }

    function setCurrentSession(id) {
        if (loadingOverlay) {
            loadingText && (loadingText.textContent = 'Loading conversation…');
            loadingOverlay.classList.add('show');
        }
        currentSessionId = id;
        setTimeout(() => {
            renderHistory();
            renderCurrentSession();
            if (loadingOverlay) loadingOverlay.classList.remove('show');
        }, 400);
    }

    function renderHistory() {
        if (!historyListEl) return;
        const sorted = [...sessions].sort((a, b) => b.updatedAt - a.updatedAt);
        historyListEl.innerHTML = '';
        for (const s of sorted) {
            const btn = document.createElement('button');
            btn.className = 'history-item' + (s.id === currentSessionId ? ' active' : '');
            btn.setAttribute('data-id', s.id);
            btn.title = s.title;
            btn.textContent = s.title;
            btn.addEventListener('click', function () { setCurrentSession(s.id); });
            historyListEl.appendChild(btn);
        }
    }

    function renderCurrentSession() {
        const s = getCurrentSession();
        messagesEl.innerHTML = '';
        if (!s || s.messages.length === 0) {
            if (chatWelcome) chatWelcome.classList.remove('hidden');
            return;
        }
        if (chatWelcome) chatWelcome.classList.add('hidden');
        for (const m of s.messages) {
            addMessage(m.role, m.content, m.risk_score, m.meta);
        }
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    function record(role, content, riskScore, meta) {
        const s = getCurrentSession();
        if (!s) return;
        s.messages.push({ role, content, risk_score: riskScore || null, meta: meta || null });
        s.updatedAt = Date.now();
        if (s.title === 'New chat' && role === 'user') {
            let t = (content || '').trim().replace(/\s+/g, ' ');
            if (t.length > 40) t = t.slice(0, 40) + '…';
            s.title = t || 'New chat';
        }
        saveSessions();
        renderHistory();
    }

    function recordAndAddMessage(role, content, riskScore, meta) {
        addMessage(role, content, riskScore, meta);
        record(role, content, riskScore, meta);
    }

    async function parseJsonResponse(res) {
        const ct = res.headers.get('content-type') || '';
        if (!ct.includes('application/json')) {
            const text = await res.text();
            throw new Error('Server returned HTML instead of JSON. Is the backend running? Try: python app.py');
        }
        return res.json();
    }

    function showApp() {
        if (!authState.authenticated) {
            openAuthModal();
            return;
        }
        if (loadingOverlay) {
            loadingText && (loadingText.textContent = 'Loading project…');
            loadingOverlay.classList.add('show');
            setTimeout(() => {
                hero.classList.add('hidden');
                app.classList.remove('hidden');
                loadingOverlay.classList.remove('show');
            }, 500);
        } else {
            hero.classList.add('hidden');
            app.classList.remove('hidden');
        }
    }

    async function fetchMe() {
        try {
            const res = await fetch(`${API_BASE}/auth/me`);
            const data = await res.json();
            authState = {
                authenticated: !!data.authenticated,
                id: data.id || null,
                name: data.name || '',
                email: data.email || ''
            };
            updateAuthUI();
            if (authState.authenticated) {
                loadSessions();
            } else {
                openAuthModal();
            }
        } catch (e) {
            authState = { authenticated: false };
            updateAuthUI();
            openAuthModal();
        }
    }

    function updateAuthUI() {
        if (authState.authenticated) {
            btnAuth && btnAuth.classList.add('hidden');
            btnLogout && btnLogout.classList.remove('hidden');
            authUser && (authUser.textContent = authState.name || authState.email || ''); 
            authUser && authUser.classList.remove('hidden');
        } else {
            btnAuth && btnAuth.classList.remove('hidden');
            btnLogout && btnLogout.classList.add('hidden');
            authUser && authUser.classList.add('hidden');
        }
    }

    function openAuthModal() {
        if (!authModal) return;
        authModal.classList.remove('hidden');
        authError.textContent = '';
        setAuthView('login');
    }
    function closeAuthModal() {
        if (!authModal) return;
        authModal.classList.add('hidden');
    }
    function setAuthView(view) {
        document.getElementById('authLogin').classList.toggle('hidden', view !== 'login');
        document.getElementById('authRegister').classList.toggle('hidden', view !== 'register');
        authTabs.forEach(t => t.classList.toggle('active', t.getAttribute('data-view') === view));
    }
    async function login() {
        authError.textContent = '';
        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: loginEmail.value.trim(), password: loginPassword.value })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || res.statusText);
            authState = { authenticated: true, id: data.id, name: data.name, email: data.email };
            closeAuthModal();
            updateAuthUI();
            loadSessions();
        } catch (e) {
            authError.textContent = e.message;
        }
    }
    async function register() {
        authError.textContent = '';
        try {
            const res = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: regName.value.trim(), email: regEmail.value.trim(), password: regPassword.value })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || res.statusText);
            authState = { authenticated: true, id: data.id, name: data.name, email: data.email };
            closeAuthModal();
            updateAuthUI();
            loadSessions();
        } catch (e) {
            authError.textContent = e.message;
        }
    }
    async function logout() {
        try {
            await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
        } catch (e) {}
        authState = { authenticated: false, id: null, name: '', email: '' };
        updateAuthUI();
        sessions = [];
        currentSessionId = null;
        renderHistory();
        renderCurrentSession();
        hero.classList.remove('hidden');
        app.classList.add('hidden');
        openAuthModal();
    }

    function setTheme(theme) {
        const themes = ['dark', 'light', 'colorful', 'transparent'];
        themes.forEach(t => document.body.classList.remove('theme-' + t));
        if (!themes.includes(theme)) theme = 'dark';
        document.body.classList.add('theme-' + theme);
        try {
            localStorage.setItem('green_ai_theme', theme);
        } catch (e) { /* ignore */ }
        // Update active state on buttons if present
        document.querySelectorAll('.theme-option').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-theme') === theme);
        });
    }

    function hideWelcome() {
        if (chatWelcome) chatWelcome.classList.add('hidden');
    }

    function addMessage(role, content, riskScore, meta) {
        hideWelcome();
        const div = document.createElement('div');
        div.className = `message ${role}`;
        let html = `<div class="content">${escapeHtml(content)}</div>`;
        if (riskScore && role === 'assistant') {
            const c = riskScore.toLowerCase();
            html += `<div class="risk-badge ${c}">Risk: ${riskScore}</div>`;
        }
        if (meta && role === 'assistant' && (meta.retrieval_time || meta.generation_time)) {
            html += `<div class="meta">${meta.retrieval_time || ''} retrieval · ${meta.generation_time || ''} generation</div>`;
        }
        div.innerHTML = html;
        messagesEl.appendChild(div);
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    function addSafetyResult(data) {
        hideWelcome();
        const div = document.createElement('div');
        if (data.safe === undefined || data.safe === null) {
            div.className = 'message assistant';
            div.innerHTML = '<div class="content">' + escapeHtml(data.detail || 'Analysis failed.') + '</div>';
        } else {
            div.className = 'safety-card ' + (data.safe ? 'safe' : 'not-safe');
            var html = '<div class="verdict">' + (data.safe ? 'Project is safe' : 'Project is not safe') + '</div>';
            if (data.file_name) html += '<div class="file-name">' + escapeHtml(data.file_name) + '</div>';
            if (data.risk_score) html += '<div class="risk-badge ' + (data.risk_score || '').toLowerCase() + '">Risk: ' + escapeHtml(data.risk_score) + '</div>';
            if (data.summary) html += '<div class="summary">' + escapeHtml(data.summary) + '</div>';
            div.innerHTML = html;
        }
        messagesEl.appendChild(div);
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML.replace(/\n/g, '<br>');
    }

    function stripRiskScore(text) {
        if (!text) return text;
        const lines = text.split(/\r?\n/);
        const filtered = lines.filter(l => !/^\s*Risk\s*Score\s*:\s*(Low|Medium|High)\s*$/i.test(l));
        return filtered.join('\n').trim();
    }

    function setLoading(loading) {
        if (typingIndicator) typingIndicator.classList.toggle('hidden', !loading);
        sendBtn.disabled = loading;
        userInput.disabled = loading;
    }

    async function uploadPpt(fileInput, fromHero) {
        if (!fileInput || !fileInput.files || !fileInput.files[0]) return;
        await uploadFile(fileInput, '/upload_ppt', fromHero);
    }
    async function uploadPdf(fileInput, fromHero) {
        if (!fileInput || !fileInput.files || !fileInput.files[0]) return;
        await uploadFile(fileInput, '/upload_pdf', fromHero);
    }
    async function uploadImage(fileInput, fromHero) {
        if (!fileInput || !fileInput.files || !fileInput.files[0]) return;
        await uploadFile(fileInput, '/upload_image', fromHero);
    }
    async function uploadFile(fileInput, endpoint, fromHero) {
        if (!fileInput || !fileInput.files || !fileInput.files[0]) return;
        if (!authState.authenticated) {
            openAuthModal();
            return;
        }
        var file = fileInput.files[0];
        if (fromHero) showApp();
        recordAndAddMessage('user', 'Uploaded: ' + file.name, null, null);
        setLoading(true);
        try {
            var form = new FormData();
            form.append('file', file);
            var res = await fetch(API_BASE + endpoint, {
                method: 'POST',
                body: form
            });
            var data = await parseJsonResponse(res);
            if (!res.ok) throw new Error(data.detail || res.statusText);
            // For images, also show quick vision summary if available
            if (endpoint === '/upload_image' && data.vision_summary) {
                recordAndAddMessage('assistant', data.vision_summary, null, null);
            } else {
                var msg = data.message || 'Document uploaded and indexed. You can now ask questions about it.';
                recordAndAddMessage('assistant', msg, null, null);
            }
        } catch (err) {
            recordAndAddMessage('assistant', 'Upload failed: ' + err.message, null, null);
        } finally {
            setLoading(false);
        }
        fileInput.value = '';
    }

    async function sendMessage(text) {
        if (!text || !text.trim()) return;
        if (!authState.authenticated) {
            openAuthModal();
            return;
        }
        recordAndAddMessage('user', text.trim(), null, null);
        userInput.value = '';
        setLoading(true);

        try {
            const res = await fetch(`${API_BASE}/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: text.trim() })
            });
            const data = await parseJsonResponse(res);
            if (!res.ok) throw new Error(data.detail || res.statusText);
            const cleanAnswer = stripRiskScore(data.final_answer);
            recordAndAddMessage('assistant', cleanAnswer, data.risk_score, {
                retrieval_time: data.retrieval_time,
                generation_time: data.generation_time
            });
        } catch (err) {
            recordAndAddMessage('assistant', 'Sorry, something went wrong: ' + err.message, null, null);
        } finally {
            setLoading(false);
        }
    }

    function setupSuggestions() {
        if (!suggestions) return;
        suggestions.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                const q = this.textContent.trim();
                userInput.value = q;
                sendMessage(q);
            });
        });
    }

    btnAnalyze.addEventListener('click', showApp);
    btnDemo.addEventListener('click', function () {
        showApp();
        setTimeout(function () {
            sendMessage('What are the main environmental risks in a typical construction project?');
        }, 300);
    });

    if (btnAuth) btnAuth.addEventListener('click', openAuthModal);
    if (btnLogout) btnLogout.addEventListener('click', logout);
    if (authClose) authClose.addEventListener('click', closeAuthModal);
    authTabs.forEach(t => t.addEventListener('click', function(){ setAuthView(this.getAttribute('data-view')); }));
    if (doLogin) doLogin.addEventListener('click', login);
    if (doRegister) doRegister.addEventListener('click', register);

    sendBtn.addEventListener('click', function () {
        sendMessage(userInput.value);
    });
    userInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(userInput.value);
        }
    });

    btnNewChat.addEventListener('click', function () {
        const s = createSession();
        sessions.unshift(s);
        currentSessionId = s.id;
        saveSessions();
        renderHistory();
        renderCurrentSession();
    });

    document.querySelectorAll('.nav-item[data-view]').forEach(item => {
        item.addEventListener('click', function () {
            const view = this.getAttribute('data-view');
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            this.classList.add('active');

            if (view === 'settings') {
                if (settingsPanel) settingsPanel.classList.remove('hidden');
                if (chatArea) chatArea.classList.add('hidden');
                if (inputArea) inputArea.classList.add('hidden');
            } else {
                if (settingsPanel) settingsPanel.classList.add('hidden');
                if (chatArea) chatArea.classList.remove('hidden');
                if (inputArea) inputArea.classList.remove('hidden');
            }
        });
    });

    if (heroPptInput) {
        heroPptInput.addEventListener('change', function () { uploadPpt(heroPptInput, true); });
    }
    if (chatPptInput) {
        chatPptInput.addEventListener('change', function () { uploadPpt(chatPptInput, false); });
    }
    if (heroPdfInput) {
        heroPdfInput.addEventListener('change', function () { uploadPdf(heroPdfInput, true); });
    }
    if (chatPdfInput) {
        chatPdfInput.addEventListener('change', function () { uploadPdf(chatPdfInput, false); });
    }
    if (heroImageInput) {
        heroImageInput.addEventListener('change', function () { uploadImage(heroImageInput, true); });
    }
    if (chatImageInput) {
        chatImageInput.addEventListener('change', function () { uploadImage(chatImageInput, false); });
    }

    // Theme controls
    const savedTheme = (() => {
        try {
            return localStorage.getItem('green_ai_theme');
        } catch (e) {
            return null;
        }
    })();
    setTheme(savedTheme || 'dark');

    document.querySelectorAll('.theme-option').forEach(btn => {
        btn.addEventListener('click', function () {
            const theme = this.getAttribute('data-theme');
            setTheme(theme);
        });
    });

    setupSuggestions();
    loadSessions();
    fetchMe();
})();
