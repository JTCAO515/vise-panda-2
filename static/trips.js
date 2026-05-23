// VisePanda Trip List
const T = document.getElementById('tripsList');
const E = document.getElementById('emptyMsg');

// Helper to safely call t() or fall back to English
function _t(key) {
    return (typeof t === 'function') ? t(key) : {
        failedLoad: 'Failed to load trips.',
        shareBtn: '🔗 Share',
        renameBtn: '✏️ Rename',
        deleteBtn: '🗑 Delete',
        messages: 'messages',
        sharePrompt: 'Share link:',
        shareFailed: 'Failed to share',
        renamePrompt: 'Rename trip:',
        deleteConfirm: 'Delete this trip and all messages?'
    }[key] || key;
}

(async () => {
    const guest = localStorage.getItem('vp_trip') || '';
    const r = await fetch('/api/trips' + (guest ? '?guest_id=' + guest : ''));
    if (!r.ok) {
        T.innerHTML = '<div class=empty>' + _t('failedLoad') + '</div>';
        return;
    }
    const trips = await r.json();
    if (!trips.length) {
        T.style.display = 'none';
        E.style.display = 'block';
        return;
    }
    T.innerHTML = trips.map(tr =>
        '<div class=trip-item>' +
        '<a href=/chat?trip=' + tr.id + ' style=text-decoration:none;color:inherit>' +
        '<h3>' + tr.cities.join(' → ') + '</h3>' +
        '<div class=meta>' + tr.msg_count + ' ' + _t('messages') + ' · ' +
        new Date(tr.updated_at).toLocaleDateString() + '</div></a>' +
        '<div style=margin-top:10px;display:flex;gap:8px>' +
        '<button onclick="event.stopPropagation();shareTrip(\'' + tr.id + '\')" ' +
        'class=btn style=font-size:11px;padding:4px 10px>' + _t('shareBtn') + '</button>' +
        '<button onclick="event.stopPropagation();renameTrip(\'' + tr.id + '\',\'' +
        (tr.title || '').replace(/'/g, '\\x27') + '\')" ' +
        'class=btn style=font-size:11px;padding:4px 10px>' + _t('renameBtn') + '</button>' +
        '<button onclick="event.stopPropagation();deleteTrip(\'' + tr.id + '\')" ' +
        'class=btn style=font-size:11px;padding:4px 10px;color:#fca5a5>' + _t('deleteBtn') + '</button>' +
        '</div></div>'
    ).join('');
})();

async function shareTrip(id) {
    const r = await fetch('/api/trips/' + id + '/share', { method: 'POST' });
    if (r.ok) {
        const d = await r.json();
        prompt(_t('sharePrompt'), location.origin + d.url);
    } else {
        alert(_t('shareFailed'));
    }
}

async function renameTrip(id, oldTitle) {
    const t = prompt(_t('renamePrompt'), oldTitle);
    if (!t) return;
    const r = await fetch('/api/trips/' + id, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: t })
    });
    if (r.ok) location.reload();
}

async function deleteTrip(id) {
    if (!confirm(_t('deleteConfirm'))) return;
    const r = await fetch('/api/trips/' + id, { method: 'DELETE' });
    if (r.ok) location.reload();
}
