// VisePanda Landing Page
let sb = null;

function goChat(q) {
    const id = 't_' + crypto.randomUUID();
    const u = new URL('/chat', location);
    u.searchParams.set('trip', id);
    if (q) u.searchParams.set('q', q);
    location.href = u.toString();
}

function initDirectAuth() {
    let uid = localStorage.getItem('vp_user_id');
    if (!uid) {
        uid = 'user_' + crypto.randomUUID().slice(0, 12);
        localStorage.setItem('vp_user_id', uid);
    }
    const token = 'test:' + uid;
    localStorage.setItem('vp_token', token);
    return uid;
}

function getSignInStatus() {
    const uid = localStorage.getItem('vp_user_id');
    const token = localStorage.getItem('vp_token');
    return { signedIn: !!(uid && token), uid: uid, token: token };
}

// ── Login Modal ──
let modalTab = 'google';
let phoneCodeTimer = 0;

function loginModalHTML() {
    const tabs = ['google', 'email', 'phone'];
    const labels = [t('googleLogin'), t('emailLogin'), t('phoneLogin')];
    const contentIds = ['loginGoogleContent', 'loginEmailContent', 'loginPhoneContent'];
    const tabBtns = tabs.map((t, i) =>
        `<button class="${modalTab === t ? 'active' : ''}" onclick="switchLoginTab('${t}')" style="flex:1;padding:8px 0;border:none;background:none;color:${modalTab === t ? 'rgba(255,255,255,.9)' : 'rgba(255,255,255,.6)'};font-size:13px;cursor:pointer;border-bottom:2px solid ${modalTab === t ? '#7dd3fc' : 'transparent'}">${labels[i]}</button>`
    ).join('');

    return `<div id="loginModalOverlay" style="position:fixed;inset:0;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;z-index:9999;animation:fadeIn .15s ease" onclick="if(event.target===this)closeLoginModal()">
<div style="background:#1a1f2e;border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:28px 24px 20px;max-width:380px;width:90vw;animation:scaleIn .15s ease" onclick="event.stopPropagation()">
<div style="display:flex;gap:0;margin-bottom:24px;border-bottom:1px solid rgba(255,255,255,.08)">${tabBtns}</div>

<div id="loginGoogleContent" style="${modalTab === 'google' ? '' : 'display:none'}">
  <button onclick="doGoogleLogin()" style="width:100%;padding:12px;border-radius:999px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.04);color:#fff;font-size:15px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:12px">
    <svg width="18" height="18" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.6 20.1H42V20H24v8h11.3C33 32.3 28.9 35 24 35c-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.8 1.1 7.9 3l5.7-5.7C33.9 5.1 29.3 3 24 3 12.4 3 3 12.4 3 24s9.4 21 21 21c10.4 0 19.3-7.5 20.9-17.4.3-1.6.5-3.2.5-4.9 0-1.6-.2-3.1-.5-4.6z"/><path fill="#FF3D00" d="m6.3 14.7 6.6 4.9C14.8 16.2 19 14 24 14c3 0 5.8 1.1 7.9 3l5.7-5.7C33.9 5.1 29.3 3 24 3 16.6 3 10 7.1 6.3 14.7z"/><path fill="#4CAF50" d="M24 45c5.5 0 10.4-2 14.1-5.3l-6.5-5.5C29.3 36.3 26.8 37 24 37c-5.1 0-9.4-3.4-11-8.1l-6.4 5c3.6 7.1 10.8 12.1 19.4 12.1z"/><path fill="#1976D2" d="M43.6 20.1H42V20H24v8h11.3c-.7 2-2 3.7-3.7 4.9l6.5 5.5c-.1.1 5.9-4.5 5.9-13.8 0-1.6-.2-3.1-.5-4.6z"/></svg>
    ${t('continueWithGoogle')}
  </button>
  <div style="text-align:center;font-size:12px;color:rgba(255,255,255,.4)">${t('googleNote')}</div>
</div>

<div id="loginEmailContent" style="${modalTab === 'email' ? '' : 'display:none'}">
  <div id="emailError" style="display:none;background:rgba(239,68,68,.15);color:#fca5a5;padding:8px 12px;border-radius:8px;font-size:13px;margin-bottom:10px"></div>
  <input id="emailInput" type="email" placeholder="${t('emailPlaceholder')}" style="width:100%;padding:12px 14px;border-radius:10px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.04);color:rgba(255,255,255,.9);font-size:14px;outline:none;box-sizing:border-box;margin-bottom:10px">
  <input id="passwordInput" type="password" placeholder="${t('passwordPlaceholder')}" style="width:100%;padding:12px 14px;border-radius:10px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.04);color:rgba(255,255,255,.9);font-size:14px;outline:none;box-sizing:border-box;margin-bottom:6px" onkeydown="if(event.key==='Enter')doEmailAuth()">
  <div style="font-size:11px;color:rgba(255,255,255,.3);margin-bottom:14px">${t('passwordHint')}</div>
  <button id="emailAuthBtn" onclick="doEmailAuth()" style="width:100%;padding:12px;border-radius:999px;border:none;background:rgba(125,211,252,.2);color:#7dd3fc;font-size:15px;cursor:pointer;margin-bottom:10px">${t('signInEmail')}</button>
  <div style="text-align:center;font-size:13px;color:rgba(255,255,255,.5)">${t('noAccount')} <a href="#" onclick="event.preventDefault();toggleEmailMode()" id="emailToggleLink" style="color:#7dd3fc;text-decoration:none">${t('signUpInstead')}</a></div>
</div>

<div id="loginPhoneContent" style="${modalTab === 'phone' ? '' : 'display:none'}">
  <div id="phoneError" style="display:none;background:rgba(239,68,68,.15);color:#fca5a5;padding:8px 12px;border-radius:8px;font-size:13px;margin-bottom:10px"></div>
  <div style="display:flex;gap:8px;margin-bottom:10px">
    <select id="phoneCountryCode" style="width:90px;padding:12px 6px;border-radius:10px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.04);color:rgba(255,255,255,.9);font-size:14px;outline:none;flex-shrink:0">
      <option value="+86">🇨🇳 +86</option>
      <option value="+1">🇺🇸 +1</option>
      <option value="+852">🇭🇰 +852</option>
      <option value="+853">🇲🇴 +853</option>
      <option value="+886">🇹🇼 +886</option>
      <option value="+81">🇯🇵 +81</option>
      <option value="+82">🇰🇷 +82</option>
      <option value="+65">🇸🇬 +65</option>
    </select>
    <input id="phoneInput" type="tel" placeholder="${t('phonePlaceholder')}" style="flex:1;padding:12px 14px;border-radius:10px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.04);color:rgba(255,255,255,.9);font-size:14px;outline:none;box-sizing:border-box">
  </div>
  <button id="phoneSendCodeBtn" onclick="doPhoneSendCode()" style="width:100%;padding:10px;border-radius:999px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.04);color:rgba(255,255,255,.7);font-size:14px;cursor:pointer;margin-bottom:10px">${t('sendCode')}</button>
  <input id="phoneCodeInput" type="text" inputmode="numeric" placeholder="${t('codePlaceholder')}" style="width:100%;padding:12px 14px;border-radius:10px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.04);color:rgba(255,255,255,.9);font-size:14px;outline:none;box-sizing:border-box;margin-bottom:10px" onkeydown="if(event.key==='Enter')doPhoneLogin()">
  <button id="phoneLoginBtn" onclick="doPhoneLogin()" style="width:100%;padding:12px;border-radius:999px;border:none;background:rgba(125,211,252,.2);color:#7dd3fc;font-size:15px;cursor:pointer">${t('signInPhone')}</button>
</div>

<button onclick="closeLoginModal()" style="display:block;margin:16px auto 0;border:none;background:none;color:rgba(255,255,255,.3);font-size:13px;cursor:pointer">${t('keepAsGuest')}</button>
</div></div>`;
}

let emailSignUpMode = false;

function toggleEmailMode() {
    emailSignUpMode = !emailSignUpMode;
    const btn = document.getElementById('emailAuthBtn');
    const link = document.getElementById('emailToggleLink');
    const hint = document.getElementById('emailError');
    btn.textContent = emailSignUpMode ? t('signUpEmail') : t('signInEmail');
    link.textContent = emailSignUpMode ? t('signInInstead') : t('signUpInstead');
    if (hint) hint.style.display = 'none';
}

function switchLoginTab(tab) {
    modalTab = tab;
    const overlay = document.getElementById('loginModalOverlay');
    if (overlay) overlay.outerHTML = loginModalHTML();
}

function showError(id, msg) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = msg;
    el.style.display = 'block';
}

// ── Email auth ──
async function doEmailAuth() {
    const email = document.getElementById('emailInput').value.trim();
    const password = document.getElementById('passwordInput').value;
    if (!email || !password) { showError('emailError', t('fillFields')); return; }

    const btn = document.getElementById('emailAuthBtn');
    btn.disabled = true;
    btn.textContent = t('loadingAuth');

    const endpoint = emailSignUpMode ? '/api/auth/email-signup' : '/api/auth/email-login';
    try {
        const r = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await r.json();
        if (!r.ok) {
            showError('emailError', data.detail || t('authError'));
            btn.disabled = false;
            btn.textContent = emailSignUpMode ? t('signUpEmail') : t('signInEmail');
            return;
        }
        localStorage.setItem('vp_token', data.token);
        localStorage.setItem('vp_user_id', data.user_id);
        if (email) localStorage.setItem('vp_email', email);
        closeLoginModal();
        location.href = '/chat';
    } catch(e) {
        showError('emailError', t('networkError'));
        btn.disabled = false;
        btn.textContent = emailSignUpMode ? t('signUpEmail') : t('signInEmail');
    }
}

// ── Phone auth ──
let phoneCountdown = 0;

async function doPhoneSendCode() {
    const cc = document.getElementById('phoneCountryCode').value;
    const phone = document.getElementById('phoneInput').value.trim();
    if (!phone) { showError('phoneError', t('fillPhone')); return; }
    const fullPhone = cc + phone;

    const btn = document.getElementById('phoneSendCodeBtn');
    btn.disabled = true;

    try {
        const r = await fetch('/api/auth/send-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: fullPhone })
        });
        const data = await r.json();
        if (!r.ok) {
            showError('phoneError', data.detail || t('authError'));
            btn.disabled = false;
            return;
        }
        showError('phoneError', t('codeSent'));
        // Start countdown
        phoneCountdown = 60;
        btn.textContent = `60s`;
        const iv = setInterval(() => {
            phoneCountdown--;
            if (phoneCountdown <= 0) {
                clearInterval(iv);
                btn.disabled = false;
                btn.textContent = t('sendCode');
            } else {
                btn.textContent = phoneCountdown + 's';
            }
        }, 1000);
        // Focus code input
        document.getElementById('phoneCodeInput').focus();
    } catch(e) {
        showError('phoneError', t('networkError'));
        btn.disabled = false;
    }
}

async function doPhoneLogin() {
    const cc = document.getElementById('phoneCountryCode').value;
    const phone = document.getElementById('phoneInput').value.trim();
    const code = document.getElementById('phoneCodeInput').value.trim();
    if (!phone || !code) { showError('phoneError', t('fillFields')); return; }
    const fullPhone = cc + phone;

    const btn = document.getElementById('phoneLoginBtn');
    btn.disabled = true;
    btn.textContent = t('loadingAuth');

    try {
        const r = await fetch('/api/auth/phone-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: fullPhone, code })
        });
        const data = await r.json();
        if (!r.ok) {
            showError('phoneError', data.detail || t('authError'));
            btn.disabled = false;
            btn.textContent = t('signInPhone');
            return;
        }
        localStorage.setItem('vp_token', data.token);
        localStorage.setItem('vp_user_id', data.user_id);
        localStorage.setItem('vp_phone', fullPhone);
        closeLoginModal();
        location.href = '/chat';
    } catch(e) {
        showError('phoneError', t('networkError'));
        btn.disabled = false;
        btn.textContent = t('signInPhone');
    }
}

// ── Google OAuth ──
function doGoogleLogin() {
    closeLoginModal();
    try {
        if (window.__SUPABASE_CONFIG__?.supabase_url && window.__SUPABASE_CONFIG__?.supabase_anon_key) {
            if (!sb) {
                import('https://esm.sh/@supabase/supabase-js@2').then(({ createClient }) => {
                    sb = createClient(
                        window.__SUPABASE_CONFIG__.supabase_url,
                        window.__SUPABASE_CONFIG__.supabase_anon_key
                    );
                    sb.auth.signInWithOAuth({
                        provider: 'google',
                        options: { redirectTo: location.origin + '/auth/callback' }
                    });
                });
            } else {
                sb.auth.signInWithOAuth({
                    provider: 'google',
                    options: { redirectTo: location.origin + '/auth/callback' }
                });
            }
            return;
        }
    } catch(e) {}
    initDirectAuth();
    location.href = '/chat';
}

function openLoginModal() {
    emailSignUpMode = false;
    modalTab = 'google';
    document.body.insertAdjacentHTML('beforeend', loginModalHTML());
}

function closeLoginModal() {
    const overlay = document.getElementById('loginModalOverlay');
    if (overlay) overlay.remove();
}

function signIn() {
    openLoginModal();
}

function signOut() {
    localStorage.removeItem('vp_token');
    localStorage.removeItem('vp_user_id');
    localStorage.removeItem('vp_email');
    localStorage.removeItem('vp_phone');
    location.reload();
}

// Update UI based on sign-in status on page load
function updateAuthUI() {
    const { signedIn, uid } = getSignInStatus();
    const authArea = document.getElementById('authArea');
    if (authArea && signedIn) {
        const email = localStorage.getItem('vp_email');
        const phone = localStorage.getItem('vp_phone');
        const label = email || phone || uid.slice(0, 8);
        authArea.innerHTML = '<span style="font-size:12px;color:var(--muted);margin-right:8px">' + label + '</span><a href="#" onclick="event.preventDefault();signOut()" class="btn" style="border:1px solid var(--line);padding:5px 10px;border-radius:999px;font-size:11px;cursor:pointer;text-decoration:none">' + t('signOut') + '</a>';
    }
}

// Try to init Supabase (for Google OAuth fallback detection)
try {
    if (window.__SUPABASE_CONFIG__?.supabase_url) {
        // Import supabase lazily only on demand
    }
} catch(e) {}

updateAuthUI();

// Recent trips
async function loadRecentTrips() {
    const container = document.getElementById('recentTrips');
    if (!container) return;

    let url = '/api/trips';
    let headers = {'Content-Type': 'application/json'};

    const token = localStorage.getItem('vp_token');
    const guestId = localStorage.getItem('vp_trip');

    if (token) {
        headers['Authorization'] = 'Bearer ' + token;
    } else if (guestId) {
        url = '/api/trips?guest_id=' + encodeURIComponent(guestId);
    } else {
        container.style.display = 'none';
        return;
    }

    try {
        const r = await fetch(url, { headers });
        if (!r.ok) { container.style.display = 'none'; return; }
        const trips = await r.json();
        if (!trips.length) { container.style.display = 'none'; return; }

        container.innerHTML = '<div class="recent-title">' + t('recentTrips') + '</div>' +
            trips.slice(0, 6).map(t => {
                const label = t.cities.length ? t.cities.join(' → ') : t.title;
                const date = new Date(t.updated_at).toLocaleDateString();
                return '<a href="/chat?trip=' + t.id + '" class="recent-trip">' +
                    '<span class="recent-trip-label">' + label + '</span>' +
                    '<span class="recent-trip-meta">' + t.msg_count + ' ' + t('messages') + ' · ' + date + '</span>' +
                    '</a>';
            }).join('');
        container.style.display = 'block';
    } catch(e) {
        container.style.display = 'none';
    }
}

loadRecentTrips();

// ── Category filter for landing page cards ──
function filterCards(cat) {
  document.querySelectorAll('.cat-tag').forEach(function(t) {
    t.classList.toggle('active', t.dataset.cat === cat);
  });
  document.querySelectorAll('#cardGrid .card').forEach(function(c) {
    c.style.display = cat === 'all' || c.dataset.cat === cat ? 'block' : 'none';
  });
}

// ── Button ripple effect ──
document.addEventListener('mousemove', function(e) {
  var btn = e.target.closest('.btn, .btn-accent, .btn-red');
  if (btn) {
    var r = btn.getBoundingClientRect();
    btn.style.setProperty('--mx', ((e.clientX - r.left) / r.width * 100) + '%');
    btn.style.setProperty('--my', ((e.clientY - r.top) / r.height * 100) + '%');
  }
});

// ── Theme toggle (dark → light → hongjin → mogreen → qinghua) ──
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
// Restore saved theme on load
(function() {
  var saved = localStorage.getItem('vp_theme');
  if (saved && saved !== 'dark') {
    if (saved === 'light') document.body.classList.add('light');
    document.documentElement.setAttribute('data-theme', saved);
  }
})();
