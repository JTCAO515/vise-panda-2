/* ═══════════════════════════════════════════════════════════
   VisePanda v3.0.1 — Frontend Application
   ═══════════════════════════════════════════════════════════ */

const VP = (function(){
  'use strict';

  // ── State ──
  const state = {
    currentView: 'home',
    messages: [],
    isStreaming: false,
    theme: document.documentElement.getAttribute('data-theme') || 'dark',
  };

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
    state.currentView = view;
    $$('.nav-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.view === view);
    });
    $$('.view').forEach(v => v.classList.remove('active'));
    const target = document.getElementById(`view-${view}`);
    if (target) target.classList.add('active');

    if (view === 'cities') loadCities();
    if (view === 'trips') renderTrips();
    if (view === 'tools') loadTools();
    if (view === 'home') loadHomeCities();

    window.location.hash = view;
  }

  // ── Focus chat on a city ──
  function focusChat(city) {
    const input = document.getElementById('chat-input');
    if (input) {
      input.value = `Plan a trip to ${city}`;
      input.style.height = 'auto';
      toggleSendButton(true);
      input.focus();
    }
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

  // ── Create city card element ──
  function createCityCard(name, info) {
    const card = document.createElement('div');
    card.className = 'city-card';
    card.onclick = () => openCityDetail(name);

    const emoji = getCityEmoji(name);
    const hasImg = info.image ? true : false;
    if (hasImg) card.classList.add('has-img');
    const tags = getCityTags(name, info);

    let imgHtml = '';
    if (hasImg) {
      imgHtml = `<img class="city-bg-img" src="${info.image}" alt="${name}" loading="lazy" onerror="this.parentElement.classList.remove('has-img');this.remove()">`;
    }

    card.innerHTML = imgHtml + `
      <div class="city-card-top">
        <span class="city-emoji">${emoji}</span>
      </div>
      <div class="city-card-bottom">
        <div class="city-name">${name}</div>
        <div class="city-sub">${info.name_cn || ''}</div>
        <div class="city-meta">${info.best_season || ''} · ${info.days || ''}</div>
        ${info.vibe ? `<div class="city-vibe">${info.vibe}</div>` : ''}
        ${tags.length ? `<div class="city-tags">${tags.map(t => `<span class="city-tag">${t}</span>`).join('')}</div>` : ''}
      </div>
    `;
    return card;
  }

  // ── Load Home Cities ──
  async function loadHomeCities() {
    const grid = document.getElementById('city-grid');
    if (!grid) return;
    const data = await apiGet('/api/cities');
    if (!data || !data.cities) return;
    grid.innerHTML = '';
    Object.entries(data.cities).slice(0, 8).forEach(([name, info]) => {
      grid.appendChild(createCityCard(name, info));
    });
  }

  // ── Load Cities (all) ──
  async function loadCities() {
    const grid = document.getElementById('cities-grid');
    if (!grid) return;
    const data = await apiGet('/api/cities');
    if (!data || !data.cities) return;
    grid.innerHTML = '';
    Object.entries(data.cities).forEach(([name, info]) => {
      grid.appendChild(createCityCard(name, info));
    });
  }

  // ── Load Tools ──
  async function loadTools() {
    const grid = document.getElementById('tools-grid');
    if (!grid) return;
    const data = await apiGet('/api/tools');
    if (!data || !data.tools) return;

    grid.innerHTML = '';
    const emojis = {packing:'🧳', pricing:'💰', visa:'🛂', phrases:'💬', emergency:'🆘'};
    Object.entries(data.tools).forEach(([name, desc]) => {
      const card = document.createElement('div');
      card.className = 'tool-card';
      card.innerHTML = `
        <div style="font-size:24px;margin-bottom:8px">${emojis[name] || '🧰'}</div>
        <div style="font-size:14px;font-weight:600;margin-bottom:2px;text-transform:capitalize">${name}</div>
        <div style="font-size:12px;color:var(--text-muted)">${desc}</div>
      `;
      grid.appendChild(card);
    });
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

    // Build food HTML
    let foodHtml = '';
    if (city.food && city.food.length) {
      const items = city.food.map(f => {
        const star = f.must_try ? '⭐ ' : '';
        const cls = f.must_try ? 'food-item must' : 'food-item';
        return '<div class="' + cls + '">'
          + '<div class="food-item-name">' + star + escHtml(f.name_en || '') + ' <span class="food-item-cn">' + escHtml(f.name_cn || '') + '</span></div>'
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
      + '<div><h2 class="detail-name">' + name + '</h2>'
      + '<div class="detail-sub">' + escHtml(city.name_cn || '') + ' · ' + escHtml(city.province || '') + '</div></div>'
      + '<button class="modal-close" onclick="VP.closeCityDetail()">✕</button></div>'
      + '<div class="detail-meta"><span>📅 Best: ' + escHtml(city.best_season || '') + '</span><span>⏱️ ' + escHtml(city.days || '') + '</span><span>' + escHtml(city.vibe || '') + '</span></div>'
      + (city.budget_tip ? '<div class="detail-tip">💰 ' + escHtml(city.budget_tip) + '</div>' : '')
      + (tags.length ? '<div class="detail-tags">' + tags.map(function(t){return '<span class="detail-tag">' + escHtml(t) + '</span>';}).join('') + '</div>' : '')
      + foodHtml
      + hotelHtml
      + tipsHtml
      + '<div class="detail-actions"><button class="btn-primary" onclick="VP.navigate(\'chat\');setTimeout(function(){VP.focusChat(\'' + name.toLowerCase() + '\')},100)">💬 Plan a Trip to ' + name + '</button></div>';
  }

  function closeCityDetail() {
    const overlay = document.getElementById('city-detail-overlay');
    if (overlay) overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  // ═══════════════════════════════════════════════════════════
  // CHAT
  // ═══════════════════════════════════════════════════════════

  let abortController = null;
  let currentCity = ''; // Track city across multi-turn conversation

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
      <div class="msg-avatar">${role === 'assistant' || role === 'bot' ? '🐼' : '👤'}</div>
      <div class="msg-body">
        <div class="msg-sender">${role === 'assistant' || role === 'bot' ? 'VisePanda' : 'You'}</div>
        <div class="msg-text">${role === 'user' ? text.replace(/\n/g, '<br>') : renderMD(text)}</div>
      </div>
    `;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
    return msg;
  }

  function addTyping() {
    const container = document.getElementById('chat-messages');
    if (!container) return null;
    const msg = document.createElement('div');
    msg.className = 'msg msg-bot';
    msg.id = 'typing-msg';
    msg.innerHTML = `
      <div class="msg-avatar">🐼</div>
      <div class="msg-body">
        <div class="msg-sender">VisePanda</div>
        <div class="msg-text"><span class="typing-dots"><span>.</span><span>.</span><span>.</span></span></div>
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
  
    saveMessages();

    // Show typing + stop button
    const typingId = addTyping();
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
              botContent += parsed.token;
              updateTyping(typingId, botContent);
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

      removeMessage(typingId);
      if (botContent) {
        addMessage(botContent, 'assistant');
        state.messages.push({role: 'assistant', content: botContent});
        saveMessages();
        // Auto-save if looks like an itinerary
        const saved = autoSaveTrip(currentCity, botContent);
        if (saved) {
          // Add subtle save indicator
          const msgs = document.getElementById('chat-messages');
          if (msgs) {
            const saveNote = document.createElement('div');
            saveNote.className = 'save-note';
            saveNote.innerHTML = '💾 Trip saved! <a href="#" onclick="VP.navigate(\'trips\');return false">View all trips →</a>';
            msgs.appendChild(saveNote);
            msgs.scrollTop = msgs.scrollHeight;
          }
        }
        updateSuggestions();
      } else if (!doneReceived) {
        addMessage('I had trouble processing that. Could you try rephrasing?', 'bot');
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        // User stopped - save partial
        if (state._partialContent) {
          state.messages.push({role: 'assistant', content: state._partialContent});
          saveMessages();
        }
      } else {
        removeMessage(typingId);
        addMessage('Connection error. Please try again.', 'bot');
      }
    } finally {
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

  function getTrips() {
    try {
      return JSON.parse(localStorage.getItem('vp_trips') || '[]');
    } catch(e) { return []; }
  }

  function saveTrips(trips) {
    try { localStorage.setItem('vp_trips', JSON.stringify(trips.slice(0, 20))); }
    catch(e) { /* quota */ }
  }

  function saveTrip(city, content) {
    const trips = getTrips();
    const title = content.split('\n')[0].replace(/[#*]/g,'').trim().slice(0, 60) || (city ? city + ' Trip' : 'China Trip');
    const dayCount = (content.match(/\*\*Day \d+/g) || content.match(/Day \d+:/g) || []).length;
    const trip = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      city: city || '',
      title: title,
      content: content,
      days: dayCount || '?',
      created: new Date().toISOString(),
    };
    trips.unshift(trip);
    saveTrips(trips);
    return trip;
  }

  function deleteTrip(id) {
    const trips = getTrips().filter(t => t.id !== id);
    saveTrips(trips);
    renderTrips();
  }

  function renderTrips() {
    const grid = document.getElementById('trips-grid');
    if (!grid) return;
    const trips = getTrips();

    if (!trips.length) {
      grid.innerHTML = '<div class="trip-empty">No saved trips yet. Chat with VisePanda to plan a trip, then save it! 🌏</div>';
      return;
    }

    grid.innerHTML = trips.map(t => {
      const date = new Date(t.created);
      const dateStr = date.toLocaleDateString('en-US', {month:'short', day:'numeric'});
      const snippet = t.content.replace(/<[^>]+>/g, '').slice(0, 120).replace(/\n/g, ' ');
      const cityEmoji = t.city ? getCityEmoji(t.city) : '🌏';
      return '<div class="trip-card">'
        + '<div class="trip-card-top">'
        + '<span class="trip-city-icon">' + cityEmoji + '</span>'
        + '<div class="trip-card-info">'
        + '<div class="trip-card-title">' + escHtml(t.title) + '</div>'
        + '<div class="trip-card-meta">' + (t.city ? escHtml(t.city) + ' · ' : '') + t.days + ' days · ' + dateStr + '</div>'
        + '</div></div>'
        + '<div class="trip-card-desc">' + escHtml(snippet) + '…</div>'
        + '<div class="trip-card-actions">'
        + '<button class="trip-action-btn load" onclick="VP.loadTrip(\'' + t.id + '\')">📂 Load</button>'
        + '<button class="trip-action-btn share" onclick="VP.shareTrip(\'' + t.id + '\')">📋 Copy</button>'
        + '<button class="trip-action-btn delete" onclick="VP.deleteTrip(\'' + t.id + '\')">🗑️</button>'
        + '</div></div>';
    }).join('');
  }

  function loadTrip(id) {
    const trips = getTrips();
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
        el.innerHTML = '<div class="msg-avatar">' + (msg.role === 'assistant' ? '🐼' : '👤') + '</div>'
          + '<div class="msg-body">'
          + '<div class="msg-sender">' + (msg.role === 'assistant' ? 'VisePanda' : 'You') + '</div>'
          + '<div class="msg-text">' + (msg.role === 'user' ? escHtml(msg.content).replace(/\n/g,'<br>') : renderMD(msg.content)) + '</div>'
          + '</div>';
        container.appendChild(el);
      });
      container.scrollTop = container.scrollHeight;
    }
  }

  function shareTrip(id) {
    const trips = getTrips();
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
      // Show toast
      const toast = document.getElementById('toast') || (function(){
        const el = document.createElement('div');
        el.id = 'toast';
        el.className = 'toast';
        document.body.appendChild(el);
        return el;
      })();
      toast.textContent = '✅ Trip copied to clipboard!';
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2000);
    }).catch(() => {
      alert('Trip copied!\n\n' + text.slice(0, 200) + '...');
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
    // Ctrl+Shift+C to clear chat
    if (e.key === 'C' && e.ctrlKey && e.shiftKey) {
      e.preventDefault();
      clearChatHistory();
    }
  });

  // ── Init ──
  function init() {
    // Theme toggle icon
    const themeBtn = document.querySelector('.theme-toggle');
    if (themeBtn) themeBtn.textContent = state.theme === 'dark' ? '🌙' : '☀️';

    // Hash-based nav
    const hash = window.location.hash.slice(1);
    if (hash && ['home','chat','trips','cities','tools'].includes(hash)) {
      navigate(hash);
    }

    // Restore chat history
    const hasHistory = loadMessages();
    if (hasHistory) restoreChatMessages();

    // Update suggestions based on conversation context
    updateSuggestions();

    // Chat input events
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendMessage();
        }
      });
    }

    // Render chat suggestions
    renderSuggestions();
  }

  // ── Expose public API ──
  return {
    navigate,
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
    init,
  };
})();

// ── Auto-init ──
document.addEventListener('DOMContentLoaded', () => VP.init());
