// VisePanda i18n — Simplified Chinese ↔ English
const I18N = {
    en: {
        title: 'VisePanda — AI China Travel Planner 🇨🇳',
        metaDesc: 'Plan your China trip with AI. Get personalized itineraries, local food recommendations, hotel tips. Beijing, Shanghai, Chengdu, Yunnan — tell us where and how long.',
        signIn: 'Sign in',
        heroTitle: 'Plan your China trip 🐼',
        heroSub: 'Ask less, chat more. Just tell me where and how long.',
        inputPlaceholder: 'e.g. Beijing 5 days, food+history, relaxed pace…',
        startBtn: 'Start',
        guestHint: 'Open chat · Sign in with Google · Continue as guest',
        footer: 'Try without login — last 3 trips saved locally. Login to sync across devices.',
        chatTitle: 'Chat · VisePanda — AI China Travel Planner',
        chatMeta: 'Chat with VisePanda AI to plan your China trip. Get day-by-day itineraries, food guides, and practical travel tips.',
        tripsBtn: 'Trips',
        clearBtn: 'Clear',
        homeBtn: 'Home',
        welcomeTitle: '👋 Welcome to VisePanda',
        welcomeSub: 'Your AI travel planner for China. Ask me anything!',
        inputMsgPlaceholder: 'Type a message…',
        sendBtn: 'Send',
        connFailed: 'Connection failed. Check your network.',
        retry: 'Retry',
        error: 'Error',
        loading: 'Loading services… please wait or ',
        refresh: 'refresh',
        tripsTitle: 'My Trips · VisePanda',
        tripsHeading: 'My Trips',
        noTrips: 'No trips yet.',
        startPlanning: 'Start Planning',
        failedLoad: 'Failed to load trips.',
        shareBtn: '🔗 Share',
        renameBtn: '✏️ Rename',
        deleteBtn: '🗑 Delete',
        sharePrompt: 'Share link:',
        shareFailed: 'Failed to share',
        renamePrompt: 'Rename trip:',
        deleteConfirm: 'Delete this trip and all messages?',
        messages: 'messages',
        homeLink: 'Home',
        signingIn: 'Signing in…',
        redirecting: 'Redirecting…',
        shareTitleSuffix: '· VisePanda',
        shareAI: 'AI-planned trip',
        planYourOwn: 'Plan your own trip',
        notFoundTitle: '404 — VisePanda',
        notFound: 'Page not found',
        backHome: 'Back home',
        langLabel: '中',
    },
    zh: {
        title: 'VisePanda — AI 中国旅行规划师 🇨🇳',
        metaDesc: '用 AI 规划你的中国之旅。获取个性化行程、美食推荐、酒店攻略。北京、上海、成都、云南——告诉我想去哪待多久。',
        signIn: '登录',
        heroTitle: '规划你的中国之旅 🐼',
        heroSub: '少问问题，多聊天。告诉我去哪、待几天就行。',
        inputPlaceholder: '例如：北京5天，美食+历史，轻松游…',
        startBtn: '开始',
        guestHint: '直接聊天 · Google 登录 · 游客模式',
        footer: '无需登录即可体验——最近3次行程保存在本地。登录后可跨设备同步。',
        chatTitle: '对话 · VisePanda — AI 中国旅行规划师',
        chatMeta: '与 VisePanda AI 对话，规划你的中国之旅。获取每日行程、美食指南和实用旅行贴士。',
        tripsBtn: '行程',
        clearBtn: '清空',
        homeBtn: '首页',
        welcomeTitle: '👋 欢迎使用 VisePanda',
        welcomeSub: '你的 AI 中国旅行规划师。尽管问我！',
        inputMsgPlaceholder: '输入消息…',
        sendBtn: '发送',
        connFailed: '连接失败。请检查网络。',
        retry: '重试',
        error: '错误',
        loading: '正在加载服务…请稍候或',
        refresh: '刷新',
        tripsTitle: '我的行程 · VisePanda',
        tripsHeading: '我的行程',
        noTrips: '还没有行程。',
        startPlanning: '开始规划',
        failedLoad: '加载行程失败。',
        shareBtn: '🔗 分享',
        renameBtn: '✏️ 重命名',
        deleteBtn: '🗑 删除',
        sharePrompt: '分享链接：',
        shareFailed: '分享失败',
        renamePrompt: '重命名行程：',
        deleteConfirm: '确认删除此行程和所有聊天记录？',
        messages: '条消息',
        homeLink: '首页',
        signingIn: '正在登录…',
        redirecting: '正在跳转…',
        shareTitleSuffix: '· VisePanda',
        shareAI: 'AI 规划的行程',
        planYourOwn: '规划你自己的行程',
        notFoundTitle: '404 — VisePanda',
        notFound: '页面未找到',
        backHome: '返回首页',
        langLabel: 'EN',
    }
};

let LANG = localStorage.getItem('vp_lang') || 'en';

function t(key) {
    return (I18N[LANG] && I18N[LANG][key]) || (I18N['en'][key] || key);
}

function setLang(lang) {
    LANG = lang;
    localStorage.setItem('vp_lang', lang);
    location.reload();
}

// Auto-detect browser language
if (!localStorage.getItem('vp_lang')) {
    var nav = navigator.language || '';
    if (nav.startsWith('zh')) {
        LANG = 'zh';
        localStorage.setItem('vp_lang', 'zh');
    }
}

// DOM walk — replace text for elements with data-i18n attributes
function i18nInit() {
    if (LANG === 'en') return; // Default is English, server renders English

    // Text content
    var els = document.querySelectorAll('[data-i18n]');
    for (var i = 0; i < els.length; i++) {
        var el = els[i];
        var key = el.getAttribute('data-i18n');
        var val = t(key);
        if (val) el.textContent = val;
    }

    // Placeholders
    els = document.querySelectorAll('[data-i18n-placeholder]');
    for (i = 0; i < els.length; i++) {
        el = els[i];
        key = el.getAttribute('data-i18n-placeholder');
        val = t(key);
        if (val) el.placeholder = val;
    }

    // Title attributes
    els = document.querySelectorAll('[data-i18n-title]');
    for (i = 0; i < els.length; i++) {
        el = els[i];
        key = el.getAttribute('data-i18n-title');
        val = t(key);
        if (val) el.title = val;
    }

    // Meta tags
    var metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc && metaDesc.getAttribute('data-i18n-content')) {
        metaDesc.content = t(metaDesc.getAttribute('data-i18n-content'));
    }

    // Page title
    var titleEl = document.querySelector('title');
    if (titleEl && titleEl.getAttribute('data-i18n')) {
        document.title = t(titleEl.getAttribute('data-i18n'));
    }
}

// Run on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', i18nInit);
} else {
    i18nInit();
}
