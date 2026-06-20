/* ═══════════════════════════════════════════════════════════
   VisePanda v5.0.9 — Frontend Application
   ═══════════════════════════════════════════════════════════ */

const VP = (function(){
  // ── Panda Mood System ──
  let _pandaMood = 'default';
  const PANDA_MOODS = {
    default:  {emoji: '🐼', label: 'Default'},
    food:     {emoji: '😋', label: 'Food'},
    money:    {emoji: '💰', label: 'Money'},
    sight:    {emoji: '🕶️', label: 'Sightseeing'},
    tip:      {emoji: '📌', label: 'Tip'},
    happy:    {emoji: '😊', label: 'Happy'},
    thinking: {emoji: '🤔', label: 'Thinking'},
    sorry:    {emoji: '😅', label: 'Sorry'},
    hotel:    {emoji: '🏨', label: 'Hotel'},
    transit:  {emoji: '🚄', label: 'Transit'},
  };

  const PANDA_KEYWORDS = [
    {pattern: /吃|eat|food|美食|restaurant|饭|菜|餐|尝|taste|delicious|yummy/i, mood: 'food'},
    {pattern: /价格|price|cost|费用|budget|预算|money|¥|free|cheap|expensive|收费/i, mood: 'money'},
    {pattern: /景点|visit|see|tour|attraction|逛|玩|gsight|park|temple|museum|palace|长城|故宫/i, mood: 'sight'},
    {pattern: /tip|注意|建议|advice|小心|提醒|remember|别忘了/i, mood: 'tip'},
    {pattern: /great|nice|good|wonderful|perfect|awesome|不错|好|棒/i, mood: 'happy'},
    {pattern: /let me|let's|让我|我想|maybe|perhaps|可以|option/i, mood: 'thinking'},
    {pattern: /sorry|抱歉|against|错误|error|unable|cannot|麻烦/i, mood: 'sorry'},
    {pattern: /hotel|住宿|住|stay|room|房间|hostel|inn/i, mood: 'hotel'},
    {pattern: /flight|飞机|高铁|train|地铁|bus|交通|transport|taxi|打车/i, mood: 'transit'},
  ];

  function setPandaMood(token) {
    if (!token || typeof token !== 'string') return;
    PANDA_KEYWORDS.some(({pattern, mood}) => {
      if (pattern.test(token)) {
        if (_pandaMood !== mood) {
          _pandaMood = mood;
          updatePandaAvatars();
        }
        return true;
      }
      return false;
    });
  }

  function resetPandaMood() {
    if (_pandaMood !== 'default') {
      _pandaMood = 'default';
      updatePandaAvatars();
    }
  }

  function getPandaAvatar() {
    const mood = PANDA_MOODS[_pandaMood] || PANDA_MOODS.default;
    return `<span class="panda-avatar" data-mood="${_pandaMood}">🐼<span class="panda-mood-badge">${mood.emoji}</span></span>`;
  }

  function updatePandaAvatars() {
    const html = getPandaAvatar();
    document.querySelectorAll('.msg-avatar').forEach(el => {
      // Only update assistant/typing avatars, not user ones
      if (el.closest('.msg-assistant, .msg-bot') || el.closest('#typing-msg')) {
        el.innerHTML = html;
      }
    });
  }
  'use strict';

  // ── State ──
  const state = {
    currentView: 'home',
    messages: [],
    isStreaming: false,
    theme: document.documentElement.getAttribute('data-theme') || 'dark',
    cityFilter: 'all',
    cityCatalog: null,
  };
  const supportedViews = new Set(['home', 'chat', 'trips', 'cities', 'tools', 'map']);

  // ── DOM refs ──
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => document.querySelectorAll(s);

  // ── Minimal Markdown Renderer ──
  function renderMD(text) {
    if (!text) return '';
    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Code blocks
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // Horizontal rules
    html = html.replace(/^-{3,}$/gm, '<hr>');

    // Lists (unordered): - item
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Lists (ordered): 1. item
    html = html.replace(/^\d+\.\s(.+)$/gm, '<li>$1</li>');
    // Only wrap in <ol> if there are <li> not already in <ul>
    html = html.replace(/(?<!<ul>)((<li>.*<\/li>\n?)+)(?!<\/ul>)/g, '<ol>$1</ol>');

    // Paragraphs
    const parts = html.split(/\n\n+/);
    return parts.map(p => {
      p = p.trim();
      if (!p) return '';
      if (p.startsWith('<')) return p;
      return `<p>${p.replace(/\n/g, '<br>')}</p>`;
    }).join('');
  }

  // ── Navigation ──
  function navigate(view) {
    const target = document.getElementById(`view-${view}`);
    if (!target || !supportedViews.has(view)) return;

    state.currentView = view;
    // Update both desktop and mobile nav buttons
    $$('.nav-btn, .bn-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.view === view);
    });
    $$('.view').forEach(v => v.classList.remove('active'));
    target.classList.add('active');

    if (view === 'cities') loadCities();
    if (view === 'trips') loadTrips();
    if (view === 'tools') loadTools();
    if (view === 'home') loadHomeCities();
    if (view === 'map') initMap();
    // Close chat overlay if open
    closeChatOverlay();
    attachImageFallbacks(target);

    window.location.hash = view;
  }

  function safeInitStep(name, fn) {
    try {
      const result = fn();
      if (result && typeof result.then === 'function') {
        return result.catch((error) => {
          console.error('[VP:init]', name, error);
          showGlobalError(`Failed to initialize ${name}.`);
        });
      }
      return result;
    } catch (error) {
      console.error('[VP:init]', name, error);
      showGlobalError(`Failed to initialize ${name}.`);
      return null;
    }
  }

  function showGlobalLoading(message) {
    const box = document.getElementById('global-loading-state');
    if (!box) return;
    const copy = box.querySelector('.global-loading-copy');
    if (copy && message) copy.textContent = message;
    box.classList.remove('hidden');
  }

  function hideGlobalLoading() {
    const box = document.getElementById('global-loading-state');
    if (box) box.classList.add('hidden');
  }

  function showGlobalError(message) {
    hideGlobalLoading();
    const box = document.getElementById('global-error-state');
    if (!box) return;
    const copy = box.querySelector('.global-error-copy');
    if (copy && message) copy.textContent = message;
    box.classList.remove('hidden');
  }

  function hideGlobalError() {
    const box = document.getElementById('global-error-state');
    if (!box) return;
    box.classList.add('hidden');
    const copy = box.querySelector('.global-error-copy');
    if (copy) copy.textContent = 'Something stalled while loading this screen.';
  }

  function setViewState(view, state, message = '') {
    const section = document.getElementById(`view-${view}`);
    const loading = document.getElementById(`${view}-loading`);
    const error = document.getElementById(`${view}-error`);

    if (loading) loading.classList.toggle('hidden', state !== 'loading');
    if (error) {
      error.classList.toggle('hidden', state !== 'error');
      if (state === 'error' && message) {
        const text = error.querySelector('span');
        if (text) text.textContent = message;
      }
    }
    if (section) {
      section.setAttribute('aria-busy', state === 'loading' ? 'true' : 'false');
    }
  }

  function retryCurrentView() {
    hideGlobalError();
    navigate(state.currentView || 'home');
  }

  function attachImageFallbacks(root = document) {
    root.querySelectorAll('img[data-img-fallback]').forEach((img) => {
      if (img.dataset.fallbackBound === 'true') return;
      img.dataset.fallbackBound = 'true';
      img.addEventListener('error', () => {
        const fallback = img.dataset.imgFallback;
        if (fallback && img.getAttribute('src') !== fallback) {
          img.src = fallback;
          img.classList.add('img-fallback');
          return;
        }
        img.closest('.image-shell')?.classList.add('image-shell-failed');
      });
    });
  }

  // ── Focus chat on a city (uses overlay on mobile) ──
  function focusChat(city) {
    const isMobile = window.innerWidth <= 640;
    if (isMobile) {
      openChatOverlay(city);
      return;
    }
    const input = document.getElementById('chat-input');
    if (input) {
      input.value = `Plan a trip to ${city}`;
      input.style.height = 'auto';
      toggleSendButton(true);
      input.focus();
    }
  }

  // ── Chat Overlay (mobile) ──
  function syncOverlayMessages() {
    const mainContainer = document.getElementById('chat-messages');
    const overlayContainer = document.getElementById('chat-messages-overlay');
    if (!mainContainer || !overlayContainer) return;
    overlayContainer.innerHTML = mainContainer.innerHTML;
    overlayContainer.scrollTop = overlayContainer.scrollHeight;
  }

  function openChatOverlay(city) {
    const overlay = document.getElementById('chat-overlay');
    const input = document.getElementById('chat-input-overlay');
    const stopBtn = document.getElementById('chat-stop-overlay');
    const sendBtn = document.getElementById('chat-send-overlay');
    if (!overlay) return;
    overlay.classList.remove('hidden');
    syncOverlayMessages();
    // Show stop button if streaming
    if (state.isStreaming && stopBtn) {
      stopBtn.style.display = 'inline-block';
      if (sendBtn) sendBtn.style.display = 'none';
    }
    if (input && city) {
      input.value = `Plan a trip to ${city}`;
      input.style.height = 'auto';
      toggleSendOverlayBtn(true);
      setTimeout(() => input.focus(), 350);
    }
  }

  function closeChatOverlay() {
    const overlay = document.getElementById('chat-overlay');
    if (overlay) overlay.classList.add('hidden');
  }

  function chatOverlayBack() {
    closeChatOverlay();
  }

  function syncOverlayMessages() {
    const mainContainer = document.getElementById('chat-messages');
    const overlayContainer = document.getElementById('chat-messages-overlay');
    if (!mainContainer || !overlayContainer) return;
    // Clone main chat messages into overlay
    overlayContainer.innerHTML = mainContainer.innerHTML;
    overlayContainer.scrollTop = overlayContainer.scrollHeight;
  }

  function toggleSendOverlayBtn(enable) {
    const btn = document.getElementById('chat-send-overlay');
    if (btn) btn.disabled = !enable;
  }

  // ── Send message via chat overlay ──
  function sendOverlayMessage() {
    const input = document.getElementById('chat-input-overlay');
    const btn = document.getElementById('chat-send-overlay');
    if (!input || !input.value.trim()) return;
    // Sync input to main chat input and send
    const mainInput = document.getElementById('chat-input');
    if (mainInput) {
      mainInput.value = input.value;
      mainInput.style.height = 'auto';
    }
    closeChatOverlay();
    navigate('chat');
    sendMessage();
  }

  // ── Theme ──
  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('vp_theme', next);
    state.theme = next;
    const btn = document.querySelector('.theme-toggle');
    if (btn) btn.textContent = next === 'dark' ? '🌙' : '☀️';
  }

  function initTheme() {
    const themeBtn = document.querySelector('.theme-toggle');
    if (themeBtn) themeBtn.textContent = state.theme === 'dark' ? '🌙' : '☀️';
  }

  function hydrateRuntimeConfig() {
    return fetch('/api/config').then(r => r.json()).then(config => {
      const ver = config.version || '5.0.9';
      const badge = document.getElementById('version-badge');
      const footerVer = document.getElementById('footer-version');
      const gsi = document.getElementById('g_id_onload');
      if (badge) badge.textContent = 'v' + ver;
      if (footerVer) footerVer.textContent = 'VisePanda v' + ver;
      if (gsi) gsi.dataset.client_id = config.google_client_id || '';
    }).catch(() => {});
  }

  function initScrollToTop() {
    const stBtn = document.getElementById('scroll-top-btn');
    if (!stBtn || stBtn.dataset.bound === 'true') return;
    stBtn.dataset.bound = 'true';
    window.addEventListener('scroll', function() {
      stBtn.classList.toggle('visible', window.scrollY > 400);
    }, { passive: true });
  }

  function initHashNavigation() {
    if (document.body.dataset.hashNavBound === 'true') return;
    document.body.dataset.hashNavBound = 'true';
    window.addEventListener('hashchange', () => {
      const hash = (window.location.hash || '#home').replace('#', '');
      if (supportedViews.has(hash) && hash !== state.currentView) {
        navigate(hash);
      }
    });
  }

  function bindAuthTriggers() {
    const authBtn = document.getElementById('auth-btn');
    if (!authBtn || authBtn.dataset.bound === 'true') return;
    authBtn.dataset.bound = 'true';
    authBtn.removeAttribute('onclick');
    authBtn.disabled = false;
    if (!auth.isLoggedIn()) authBtn.style.display = 'block';
    authBtn.addEventListener('click', (event) => {
      event.preventDefault();
      hideGlobalError();
      auth.showModal();
    });
  }

  function bindPrimaryNav() {
    document.querySelectorAll('.nav-btn, .bn-btn').forEach((btn) => {
      if (btn.dataset.bound === 'true') return;
      btn.dataset.bound = 'true';
      btn.removeAttribute('onclick');
      btn.disabled = false;
      btn.addEventListener('click', (event) => {
        event.preventDefault();
        hideGlobalError();
        if (btn.dataset.view && supportedViews.has(btn.dataset.view)) {
          navigate(btn.dataset.view);
        }
      });
    });
  }

  function bindChatInputs() {
    const chatInput = document.getElementById('chat-input');
    if (chatInput && chatInput.dataset.bound !== 'true') {
      chatInput.dataset.bound = 'true';
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendMessage();
        }
      });
      chatInput.addEventListener('input', () => {
        toggleSendButton(chatInput.value.trim().length > 0);
      });
    }

    const overlayInput = document.getElementById('chat-input-overlay');
    if (overlayInput && overlayInput.dataset.bound !== 'true') {
      overlayInput.dataset.bound = 'true';
      overlayInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendOverlayMessage();
        }
      });
      overlayInput.addEventListener('input', () => {
        toggleSendOverlayBtn(overlayInput.value.trim().length > 0);
      });
    }

    const overlaySend = document.getElementById('chat-send-overlay');
    if (overlaySend && overlaySend.dataset.bound !== 'true') {
      overlaySend.dataset.bound = 'true';
      overlaySend.addEventListener('click', sendOverlayMessage);
    }

    const overlayStop = document.getElementById('chat-stop-overlay');
    if (overlayStop && overlayStop.dataset.bound !== 'true') {
      overlayStop.dataset.bound = 'true';
      overlayStop.addEventListener('click', stopStreaming);
    }
  }

  function initStartupState() {
    const hasHistory = loadMessages();
    if (hasHistory) restoreChatMessages();
    updateSuggestions();
    ensureCityCatalog().catch(() => {});
    setupCitiesFilterRail();
    applyCitiesFilter(state.cityFilter);
    renderSuggestions();
  }

  // ── API helpers ──
  async function apiGet(path) {
    try {
      const r = await fetch(path);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (e) {
      console.error(`API GET ${path}:`, e);
      return null;
    }
  }

  // ── Chat History Persistence ──
  function saveMessages() {
    try {
      localStorage.setItem('vp_chat_msgs', JSON.stringify(state.messages.slice(-50)));
    } catch (e) { /* quota exceeded - ignore */ }
  }

  function loadMessages() {
    try {
      const saved = localStorage.getItem('vp_chat_msgs');
      if (saved) {
        const msgs = JSON.parse(saved);
        if (Array.isArray(msgs) && msgs.length) {
          state.messages = msgs;
          return true;
        }
      }
    } catch (e) { /* corrupt data */ }
    return false;
  }

  function restoreChatMessages() {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    // Keep welcome message, then restore history
    const welcome = container.querySelector('.msg-bot:first-child');
    container.innerHTML = '';
    if (welcome) container.appendChild(welcome.cloneNode(true));

    state.messages.forEach(msg => {
      const el = document.createElement('div');
      el.className = `msg msg-${msg.role}`;
      el.innerHTML = `
        <div class="msg-avatar">${msg.role === 'assistant' ? '🐼' : '👤'}</div>
        <div class="msg-body">
          <div class="msg-sender">${msg.role === 'assistant' ? 'VisePanda' : 'You'}</div>
          <div class="msg-text">${renderMD(msg.content)}</div>
        </div>
      `;
      container.appendChild(el);
    });
    container.scrollTop = container.scrollHeight;
  }

  function clearChatHistory() {
    state.messages = [];
    localStorage.removeItem('vp_chat_msgs');
    const container = document.getElementById('chat-messages');
    if (container) {
      container.innerHTML = `
        <div class="msg msg-bot">
          <div class="msg-avatar">🐼</div>
          <div class="msg-body">
            <div class="msg-sender">VisePanda</div>
            <div class="msg-text">Hi! I'm your China travel assistant. Tell me what kind of trip you're planning — cities, duration, interests, budget... I'll create a personalized itinerary for you! 🌏</div>
          </div>
        </div>
      `;
    }
  }

  // ── HTML escape helper ──
  function escHtml(s) {
    if (typeof s !== 'string') return '';
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }

  function escAttr(s) {
    return escHtml(String(s || ''));
  }

  function formatDisplayText(primary, chinese) {
    const first = typeof primary === 'string' ? primary.trim() : '';
    const second = typeof chinese === 'string' ? chinese.trim() : '';
    if (first && second && first !== second) return `${first}（${second}）`;
    return first || second || '';
  }

  function humanizeCityKey(key) {
    const special = {
      xian: "Xi'an",
      lasa: 'Lhasa',
      hohhot: 'Hohhot',
      jiuzhaigou: 'Jiuzhaigou',
      zhangjiajie: 'Zhangjiajie',
    };
    if (!key) return '';
    return special[key] || key.replace(/(^|-)([a-z])/g, (_, sep, ch) => `${sep === '-' ? ' ' : ''}${ch.toUpperCase()}`);
  }

  async function ensureCityCatalog() {
    if (state.cityCatalog && Object.keys(state.cityCatalog).length) return state.cityCatalog;
    const data = await apiGet('/api/cities');
    state.cityCatalog = data && data.cities ? data.cities : null;
    return state.cityCatalog;
  }

  // ── City emoji helper ──
  function getCityEmoji(name) {
    const map = {
      beijing:'🏯', shanghai:'🌃', chengdu:'🐼', guangzhou:'🥟',
      shenzhen:'🌆', hangzhou:'🌊', xi_an:'🏛️', guilin:'🏞️',
      chongqing:'🌉', kunming:'🌸', suzhou:'🏯', nanjing:'🏛️',
      lhasa:'🏔️', hong_kong:'🌃', macau:'🎰',
    };
    return map[name.toLowerCase().replace(/ /g,'_')] || '🏙️';
  }

  // ── City tag extractor ──
  function getCityTags(name, info) {
    const tags = [];
    const vibe = (info.vibe || '').toLowerCase();
    if (vibe.includes('food') || vibe.includes('cuisine') || name === 'chengdu' || name === 'guangzhou') tags.push('🍜 Foodie');
    if (vibe.includes('nature') || vibe.includes('mountain') || vibe.includes('scenery')) tags.push('🏞️ Nature');
    if (vibe.includes('history') || vibe.includes('ancient') || vibe.includes('culture')) tags.push('🏛️ History');
    if (vibe.includes('modern') || vibe.includes('city')) tags.push('🌃 Urban');
    if (vibe.includes('nightlife') || vibe.includes('vibrant')) tags.push('🌙 Nightlife');
    if (!tags.length) tags.push('📍 Destination');
    return tags.slice(0, 2);
  }

  function getCityFilterKeys(name, info, tags) {
    const keys = new Set();
    const vibe = (info.vibe || '').toLowerCase();
    const base = tags.join(' ').toLowerCase();
    if (vibe.includes('history') || vibe.includes('ancient') || vibe.includes('culture') || base.includes('history')) keys.add('history');
    if (vibe.includes('food') || vibe.includes('cuisine') || base.includes('foodie') || ['chengdu', 'guangzhou'].includes(name.toLowerCase())) keys.add('food');
    if (vibe.includes('nature') || vibe.includes('mountain') || vibe.includes('scenery') || base.includes('nature')) keys.add('nature');
    if (vibe.includes('modern') || vibe.includes('city') || vibe.includes('nightlife') || base.includes('urban')) keys.add('urban');
    if (!keys.size) keys.add('all');
    return Array.from(keys);
  }

  // ── Create city card element ──
  function createCityCard(name, info) {
    const card = document.createElement('div');
    card.className = 'city-card';
    card.onclick = () => openCityDetail(name);

    const emoji = getCityEmoji(name);
    const hasImg = info.image ? true : false;
    if (hasImg) card.classList.add('has-img');
    const tags = getCityTags(name, info);
    const filterKeys = getCityFilterKeys(name, info, tags);
    card.dataset.filters = filterKeys.join(' ');

    let imgHtml = '';
    if (hasImg) {
      imgHtml = `
        <div class="image-shell" aria-hidden="true">
          <img class="city-bg-img" src="${info.image}" alt="${name}" loading="lazy" decoding="async" data-img-fallback="/static/img/logo-panda.jpg">
        </div>
      `;
    }
    const caption = info.vibe
      ? `Best for ${String(info.vibe).toLowerCase()} days with a quick dossier preview.`
      : 'Editorial browse card with a quick cue before opening the dossier.';
    const displayName = formatDisplayText(info.name_en || humanizeCityKey(name), info.name_cn);

    card.innerHTML = imgHtml + `
      <div class="city-card-top">
        <span class="city-emoji">${emoji}</span>
      </div>
      <div class="city-card-bottom">
        <div class="city-name">${displayName}</div>
        <div class="city-sub">${info.province || ''}</div>
        <div class="city-meta">${info.best_season || ''} · ${info.days || ''}</div>
        ${info.vibe ? `<div class="city-vibe">${info.vibe}</div>` : ''}
        <div class="city-card-caption">${caption}</div>
        ${tags.length ? `<div class="city-tags">${tags.map(t => `<span class="city-tag">${t}</span>`).join('')}</div>` : ''}
      </div>
    `;
    return card;
  }

  // ── Load Home Cities ──
  async function loadHomeCities() {
    const grid = document.getElementById('city-grid');
    if (!grid) return;
    const cities = await ensureCityCatalog();
    if (!cities) return;
    grid.innerHTML = '';
    Object.entries(cities).slice(0, 8).forEach(([name, info]) => {
      grid.appendChild(createCityCard(name, info));
    });
    attachImageFallbacks(grid);
  }

  // ── Load Cities (all) ──
  async function loadCities() {
    const grid = document.getElementById('cities-grid');
    if (!grid) return;
    setViewState('cities', 'loading');
    try {
      const cities = await ensureCityCatalog();
      if (!cities || !Object.keys(cities).length) {
        throw new Error('Cities unavailable');
      }
      grid.innerHTML = '';
      Object.entries(cities).forEach(([name, info]) => {
        grid.appendChild(createCityCard(name, info));
      });
      attachImageFallbacks(grid);
      applyCitiesFilter(state.cityFilter);
      setViewState('cities', 'ready');
    } catch (error) {
      console.error('[VP:cities]', error);
      setViewState('cities', 'error', 'Could not load city data.');
    }
  }

  function applyCitiesFilter(filter) {
    const grid = document.getElementById('cities-grid');
    if (!grid) return;
    const activeFilter = filter || 'all';
    state.cityFilter = activeFilter;
    grid.querySelectorAll('.city-card').forEach(card => {
      const filters = (card.dataset.filters || '').split(/\s+/).filter(Boolean);
      const isVisible = activeFilter === 'all' || filters.includes(activeFilter);
      card.classList.toggle('is-filtered-out', !isVisible);
      card.toggleAttribute('hidden', !isVisible);
    });
    document.querySelectorAll('#cities-filter-rail .cities-filter-chip').forEach(btn => {
      const isActive = btn.dataset.filter === activeFilter;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-pressed', String(isActive));
      if (isActive) {
        btn.scrollIntoView({ block: 'nearest', inline: 'center', behavior: 'smooth' });
      }
    });
  }

  function setupCitiesFilterRail() {
    const rail = document.getElementById('cities-filter-rail');
    if (!rail || rail.dataset.bound === 'true') return;
    rail.dataset.bound = 'true';
    rail.addEventListener('click', event => {
      const button = event.target.closest('.cities-filter-chip');
      if (!button) return;
      applyCitiesFilter(button.dataset.filter || 'all');
    });
  }

  // ── Load Tools ──
  const TOOL_PRICE_LABELS = {
    '故宫': 'Forbidden City（故宫）',
    '长城': 'Great Wall（长城）',
    '天坛': 'Temple of Heaven（天坛）',
    '颐和园': 'Summer Palace（颐和园）',
    '兵马俑': 'Terracotta Army（兵马俑）',
    '大熊猫基地': 'Giant Panda Base（大熊猫基地）',
    '都江堰': 'Dujiangyan（都江堰）',
    '西湖': 'West Lake（西湖）',
    '灵隐寺': 'Lingyin Temple（灵隐寺）',
    '鼓浪屿': 'Gulangyu（鼓浪屿）',
    '黄鹤楼': 'Yellow Crane Tower（黄鹤楼）',
    '嵩山少林': 'Shaolin Temple（嵩山少林）',
    '张家界': 'Zhangjiajie（张家界）',
    '黄山': 'Yellow Mountain（黄山）',
    '九寨沟': 'Jiuzhaigou（九寨沟）',
    '莫高窟': 'Mogao Caves（莫高窟）',
    '青海湖': 'Qinghai Lake（青海湖）',
    '布达拉宫': 'Potala Palace（布达拉宫）',
    '玉龙雪山': 'Jade Dragon Snow Mountain（玉龙雪山）',
    '高铁_每100km': 'High-speed rail / 100 km',
    '飞机_国内': 'Domestic flight',
    '地铁_次': 'Metro ride',
    '打车_起步': 'Taxi base fare',
    '打车_perkm': 'Taxi / km',
    '青旅_晚': 'Hostel / night',
    '快捷_晚': 'Budget hotel / night',
    '精品_晚': 'Boutique hotel / night',
    '五星_晚': 'Luxury hotel / night',
    '早餐': 'Breakfast',
    '午餐': 'Lunch',
    '晚餐_普通': 'Dinner (casual)',
    '晚餐_豪华': 'Dinner (upscale)',
    '小吃_次': 'Street snack',
    '饮料_杯': 'Drink'
  };
  const TOOL_PRICE_GROUPS = {
    'Iconic sights': ['故宫','长城','天坛','颐和园','兵马俑','大熊猫基地','都江堰','西湖','灵隐寺','鼓浪屿','黄鹤楼','嵩山少林','张家界','黄山','九寨沟','莫高窟','青海湖','布达拉宫','玉龙雪山'],
    'Transport': ['高铁_每100km','飞机_国内','地铁_次','打车_起步','打车_perkm'],
    'Stays': ['青旅_晚','快捷_晚','精品_晚','五星_晚'],
    'Daily food': ['早餐','午餐','晚餐_普通','晚餐_豪华','小吃_次','饮料_杯'],
  };
  const TOOL_CITY_LABELS = {
    '北京': 'Beijing', '上海': 'Shanghai', '广州': 'Guangzhou', '成都': 'Chengdu',
    '沈阳': 'Shenyang', '武汉': 'Wuhan', '重庆': 'Chongqing', '厦门': 'Xiamen'
  };

  function stripChinesePrefix(text) {
    if (!text || typeof text !== 'string') return '';
    const match = text.match(/^(.*)\(([^()]+)\)\s*$/);
    if (match) {
      const prefix = (match[1] || '').trim();
      const english = (match[2] || '').trim();
      const emoji = (prefix.match(/^[^\w(]+/u) || [''])[0];
      return `${emoji}${english}`.trim();
    }
    return text.trim();
  }

  function renderToolBadge(text, tone = '') {
    const cls = tone ? `tool-detail-badge ${tone}` : 'tool-detail-badge';
    return `<span class="${cls}">${escHtml(text)}</span>`;
  }

  function renderToolChecklistSection(section) {
    const title = stripChinesePrefix(section.title || 'Checklist');
    const items = (section.items || []).map(item => {
      const english = item[1] || item[0] || '';
      const required = !!item[2];
      return `<div class="tool-check-item">${renderToolBadge(required ? 'Essential' : 'Nice to have', required ? 'required' : 'optional')}<span>${escHtml(english)}</span></div>`;
    }).join('');
    return `<section class="tool-detail-section"><h3>${escHtml(title)}</h3><div class="tool-checklist">${items}</div></section>`;
  }

  function renderToolPricingSection(data) {
    return Object.entries(TOOL_PRICE_GROUPS).map(([group, keys]) => {
      const rows = keys.filter(key => Object.prototype.hasOwnProperty.call(data, key)).map(key => {
        const value = data[key];
        return `<div class="tool-price-row"><span>${escHtml(TOOL_PRICE_LABELS[key] || key)}</span><strong>¥${escHtml(String(value))}</strong></div>`;
      }).join('');
      return `<section class="tool-detail-section"><h3>${escHtml(group)}</h3><div class="tool-price-grid">${rows}</div></section>`;
    }).join('');
  }

  function renderToolVisaSection(data) {
    const cards = ['visa_free_transit_144h','visa_free_hainan','tourist_visa_l','visa_free_hong_kong'].map(key => {
      const item = data[key];
      if (!item) return '';
      const conditions = (item.conditions || []).map(line => `<li>${escHtml(line)}</li>`).join('');
      const steps = (Array.isArray(item.how_to_apply) ? item.how_to_apply : [item.how_to_apply]).filter(Boolean).map(line => `<li>${escHtml(line)}</li>`).join('');
      return `<article class="tool-visa-card">
        <div class="tool-visa-card-head">
          <h3>${escHtml(item.name || key)}</h3>
          ${item.duration ? renderToolBadge(item.duration, 'gold') : ''}
        </div>
        ${item.eligible ? `<p class="tool-copy">${escHtml(item.eligible)}</p>` : ''}
        ${item.cities ? `<p class="tool-copy"><strong>Where it works:</strong> ${escHtml(item.cities)}</p>` : ''}
        ${conditions ? `<div class="tool-detail-subsection"><div class="tool-subtitle">Conditions</div><ul>${conditions}</ul></div>` : ''}
        ${steps ? `<div class="tool-detail-subsection"><div class="tool-subtitle">How to apply</div><ul>${steps}</ul></div>` : ''}
        ${item.note ? `<p class="tool-copy"><strong>Note:</strong> ${escHtml(item.note)}</p>` : ''}
        ${item.tip ? `<p class="tool-copy"><strong>Tip:</strong> ${escHtml(item.tip)}</p>` : ''}
      </article>`;
    }).join('');
    const recs = (data.apr_recommendations || []).map(line => `<li>${escHtml(line)}</li>`).join('');
    const notes = (data.important_notes || []).map(line => `<li>${escHtml(line)}</li>`).join('');
    return cards
      + `<section class="tool-detail-section"><h3>Quick recommendations</h3><ul>${recs}</ul></section>`
      + `<section class="tool-detail-section"><h3>Important notes</h3><ul>${notes}</ul></section>`;
  }

  function renderToolPhrasesSection(data) {
    return Object.values(data || {}).map(section => {
      const phrases = (section.phrases || []).map(([zh, pinyin, en]) => `
        <div class="tool-phrase-item">
          <div class="tool-phrase-en">${escHtml(en || '')}</div>
          <div class="tool-phrase-ref">${escHtml(zh || '')}${pinyin ? ` · ${escHtml(pinyin)}` : ''}</div>
        </div>
      `).join('');
      return `<section class="tool-detail-section">
        <h3>${escHtml(section.title_en || stripChinesePrefix(section.title_zh || 'Phrase Set'))}</h3>
        <div class="tool-phrase-list">${phrases}</div>
      </section>`;
    }).join('');
  }

  function renderToolEmergencySection(data) {
    const phoneRows = Object.entries(data.phone || {}).map(([key, item]) => `
      <div class="tool-phone-card">
        <span class="tool-phone-number">${escHtml(item.number || '')}</span>
        <div class="tool-phone-copy">
          <strong>${escHtml(key.replace(/_/g, ' '))}</strong>
          <span>${escHtml(item.description || '')}</span>
        </div>
      </div>
    `).join('');
    const emergencyCards = Object.values(data.common_emergencies || {}).map(item => `
      <article class="tool-detail-card">
        <h3>${escHtml(item.title || '')}</h3>
        <ol>${(item.steps || []).map(step => `<li>${escHtml(step)}</li>`).join('')}</ol>
        ${item.tip ? `<p class="tool-copy"><strong>Tip:</strong> ${escHtml(item.tip)}</p>` : ''}
      </article>
    `).join('');
    const embassies = Object.values(data.embassies || {}).map(item => `
      <article class="tool-detail-card embassy-card">
        <h3>${escHtml(stripChinesePrefix(item.country || 'Embassy'))}</h3>
        <p class="tool-copy"><strong>Main line:</strong> ${escHtml(item.phone || '')}</p>
        <p class="tool-copy"><strong>Emergency:</strong> ${escHtml(item.emergency || '')}</p>
        <p class="tool-copy"><strong>Coverage:</strong> ${escHtml((item.cities || []).map(city => TOOL_CITY_LABELS[city] || city).join(', '))}</p>
        ${item.website ? `<p class="tool-copy"><a href="${escAttr(item.website)}" target="_blank" rel="noreferrer">Official website</a></p>` : ''}
      </article>
    `).join('');
    return `<section class="tool-detail-section"><h3>Emergency hotlines</h3><div class="tool-phone-grid">${phoneRows}</div></section>`
      + `<section class="tool-detail-section"><h3>Common situations</h3><div class="tool-detail-card-grid">${emergencyCards}</div></section>`
      + `<section class="tool-detail-section"><h3>Embassies & consulates</h3><div class="tool-detail-card-grid">${embassies}</div></section>`;
  }

  function renderToolDetailBody(name, tool) {
    const data = tool.data || {};
    if (name === 'packing') return Object.values(data).map(renderToolChecklistSection).join('');
    if (name === 'pricing') return renderToolPricingSection(data);
    if (name === 'visa') return renderToolVisaSection(data);
    if (name === 'phrases') return renderToolPhrasesSection(data);
    if (name === 'emergency') return renderToolEmergencySection(data);
    return `<section class="tool-detail-section"><pre>${escHtml(JSON.stringify(data, null, 2))}</pre></section>`;
  }

  async function openToolDetail(name) {
    const overlay = document.getElementById('tool-detail-overlay');
    const panel = document.getElementById('tool-detail-panel');
    if (!overlay || !panel) return;
    panel.innerHTML = '<div class="modal-loading">Loading toolkit...</div>';
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    const data = await apiGet(`/api/tools/${name}`);
    if (!data || !data.tool) {
      panel.innerHTML = '<div class="modal-error">Failed to load toolkit data</div>';
      return;
    }
    const tool = data.tool;
    panel.innerHTML = `
      <div class="tool-detail-shell">
        <div class="tool-detail-header">
          <div>
            <div class="tool-detail-kicker">Travel toolkit</div>
            <h2 class="tool-detail-title">${escHtml(tool.name || humanizeCityKey(name))}</h2>
            <p class="tool-detail-sub">${escHtml(tool.desc || '')}</p>
          </div>
          <button class="modal-close" onclick="VP.closeToolDetail()">✕</button>
        </div>
        <div class="tool-detail-body">${renderToolDetailBody(name, tool)}</div>
      </div>
    `;
  }

  function closeToolDetail() {
    const overlay = document.getElementById('tool-detail-overlay');
    if (!overlay) return;
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  async function loadTools() {
    const grid = document.getElementById('tools-grid');
    if (!grid) return;
    setViewState('tools', 'loading');
    try {
      const data = await apiGet('/api/tools');
      if (!data || !data.tools) {
        throw new Error('Tools unavailable');
      }

      grid.innerHTML = '';
      const emojis = {packing:'🧳', pricing:'💰', visa:'🛂', phrases:'💬', emergency:'🆘'};
      const kickers = {packing:'Ready kit', pricing:'Budget lens', visa:'Border prep', phrases:'Quick talk', emergency:'Need now'};
      Object.entries(data.tools).forEach(([name, desc]) => {
        const card = document.createElement('div');
        card.className = 'tool-card';
        card.setAttribute('role', 'button');
        card.tabIndex = 0;
        card.innerHTML = `
          <div class="tool-card-kicker">${kickers[name] || 'Quick utility'}</div>
          <div class="tool-card-icon">${emojis[name] || '🧰'}</div>
          <div class="tool-card-title">${humanizeCityKey(name)}</div>
          <div class="tool-card-desc">${desc}</div>
          <div class="tool-card-link">Open toolkit →</div>
        `;
        card.style.cursor = 'pointer';
        card.addEventListener('click', () => openToolDetail(name));
        card.addEventListener('keydown', (event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            openToolDetail(name);
          }
        });
        grid.appendChild(card);
      });
      setViewState('tools', 'ready');
    } catch (error) {
      console.error('[VP:tools]', error);
      setViewState('tools', 'error', 'Could not load toolkit data.');
    }
  }

  // ═══════════════════════════════════════════════════════════
  // CITY DETAIL MODAL
  // ═══════════════════════════════════════════════════════════

  function openCityDetail(name) {
    const overlay = document.getElementById('city-detail-overlay');
    const panel = document.getElementById('city-detail-panel');
    if (!overlay || !panel) return;

    panel.innerHTML = '<div class="modal-loading">Loading...</div>';
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';

    apiGet(`/api/cities/${name}`).then(data => {
      if (!data || !data.city) {
        panel.innerHTML = '<div class="modal-error">Failed to load city data</div>';
        return;
      }
      renderCityDetail(panel, name, data.city);
    });
  }

  function renderCityDetail(panel, name, city) {
    const emoji = getCityEmoji(name);
    const tags = (city.highlights || []).slice(0, 4);
    const mapData = city.map || {};
    const hasMap = mapData.lat && mapData.lng;
    const est = city.estimate || {};
    const displayName = formatDisplayText(city.name_en || humanizeCityKey(name), city.name_cn);

    // Build price estimate HTML
    let estHtml = '';
    if (est.mid_daily) {
      estHtml = '<div class="detail-section"><h3 class="detail-section-title">💰 Price Estimates</h3><div class="estimate-grid">'
        + '<div class="estimate-item"><span class="estimate-label">Budget/day</span><span class="estimate-val">' + escHtml(est.budget_daily || '') + '</span></div>'
        + '<div class="estimate-item"><span class="estimate-label">Mid/day</span><span class="estimate-val">' + escHtml(est.mid_daily || '') + '</span></div>'
        + '<div class="estimate-item"><span class="estimate-label">Luxury/day</span><span class="estimate-val">' + escHtml(est.luxury_daily || '') + '</span></div>'
        + '<div class="estimate-item"><span class="estimate-label">Avg flight</span><span class="estimate-val">' + escHtml(est.flight_avg || '') + '</span></div>'
        + '<div class="estimate-item"><span class="estimate-label">Avg meal</span><span class="estimate-val">' + escHtml(est.food_avg || '') + '</span></div>'
        + '</div></div>';
    }

    // Build POI map HTML
    let mapHtml = '';
    let mapId = '';
    if (hasMap) {
      mapId = 'map-' + Date.now() + '-' + Math.random().toString(36).slice(2, 6);
      mapHtml = '<div class="detail-section"><h3 class="detail-section-title">🗺️ Map</h3><div id="' + mapId + '" class="city-map"></div></div>';
    }

    // Build food HTML
    let foodHtml = '';
    if (city.food && city.food.length) {
      const items = city.food.map(f => {
        const star = f.must_try ? '⭐ ' : '';
        const cls = f.must_try ? 'food-item must' : 'food-item';
        const foodName = formatDisplayText(f.name_en || '', f.name_zh || f.name_cn || '');
        return '<div class="' + cls + '">'
          + '<div class="food-item-name">' + star + escHtml(foodName) + '</div>'
          + '<div class="food-item-desc">' + escHtml(f.description || '') + '</div>'
          + '<div class="food-item-price">💰 ' + escHtml(f.price_range || '') + '</div>'
          + '</div>';
      }).join('');
      foodHtml = '<div class="detail-section"><h3 class="detail-section-title">🍽️ Must-Eat Foods</h3><div class="detail-list">' + items + '</div></div>';
    }

    // Build hotel HTML
    let hotelHtml = '';
    if (city.hotels) {
      const h = city.hotels;
      const tiers = [];
      if (h.budget) tiers.push('<div class="hotel-tier"><div class="hotel-tier-label">Budget</div><div class="hotel-tier-range">' + escHtml(h.budget.range || '') + '</div><div class="hotel-tier-desc">' + escHtml(h.budget.desc || '') + ' · ' + escHtml(h.budget.areas || '') + '</div></div>');
      if (h.mid) tiers.push('<div class="hotel-tier"><div class="hotel-tier-label">Mid</div><div class="hotel-tier-range">' + escHtml(h.mid.range || '') + '</div><div class="hotel-tier-desc">' + escHtml(h.mid.desc || '') + ' · ' + escHtml(h.mid.areas || '') + '</div></div>');
      if (h.luxury) tiers.push('<div class="hotel-tier"><div class="hotel-tier-label">Luxury</div><div class="hotel-tier-range">' + escHtml(h.luxury.range || '') + '</div><div class="hotel-tier-desc">' + escHtml(h.luxury.desc || '') + ' · ' + escHtml(h.luxury.areas || '') + '</div></div>');
      const tip = h.tip ? '<div class="detail-tip">💡 ' + escHtml(h.tip) + '</div>' : '';
      hotelHtml = '<div class="detail-section"><h3 class="detail-section-title">🏨 Accommodation</h3><div class="hotel-grid">' + tiers.join('') + '</div>' + tip + '</div>';
    }

    // Build tips HTML
    let tipsHtml = '';
    if (city.tips && city.tips.length) {
      const items = city.tips.map(t => {
        const content = typeof t === 'object' ? '<strong>' + escHtml(t.en || '') + '</strong>: ' + escHtml(t.tip || '') : escHtml(String(t));
        return '<div class="tip-item">' + content + '</div>';
      }).join('');
      tipsHtml = '<div class="detail-section"><h3 class="detail-section-title">💡 Local Tips</h3><div class="detail-list">' + items + '</div></div>';
    }

    panel.innerHTML =
      '<div class="detail-header">'
      + '<span class="detail-emoji">' + emoji + '</span>'
      + '<div><h2 class="detail-name">' + escHtml(displayName) + '</h2>'
      + '<div class="detail-sub">' + escHtml(city.province || '') + '</div></div>'
      + '<button class="modal-close" onclick="VP.closeCityDetail()">✕</button></div>'
      + '<div class="detail-meta"><span>📅 Best: ' + escHtml(city.best_season || '') + '</span><span>⏱️ ' + escHtml(city.days || '') + '</span><span>' + escHtml(city.vibe || '') + '</span></div>'
      + (city.budget_tip ? '<div class="detail-tip">💰 ' + escHtml(city.budget_tip) + '</div>' : '')
      + (tags.length ? '<div class="detail-tags">' + tags.map(function(t){return '<span class="detail-tag">' + escHtml(t) + '</span>';}).join('') + '</div>' : '')
      + estHtml
      + mapHtml
      + foodHtml
      + hotelHtml
      + tipsHtml
      + '<div class="detail-actions"><button class="btn-primary" onclick="VP.navigate(\'chat\');setTimeout(function(){VP.focusChat(\'' + name.toLowerCase() + '\')},100)">💬 Plan a Trip to ' + name + '</button></div>';

    // Initialize map after DOM is rendered
    if (hasMap && mapId) {
      setTimeout(function() { initCityMap(mapId, mapData); }, 100);
    }
  }

  function closeCityDetail() {
    const overlay = document.getElementById('city-detail-overlay');
    if (overlay) overlay.classList.remove('active');
    document.body.style.overflow = '';
    // Clean up map instances
    if (window._vpMaps) {
      window._vpMaps.forEach(function(m) { m.remove(); });
      window._vpMaps = [];
    }
  }

  // Leaflet map initialization with dark theme
  function initCityMap(mapId, mapData) {
    if (!window.L || !mapData.lat || !mapData.lng) return;
    
    // Store map instances for cleanup
    if (!window._vpMaps) window._vpMaps = [];
    
    // Dark tile layer
    var tileUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
    var tileAttr = '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> contributors, &copy; CartoDB';
    
    var map = window.L.map(mapId, {
      center: [mapData.lat, mapData.lng],
      zoom: mapData.zoom || 11,
      zoomControl: true,
      attributionControl: false,
    });
    
    window.L.tileLayer(tileUrl, { attribution: tileAttr, maxZoom: 18 }).addTo(map);
    
    // City center marker
    var goldIcon = window.L.divIcon({
      className: 'map-marker-city',
      html: '<div style="background:#bc3a2c;width:16px;height:16px;border-radius:50%;border:3px solid #c9a96e;box-shadow:0 2px 8px rgba(0,0,0,.5)"></div>',
      iconSize: [16, 16],
      iconAnchor: [8, 8],
    });
    window.L.marker([mapData.lat, mapData.lng], { icon: goldIcon }).addTo(map);
    
    // POI markers with colored icons by type
    var typeColors = {
      history: '#c9a96e',
      nature: '#7dd3fc',
      food: '#bc3a2c',
      culture: '#a78bfa',
      landmark: '#f59e0b',
      modern: '#6ee7b7',
      entertainment: '#f472b6',
    };
    
    if (mapData.pois) {
      mapData.pois.forEach(function(poi) {
        var color = typeColors[poi.type] || '#888';
        var poiIcon = window.L.divIcon({
          className: 'map-marker-poi',
          html: '<div style="background:' + color + ';width:10px;height:10px;border-radius:50%;border:2px solid rgba(255,255,255,.6);box-shadow:0 2px 6px rgba(0,0,0,.4)"></div>',
          iconSize: [10, 10],
          iconAnchor: [5, 5],
        });
        var marker = window.L.marker([poi.lat, poi.lng], { icon: poiIcon }).addTo(map);
        marker.bindPopup('<b>' + escHtml(formatDisplayText(poi.name, poi.name_cn)) + '</b>');
      });
    }
    
    window._vpMaps.push(map);
    
    // Invalidate after render to fix sizing
    setTimeout(function() { map.invalidateSize(); }, 200);
  }

  // ═══════════════════════════════════════════════════════════
  // CHAT
  // ═══════════════════════════════════════════════════════════

  let abortController = null;
  let currentCity = ''; // Track city across multi-turn conversation
  let faqBadgeId = null; // FAQ match badge tracking

  const CITY_NAMES = [
    'beijing','shanghai','chengdu','xian','guilin','yunnan','hangzhou',
    'guangzhou','shenzhen','chongqing','changsha','nanjing','suzhou',
    'harbin','zhangjiajie','tibet','sanya','dunhuang','luoyang','wuhan',
    'xiamen','qingdao','dali','lijiang','huangshan','jiuzhaigou','lanzhou',
    'kunming','hohhot','guiyang','fuzhou','macau','hong kong','taipei',
  ];

  function detectCity(text) {
    const lower = text.toLowerCase();
    for (const city of CITY_NAMES) {
      if (lower.includes(city)) return city;
    }
    return '';
  }

  const SUGGESTIONS = [
    '3 days in Beijing',
    'Shanghai food tour',
    'Chengdu panda trip',
    'Guilin nature escape',
    "Xi'an history guide",
    'Budget tips for China',
  ];

  function renderSuggestions() {
    const bar = document.getElementById('chat-suggestions');
    if (!bar) return;
    bar.innerHTML = '';
    SUGGESTIONS.forEach(s => {
      const chip = document.createElement('button');
      chip.className = 'chat-chip';
      chip.textContent = s;
      chip.onclick = () => {
        const input = document.getElementById('chat-input');
        if (input) {
          input.value = s;
          input.style.height = 'auto';
          toggleSendButton(true);
          input.focus();
        }
      };
      bar.appendChild(chip);
    });
  }

  // Context-aware suggestions
  function updateSuggestions() {
    const bar = document.getElementById('chat-suggestions');
    if (!bar) return;

    let suggestions;
    const lastMsg = state.messages[state.messages.length - 1];
    const lastCity = currentCity || '';

    if (lastMsg && lastMsg.role === 'assistant' && lastCity) {
      // After discussing a city, show follow-up options
      suggestions = [
        `Make the ${lastCity} trip cheaper`,
        `Show me a different ${lastCity} itinerary`,
        `What about ${lastCity} nightlife?`,
        `Another city similar to ${lastCity}`,
        'Compare with a different city',
        'Add this to my saved trips',
      ];
    } else if (lastCity) {
      suggestions = [
        `3 days in ${lastCity}`,
        `${lastCity} food guide`,
        `${lastCity} budget trip`,
        `${lastCity} with kids`,
        'Show me another city',
        'Compare cities',
      ];
    } else {
      suggestions = SUGGESTIONS;
    }

    bar.innerHTML = '';
    suggestions.forEach(s => {
      const chip = document.createElement('button');
      chip.className = 'chat-chip';
      chip.textContent = s;
      chip.onclick = () => {
        const input = document.getElementById('chat-input');
        if (input) {
          input.value = s;
          input.style.height = 'auto';
          toggleSendButton(true);
          input.focus();
        }
      };
      bar.appendChild(chip);
    });
  }

  function addMessage(text, role) {
    const container = document.getElementById('chat-messages');
    if (!container) return null;
    const msg = document.createElement('div');
    msg.className = `msg msg-${role}`;
    msg.innerHTML = `
      <div class="msg-avatar">${role === 'assistant' || role === 'bot' ? getPandaAvatar() : '👤'}</div>
      <div class="msg-body">
        <div class="msg-sender">${role === 'assistant' || role === 'bot' ? 'VisePanda' : 'You'}</div>
        <div class="msg-text">${role === 'user' ? text.replace(/\n/g, '<br>') : renderMD(text)}</div>
      </div>
    `;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
    // Sync overlay if visible
    const overlay = document.getElementById('chat-overlay');
    if (overlay && !overlay.classList.contains('hidden')) {
      syncOverlayMessages();
    }
    return msg;
  }

  function addTyping() {
    const container = document.getElementById('chat-messages');
    if (!container) return null;
    const msg = document.createElement('div');
    msg.className = 'msg msg-bot';
    msg.id = 'typing-msg';
    const ta = getPandaAvatar();
    msg.innerHTML = `
      <div class="msg-avatar">${ta}</div>
      <div class="msg-body">
        <div class="msg-sender">VisePanda</div>
        <div class="msg-text typing-indicator"><span></span><span></span><span></span></div>
      </div>
    `;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
    return msg;
  }

  function updateTyping(el, content) {
    if (!el) return;
    const textDiv = el.querySelector('.msg-text');
    if (textDiv && content) {
      textDiv.innerHTML = renderMD(content) + '<span class="cursor-blink">▌</span>';
    }
  }

  function removeMessage(el) {
    if (el && el.parentNode) el.parentNode.removeChild(el);
  }

  // ── FAQ Match Badge ──
  function showFaqBadge(typingEl, icon, title, terms) {
    if (!typingEl) return null;
    // Remove previous badge if any
    const old = typingEl.querySelector('.faq-badge');
    if (old) old.remove();

    const badge = document.createElement('div');
    badge.className = 'faq-badge';
    const termStr = terms && terms.length ? `<span class="faq-terms">${terms.map(t => t.replace(/_/g,' ')).slice(0,3).join(' · ')}</span>` : '';
    badge.innerHTML = `${icon} <span class="faq-label">${title}</span>${termStr}`;
    typingEl.querySelector('.msg-body').insertBefore(badge, typingEl.querySelector('.msg-text'));
    return badge;
  }

  function toggleSendButton(enabled) {
    const btn = document.getElementById('chat-send');
    if (btn) btn.disabled = !enabled;
  }

  function toggleStopButton(show) {
    const stopBtn = document.getElementById('chat-stop');
    const sendBtn = document.getElementById('chat-send');
    if (stopBtn) stopBtn.style.display = show ? 'flex' : 'none';
    if (sendBtn) sendBtn.style.display = show ? 'none' : 'flex';
  }

  function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    if (!state.isStreaming) toggleSendButton(el.value.trim().length > 0);
  }

  async function sendMessage() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text || state.isStreaming) return;

    input.value = '';
    input.style.height = 'auto';

    // Add user message
    addMessage(text, 'user');
    state.messages.push({role: 'user', content: text});

    // Track current city across multi-turn conversation
    const detected = detectCity(text);
    if (detected) currentCity = detected;

    // Auto-detect compare intent (对比北京和成都 → show comparison table)
    const compareIntent = detectCompareIntent(text);
    if (compareIntent && compareIntent.length >= 2) {
      compareCities(compareIntent);
    }
  
    saveMessages();

    // Show typing + stop button
    let typingId = addTyping();
    state.isStreaming = true;
    toggleStopButton(true);
    abortController = new AbortController();

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          messages: state.messages.slice(-12),
          city: detectCity(text) || currentCity,
        }),
        signal: abortController.signal,
      });

      if (!resp.ok) {
        removeMessage(typingId);
        addMessage('Sorry, I couldn\'t process that. Please try again.', 'bot');
        toggleStopButton(false);
        state.isStreaming = false;
        toggleSendButton(input.value.trim().length > 0);
        return;
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let botContent = '';
      let doneReceived = false;
      // Multi-bubble support
      let bubbleParts = [];
      let currentBubble = '';

      while (true) {
        const {done, value} = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, {stream: true});
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const data = line.slice(6).trim();
          if (!data) continue;

          try {
            const parsed = JSON.parse(data);
            if (parsed.token) {
              currentBubble += parsed.token;
              setPandaMood(parsed.token);
              updateTyping(typingId, currentBubble);
            } else if (parsed.split) {
              // Commit current bubble and start a new one
              if (currentBubble.trim()) {
                bubbleParts.push(currentBubble);
              }
              currentBubble = '';
              // Keep typing indicator connected — just clear and reset
              removeMessage(typingId);
              const newId = addTyping();
              typingId = newId;
              // Update typing with accumulated content
              setTimeout(() => updateTyping(typingId, ''), 50);
            } else if (parsed.image) {
              // Insert an image bubble
              const img = parsed.image;
              const safeLabel = escHtml(img.label || '');
              const safeUrl = escHtml(img.url || '');
              // Only allow relative or https URLs
              if (safeUrl && (safeUrl.startsWith('/') || safeUrl.startsWith('https://'))) {
                const imgBubble = document.createElement('div');
                imgBubble.className = 'msg msg-bot msg-image';
                imgBubble.innerHTML = `
                  <div class="msg-avatar">🐼</div>
                  <div class="msg-body">
                    <div class="msg-sender">VisePanda · ${safeLabel}</div>
                    <div class="msg-text img-msg">
                      <img src="${safeUrl}" alt="${safeLabel}" class="chat-image" loading="lazy" onclick="window.open('${safeUrl}')">
                    </div>
                  </div>
                `;
                const container = document.getElementById('chat-messages');
                if (container) {
                  container.appendChild(imgBubble);
                  container.scrollTop = container.scrollHeight;
                }
              }
            } else if (parsed.faq) {
              // FAQ match badge - show above the response
              const f = parsed.faq;
              faqBadgeId = showFaqBadge(typingId, f.icon, f.title, f.matched_terms);
            } else if (parsed.error) {
              removeMessage(typingId);
              addMessage('Error: ' + parsed.error, 'bot');
              doneReceived = true;
            } else if (parsed.done) {
              doneReceived = true;
            }
          } catch (e) {
            // Incomplete chunk
          }
        }
      }

      // ── Commit final bubbles ──
      removeMessage(typingId);
      // Add remaining current bubble
      if (currentBubble.trim()) {
        bubbleParts.push(currentBubble);
      }

      // Build combined content for state + auto-save
      const combinedContent = bubbleParts.join('\n\n---\n\n');

      if (bubbleParts.length > 0) {
        // Render each bubble separately
        bubbleParts.forEach((part, idx) => {
          addMessage(part, 'assistant');
          // Small delay between bubbles for visual cascade
          if (idx < bubbleParts.length - 1) {
            const container = document.getElementById('chat-messages');
            if (container) {
              const spacer = document.createElement('div');
              spacer.className = 'bubble-spacer';
              container.appendChild(spacer);
              container.scrollTop = container.scrollHeight;
            }
          }
        });
        state.messages.push({role: 'assistant', content: combinedContent});
        saveMessages();
        // Auto-save if looks like an itinerary
        const saved = autoSaveTrip(currentCity, combinedContent);
        if (saved) {
          const msgs = document.getElementById('chat-messages');
          if (msgs) {
            const saveNote = document.createElement('div');
            saveNote.className = 'save-note';
            saveNote.innerHTML = '💾 Trip saved! <a href="#" onclick="VP.navigate(\'trips\');return false">View all trips →</a>';
            msgs.appendChild(saveNote);
            msgs.scrollTop = msgs.scrollHeight;
          }
        }
        // Inject visual timeline if content looks like a trip itinerary
        const msgsEl = document.getElementById('chat-messages');
        if (msgsEl && window.TripTimeline) {
          TripTimeline.inject(combinedContent, msgsEl);
        }
        updateSuggestions();
      } else if (!doneReceived) {
        addMessage('I had trouble processing that. Could you try rephrasing?', 'bot');
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        // User stopped - save multi-bubble content
        removeMessage(typingId);
        // Add the current incomplete bubble
        if (currentBubble && currentBubble.trim()) {
          bubbleParts.push(currentBubble);
        }
        if (bubbleParts.length > 0) {
          const combined = bubbleParts.join('\n\n---\n\n');
          state.messages.push({role: 'assistant', content: combined});
          saveMessages();
        } else if (state._partialContent) {
          state.messages.push({role: 'assistant', content: state._partialContent});
          saveMessages();
        }
      } else {
        removeMessage(typingId);
        const errMsg = document.createElement('div');
        errMsg.className = 'msg msg-bot';
        errMsg.innerHTML = '<div class="msg-avatar">' + getPandaAvatar() + '</div><div class="msg-body"><div class="msg-sender">VisePanda</div><div class="msg-text" style="color:#e74c3c">⚠️ Connection error. <a href="#" onclick="const i=document.getElementById(\'chat-input\');if(i){const e=new Event(\'keydown\');e.key=\'Enter\';i.dispatchEvent(e)}return false" style="color:var(--accent,#e67e22);font-weight:600">Retry ↻</a></div></div>';
        const container = document.getElementById('chat-messages');
        if (container) container.appendChild(errMsg);
      }
    } finally {
      resetPandaMood();
      state.isStreaming = false;
      toggleStopButton(false);
      abortController = null;
      const input2 = document.getElementById('chat-input');
      if (input2) toggleSendButton(input2.value.trim().length > 0);
    }
  }

  function stopStreaming() {
    if (abortController) {
      // Save whatever we have before aborting
      const typing = document.getElementById('typing-msg');
      if (typing) {
        const textDiv = typing.querySelector('.msg-text');
        if (textDiv) {
          const raw = textDiv.textContent.replace('▌', '').trim();
          if (raw && raw !== '...') {
            state._partialContent = raw;
          }
        }
      }
      abortController.abort();
    }
  }

  // ═══════════════════════════════════════════════════════════
  // TRIP MANAGEMENT (Persistent Itineraries)
  // ═══════════════════════════════════════════════════════════

  function getToken() {
    return localStorage.getItem('vp_token') || '';
  }

  /** Load trips from API (logged-in) or localStorage (guest) */
  async function loadTripsFromApi() {
    const tok = getToken();
    if (!tok) return null; // not logged in
    try {
      const resp = await fetch('/api/trips', {
        headers: { 'Authorization': 'Bearer ' + tok }
      });
      if (!resp.ok) return null;
      const data = await resp.json();
      // API returns: {trips: {recent: [...], saved: [...]}}
      const all = [];
      if (data.trips) {
        const src = data.trips.recent || data.trips.saved ? data.trips : { recent: data.trips };
        const recent = (src.recent || []).map(t => ({
          id: t.id,
          city: t.city || '',
          title: t.title || (t.city ? t.city + ' Trip' : 'Saved Trip'),
          preview: t.preview || '',
          content: t.content || t.preview || '',
          days: t.days || '?',
          created: t.created_at || t.created || new Date().toISOString(),
        }));
        const saved = (src.saved || []).map(t => ({
          id: t.id,
          city: t.city || '',
          title: t.title || (t.city ? t.city + ' Trip' : 'Saved Trip'),
          preview: t.preview || '',
          content: t.content || t.preview || '',
          days: t.days || '?',
          created: t.created_at || t.created || new Date().toISOString(),
        }));
        all.push(...recent, ...saved);
      }
      return all;
    } catch(e) {
      return null;
    }
  }

  /** Get local trips (always fallback) */
  function getLocalTrips() {
    try {
      return JSON.parse(localStorage.getItem('vp_trips') || '[]');
    } catch(e) { return []; }
  }

  function saveLocalTrips(trips) {
    try { localStorage.setItem('vp_trips', JSON.stringify(trips.slice(0, 20))); }
    catch(e) { /* quota */ }
  }

  /** Get trips: API if logged in, localStorage fallback */
  async function getTrips() {
    const api = await loadTripsFromApi();
    if (api !== null && api.length > 0) return api;
    return getLocalTrips();
  }

  function saveTrip(city, content) {
    const title = content.split('\n')[0].replace(/[#*]/g,'').trim().slice(0, 60) || (city ? city + ' Trip' : 'China Trip');
    const dayCount = (content.match(/\*\*Day \d+/g) || content.match(/Day \d+:/g) || []).length;
    const tripId = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);

    // API save if logged in
    const tok = getToken();
    if (tok) {
      fetch('/api/trips', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + tok },
        body: JSON.stringify({
          title: title,
          city: city || '',
          days: String(dayCount || '?'),
          preview: content.slice(0, 220),
          content: content,
          is_saved: false,
        })
      }).catch(() => {}); // fire-and-forget API save
    }

    // Always save locally too (instant feedback)
    const trips = getLocalTrips();
    const trip = {
      id: tripId,
      city: city || '',
      title: title,
      content: content,
      days: dayCount || '?',
      created: new Date().toISOString(),
    };
    trips.unshift(trip);
    saveLocalTrips(trips);
    showToast('✅ Trip saved!');
    return trip;
  }

  function showToast(msg, duration) {
    const el = document.getElementById('toast') || (function(){
      const e = document.createElement('div');
      e.id = 'toast'; e.className = 'toast';
      document.body.appendChild(e);
      return e;
    })();
    el.textContent = msg;
    el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), duration || 2000);
  }

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function scrollChatToLatest() {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
  }

  function deleteTrip(id) {
    const tok = getToken();
    if (tok) {
      fetch('/api/trips/' + encodeURIComponent(id), {
        method: 'DELETE',
        headers: { 'Authorization': 'Bearer ' + tok }
      }).catch(() => {});
    }
    // Remove from local too
    const trips = getLocalTrips().filter(t => t.id !== id);
    saveLocalTrips(trips);
    showToast('🗑️ Trip deleted');
    loadTrips();
  }

  function saveCurrentTrip() {
    const latestAssistant = [...state.messages].reverse().find(msg => msg.role === 'assistant' && msg.content);
    if (!latestAssistant) {
      showToast('Plan a trip in chat first, then save it here.');
      return null;
    }
    const latestUser = [...state.messages].reverse().find(msg => msg.role === 'user' && msg.content);
    const city = latestUser?.content?.match(/(?:to|in)\s+([A-Za-z][A-Za-z\s-]{1,40})/i)?.[1]?.trim() || '';
    const trip = saveTrip(city, latestAssistant.content);
    if (state.currentView === 'trips') loadTrips();
    return trip;
  }

  async function loadTrips() {
    setViewState('trips', 'loading');
    try {
      await renderTrips();
      setViewState('trips', 'ready');
    } catch (error) {
      console.error('[VP:trips]', error);
      setViewState('trips', 'error', 'Could not load saved trips.');
    }
  }

  async function renderTrips() {
    const recent = document.getElementById('trips-recent');
    const saved = document.getElementById('trips-saved');
    const legacyGrid = document.getElementById('trips-grid');
    const target = recent || saved || legacyGrid;
    if (!target) return;
    const trips = await getTrips();

    function renderTripCards(items, emptyMessage) {
      if (!items.length) {
        return '<div class="trip-empty">' + emptyMessage + '</div>';
      }
      return items.map(t => {
        const date = new Date(t.created);
        const dateStr = date.toLocaleDateString('en-US', {month:'short', day:'numeric'});
        const snippet = t.content.replace(/<[^>]+>/g, '').slice(0, 120).replace(/\n/g, ' ');
        const cityEmoji = t.city ? getCityEmoji(t.city) : '🌏';
        return '<div class="trip-card">'
          + '<div class="trip-card-mobile-head">'
          + '<div class="trip-card-top">'
          + '<span class="trip-city-icon">' + cityEmoji + '</span>'
          + '<div class="trip-card-info">'
          + '<div class="trip-card-title">' + escHtml(t.title) + '</div>'
          + '<div class="trip-card-meta">' + (t.city ? escHtml(t.city) + ' · ' : '') + t.days + ' days · ' + dateStr + '</div>'
          + '</div></div>'
          + '<div class="trip-card-mobile-actions">'
          + '<button class="trip-action-btn load" onclick="VP.loadTrip(\'' + t.id + '\')">📂 Load</button>'
          + '<button class="trip-action-btn share" onclick="VP.shareTrip(\'' + t.id + '\')">📋 Copy</button>'
          + '</div></div>'
          + '<div class="trip-card-desc">' + escHtml(snippet) + '…</div>'
          + '<div class="trip-card-actions">'
          + '<button class="trip-action-btn delete" onclick="VP.deleteTrip(\'' + t.id + '\')">🗑️</button>'
          + '</div></div>';
      }).join('');
    }

    if (!trips.length) {
      if (recent) recent.innerHTML = renderTripCards([], 'No recent trips yet. Chat with VisePanda to plan a trip! 🌏');
      if (saved) saved.innerHTML = renderTripCards([], 'Saved trips will appear here as your library grows.');
      if (legacyGrid) legacyGrid.innerHTML = renderTripCards([], 'No saved trips yet. Chat with VisePanda to plan a trip, then save it! 🌏');
      return;
    }

    const recentTrips = trips.slice(0, 3);
    const savedTrips = trips.slice(3);
    if (recent) recent.innerHTML = renderTripCards(recentTrips, 'No recent trips yet. Chat with VisePanda to plan a trip! 🌏');
    if (saved) saved.innerHTML = renderTripCards(savedTrips, 'Everything you save next will appear in this archive.');
    if (legacyGrid) legacyGrid.innerHTML = renderTripCards(trips, 'No saved trips yet. Chat with VisePanda to plan a trip, then save it! 🌏');
  }

  async function loadTrip(id) {
    const trips = await getTrips();
    const trip = trips.find(t => t.id === id);
    if (!trip) return;

    // Restore content to chat
    state.messages.push({role: 'user', content: 'Show me my saved trip: ' + trip.title});
    state.messages.push({role: 'assistant', content: trip.content});
    saveMessages();

    // Navigate to chat
    navigate('chat');

    // Reload chat messages
    const container = document.getElementById('chat-messages');
    if (container) {
      // Keep welcome, remove old messages
      const welcome = container.querySelector('.msg-bot:first-child');
      container.innerHTML = '';
      if (welcome) container.appendChild(welcome.cloneNode(true));

      state.messages.forEach(msg => {
        const el = document.createElement('div');
        el.className = 'msg msg-' + (msg.role === 'user' ? 'user' : 'bot');
        el.innerHTML = '<div class="msg-avatar">' + (msg.role === 'assistant' ? getPandaAvatar() : '👤') + '</div>'
          + '<div class="msg-body">'
          + '<div class="msg-sender">' + (msg.role === 'assistant' ? 'VisePanda' : 'You') + '</div>'
          + '<div class="msg-text">' + (msg.role === 'user' ? escHtml(msg.content).replace(/\n/g,'<br>') : renderMD(msg.content)) + '</div>'
          + '</div>';
        container.appendChild(el);
      });
      container.scrollTop = container.scrollHeight;
    }
  }

  async function shareTrip(id) {
    const trips = await getTrips();
    const trip = trips.find(t => t.id === id);
    if (!trip) return;

    // Strip markdown for clean sharing
    const clean = trip.content
      .replace(/\*\*/g, '')
      .replace(/#/g, '')
      .replace(/---+/g, '')
      .trim();

    const text = '🌏 VisePanda Trip: ' + trip.title + '\n'
      + (trip.city ? '📍 ' + trip.city + ' · ' : '')
      + trip.days + ' days\n'
      + '─────────────────\n\n'
      + clean
      + '\n\n─────────────────\n'
      + 'Planned with VisePanda 🐼';

    navigator.clipboard.writeText(text).then(() => {
      showToast('📋 Trip copied to clipboard!');
    }).catch(() => {
      alert('Trip copied!\n\n' + text.slice(0, 200) + '...');
    });
  }

  function copyTimeline() {
    if (window.TripTimeline) TripTimeline.copy();
  }

  // ── City Comparison ──
  function compareCities(cityNames) {
    if (!cityNames || cityNames.length < 2) return;

    const q = cityNames.map(c => encodeURIComponent(c.trim().toLowerCase())).join(',');
    fetch('/api/cities/compare?cities=' + q)
      .then(r => r.json())
      .then(data => {
        if (!data.comparisons || !data.comparisons.cities) return;
        renderComparison(data.comparisons.cities);
      })
      .catch(() => {});
  }

  function renderComparison(cities) {
    if (!cities || cities.length < 2) return;

    // Fields to compare (excluding found/highlights/keywords)
    const fieldLabels = {
      vibe: 'Vibe',
      best_season: 'Best Season',
      days: 'Recommended',
      budget_tip: 'Budget Tip',
      province: 'Province',
    };
    const fieldKeys = Object.keys(fieldLabels);

    let html = '<div class="compare-overlay" id="compare-overlay">'
      + '<div class="compare-modal">'
      + '<div class="compare-header">'
      + '<span class="compare-title">🏙️ City Comparison</span>'
      + '<button class="compare-close" onclick="this.closest(\'.compare-overlay\').remove()">✕</button>'
      + '</div>'
      + '<div class="compare-table-wrap"><table class="compare-table">';

    // Header row
    html += '<tr><th></th>';
    cities.forEach(c => {
      html += '<th>' + escHtml(formatDisplayText(c.name_en || '', c.name_cn || '')) + '</th>';
    });
    html += '</tr>';

    // Field rows
    fieldKeys.forEach(k => {
      if (!fieldLabels[k]) return;
      const values = cities.map(c => {
        const v = c[k];
        if (!v) return '<span class="na">N/A</span>';
        return escHtml(String(v));
      });
      // Skip rows where all values are empty
      if (values.every(v => v === '<span class="na">N/A</span>')) return;
      
      html += '<tr><td class="field-label">' + fieldLabels[k] + '</td>';
      values.forEach(v => {
        html += '<td>' + v + '</td>';
      });
      html += '</tr>';
    });

    // Highlights row
    html += '<tr><td class="field-label">Highlights</td>';
    cities.forEach(c => {
      const h = c.highlights || [];
      html += '<td class="highlights-cell">' + h.slice(0, 5).map(x => '<span class="hl-tag">' + escHtml(x) + '</span>').join('') + '</td>';
    });
    html += '</tr>';

    html += '</table></div>'
      + '<div class="compare-footer"><button class="compare-btn-chat" onclick="this.closest(\'.compare-overlay\').remove()">Close</button></div>'
      + '</div></div>';

    // Add to body
    const existing = document.getElementById('compare-overlay');
    if (existing) existing.remove();
    const div = document.createElement('div');
    div.innerHTML = html;
    document.body.appendChild(div.firstElementChild);
  }

  // ── Detect compare intent in chat input ──
  function detectCompareIntent(text) {
    // Match patterns like: "对比北京和成都", "compare beijing chengdu", "北京 vs 成都"
    if (!text || typeof text !== 'string') return null;

    const cityNames = [];
    // Try to load city names from the data
    const cityData = window.__cityNamesCache || [];
    
    // First try Chinese patterns: 对比/比较X和Y
    const cnMatch = text.match(/(?:对比|比较|compare)\s*(.+?)(?:和|与|vs|vs\.|and)\s*(.+)/i);
    if (cnMatch) {
      const a = cnMatch[1].trim();
      const b = cnMatch[2].trim();
      // Remove trailing punctuation / whitespace from b
      const bClean = b.replace(/[？?。！!\s]+$/, '').trim();
      return [a, bClean];
    }

    // Try "X vs Y" pattern
    const vsMatch = text.match(/(.+?)\s*(?:vs\.?|对比)\s*(.+)/i);
    if (vsMatch) {
      const a = vsMatch[1].trim();
      const b = vsMatch[2].trim().replace(/[？?。！!\s]+$/, '').trim();
      if (a.length < 20 && b.length < 20) return [a, b];
    }

    return null;
  }

  // ── Visa Kit ──
  function showVisaModal() {
    // Remove existing
    const old = document.getElementById('visa-overlay');
    if (old) old.remove();

    // Fetch supported countries
    fetch('/api/visa/countries').then(r => r.json()).then(data => {
      const countries = data.countries || [];

      let countryOptions = '<option value="">Select nationality...</option>';
      countries.forEach(c => {
        countryOptions += `<option value="${c.code}">${c.country} (${c.nationality})</option>`;
      });

      // Get the latest trip for auto-fill
      getTrips().then(trips => {
        const latest = trips[0] || {};

        const html = `
        <div class="visa-overlay" id="visa-overlay">
          <div class="visa-modal">
            <div class="visa-header">
              <span class="visa-title">🛂 Visa Kit</span>
              <button class="visa-close" onclick="document.getElementById('visa-overlay').remove()">✕</button>
            </div>
            <div class="visa-body">
              <div class="visa-section">
                <label class="visa-label">Your Nationality</label>
                <select class="visa-select" id="visa-nationality">${countryOptions}</select>
              </div>
              <div class="visa-section">
                <label class="visa-label">Trip (auto-filled from latest)</label>
                <input class="visa-input" id="visa-title" value="${escHtml(latest.title||'')}" placeholder="Trip name">
                <div class="visa-row">
                  <input class="visa-input visa-input-half" id="visa-city" value="${escHtml(latest.city||'')}" placeholder="City">
                  <input class="visa-input visa-input-half" id="visa-days" value="${latest.days||''}" placeholder="Days">
                </div>
              </div>
              <div class="visa-actions">
                <button class="visa-btn visa-btn-primary" id="visa-check-btn" onclick="VP.checkVisa()">🔍 Check Visa Requirements</button>
                <button class="visa-btn visa-btn-secondary" id="visa-gen-btn" onclick="VP.generateVisaDoc()" style="display:none">📄 Generate Itinerary Document</button>
              </div>
              <div class="visa-result" id="visa-result" style="display:none"></div>
            </div>
          </div>
        </div>`;

        const div = document.createElement('div');
        div.innerHTML = html;
        document.body.appendChild(div.firstElementChild);
      });
    }).catch(() => {});
  }

  // Check visa requirements
  function checkVisa() {
    const nat = document.getElementById('visa-nationality').value;
    const result = document.getElementById('visa-result');
    if (!nat) { result.innerHTML = '<p class="visa-error">Please select your nationality</p>'; result.style.display='block'; return; }

    result.innerHTML = '<p class="visa-loading">Checking...</p>';
    result.style.display = 'block';
    document.getElementById('visa-check-btn').disabled = true;

    fetch('/api/visa/info?nationality=' + encodeURIComponent(nat))
      .then(r => r.json())
      .then(data => {
        document.getElementById('visa-check-btn').disabled = false;
        if (!data.found) {
          result.innerHTML = '<div class="visa-alert"><span class="visa-alert-icon">⚠️</span><p>' + escHtml(data.message || 'Visa info not available') + '</p></div>';
          document.getElementById('visa-gen-btn').style.display = 'none';
          return;
        }
        const v = data.visa;
        let html = '<div class="visa-card">';
        html += '<div class="visa-card-row"><span class="visa-label">Visa Required</span><span class="visa-value ' + (v.visa_required ? 'visa-req-yes' : 'visa-req-no') + '">' + (v.visa_required ? 'Yes' : 'No (visa-free)') + '</span></div>';
        html += '<div class="visa-card-row"><span class="visa-label">Visa Type</span><span class="visa-value">' + escHtml(v.visa_type) + '</span></div>';
        html += '<div class="visa-card-row"><span class="visa-label">Processing</span><span class="visa-value">' + escHtml(v.processing_time) + '</span></div>';
        html += '<div class="visa-card-row"><span class="visa-label">Validity</span><span class="visa-value">' + escHtml(v.validity) + '</span></div>';
        html += '<div class="visa-card-row"><span class="visa-label">Max Stay</span><span class="visa-value">' + escHtml(v.max_stay) + '</span></div>';
        html += '<div class="visa-card-row"><span class="visa-label">Fee</span><span class="visa-value">' + escHtml(v.fee) + '</span></div>';
        html += '</div>';

        if (v.documents_required && v.documents_required.length > 0) {
          html += '<div class="visa-docs"><div class="visa-docs-title">📋 Required Documents</div>';
          v.documents_required.forEach(d => { html += '<div class="visa-doc-item">• ' + escHtml(d) + '</div>'; });
          html += '</div>';
        }

        if (v.special_notes) {
          html += '<div class="visa-notes"><span class="visa-notes-icon">💡</span>' + escHtml(v.special_notes) + '</div>';
        }

        result.innerHTML = html;
        document.getElementById('visa-gen-btn').style.display = 'inline-block';
      })
      .catch(() => {
        document.getElementById('visa-check-btn').disabled = false;
        result.innerHTML = '<p class="visa-error">Failed to check. Try again.</p>';
      });
  }

  // Generate visa itinerary document
  function generateVisaDoc() {
    const nat = document.getElementById('visa-nationality').value;
    const title = document.getElementById('visa-title').value;
    const city = document.getElementById('visa-city').value;
    const days = document.getElementById('visa-days').value;
    const result = document.getElementById('visa-result');

    // Try to get trip content from latest trip
    getTrips().then(trips => {
      const latest = trips.find(t => t.id === trips[0]?.id) || {};
      const content = latest.content || '';

      result.innerHTML = '<p class="visa-loading">Generating document...</p>';

      fetch('/api/visa/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          nationality: nat,
          title: title,
          city: city,
          days: days,
          content: content,
        })
      }).then(r => r.json()).then(data => {
        if (data.error) {
          result.innerHTML = '<p class="visa-error">' + escHtml(data.error) + '</p>';
          return;
        }
        const doc = data.document || '';
        result.innerHTML = '<div class="visa-doc-preview"><pre>' + escHtml(doc.substring(0, 2000)) + '</pre></div>'
          + '<div class="visa-doc-actions">'
          + '<button class="visa-btn visa-btn-primary" onclick="navigator.clipboard.writeText(' + JSON.stringify(doc) + ').then(function(){this.textContent=\'✅ Copied!\'}.bind(this))">📋 Copy Full Document</button>'
          + '</div>';
      }).catch(() => {
        result.innerHTML = '<p class="visa-error">Failed to generate. Try again.</p>';
      });
    });
  }

  function autoSaveTrip(city, content) {
    // Detect if content looks like an itinerary
    const hasDay = /\*\*Day \d+|Day \d+:/i.test(content);
    const hasList = /^\- /m.test(content);
    const hasEmoji = /[🕐🍽️🏨💡🎯💰]/i.test(content);
    if ((hasDay || (hasList && content.length > 300)) && content.length > 200) {
      const trip = saveTrip(city, content);
      return trip;
    }
    return null;
  }

  // ── Keyboard shortcuts ──
  document.addEventListener('keydown', (e) => {
    // Escape to close modal
    if (e.key === 'Escape') closeCityDetail();
    if (e.key === 'Escape') closeToolDetail();
    // Ctrl+Shift+C to clear chat
    if (e.key === 'C' && e.ctrlKey && e.shiftKey) {
      e.preventDefault();
      clearChatHistory();
    }
  });

  // ── Map State ──
  let mapInstance = null;
  let mapMarkers = [];
  let mapInitialized = false;

  // ── City Tags (for map markers) ──
  const CITY_TAGS = {
    'beijing': {emoji: '🏛️', tag: 'popular', desc: 'Capital — Forbidden City, Great Wall, imperial history'},
    'shanghai': {emoji: '🌃', tag: 'popular', desc: 'Global metropolis — Bund, futuristic skyline, shopping'},
    'guangzhou': {emoji: '🍜', tag: 'popular', desc: 'Canton cuisine hub — dim sum, Cantonese culture'},
    'shenzhen': {emoji: '🚀', tag: 'regional', desc: 'Tech powerhouse — innovation, modern parks'},
    'chengdu': {emoji: '🐼', tag: 'popular', desc: 'Panda homeland — spicy food, teahouses'},
    'chongqing': {emoji: '🌆', tag: 'popular', desc: 'Mountain city — cyberpunk skyline, hotpot'},
    'hangzhou': {emoji: '🏞️', tag: 'popular', desc: 'West Lake — poetic gardens, tea culture'},
    'suzhou': {emoji: '🏯', tag: 'regional', desc: 'Classic gardens — silk, canals, water towns'},
    'kunming': {emoji: '🌸', tag: 'regional', desc: 'Spring City — year-round mild weather, Stone Forest'},
    'dali': {emoji: '🏔️', tag: 'hidden-gem', desc: 'Ancient town — snow mountains, Erhai Lake, indie cafes'},
    'lijiang': {emoji: '🏘️', tag: 'hidden-gem', desc: 'UNESCO old town — Naxi culture, Jade Dragon Mountain'},
    'guilin': {emoji: '🏔️', tag: 'popular', desc: 'Karst landscapes — Li River, Yangshuo countryside'},
    'xian': {emoji: '🏛️', tag: 'popular', desc: 'Terracotta Warriors — ancient capital, Muslim Quarter'},
    'wuhan': {emoji: '🌉', tag: 'regional', desc: 'Central hub — Yangtze bridges, university district'},
    'changsha': {emoji: '🌶️', tag: 'regional', desc: 'Spice central — Orange Island, vibrant nightlife'},
    'nanjing': {emoji: '🏛️', tag: 'popular', desc: 'Ancient capital — Ming tombs, Confucius Temple'},
    'qingdao': {emoji: '🍺', tag: 'regional', desc: 'Coastal city — Tsingtao beer, German architecture'},
    'dalian': {emoji: '🏖️', tag: 'regional', desc: 'Seaside resort — European vibes, seafood'},
    'xiamen': {emoji: '🏝️', tag: 'regional', desc: 'Island garden — Gulangyu, colonial architecture'},
    'harbin': {emoji: '❄️', tag: 'hidden-gem', desc: 'Ice City — winter festival, Russian heritage'},
    'tibet': {emoji: '🏔️', tag: 'hidden-gem', desc: 'Roof of the World — Potala Palace, high-altitude wonder'},
    'lanzhou': {emoji: '🍜', tag: 'hidden-gem', desc: 'Silk Road gateway — beef noodles, Yellow River'},
    'dunhuang': {emoji: '🏜️', tag: 'hidden-gem', desc: 'Mogao Caves — Silk Road art, sand dunes'},
    'urumqi': {emoji: '🏔️', tag: 'hidden-gem', desc: 'Central Asia gateway — bazaars, Tianshan Mountains'},
    'huangshan': {emoji: '🏔️', tag: 'popular', desc: 'Yellow Mountain — iconic peaks, hot springs'},
    'zhangjiajie': {emoji: '🌲', tag: 'regional', desc: 'Avatar Mountains — towering sandstone pillars'},
    'luoyang': {emoji: '🏛️', tag: 'regional', desc: 'Ancient capital — Longmen Grottoes, peonies'},
    'kaifeng': {emoji: '🏛️', tag: 'hidden-gem', desc: 'Song dynasty capital — Millennium City Park'},
    'hohhot': {emoji: '🌿', tag: 'hidden-gem', desc: 'Inner Mongolia — grasslands, dairy culture'},
    'guiyang': {emoji: '🌳', tag: 'hidden-gem', desc: 'Green capital — minority villages, Huangguoshu Falls'},
    'fuzhou': {emoji: '🏖️', tag: 'hidden-gem', desc: 'Coastal gateway — hot springs, Min culture'},
    'ningbo': {emoji: '🏯', tag: 'hidden-gem', desc: 'Port city — Tianyi Pavilion, Dongqian Lake'},
    'nanning': {emoji: '🌴', tag: 'hidden-gem', desc: 'Green City — ASEAN gateway, tropical vibes'},
    'haikou': {emoji: '🏖️', tag: 'hidden-gem', desc: 'Island capital — beaches, coconut plantations'},
    'sanya': {emoji: '🏖️', tag: 'popular', desc: 'China\'s Hawaii — tropical beaches, resorts'},
    'macau': {emoji: '🎰', tag: 'regional', desc: 'Las Vegas of Asia — Portuguese heritage, casinos'},
  };

  // ── Map Functions ──
  function initMap() {
    const canvas = document.getElementById('map-canvas');
    if (!canvas) return;
    if (mapInitialized && mapInstance) {
      mapInstance.invalidateSize();
      return;
    }

    // Use API config to decide AMap vs Leaflet
    fetch('/api/config').then(r => r.json()).then(config => {
      if (config.use_amap && config.amap_key && config.amap_security_code) {
        initAMap(config.amap_key, config.amap_security_code);
      } else {
        initLeafletMap();
      }
    }).catch(() => {
      initLeafletMap();
    });
  }

  function initLeafletMap() {
    const canvas = document.getElementById('map-canvas');
    if (!canvas) return;

    mapInstance = L.map('map-canvas', {
      center: [35.0, 108.0],
      zoom: 4,
      zoomControl: true,
      attributionControl: true,
    });

    // Dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(mapInstance);

    plotMapMarkers();
    mapInitialized = true;
  }

  function initAMap(apiKey, securityCode) {
    // AMap initialization — load script dynamically
    const canvas = document.getElementById('map-canvas');
    if (!canvas) return;

    // Set security config BEFORE loading the API
    window._AMapSecurityConfig = {
      securityJsCode: securityCode || '',
    };

    // Load AMap JS API v2.0
    const script = document.createElement('script');
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${apiKey}`;
    script.onload = () => {
      if (typeof AMap === 'undefined') return;
      const map = new AMap.Map('map-canvas', {
        zoom: 4,
        center: [104.0, 35.0],
        mapStyle: 'amap://styles/darkblue',
      });
      mapInstance = map;

      // Plot markers
      fetch('/api/map').then(r => r.json()).then(data => {
        const cities = data.cities || {};
        Object.keys(cities).forEach(key => {
          const c = cities[key];
          if (!c.lat || !c.lng) return;
          const tags = CITY_TAGS[key] || {emoji: '📍', tag: 'regional'};
          const marker = new AMap.Marker({
            position: [c.lng, c.lat],
            title: key.charAt(0).toUpperCase() + key.slice(1),
            label: {content: tags.emoji, offset: new AMap.Pixel(-15, -15)},
          });
          marker.on('click', () => showMapDetail(key));
          marker._cityKey = key;
          map.add(marker);
          mapMarkers.push(marker);
        });
      });

      mapInitialized = true;
    };
    document.head.appendChild(script);
  }

  function plotMapMarkers() {
    if (!mapInstance) return;
    fetch('/api/map').then(r => r.json()).then(data => {
      const cities = data.cities || {};

      Object.keys(cities).forEach(key => {
        const c = cities[key];
        if (!c.lat || !c.lng) return;
        const tags = CITY_TAGS[key] || {emoji: '📍', tag: 'regional'};
        const markerColor = tags.tag === 'popular' ? '#e74c3c' : tags.tag === 'regional' ? '#f39c12' : '#2ecc71';

        const icon = L.divIcon({
          className: 'custom-marker ' + tags.tag,
          html: tags.emoji,
          iconSize: [32, 32],
          iconAnchor: [16, 16],
        });

        const marker = L.marker([c.lat, c.lng], {icon})
          .addTo(mapInstance)
          .on('click', () => showMapDetail(key));

        mapMarkers.push(marker);
      });
    });
  }

  function showMapDetail(cityKey) {
    const detail = document.getElementById('map-city-detail');
    const nameEl = document.getElementById('map-detail-name');
    const descEl = document.getElementById('map-detail-desc');
    const tagsEl = document.getElementById('map-detail-tags');

    if (!detail || !nameEl) return;

    const tags = CITY_TAGS[cityKey] || {emoji: '📍', tag: 'regional', desc: ''};
    const summary = state.cityCatalog && state.cityCatalog[cityKey] ? state.cityCatalog[cityKey] : {};
    const cityName = formatDisplayText(summary.name_en || humanizeCityKey(cityKey), summary.name_cn);

    nameEl.textContent = `${tags.emoji} ${cityName}`;
    descEl.textContent = tags.desc;

    // Tag badges
    tagsEl.innerHTML = '';
    const tagBadge = document.createElement('span');
    tagBadge.className = 'tag';
    tagBadge.textContent = tags.tag === 'popular' ? '⭐ Top Destination' : tags.tag === 'regional' ? '📍 Regional Hub' : '💎 Hidden Gem';
    tagsEl.appendChild(tagBadge);

    // Store for plan button
    detail.dataset.city = cityKey;

    detail.classList.remove('hidden');
  }

  function mapCloseDetail() {
    const detail = document.getElementById('map-city-detail');
    if (detail) detail.classList.add('hidden');
  }

  function mapOpenChat() {
    const detail = document.getElementById('map-city-detail');
    if (detail && detail.dataset.city) {
      const city = detail.dataset.city;
      mapCloseDetail();
      const isMobile = window.innerWidth <= 640;
      if (isMobile) {
        openChatOverlay(city);
      } else {
        focusChat(city);
        navigate('chat');
      }
    }
  }

  // ── Init ──
  function init() {
    hideGlobalError();
    showGlobalLoading('Loading VisePanda…');

    safeInitStep('theme', initTheme);
    safeInitStep('runtime config', hydrateRuntimeConfig);
    safeInitStep('scroll helpers', initScrollToTop);
    safeInitStep('auth triggers', bindAuthTriggers);
    safeInitStep('primary nav', bindPrimaryNav);
    safeInitStep('chat inputs', bindChatInputs);
    safeInitStep('startup state', initStartupState);
    safeInitStep('hash navigation', initHashNavigation);
    safeInitStep('initial view', () => {
      const hash = (window.location.hash || '#home').replace('#', '');
      navigate(supportedViews.has(hash) ? hash : 'home');
    });
    attachImageFallbacks(document);

    hideGlobalLoading();
  }

  // ════════════════════════════════════════════════════════════
  // AUTH MODULE
  // ════════════════════════════════════════════════════════════

  var _authToken = localStorage.getItem('vp_token');
  var _authUser = null;

  if (_authToken) {
    // Try to restore session on load
    fetch('/api/auth/me', {
      headers: {'Authorization': 'Bearer ' + _authToken}
    }).then(function(r){
      if (r.ok) return r.json();
      _authToken = null;
      localStorage.removeItem('vp_token');
    }).then(function(data){
      if (data && data.user) {
        _authUser = data.user;
        localStorage.setItem('vp_user', JSON.stringify(data.user));
      }
      _updateAuthUI();
    }).catch(function(){
      _authToken = null;
      localStorage.removeItem('vp_token');
      _updateAuthUI();
    });
  } else {
    _updateAuthUI();
  }

  function _updateAuthUI() {
    var authBtn = document.getElementById('auth-btn');
    var userMenu = document.getElementById('user-menu');
    var adminLink = document.getElementById('admin-link');
    if (_authToken && _authUser) {
      authBtn.style.display = 'none';
      userMenu.style.display = 'block';
      document.getElementById('user-avatar-text').textContent =
        (_authUser.display_name || _authUser.email || 'U')[0].toUpperCase();
      document.getElementById('dropdown-user-email').textContent =
        _authUser.display_name || _authUser.email || '';
      if (adminLink) {
        adminLink.style.display = (_authUser.role === 'admin' || _authUser.role === 'ops') ? 'block' : 'none';
      }
    } else {
      authBtn.style.display = 'block';
      userMenu.style.display = 'none';
    }
  }

  var auth = {
    // State
    isLoggedIn: function() { return !!_authToken && !!_authUser; },
    getUser: function() { return _authUser; },
    getToken: function() { return _authToken; },

    // Show login modal
    showModal: function() {
      document.getElementById('auth-modal-overlay').classList.remove('hidden');
      document.getElementById('auth-error').classList.add('hidden');
      document.getElementById('auth-reg-error').classList.add('hidden');
      document.getElementById('auth-login-form').classList.remove('hidden');
      document.getElementById('auth-register-form').classList.add('hidden');
      document.getElementById('auth-success').classList.add('hidden');
      document.getElementById('login-email').value = '';
      document.getElementById('login-password').value = '';
      document.getElementById('login-email').focus();
    },

    closeModal: function() {
      document.getElementById('auth-modal-overlay').classList.add('hidden');
    },

    showLogin: function() {
      document.getElementById('auth-login-form').classList.remove('hidden');
      document.getElementById('auth-register-form').classList.add('hidden');
      document.getElementById('auth-success').classList.add('hidden');
      document.getElementById('auth-error').classList.add('hidden');
    },

    showRegister: function() {
      document.getElementById('auth-login-form').classList.add('hidden');
      document.getElementById('auth-register-form').classList.remove('hidden');
      document.getElementById('auth-success').classList.add('hidden');
      document.getElementById('auth-reg-error').classList.add('hidden');
    },

    // Password Reset
    showForgotPassword: function() {
      document.getElementById('auth-login-form').classList.add('hidden');
      document.getElementById('auth-register-form').classList.add('hidden');
      document.getElementById('auth-success').classList.add('hidden');
      document.getElementById('auth-forgot-form').classList.remove('hidden');
      document.getElementById('auth-reset-form').classList.add('hidden');
      document.getElementById('auth-forgot-error').classList.add('hidden');
      document.getElementById('auth-forgot-success').classList.add('hidden');
      document.getElementById('auth-reset-error').classList.add('hidden');
      document.getElementById('auth-reset-success').classList.add('hidden');
      document.getElementById('forgot-email').value = '';
      document.getElementById('forgot-email').focus();
    },

    sendResetCode: function() {
      var email = document.getElementById('forgot-email').value.trim();
      var errEl = document.getElementById('auth-forgot-error');
      var succEl = document.getElementById('auth-forgot-success');
      errEl.classList.add('hidden');
      succEl.classList.add('hidden');

      if (!email) {
        errEl.textContent = 'Please enter your email.';
        errEl.classList.remove('hidden');
        return;
      }

      var btn = document.querySelector('#auth-forgot-form .auth-submit');
      btn.disabled = true;
      btn.textContent = 'Sending...';

      fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: email})
      }).then(function(r){ return r.json(); }).then(function(data){
        btn.disabled = false;
        btn.textContent = 'Send Reset Code';

        // Show the reset code if returned (in production this would be sent via email)
        if (data.reset_token) {
          // Pre-fill the reset code for convenience
          document.getElementById('reset-code').value = data.reset_token;
          // Show the reset form
          document.getElementById('auth-forgot-form').classList.add('hidden');
          document.getElementById('auth-reset-form').classList.remove('hidden');
          document.getElementById('auth-reset-error').classList.add('hidden');
          document.getElementById('auth-reset-success').classList.add('hidden');
          document.getElementById('reset-password').focus();
        } else {
          // Email not found — show message but don't reveal if email exists
          succEl.textContent = data.message || 'If this email exists, a reset code has been sent.';
          succEl.classList.remove('hidden');
        }
      }).catch(function(){
        btn.disabled = false;
        btn.textContent = 'Send Reset Code';
        errEl.textContent = 'Failed to send. Try again.';
        errEl.classList.remove('hidden');
      });
    },

    completeReset: function() {
      var code = document.getElementById('reset-code').value.trim();
      var pw = document.getElementById('reset-password').value;
      var pw2 = document.getElementById('reset-password-confirm').value;
      var errEl = document.getElementById('auth-reset-error');
      var succEl = document.getElementById('auth-reset-success');
      errEl.classList.add('hidden');
      succEl.classList.add('hidden');

      if (!code) {
        errEl.textContent = 'Please enter the reset code.';
        errEl.classList.remove('hidden');
        return;
      }
      if (!pw || pw.length < 4) {
        errEl.textContent = 'Password must be at least 4 characters.';
        errEl.classList.remove('hidden');
        return;
      }
      if (pw !== pw2) {
        errEl.textContent = 'Passwords do not match.';
        errEl.classList.remove('hidden');
        return;
      }

      var btn = document.querySelector('#auth-reset-form .auth-submit');
      btn.disabled = true;
      btn.textContent = 'Resetting...';

      fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({token: code, password: pw})
      }).then(function(r){ return r.json(); }).then(function(data){
        btn.disabled = false;
        btn.textContent = 'Reset Password';
        if (data.error) {
          errEl.textContent = data.error;
          errEl.classList.remove('hidden');
          return;
        }
        succEl.textContent = 'Password reset successfully! You can now sign in.';
        succEl.classList.remove('hidden');
        // Show login after 2 seconds
        setTimeout(function(){
          document.getElementById('auth-reset-form').classList.add('hidden');
          document.getElementById('auth-login-form').classList.remove('hidden');
          document.getElementById('login-email').focus();
        }, 2000);
      }).catch(function(){
        btn.disabled = false;
        btn.textContent = 'Reset Password';
        errEl.textContent = 'Failed to reset. Try again.';
        errEl.classList.remove('hidden');
      });
    },

    // Login
    login: function() {
      var email = document.getElementById('login-email').value.trim();
      var password = document.getElementById('login-password').value;
      var errEl = document.getElementById('auth-error');

      if (!email || !password) {
        errEl.textContent = 'Please enter email and password';
        errEl.classList.remove('hidden');
        return;
      }

      errEl.classList.add('hidden');
      var btn = document.querySelector('#auth-login-form .auth-submit');
      btn.disabled = true;
      btn.textContent = 'Signing in...';

      fetch('/api/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: email, password: password})
      }).then(function(r){
        return r.json().then(function(d){ d._status = r.status; return d; });
      }).then(function(data){
        if (data._status >= 400) {
          throw new Error(data.error || 'Login failed');
        }
        _authToken = data.token;
        _authUser = data.user;
        localStorage.setItem('vp_token', _authToken);
        localStorage.setItem('vp_user', JSON.stringify(data.user));
        _updateAuthUI();
        // Show success
        document.getElementById('auth-login-form').classList.add('hidden');
        document.getElementById('auth-success-title').textContent = 'Welcome back! 🐼';
        document.getElementById('auth-success-msg').textContent = 'You\'re signed in as ' + email;
        document.getElementById('auth-success').classList.remove('hidden');
      }).catch(function(err){
        errEl.textContent = err.message;
        errEl.classList.remove('hidden');
        btn.disabled = false;
        btn.textContent = 'Sign In';
      });
    },

    // Register
    register: function() {
      var email = document.getElementById('reg-email').value.trim();
      var password = document.getElementById('reg-password').value;
      var name = document.getElementById('reg-name').value.trim();
      var errEl = document.getElementById('auth-reg-error');

      if (!email || !password) {
        errEl.textContent = 'Email and password are required';
        errEl.classList.remove('hidden');
        return;
      }
      if (password.length < 6) {
        errEl.textContent = 'Password must be at least 6 characters';
        errEl.classList.remove('hidden');
        return;
      }

      errEl.classList.add('hidden');
      var btn = document.querySelector('#auth-register-form .auth-submit');
      btn.disabled = true;
      btn.textContent = 'Creating account...';

      var payload = {email: email, password: password};
      if (name) payload.display_name = name;

      fetch('/api/auth/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      }).then(function(r){
        return r.json().then(function(d){ d._status = r.status; return d; });
      }).then(function(data){
        if (data._status >= 400) {
          throw new Error(data.error || 'Registration failed');
        }
        // Auto-login after register
        return fetch('/api/auth/login', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({email: email, password: password})
        }).then(function(r){
          return r.json().then(function(d){ d._status = r.status; return d; });
        }).then(function(loginData){
          if (loginData._status >= 400) throw new Error('Auto-login failed');
          _authToken = loginData.token;
          _authUser = loginData.user;
          localStorage.setItem('vp_token', _authToken);
          localStorage.setItem('vp_user', JSON.stringify(loginData.user));
          _updateAuthUI();
          document.getElementById('auth-register-form').classList.add('hidden');
          document.getElementById('auth-success-title').textContent = 'Account created! 🎉';
          document.getElementById('auth-success-msg').textContent = 'Welcome to VisePanda, ' + email;
          document.getElementById('auth-success').classList.remove('hidden');
        });
      }).catch(function(err){
        errEl.textContent = err.message;
        errEl.classList.remove('hidden');
        btn.disabled = false;
        btn.textContent = 'Create Account';
      });
    },

    // Logout
    logout: function() {
      // Invalidate token on server (fire-and-forget)
      fetch('/api/auth/logout', {
        method: 'POST',
        headers: {'Authorization': 'Bearer ' + (_authToken || localStorage.getItem('vp_token'))}
      }).catch(function(){});
      _authToken = null;
      _authUser = null;
      localStorage.removeItem('vp_token');
      localStorage.removeItem('vp_user');
      _updateAuthUI();
      // Close dropdown
      document.getElementById('user-dropdown').classList.add('hidden');
      // Reload to reset all state
      location.reload();
    },

    // User menu dropdown
    toggleMenu: function() {
      var dd = document.getElementById('user-dropdown');
      dd.classList.toggle('hidden');
      // Add click-outside-to-close listener
      if (!dd.classList.contains('hidden')) {
        setTimeout(function(){
          document.addEventListener('click', VP.auth._closeDropdownOutside);
        }, 0);
      }
    },

    _closeDropdownOutside: function(e) {
      var dd = document.getElementById('user-dropdown');
      var avatar = document.querySelector('.user-avatar');
      if (dd && !dd.contains(e.target) && avatar && !avatar.contains(e.target)) {
        dd.classList.add('hidden');
        document.removeEventListener('click', VP.auth._closeDropdownOutside);
      }
    },

    // My Chats modal
    showMyChats: function() {
      document.getElementById('user-dropdown').classList.add('hidden');
      document.getElementById('chats-modal-overlay').classList.remove('hidden');
      document.getElementById('chats-list').innerHTML = '<p class="chats-empty">Loading...</p>';

      fetch('/api/auth/chat-history', {
        headers: {'Authorization': 'Bearer ' + _authToken}
      }).then(function(r){ return r.json(); }).then(function(data){
        var html = '';
        if (!data.conversations || data.conversations.length === 0) {
          html = '<p class="chats-empty">No saved conversations yet.</p>';
        } else {
          data.conversations.forEach(function(conv){
            var title = conv.title || 'Chat';
            var date = (conv.updated_at || conv.created_at || '').split('T')[0] || '';
            html += '<div class="chat-item" onclick="VP.auth.loadChat(\'' + conv.id + '\')">'
              + '<div class="chat-item-title">' + escHtml(title) + '</div>'
              + '<div class="chat-item-meta">' + (conv.message_count || 0) + ' messages · ' + date + '</div>'
              + '</div>';
          });
        }
        document.getElementById('chats-list').innerHTML = html;
      }).catch(function(){
        document.getElementById('chats-list').innerHTML = '<p class="chats-empty">Failed to load conversations.</p>';
      });
    },

    closeChatsModal: function() {
      document.getElementById('chats-modal-overlay').classList.add('hidden');
    },

    loadChat: function(convId) {
      // Fetch and display conversation messages in the modal
      var viewer = document.getElementById('chat-viewer');
      var list = document.getElementById('chats-list');
      var msgsEl = document.getElementById('chat-viewer-messages');
      var titleEl = document.getElementById('chat-viewer-title');

      msgsEl.innerHTML = '<div class="chat-loading">Loading...</div>';
      list.style.display = 'none';
      viewer.classList.add('active');

      fetch('/api/auth/chat/' + convId, {
        headers: {'Authorization': 'Bearer ' + _authToken}
      }).then(function(r){ return r.json(); }).then(function(data){
        if (data.error) {
          msgsEl.innerHTML = '<div class="chats-empty">' + escHtml(data.error) + '</div>';
          return;
        }
        titleEl.textContent = (data.conversation && data.conversation.title) || 'Chat';
        var msgs = data.messages || [];
        if (msgs.length === 0) {
          msgsEl.innerHTML = '<div class="chats-empty">No messages</div>';
          return;
        }
        msgsEl.innerHTML = msgs.map(function(m){
          var roleClass = m.role === 'user' ? 'user' : 'assistant';
          var time = (m.created_at || '').split('T').join(' ');
          return '<div class="chat-message-item">'
            + '<div class="chat-message-role ' + roleClass + '">' + escHtml(m.role) + '</div>'
            + '<div class="chat-message-content">' + escHtml(m.content) + '</div>'
            + '<div class="chat-message-time">' + time + '</div>'
            + '</div>';
        }).join('');
        // Scroll to bottom
        msgsEl.scrollTop = msgsEl.scrollHeight;
      }).catch(function(){
        msgsEl.innerHTML = '<div class="chats-empty">Failed to load conversation.</div>';
      });
    },

    backToChatList: function() {
      document.getElementById('chat-viewer').classList.remove('active');
      document.getElementById('chats-list').style.display = '';
    },

    showMyTrips: function() {
      document.getElementById('user-dropdown').classList.add('hidden');
      navigate('trips');
    },

    goToAdmin: function() {
      document.getElementById('user-dropdown').classList.add('hidden');
      window.location.href = '/admin';
    },

    // ═══ Settings ═══
    showSettings: function() {
      document.getElementById('user-dropdown').classList.add('hidden');
      // Pre-fill display name
      var nameInput = document.getElementById('settings-name');
      if (_authUser && _authUser.display_name) {
        nameInput.value = _authUser.display_name;
      } else {
        nameInput.value = '';
      }
      document.getElementById('settings-password').value = '';
      document.getElementById('settings-password-confirm').value = '';
      document.getElementById('settings-error').classList.add('hidden');
      document.getElementById('settings-success').classList.add('hidden');
      document.getElementById('settings-modal-overlay').classList.remove('hidden');
    },

    closeSettings: function() {
      document.getElementById('settings-modal-overlay').classList.add('hidden');
    },

    saveSettings: function() {
      var errEl = document.getElementById('settings-error');
      var succEl = document.getElementById('settings-success');
      errEl.classList.add('hidden');
      succEl.classList.add('hidden');

      var name = document.getElementById('settings-name').value.trim();
      var pw = document.getElementById('settings-password').value;
      var pw2 = document.getElementById('settings-password-confirm').value;

      if (!name && !pw) {
        errEl.textContent = 'No changes to save.';
        errEl.classList.remove('hidden');
        return;
      }

      if (pw && pw !== pw2) {
        errEl.textContent = 'Passwords do not match.';
        errEl.classList.remove('hidden');
        return;
      }

      if (pw && pw.length < 4) {
        errEl.textContent = 'Password must be at least 4 characters.';
        errEl.classList.remove('hidden');
        return;
      }

      var body = {};
      if (name) body.display_name = name;
      if (pw) body.password = pw;

      fetch('/api/auth/update-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + _authToken
        },
        body: JSON.stringify(body)
      }).then(function(r){ return r.json(); }).then(function(data){
        if (data.error) {
          errEl.textContent = data.error;
          errEl.classList.remove('hidden');
          return;
        }
        // Update local user info
        if (_authUser && name) _authUser.display_name = name;
        // Show success
        succEl.textContent = 'Settings saved!';
        succEl.classList.remove('hidden');
        // Clear password fields
        document.getElementById('settings-password').value = '';
        document.getElementById('settings-password-confirm').value = '';
      }).catch(function(){
        errEl.textContent = 'Failed to save. Try again.';
        errEl.classList.remove('hidden');
      });
    },

    // Save current chat (to be called from chat module)
    saveChat: function(convId, messages) {
      if (!_authToken) return Promise.resolve(null);
      var title = '';
      if (messages && messages.length > 0 && messages[0].content) {
        title = messages[0].content.substring(0, 50);
      }
      return fetch('/api/auth/chat/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + _authToken
        },
        body: JSON.stringify({
          conversation_id: convId || null,
          title: title,
          messages: messages || []
        })
      }).then(function(r){ return r.json(); });
    },

    // Google login
    googleLogin: function(credential) {
      if (!credential) return;
      var errEl = document.getElementById('auth-error');
      errEl.classList.add('hidden');

      fetch('/api/auth/google/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({credential: credential})
      }).then(function(r){
        return r.json().then(function(d){ d._status = r.status; return d; });
      }).then(function(data){
        if (data._status >= 400) {
          throw new Error(data.error || 'Google login failed');
        }
        _authToken = data.token;
        _authUser = data.user;
        localStorage.setItem('vp_token', _authToken);
        localStorage.setItem('vp_user', JSON.stringify(data.user));
        _updateAuthUI();
        document.getElementById('auth-login-form').classList.add('hidden');
        document.getElementById('auth-success-title').textContent = 'Welcome! 🐼';
        document.getElementById('auth-success-msg').textContent = 'Signed in with Google as ' + (data.user.email || '');
        document.getElementById('auth-success').classList.remove('hidden');
      }).catch(function(err){
        errEl.textContent = err.message;
        errEl.classList.remove('hidden');
      });
    },
  };

  // Google OAuth callback (called from GIS library)
  window.handleGoogleCredential = function(response) {
    if (response && response.credential) {
      auth.googleLogin(response.credential);
    }
  };

  // ── Expose public API ──
  return {
    navigate,
    retryCurrentView,
    toggleTheme,
    focusChat,
    sendMessage,
    stopStreaming,
    autoResize,
    clearChatHistory,
    openCityDetail,
    closeCityDetail,
    loadTrip,
    shareTrip,
    deleteTrip,
    saveCurrentTrip,
    copyTimeline,
    compareCities,
    showVisaModal,
    openToolDetail,
    closeToolDetail,
    checkVisa,
    generateVisaDoc,
    mapCloseDetail,
    mapOpenChat,
    chatOverlayBack,
    init,
    scrollChatToLatest,
    scrollToTop,
    auth,
  };
})();

// ── Auto-init ──
document.addEventListener('DOMContentLoaded', () => VP.init());
