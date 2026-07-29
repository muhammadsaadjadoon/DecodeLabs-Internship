let API_BASE = (() => {
  const saved = localStorage.getItem('oryn-api-base');
  if (saved !== null) return saved.trim();
  const host = window.location.hostname;
  const port = window.location.port;
  const staticPorts = new Set(['3000', '5173', '5500', '5501', '8001', '8080']);
  if (window.location.protocol === 'file:' || staticPorts.has(port)) return 'http://127.0.0.1:8000';
  if ((host === 'localhost' || host === '127.0.0.1') && port && port !== '8000') return 'http://127.0.0.1:8000';
  return '';
})();

const DEFAULT_AVATAR = `data:image/svg+xml;utf8,${encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <defs><linearGradient id="g" x1="18" y1="14" x2="110" y2="114"><stop stop-color="#4fd8ff"/><stop offset="1" stop-color="#765cff"/></linearGradient></defs>
  <rect width="128" height="128" rx="34" fill="url(#g)"/>
  <circle cx="64" cy="50" r="22" fill="white" fill-opacity=".88"/>
  <path d="M25 112c7-25 23-38 39-38s32 13 39 38" fill="white" fill-opacity=".88"/>
</svg>`)}`;

const state = {
  chats: [],
  activeChatId: null,
  activeChat: null,
  health: null,
  busy: false,
  theme: localStorage.getItem('oryn-theme') || 'dark',
  profile: loadProfile(),
  pinsOnly: false,
};

const $ = (id) => document.getElementById(id);
const els = {
  app: $('app'),
  sidebar: $('sidebar'),
  chatList: $('chatList'),
  chatSearch: $('chatSearch'),
  newChatBtn: $('newChatBtn'),
  collapsePinsBtn: $('collapsePinsBtn'),
  deleteAllChatsBtn: $('deleteAllChatsBtn'),
  messages: $('messages'),
  welcomeHero: $('welcomeHero'),
  activeTitle: $('activeTitle'),
  composerForm: $('composerForm'),
  messageInput: $('messageInput'),
  sendBtn: $('sendBtn'),
  tokenGauge: $('tokenGauge'),
  openSidebarBtn: $('openSidebarBtn'),
  closeSidebarBtn: $('closeSidebarBtn'),
  mobileBackdrop: $('mobileBackdrop'),
  settingsBtn: $('settingsBtn'),
  settingsModal: $('settingsModal'),
  closeSettingsBtn: $('closeSettingsBtn'),
  themeBtn: $('themeBtn'),
  refreshHealthBtn: $('refreshHealthBtn'),
  settingsBackendText: $('settingsBackendText'),
  statusDot: $('statusDot'),
  statusTitle: $('statusTitle'),
  statusText: $('statusText'),
  renameBtn: $('renameBtn'),
  exportBtn: $('exportBtn'),
  clearBtn: $('clearBtn'),
  pinBtn: $('pinBtn'),
  promptGrid: $('promptGrid'),
  toastWrap: $('toastWrap'),
  profileBtn: $('profileBtn'),
  profileModal: $('profileModal'),
  closeProfileBtn: $('closeProfileBtn'),
  profileAvatar: $('profileAvatar'),
  profileAvatarLarge: $('profileAvatarLarge'),
  profileNameSmall: $('profileNameSmall'),
  profileRoleSmall: $('profileRoleSmall'),
  profileNameInput: $('profileNameInput'),
  profileRoleInput: $('profileRoleInput'),
  profileNoteInput: $('profileNoteInput'),
  avatarFileInput: $('avatarFileInput'),
  uploadAvatarBtn: $('uploadAvatarBtn'),
  saveProfileBtn: $('saveProfileBtn'),
  resetProfileBtn: $('resetProfileBtn'),
  apiBaseInput: $('apiBaseInput'),
};

function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (options.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';
  const url = `${API_BASE}${path}`;
  return fetch(url, { ...options, headers, mode: 'cors' }).then(async (response) => {
    const text = await response.text();
    let data = {};
    try { data = text ? JSON.parse(text) : {}; } catch { data = { detail: text }; }
    if (!response.ok) {
      const detail = data.detail || data.message || `Backend request failed (${response.status}).`;
      throw new Error(detail);
    }
    return data;
  }).catch((error) => {
    if (error instanceof TypeError) {
      if (navigator && navigator.onLine === false) {
        throw new Error('No internet connection. Oryn could not reach the AI service. Please connect to the internet and try again.');
      }
      throw new Error('Backend is not reachable. Please start the local server and refresh the page.');
    }
    throw new Error(formatErrorMessage(error.message));
  });
}

function formatErrorMessage(message) {
  const text = String(message || '').trim();
  const lower = text.toLowerCase();
  if (!text) return 'Something went wrong. Please try again.';
  if (lower.includes('no internet') || lower.includes('network') || lower.includes('connection')) {
    return 'No internet connection. Oryn could not reach the AI service. Please connect to the internet and try again.';
  }
  if (lower.includes('gemini_api_key') || lower.includes('api key') || lower.includes('unauthorized') || lower.includes('permission')) {
    return 'The AI service is not configured correctly. Please check the API key in backend/.env and restart the server.';
  }
  if (lower.includes('quota') || lower.includes('rate') || lower.includes('429') || lower.includes('resource exhausted')) {
    return 'The AI service is temporarily busy or the usage limit has been reached. Please wait a moment and try again.';
  }
  if (lower.includes('model call failed') || lower.includes('traceback') || lower.includes('exception')) {
    return 'Oryn could not complete this request right now. Please try again in a moment.';
  }
  return text;
}

function loadProfile() {
  try {
    const saved = JSON.parse(localStorage.getItem('oryn-profile') || '{}');
    return {
      name: saved.name || 'Your profile',
      role: saved.role || 'Customize workspace',
      note: saved.note || '',
      avatar: saved.avatar || DEFAULT_AVATAR,
    };
  } catch {
    return { name: 'Your profile', role: 'Customize workspace', note: '', avatar: DEFAULT_AVATAR };
  }
}

function saveProfile(profile) {
  state.profile = { ...state.profile, ...profile };
  localStorage.setItem('oryn-profile', JSON.stringify(state.profile));
  renderProfile();
}

function renderProfile() {
  const { name, role, avatar, note } = state.profile;
  els.profileAvatar.src = avatar || DEFAULT_AVATAR;
  els.profileAvatarLarge.src = avatar || DEFAULT_AVATAR;
  els.profileNameSmall.textContent = name || 'Your profile';
  els.profileRoleSmall.textContent = role || 'Customize workspace';
  els.profileNameInput.value = name || '';
  els.profileRoleInput.value = role || '';
  els.profileNoteInput.value = note || '';
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function renderMarkdown(text) {
  const fences = [];
  let safe = escapeHtml(text).replace(/```([\s\S]*?)```/g, (_, code) => {
    const key = `@@CODE_${fences.length}@@`;
    fences.push(`<pre><code>${code.trim()}</code></pre>`);
    return key;
  });
  safe = safe
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/^### (.*)$/gm, '<h3>$1</h3>')
    .replace(/^## (.*)$/gm, '<h2>$1</h2>')
    .replace(/^# (.*)$/gm, '<h1>$1</h1>')
    .replace(/^[-•] (.*)$/gm, '<p>• $1</p>')
    .split(/\n{2,}/)
    .map((block) => block.startsWith('<pre>') || block.startsWith('<h') || block.startsWith('<p>') ? block : `<p>${block.replace(/\n/g, '<br>')}</p>`)
    .join('');
  fences.forEach((html, index) => { safe = safe.replace(`@@CODE_${index}@@`, html); });
  return safe;
}

function formatTime(timestamp) {
  if (!timestamp) return '';
  return new Date(timestamp * 1000).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function shortTime(timestamp) {
  if (!timestamp) return 'Now';
  const diff = Date.now() - timestamp * 1000;
  if (diff < 60000) return 'Now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`;
  return new Date(timestamp * 1000).toLocaleDateString([], { month: 'short', day: 'numeric' });
}

function showToast(message, type = '') {
  const item = document.createElement('div');
  item.className = `toast ${type}`.trim();
  item.textContent = message;
  els.toastWrap.appendChild(item);
  setTimeout(() => item.remove(), 3600);
}

function setBusy(value) {
  state.busy = value;
  els.sendBtn.disabled = value || !els.messageInput.value.trim();
  els.messageInput.disabled = value;
}

function updateTheme() {
  document.documentElement.dataset.theme = state.theme;
  localStorage.setItem('oryn-theme', state.theme);
}

function updateHealthUI() {
  const health = state.health;
  els.statusDot.className = 'status-dot';
  if (!health) {
    els.statusDot.classList.add('bad');
    els.statusTitle.textContent = 'Offline';
    els.statusText.textContent = 'Backend unavailable';
    els.settingsBackendText.textContent = 'Backend unavailable. Check the server terminal.';
    return;
  }
  if (health.api_key_configured) {
    els.statusDot.classList.add('ok');
    els.statusTitle.textContent = 'AI connected';
    els.statusText.textContent = health.model || 'Model ready';
    els.settingsBackendText.textContent = `Connected · ${health.model || 'model ready'}`;
  } else if (health.demo_mode) {
    els.statusTitle.textContent = 'Demo mode';
    els.statusText.textContent = 'Add GEMINI_API_KEY';
    els.settingsBackendText.textContent = 'Demo mode is active. Add GEMINI_API_KEY in backend/.env for real replies.';
  } else {
    els.statusDot.classList.add('bad');
    els.statusTitle.textContent = 'Key missing';
    els.statusText.textContent = 'Configure .env';
    els.settingsBackendText.textContent = 'GEMINI_API_KEY is missing in backend/.env.';
  }
}

async function loadHealth() {
  try { state.health = await api('/api/health'); }
  catch { state.health = null; }
  updateHealthUI();
}

async function loadChats() {
  const data = await api('/api/chats');
  state.chats = data.chats || [];
  renderChatList();
}

function filteredChats() {
  const q = els.chatSearch.value.trim().toLowerCase();
  let chats = state.chats;
  if (state.pinsOnly) chats = chats.filter((chat) => chat.pinned);
  if (!q) return chats;
  return chats.filter((chat) => `${chat.title} ${chat.preview}`.toLowerCase().includes(q));
}

function chatItemTemplate(chat) {
  const active = chat.id === state.activeChatId ? 'active' : '';
  const star = chat.pinned ? '<span class="star">★</span>' : '';
  return `
    <button class="chat-item ${active}" data-chat-id="${chat.id}" type="button">
      <b title="${escapeHtml(chat.title)}">${escapeHtml(chat.title || 'New chat')}</b>
      <span class="time">${shortTime(chat.updated_at)}</span>
      <small>${escapeHtml(chat.preview || 'No messages yet')}</small>
      <span class="meta"><span>${chat.message_count || 0} messages</span><span>·</span><span>${chat.pinned ? 'Pinned' : 'Recent'}</span>${star}</span>
    </button>
  `;
}

function renderChatList() {
  const chats = filteredChats();
  els.collapsePinsBtn.textContent = state.pinsOnly ? 'Pinned' : 'All';
  if (!chats.length) {
    els.chatList.innerHTML = `<div class="chat-empty">No chats found</div>`;
    return;
  }
  const pinned = chats.filter((chat) => chat.pinned);
  const recent = chats.filter((chat) => !chat.pinned);
  let html = '';
  if (pinned.length) html += `<div class="chat-group-label">Pinned</div>${pinned.map(chatItemTemplate).join('')}`;
  if (recent.length) html += `${pinned.length ? '<div class="chat-group-label">Recent</div>' : ''}${recent.map(chatItemTemplate).join('')}`;
  els.chatList.innerHTML = html;
}

async function ensureChat() {
  if (state.chats.length) await openChat(state.chats[0].id);
  else await createChat();
}

async function createChat(title = 'New chat') {
  try {
    const chat = await api('/api/chats', { method: 'POST', body: JSON.stringify({ title }) });
    await loadChats();
    await openChat(chat.id);
    els.messageInput.focus();
    closeMobileSidebar();
    return chat;
  } catch (error) {
    showToast(error.message, 'bad');
    throw error;
  }
}

async function openChat(chatId) {
  if (!chatId) return;
  try {
    const chat = await api(`/api/chats/${chatId}`);
    state.activeChatId = chat.id;
    state.activeChat = chat;
    els.activeTitle.textContent = chat.title || 'New chat';
    renderChatList();
    renderMessages();
    updatePinButton();
    closeMobileSidebar();
  } catch (error) {
    showToast(error.message, 'bad');
  }
}

function updatePinButton() {
  const pinned = Boolean(state.activeChat?.pinned);
  els.pinBtn.classList.toggle('primary', pinned);
  els.pinBtn.querySelector('span').textContent = pinned ? 'Pinned' : 'Pin';
}

function renderMessages() {
  const messages = state.activeChat?.messages || [];
  const hasMessages = messages.length > 0;
  els.welcomeHero.hidden = hasMessages;
  els.messages.classList.toggle('show', hasMessages);
  els.messages.innerHTML = messages.map((message, index) => {
    const assistant = message.role === 'assistant';
    const lastAssistant = assistant && index === messages.length - 1;
    const avatar = assistant
      ? '<img src="assets/zorex-oryn-logo.svg" alt="" />'
      : `<img src="${escapeHtml(state.profile.avatar || DEFAULT_AVATAR)}" alt="" />`;
    return `
      <article class="message-row ${message.role}" data-message-id="${message.id}">
        <div class="message-avatar">${avatar}</div>
        <div class="message-body">
          <div class="message-head"><b>${assistant ? 'Oryn' : 'You'}</b><span>${formatTime(message.timestamp)}</span></div>
          <div class="message-card"><div class="message-content">${renderMarkdown(message.content)}</div></div>
          <div class="message-actions">
            <button class="mini-btn copy-message" type="button">Copy</button>
            ${lastAssistant ? '<button class="mini-btn regenerate-message" type="button">Regenerate</button>' : ''}
          </div>
        </div>
      </article>
    `;
  }).join('');
  requestAnimationFrame(() => { els.messages.scrollTop = els.messages.scrollHeight; });
  const stats = state.activeChat?.stats;
  if (stats) els.tokenGauge.textContent = `${stats.message_count} messages · ${stats.estimated_tokens}/${stats.max_history_tokens} tokens`;
  else els.tokenGauge.textContent = 'Ready';
}

function addTypingIndicator() {
  els.welcomeHero.hidden = true;
  els.messages.classList.add('show');
  const node = document.createElement('article');
  node.className = 'message-row assistant';
  node.id = 'typingIndicator';
  node.innerHTML = `
    <div class="message-avatar"><img src="assets/zorex-oryn-logo.svg" alt="" /></div>
    <div class="message-body">
      <div class="message-head"><b>Oryn</b><span>Thinking</span></div>
      <div class="message-card"><div class="typing"><i></i><i></i><i></i></div></div>
    </div>
  `;
  els.messages.appendChild(node);
  els.messages.scrollTop = els.messages.scrollHeight;
}

function removeTypingIndicator() {
  const node = $('typingIndicator');
  if (node) node.remove();
}

async function sendMessage(textOverride) {
  const message = (textOverride ?? els.messageInput.value).trim();
  if (!message || state.busy) return;
  if (!state.activeChatId) {
    try { await createChat(); } catch { return; }
  }
  const localUser = { id: `local_${Date.now()}`, role: 'user', content: message, timestamp: Date.now() / 1000 };
  state.activeChat.messages = [...(state.activeChat.messages || []), localUser];
  renderMessages();
  els.messageInput.value = '';
  autosizeInput();
  setBusy(true);
  addTypingIndicator();
  try {
    const data = await api(`/api/chats/${state.activeChatId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
    state.activeChat = data;
    await loadChats();
    renderMessages();
  } catch (error) {
    removeTypingIndicator();
    state.activeChat.messages = (state.activeChat.messages || []).filter((m) => m.id !== localUser.id);
    renderMessages();
    showToast(error.message, 'bad');
  } finally {
    removeTypingIndicator();
    setBusy(false);
    els.messageInput.focus();
  }
}

async function regenerateLast() {
  if (!state.activeChatId || state.busy) return;
  setBusy(true);
  addTypingIndicator();
  try {
    state.activeChat = await api(`/api/chats/${state.activeChatId}/regenerate`, { method: 'POST', body: JSON.stringify({}) });
    await loadChats();
    renderMessages();
    showToast('Response regenerated', 'good');
  } catch (error) {
    showToast(error.message, 'bad');
  } finally {
    removeTypingIndicator();
    setBusy(false);
  }
}

function autosizeInput() {
  const input = els.messageInput;
  input.style.height = 'auto';
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
  els.sendBtn.disabled = state.busy || !input.value.trim();
}

async function renameActiveChat() {
  if (!state.activeChatId) return;
  const current = state.activeChat?.title || 'New chat';
  const title = prompt('Rename chat', current);
  if (title === null) return;
  const cleaned = title.trim();
  if (!cleaned) return showToast('Title cannot be empty.', 'bad');
  try {
    const chat = await api(`/api/chats/${state.activeChatId}`, { method: 'PATCH', body: JSON.stringify({ title: cleaned }) });
    state.activeChat = chat;
    els.activeTitle.textContent = chat.title;
    await loadChats();
    showToast('Chat renamed', 'good');
  } catch (error) { showToast(error.message, 'bad'); }
}

async function togglePinActiveChat() {
  if (!state.activeChatId) return;
  try {
    const chat = await api(`/api/chats/${state.activeChatId}`, { method: 'PATCH', body: JSON.stringify({ pinned: !state.activeChat?.pinned }) });
    state.activeChat = chat;
    await loadChats();
    updatePinButton();
    showToast(chat.pinned ? 'Chat pinned' : 'Chat unpinned', 'good');
  } catch (error) { showToast(error.message, 'bad'); }
}

async function clearActiveChat() {
  if (!state.activeChatId) return;
  if (!confirm('Clear all messages in this chat?')) return;
  try {
    state.activeChat = await api(`/api/chats/${state.activeChatId}/clear`, { method: 'POST' });
    els.activeTitle.textContent = state.activeChat?.title || 'New chat';
    await loadChats();
    updatePinButton();
    renderMessages();
    showToast('Chat cleared and reset', 'good');
  } catch (error) { showToast(error.message, 'bad'); }
}

async function deleteAllChats() {
  const chats = [...state.chats];
  if (!chats.length) {
    showToast('No chats to delete.', 'bad');
    return;
  }
  if (!confirm(`Delete all ${chats.length} chats? This cannot be undone.`)) return;
  try {
    await Promise.all(chats.map((chat) => api(`/api/chats/${chat.id}`, { method: 'DELETE' }).catch(() => null)));
    state.activeChatId = null;
    state.activeChat = null;
    state.pinsOnly = false;
    els.chatSearch.value = '';
    els.activeTitle.textContent = 'New chat';
    await loadChats();
    renderMessages();
    updatePinButton();
    showToast('All chats deleted', 'good');
  } catch (error) {
    showToast(error.message, 'bad');
  }
}

function exportActiveChat() {
  if (!state.activeChat) return;
  const lines = [`# ${state.activeChat.title || 'Oryn chat'}`, ''];
  for (const message of state.activeChat.messages || []) {
    lines.push(`## ${message.role === 'assistant' ? 'Oryn' : 'You'} · ${formatTime(message.timestamp)}`);
    lines.push(message.content);
    lines.push('');
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${(state.activeChat.title || 'oryn-chat').replace(/[^a-z0-9]+/gi, '-').toLowerCase()}.md`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  showToast('Chat exported', 'good');
}

function isMobileSidebarLayout() {
  return window.matchMedia('(max-width: 760px)').matches;
}

function openMobileSidebar() { els.app.classList.add('sidebar-open'); }
function closeMobileSidebar() { els.app.classList.remove('sidebar-open'); }

function openSidebarPanel() {
  if (isMobileSidebarLayout()) {
    openMobileSidebar();
    return;
  }
  els.app.classList.remove('sidebar-collapsed');
}

function closeSidebarPanel() {
  if (isMobileSidebarLayout()) {
    closeMobileSidebar();
    return;
  }
  els.app.classList.add('sidebar-collapsed');
}

function syncSidebarMode() {
  if (isMobileSidebarLayout()) {
    els.app.classList.remove('sidebar-collapsed');
  } else {
    closeMobileSidebar();
  }
}
function openModal(modal) { modal.classList.add('show'); modal.setAttribute('aria-hidden', 'false'); }
function closeModal(modal) { modal.classList.remove('show'); modal.setAttribute('aria-hidden', 'true'); }

function applyToolPrompt(tool) {
  const prefixes = {
    focus: 'Make this clear, focused, and practical: ',
    draft: 'Draft this professionally: ',
    code: 'Help me write or improve this code: ',
    explain: 'Explain this simply with examples: ',
  };
  const prefix = prefixes[tool] || '';
  els.messageInput.value = prefix + els.messageInput.value;
  autosizeInput();
  els.messageInput.focus();
}

function bindEvents() {
  els.newChatBtn.addEventListener('click', () => createChat());
  els.chatSearch.addEventListener('input', renderChatList);
  els.collapsePinsBtn.addEventListener('click', () => { state.pinsOnly = !state.pinsOnly; renderChatList(); });
  els.deleteAllChatsBtn?.addEventListener('click', deleteAllChats);
  els.chatList.addEventListener('click', (event) => {
    const item = event.target.closest('[data-chat-id]');
    if (item) openChat(item.dataset.chatId);
  });
  els.composerForm.addEventListener('submit', (event) => { event.preventDefault(); sendMessage(); });
  els.messageInput.addEventListener('input', autosizeInput);
  els.messageInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage(); }
  });
  els.messages.addEventListener('click', async (event) => {
    const copyBtn = event.target.closest('.copy-message');
    if (copyBtn) {
      const row = copyBtn.closest('[data-message-id]');
      const message = (state.activeChat?.messages || []).find((m) => m.id === row?.dataset.messageId);
      if (message) {
        await navigator.clipboard.writeText(message.content);
        showToast('Message copied', 'good');
      }
      return;
    }
    if (event.target.closest('.regenerate-message')) regenerateLast();
  });
  els.promptGrid.addEventListener('click', (event) => {
    const btn = event.target.closest('[data-prompt]');
    if (!btn) return;
    els.messageInput.value = btn.dataset.prompt;
    autosizeInput();
    els.messageInput.focus();
  });
  document.querySelector('.tool-row').addEventListener('click', (event) => {
    const btn = event.target.closest('[data-tool]');
    if (btn) applyToolPrompt(btn.dataset.tool);
  });
  els.renameBtn.addEventListener('click', renameActiveChat);
  els.clearBtn.addEventListener('click', clearActiveChat);
  els.exportBtn.addEventListener('click', exportActiveChat);
  els.pinBtn.addEventListener('click', togglePinActiveChat);
  els.openSidebarBtn.addEventListener('click', openSidebarPanel);
  els.closeSidebarBtn.addEventListener('click', closeSidebarPanel);
  els.mobileBackdrop.addEventListener('click', closeMobileSidebar);
  window.addEventListener('resize', syncSidebarMode);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeMobileSidebar();
      closeModal(els.settingsModal);
      closeModal(els.profileModal);
    }
  });
  els.settingsBtn.addEventListener('click', () => openModal(els.settingsModal));
  els.closeSettingsBtn.addEventListener('click', () => closeModal(els.settingsModal));
  els.settingsModal.addEventListener('click', (event) => { if (event.target === els.settingsModal) closeModal(els.settingsModal); });
  els.themeBtn.addEventListener('click', () => { state.theme = state.theme === 'dark' ? 'light' : 'dark'; updateTheme(); });
  els.refreshHealthBtn.addEventListener('click', loadHealth);
  if (els.apiBaseInput) {
    els.apiBaseInput.addEventListener('change', () => {
      API_BASE = els.apiBaseInput.value.trim();
      localStorage.setItem('oryn-api-base', API_BASE);
      loadHealth();
      showToast('API base updated', 'good');
    });
  }
  els.profileBtn.addEventListener('click', () => openModal(els.profileModal));
  els.closeProfileBtn.addEventListener('click', () => closeModal(els.profileModal));
  els.profileModal.addEventListener('click', (event) => { if (event.target === els.profileModal) closeModal(els.profileModal); });
  els.uploadAvatarBtn.addEventListener('click', () => els.avatarFileInput.click());
  els.avatarFileInput.addEventListener('change', () => {
    const file = els.avatarFileInput.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) return showToast('Please select an image file.', 'bad');
    const reader = new FileReader();
    reader.onload = () => saveProfile({ avatar: String(reader.result) });
    reader.readAsDataURL(file);
  });
  els.saveProfileBtn.addEventListener('click', () => {
    saveProfile({
      name: els.profileNameInput.value.trim() || 'Your profile',
      role: els.profileRoleInput.value.trim() || 'Customize workspace',
      note: els.profileNoteInput.value.trim(),
    });
    closeModal(els.profileModal);
    showToast('Profile saved', 'good');
  });
  els.resetProfileBtn.addEventListener('click', () => {
    localStorage.removeItem('oryn-profile');
    state.profile = loadProfile();
    renderProfile();
    showToast('Profile reset', 'good');
  });
  document.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      els.chatSearch.focus();
    }
    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key.toLowerCase() === 'o') {
      event.preventDefault();
      createChat();
    }
    if (event.key === 'Escape') {
      closeModal(els.settingsModal);
      closeModal(els.profileModal);
      closeMobileSidebar();
    }
  });
}

async function init() {
  updateTheme();
  renderProfile();
  if (els.apiBaseInput) els.apiBaseInput.value = API_BASE;
  bindEvents();
  autosizeInput();
  syncSidebarMode();
  await loadHealth();
  try {
    await loadChats();
    await ensureChat();
  } catch (error) {
    showToast(error.message, 'bad');
  }
}

init();
