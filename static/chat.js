// VisePanda Chat Page
let sb = null, tripId = null;

async function i() {
    try {
        const { createClient } = await import('https://esm.sh/@supabase/supabase-js@2');
        sb = createClient(
            window.__SUPABASE_CONFIG__.supabase_url,
            window.__SUPABASE_CONFIG__.supabase_anon_key
        );
    } catch(e) {
        // Supabase unavailable (China network) — continue with local auth
        sb = null;
    }
}

const W = window;
const Q = s => document.querySelector(s);
const H = s => s.replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;',
    '"': '&quot;', "'": '&#39;'
}[c]));

const M = text => {
    let h = text
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
        .replace(/\*(.+?)\*/g, '<i>$1</i>')
        .replace(/¥(\d+)([–-]\d+)?(\s*\+\s*)?/g, function(m, n1, n2, plus) {
            const num = parseInt(n1);
            let cls = 'price-budget';
            if (num >= 300 && num < 1000) cls = 'price-mid';
            else if (num >= 1000) cls = 'price-luxury';
            return '<span class=' + cls + '>¥' + n1 + (n2 || '') + (plus || '') + '</span>';
        })
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
    if (text.includes('**Day ')) h = '<div class=trip-highlight>' + h + '</div>';
    return h;
};

function msg(r, c) {
    const d = document.createElement('div');
    d.className = 'msg ' + r;
    const tm = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const avatar = r === 'bot'
        ? '<div class=avatar avatar-bot></div>'
        : '<div class=avatar avatar-user><span>Y</span></div>';
    d.innerHTML = avatar + '<div class=msg-body><div class=bubble>' + M(c) + '</div><div class=time>' + tm + '</div></div>';
    Q('#thread').appendChild(d);
    smartScroll();
    return d;
}

async function loadHistory() {
    if (!tripId) return;
    try {
        const r = await fetch('/api/trips/' + tripId + '/messages');
        if (!r.ok) return;
        const msgs = await r.json();
        if (msgs.length > 0) {
            const w = Q('#welcomeMsg');
            if (w) w.remove();
        }
        for (const m of msgs) {
            msg(m.role === 'user' ? 'user' : 'bot', m.content);
        }
    } catch (e) {}
}

function smartScroll() {
    const el = Q('#thread');
    if (el.scrollHeight - el.scrollTop - el.clientHeight < 200)
        el.scrollTop = el.scrollHeight;
}

function clearChat() {
    Q('#thread').innerHTML = '';
    localStorage.removeItem('vp_trip');
}

async function send(text) {
    const sbb = Q('#sendBtn');
    sbb.disabled = true;
    sbb.textContent = '...';
    msg('user', text);
    const w = Q('#welcomeMsg');
    if (w) w.remove();
    tripId = tripId || 't_' + crypto.randomUUID();
    localStorage.setItem('vp_trip', tripId);

    const b = msg('bot',
        '<div class="skel-block"><div class="skel-line skel-w-70"></div><div class="skel-line skel-w-50"></div><div class="skel-line skel-w-60"></div></div>' +
        '<div class="skel-block" style="margin-top:12px"><div class="skel-line skel-w-40"></div><div class="skel-line skel-w-80"></div><div class="skel-line skel-w-30"></div></div>'
    );
    const bubble = b.querySelector('.bubble') || b;

    var getT = function(k) { return (typeof t === 'function') ? t(k) : {
        connFailed: 'Connection failed. Check your network.',
        retry: 'Retry', sendBtn: 'Send', error: 'Error', loading: 'Loading services… please wait or ',
        refresh: 'refresh'
    }[k]; };

    let f = '';
    try {
        const token = localStorage.getItem('vp_token');
        const h = { 'Content-Type': 'application/json' };
        if (token) {
            h['Authorization'] = 'Bearer ' + token;
        } else if (sb) {
            const s = await sb.auth.getSession();
            const tok = s?.data?.session?.access_token;
            if (tok) h['Authorization'] = 'Bearer ' + tok;
        }
        // No token? Send without auth — backend handles guest mode

        let r;
        try {
            r = await fetch('/api/chat', {
                method: 'POST', headers: h,
                body: JSON.stringify({
                    trip_id: tripId,
                    text: text,
                    guest_id: localStorage.getItem('vp_trip') || '',
                    lang: localStorage.getItem('vp_lang') || 'en'
                })
            });
        } catch (fe) {
            // Auto-reconnect with exponential backoff
            for (let retries = 0; retries < 3; retries++) {
                await new Promise(r => setTimeout(r, 1000 * Math.pow(2, retries)));
                try {
                    r = await fetch('/api/chat', {
                        method: 'POST', headers: h,
                        body: JSON.stringify({
                            trip_id: tripId,
                            text: text,
                            guest_id: localStorage.getItem('vp_trip') || '',
                            lang: localStorage.getItem('vp_lang') || 'en'
                        })
                    });
                    if (r.ok) break;
                } catch (_) {}
            }
            if (!r || !r.ok) {
                b.innerHTML = '<span style=color:#fca5a5>' + getT('connFailed') + '</span> ' +
                    '<a href=# onclick="W.send(\'' + text.replace(/'/g, '\\x27') + '\');return false" ' +
                    'style=color:var(--accent);text-decoration:underline>' + getT('retry') + '</a>';
                sbb.disabled = false;
                sbb.textContent = getT('sendBtn');
                return;
            }
        }

        if (!r || !r.ok) {
            let detail = '';
            try { detail = (await r.text()).slice(0, 500); } catch (_) {}
            const rid = r && r.headers ? (r.headers.get('x-request-id') || r.headers.get('X-Request-Id') || '') : '';
            bubble.innerHTML =
                '<span style=color:#fca5a5>Request failed.</span><br>' +
                '<small style=color:rgba(255,255,255,.55)>' +
                (rid ? ('request_id: ' + H(rid) + '<br>') : '') +
                'HTTP ' + (r ? r.status : '0') + (detail ? (': ' + H(detail)) : '') +
                '</small>';
            sbb.disabled = false;
            sbb.textContent = getT('sendBtn');
            return;
        }

        const rd = r.body.getReader();
        const dc = new TextDecoder();
        let buf = '';

        while (1) {
            let done, value;
            try {
                ({ done, value } = await rd.read());
            } catch (re) {
                // Stream interrupted mid-response
                b.innerHTML = b.innerHTML + '<br><small style=color:rgba(255,255,255,.4)>' +
                    '<span style=color:#fca5a5>' + getT('connFailed') + '</span> ' +
                    '<a href=# onclick="W.send(\'' + text.replace(/'/g, '\\x27') + '\');return false" ' +
                    'style=color:var(--accent)">' + getT('retry') + '</a></small>';
                sbb.disabled = false;
                sbb.textContent = getT('sendBtn');
                return;
            }
            if (done) break;
            buf += dc.decode(value, { stream: true });
            for (const l of buf.split('\n')) {
                if (!l.startsWith('data:')) continue;
                const d = l.slice(5).trim();
                if (d === '[DONE]') continue;
                try {
                    const j = JSON.parse(d);
                    if (j.error) {
                        const rid = j.request_id ? ('<br><small style="color:rgba(255,255,255,.45)">request_id: ' + H(j.request_id) + '</small>') : '';
                        bubble.innerHTML = '<span style=color:#fca5a5>' + H(j.error) + '</span>' + rid + ' ' +
                          '<a href=# onclick="W.send(\'' + text.replace(/'/g, '\\x27') + '\');return false" ' +
                          'style=color:var(--accent);text-decoration:underline>' + getT('retry') + '</a>';
                        sbb.disabled = false;
                        sbb.textContent = 'Send';
                        smartScroll();
                        return;
                    }
                    if (j.token) f += j.token;
                    if (j.trip_update) {
                        // Notify user that itinerary was detected and saved
                        const note = document.createElement('div');
                        note.style.cssText = 'font-size:11px;color:rgba(125,211,252,.6);text-align:center;padding:6px 0';
                        note.textContent = '📋 Itinerary saved — ' + (j.cities || []).join(', ') + ' · ' + j.days + ' days';
                        Q('#thread').appendChild(note);
                        smartScroll();
                        
                        // Show map with trip data
                        updateSidebar(j);
                        const mapContainer = Q('#tripMap');
                        if (mapContainer && tripId && !mapContainer._mapLoading) {
                            mapContainer._mapLoading = true;
                            mapContainer.style.display = 'block';
                            (async () => {
                                try {
                                    const resp = await fetch('/api/trips/' + tripId);
                                    const td = await resp.json();
                                    if (td.current_itinerary && td.current_itinerary.cities && td.current_itinerary.cities.length > 0) {
                                        await VP_MAP.loadItinerary('tripMap', td);
                                        mapContainer.style.display = 'block';
                                    }
                                } catch (e) {}
                                mapContainer._mapLoading = false;
                            })();
                        }
                    }
                    // Don't wipe the skeleton if we still have no text.
                    if (f && f.trim()) bubble.innerHTML = M(f);
                } catch (_) {}
            }
            buf = buf.includes('\n') ? buf.split('\n').pop() : buf;
            smartScroll();
        }

        // Stream ended but we got no content — show a helpful message instead of an empty bubble.
        if (!f || !f.trim()) {
            bubble.innerHTML =
                '<span style=color:#fca5a5>No response from the model.</span><br>' +
                '<small style=color:rgba(255,255,255,.55)>' +
                'Please verify <code>LLM_API_KEY</code> and model settings on Vercel, then try again.' +
                '</small>';
        }

        const sm = f.split('---SUGGESTIONS---');
        if (sm[1]) {
            const sgs = sm[1].split('\n')
                .filter(l => l.trim().startsWith('-'))
                .map(l => l.replace(/^-\s*/, ''));
            const qr = Q('#quickReplies');
            qr.innerHTML = sgs.map(s =>
                '<span class=chip onclick="document.getElementById(\'msgInput\').value=\'' +
                s.replace(/'/g, '\\x27') +
                '\';document.getElementById(\'msgForm\').dispatchEvent(new Event(\'submit\'))">' +
                s + '</span>'
            ).join('');
        }
    } catch (e) {
        b.innerHTML = '<span style=color:#fca5a5>' + getT('error') + ': ' + H(e.message) + '</span> ' +
            '<a href=# onclick="W.send(\'' + text.replace(/'/g, '\\x27') + '\');return false" ' +
            'style=color:var(--accent);text-decoration:underline>' + getT('retry') + '</a>';
        sbb.disabled = false;
        sbb.textContent = getT('sendBtn');
    }
    sbb.disabled = false;
    sbb.textContent = getT('sendBtn');
    smartScroll();
}

// Init — on DOM ready
(async function() {
    await i();
    const p = new URL(W.location);
    tripId = p.searchParams.get('trip') || localStorage.getItem('vp_trip');
    if (tripId) loadHistory();
    const q = p.searchParams.get('q');

    Q('#msgForm').onsubmit = e => {
        e.preventDefault();
        const v = Q('#msgInput').value.trim();
        if (!v) return;
        Q('#msgInput').value = '';
        Q('#quickReplies').innerHTML = '';
        send(v);
    };

    if (q) {
        p.searchParams.delete('q');
        history.replaceState(null, '', p.toString());
        send(q);
    }
})();

// Expose send globally for onclick handlers
W.send = send;

// ── Sidebar toggle ──
function toggleSidebar() {
    var sb = document.getElementById('sidebar');
    var btn = document.getElementById('sidebarToggle');
    sb.classList.toggle('visible');
    btn.classList.toggle('visible');
}

// ── Update sidebar trip info ──
function updateSidebar(tripData) {
    var itin = tripData.current_itinerary || {};
    var cities = document.getElementById('tripCities');
    var days = document.getElementById('tripDays');
    if (cities) cities.textContent = (itin.cities || ['—']).join(' → ');
    if (days) days.textContent = (itin.day_count || '—') + ' days';
}

// ── Theme toggle ──
function toggleTheme() {
  var themes = ['dark', 'light', 'hongjin', 'mogreen', 'qinghua'];
  var cur = document.documentElement.getAttribute('data-theme') || 'dark';
  var idx = themes.indexOf(cur);
  var next = themes[(idx + 1) % themes.length];
  if (next === 'light') document.body.classList.add('light');
  else document.body.classList.remove('light');
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('vp_theme', next);
}
(function() {
  var saved = localStorage.getItem('vp_theme');
  if (saved && saved !== 'dark') {
    if (saved === 'light') document.body.classList.add('light');
    document.documentElement.setAttribute('data-theme', saved);
  }
})();
