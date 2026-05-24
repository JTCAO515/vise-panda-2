// VisePanda Chat Page
let sb = null, tripId = null;

async function i() {
    sb = supabase.createClient(
        window.__SUPABASE_CONFIG__.supabase_url,
        window.__SUPABASE_CONFIG__.supabase_anon_key
    );
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
    if (text.includes('**Day ')) h = '<div class=trip-card>' + h + '</div>';
    return h;
};

function msg(r, c) {
    const d = document.createElement('div');
    d.className = 'msg ' + r;
    const tm = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    d.innerHTML = '<div class=bubble>' + M(c) + '</div><div class=time>' + tm + '</div>';
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
        '<div class=skeleton style=width:60%></div>' +
        '<div class=skeleton style=width:40%;margin-top:8px></div>' +
        '<div class=skeleton style=width:50%;margin-top:8px></div>'
    );

    var getT = function(k) { return (typeof t === 'function') ? t(k) : {
        connFailed: 'Connection failed. Check your network.',
        retry: 'Retry', sendBtn: 'Send', error: 'Error', loading: 'Loading services… please wait or ',
        refresh: 'refresh'
    }[k]; };

    let f = '';
    try {
        // Auth: try local token first, then Supabase
        const token = localStorage.getItem('vp_token');
        const h = { 'Content-Type': 'application/json' };
        if (token) {
            h['Authorization'] = 'Bearer ' + token;
        } else {
            const s = await sb?.auth.getSession();
            const tok = s?.data?.session?.access_token;
            if (tok) h['Authorization'] = 'Bearer ' + tok;
        }

        let r;
        try {
            r = await fetch('/api/chat', {
                method: 'POST', headers: h,
                body: JSON.stringify({ trip_id: tripId, text: text, guest_id: localStorage.getItem('vp_trip') || '' })
            });
        } catch (fe) {
            b.innerHTML = '<span style=color:#fca5a5>' + getT('connFailed') + '</span> ' +
                '<a href=# onclick="W.send(\'' + text.replace(/'/g, '\\x27') + '\');return false" ' +
                'style=color:var(--accent);text-decoration:underline>' + getT('retry') + '</a>';
            sbb.disabled = false;
            sbb.textContent = getT('sendBtn');
            return;
        }

        const rd = r.body.getReader();
        const dc = new TextDecoder();
        let buf = '';

        while (1) {
            const { done, value } = await rd.read();
            if (done) break;
            buf += dc.decode(value, { stream: true });
            for (const l of buf.split('\n')) {
                if (!l.startsWith('data:')) continue;
                const d = l.slice(5).trim();
                if (d === '[DONE]') continue;
                try {
                    const j = JSON.parse(d);
                    if (j.token) f += j.token;
                    b.innerHTML = M(f);
                } catch (_) {}
            }
            buf = buf.includes('\n') ? buf.split('\n').pop() : buf;
            smartScroll();
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

// Init
i();
setTimeout(function() {
    if (!sb) {
        var lt = (typeof t === 'function') ? t('loading') : 'Loading services… please wait or ';
        var rf = (typeof t === 'function') ? t('refresh') : 'refresh';
        Q('#thread').innerHTML = '<div style=padding:20px;color:var(--muted)>' + lt + '<a href=# onclick=location.reload() style=color:var(--accent)>' + rf + '</a></div>';
    }
}, 5000);
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

// Expose send globally for onclick handlers
W.send = send;
