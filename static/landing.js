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
    // Local auth: create a persistent user ID without Supabase
    let uid = localStorage.getItem('vp_user_id');
    if (!uid) {
        uid = 'user_' + crypto.randomUUID().slice(0, 12);
        localStorage.setItem('vp_user_id', uid);
    }
    // Generate a test-bypass token
    const token = 'test:' + uid;
    localStorage.setItem('vp_token', token);
    return uid;
}

function getSignInStatus() {
    const uid = localStorage.getItem('vp_user_id');
    const token = localStorage.getItem('vp_token');
    return { signedIn: !!(uid && token), uid: uid, token: token };
}

async function signIn() {
    // Try Supabase OAuth first (for users who configured it)
    try {
        if (!sb) {
            if (window.__SUPABASE_CONFIG__?.supabase_url && window.__SUPABASE_CONFIG__?.supabase_anon_key) {
                const { createClient } = await import('https://esm.sh/@supabase/supabase-js@2');
                sb = createClient(
                    window.__SUPABASE_CONFIG__.supabase_url,
                    window.__SUPABASE_CONFIG__.supabase_anon_key
                );
                await sb.auth.signInWithOAuth({
                    provider: 'google',
                    options: { redirectTo: location.origin + '/auth/callback' }
                });
                return;
            }
        } else {
            await sb.auth.signInWithOAuth({
                provider: 'google',
                options: { redirectTo: location.origin + '/auth/callback' }
            });
            return;
        }
    } catch(e) {}
    
    // Fallback: local auth
    initDirectAuth();
    location.href = '/chat';
}

function signOut() {
    localStorage.removeItem('vp_token');
    localStorage.removeItem('vp_user_id');
    location.reload();
}

// Update UI based on sign-in status on page load
function updateAuthUI() {
    const { signedIn, uid } = getSignInStatus();
    const authArea = document.getElementById('authArea');
    if (authArea && signedIn) {
        authArea.innerHTML = '<span style="font-size:12px;color:var(--muted);margin-right:8px">' + uid.slice(0, 8) + '</span><a href="#" onclick="event.preventDefault();signOut()" class="btn" style="border:1px solid var(--line);padding:5px 10px;border-radius:999px;font-size:11px;cursor:pointer;text-decoration:none">Sign out</a>';
    }
}

// Only try to init Supabase if configured
try {
    if (window.__SUPABASE_CONFIG__?.supabase_url) {
        initSupabase();
    }
} catch(e) {}

// Apply auth UI on load
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

        container.innerHTML = '<div class="recent-title">Your recent trips</div>' +
            trips.slice(0, 6).map(t => {
                const label = t.cities.length ? t.cities.join(' → ') : t.title;
                const date = new Date(t.updated_at).toLocaleDateString();
                return '<a href="/chat?trip=' + t.id + '" class="recent-trip">' +
                    '<span class="recent-trip-label">' + label + '</span>' +
                    '<span class="recent-trip-meta">' + t.msg_count + ' msgs · ' + date + '</span>' +
                    '</a>';
            }).join('');
        container.style.display = 'block';
    } catch(e) {
        container.style.display = 'none';
    }
}

loadRecentTrips();
