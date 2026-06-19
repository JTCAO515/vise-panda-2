/**
 * VisePanda Trip Timeline — v4.0.2
 * Renders AI trip itineraries as a visual vertical timeline.
 * Pure frontend, no dependencies.
 */

(function() {
  'use strict';

  // ── Parse AI trip content into structured days ──
  function parseTrip(content) {
    // Detect: "### Day 1: Title", "**Day 1:** Title", "Day 1 - Title", "Day 1: Title"
    const dayPattern = /(?:^|\n)(?:###\s*)?(?:\*\*)?\s*Day\s*(\d+)\s*(?::|：|–|—|-)\s*(.*?)(?:\*\*)?(?:\n|$)/gim;
    const days = [];
    let lastIndex = 0;
    let match;

    // Save between-day content as context
    const contextParts = content.split(dayPattern);
    
    while ((match = dayPattern.exec(content)) !== null) {
      const dayNum = parseInt(match[1]);
      const title = match[2].trim();
      
      // Find content between this day header and the next one
      const nextMatch = dayPattern.exec(content);
      dayPattern.lastIndex = nextMatch ? nextMatch.index : content.length;
      const endIdx = nextMatch ? nextMatch.index : content.length;
      
      let dayContent = '';
      if (nextMatch) {
        // Reset so next iteration finds it
        dayPattern.lastIndex = nextMatch.index;
      }

      // Extract bullet points or paragraphs after the day header
      const daySection = content.slice(match.index + match[0].length, nextMatch ? nextMatch.index : content.length).trim();
      
      // Parse activities from bullet points
      const activities = [];
      const bulletRe = /[•▪▸*-]\s*(.+?)(?:\n|$)/g;
      let bMatch;
      while ((bMatch = bulletRe.exec(daySection)) !== null) {
        const text = bMatch[1].trim();
        if (text) {
          activities.push({
            text: text,
            type: classifyActivity(text),
            icon: activityIcon(classifyActivity(text)),
          });
        }
      }

      days.push({
        day: dayNum,
        title: title,
        content: daySection,
        activities: activities,
      });
    }

    return days;
  }

  // ── Classify activity type ──
  function classifyActivity(text) {
    const t = text.toLowerCase();
    if (/hotel|stay|入住|check.in|住宿/.test(t)) return 'accommodation';
    if (/eat|restaurant|food|breakfast|lunch|dinner|cuisine|菜|餐|吃/.test(t)) return 'food';
    if (/flight|train|bus|subway|taxi|drive|transfer|交通|高铁|飞机|地铁/.test(t)) return 'transport';
    if (/visit|temple|museum|park|square|palace|garden|景点|参观|寺|馆|园/.test(t)) return 'attraction';
    if (/shop|market|mall|street|购物|街|market/.test(t)) return 'shopping';
    if (/tour|walk|hike|explore|徒步|游览/.test(t)) return 'activity';
    return 'other';
  }

  function activityIcon(type) {
    const icons = {
      accommodation: '🏨',
      food: '🍜',
      transport: '🚄',
      attraction: '🏯',
      shopping: '🛍️',
      activity: '🎯',
      other: '📍',
    };
    return icons[type] || '📍';
  }

  // ── Render timeline HTML ──
  function renderTimeline(days) {
    if (!days || days.length === 0) return '';

    return `<div class="trip-timeline">${days.map(d => `
      <div class="tl-day">
        <div class="tl-marker">
          <div class="tl-dot tl-dot--${d.activities[0] ? d.activities[0].type : 'other'}"></div>
          ${d.day < days.length ? '<div class="tl-line"></div>' : ''}
        </div>
        <div class="tl-card">
          <div class="tl-card-header">
            <span class="tl-day-badge">Day ${d.day}</span>
            <span class="tl-day-title">${escHtml(d.title)}</span>
          </div>
          ${d.activities.length > 0 ? `<div class="tl-activities">
            ${d.activities.map(a => `
              <div class="tl-activity tl-activity--${a.type}">
                <span class="tl-activity-icon">${a.icon}</span>
                <span class="tl-activity-text">${escHtml(a.text)}</span>
              </div>
            `).join('')}
          </div>` : ''}
        </div>
      </div>
    `).join('')}</div>`;
  }

  // ── Check if content looks like a trip itinerary ──
  function isTripContent(content) {
    if (!content || typeof content !== 'string') return false;
    return /(?:^|\n)(?:###\s*)?(?:\*\*)?\s*Day\s*(\d+)\s*(?::|：|–|—|-)\s*/im.test(content);
  }

  // ── Inject timeline after chat messages ──
  function injectTimeline(content, container) {
    if (!isTripContent(content)) return;
    
    const days = parseTrip(content);
    if (days.length === 0) return;

    // Remove any existing timeline
    const existing = container.querySelector('.trip-timeline-wrap');
    if (existing) existing.remove();

    const wrap = document.createElement('div');
    wrap.className = 'trip-timeline-wrap';
    wrap.innerHTML = `
      <div class="tl-title-row">
        <span class="tl-title">📋 Itinerary Timeline</span>
        <button class="tl-copy-btn" onclick="VP.copyTimeline()" title="Copy to clipboard">📋 Copy</button>
      </div>
      ${renderTimeline(days)}
    `;
    container.appendChild(wrap);
    container.scrollTop = container.scrollHeight;
    
    // Store for copy
    window._lastTimelineDays = days;
    window._lastTimelineContent = content;
  }

  // ── Helper ──
  function escHtml(s) {
    if (!s) return '';
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // ── Copy timeline to clipboard ──
  function copyTimeline() {
    const content = window._lastTimelineContent || '';
    navigator.clipboard.writeText(content).then(() => {
      const btn = document.querySelector('.tl-copy-btn');
      if (btn) { btn.textContent = '✅ Copied!'; setTimeout(() => { btn.textContent = '📋 Copy'; }, 2000); }
    }).catch(() => {});
  }

  // ── Expose ──
  window.TripTimeline = {
    parse: parseTrip,
    render: renderTimeline,
    isTrip: isTripContent,
    inject: injectTimeline,
    copy: copyTimeline,
  };
})();
