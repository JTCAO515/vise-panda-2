// VisePanda Auth Callback
(async () => {
    // Check if we have a local token already (direct auth)
    if (localStorage.getItem('vp_token')) {
        location.href = '/chat';
        return;
    }
    // Try Supabase OAuth flow
    try {
        if (typeof supabase !== 'undefined' && window.__SUPABASE_CONFIG__?.supabase_url) {
            const sb = supabase.createClient(
                window.__SUPABASE_CONFIG__.supabase_url,
                window.__SUPABASE_CONFIG__.supabase_anon_key
            );
            const { data, error } = await sb.auth.getSession();
            if (data?.session) {
                localStorage.setItem('visepanda_session', JSON.stringify(data.session));
                location.href = '/chat';
                return;
            }
        }
    } catch(e) {}
    // Fallback: redirect to chat as guest
    setTimeout(() => location.href = '/chat', 1000);
})();
