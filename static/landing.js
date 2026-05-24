// VisePanda Landing Page
let sb = null;

function goChat(q) {
    const id = 't_' + crypto.randomUUID();
    const u = new URL('/chat', location);
    u.searchParams.set('trip', id);
    if (q) u.searchParams.set('q', q);
    location.href = u.toString();
}

async function initSupabase() {
    sb = supabase.createClient(
        window.__SUPABASE_CONFIG__.supabase_url,
        window.__SUPABASE_CONFIG__.supabase_anon_key
    );
}

async function signIn() {
    if (!sb) await initSupabase();
    sb.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo: location.origin + '/auth/callback' }
    });
}

initSupabase();

// Recent trips
async function loadRecentTrips() {
    const container = document.getElementById('recentTrips');
    if (!container) return;

    let url = '/api/trips';
    let headers = {'Content-Type': 'application/json'};

    const sessionData = localStorage.getItem('visepanda_session');
    const guestId = localStorage.getItem('vp_trip');

    if (sessionData) {
        try {
            const sess = JSON.parse(sessionData);
            if (sess.access_token) {
                headers['Authorization'] = 'Bearer ' + sess.access_token;
            }
        } catch(e) {
            container.style.display = 'none';
            return;
        }
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
