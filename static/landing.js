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
