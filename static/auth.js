// VisePanda Auth Callback
(async () => {
    const sb = supabase.createClient(
        window.__SUPABASE_CONFIG__.supabase_url,
        window.__SUPABASE_CONFIG__.supabase_anon_key
    );
    const { data, error } = await sb.auth.getSession();
    if (data?.session) {
        localStorage.setItem('visepanda_session', JSON.stringify(data.session));
        location.href = '/chat';
    } else {
        setTimeout(() => location.href = '/', 3000);
    }
})();
