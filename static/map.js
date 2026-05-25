// VisePanda Trip Map v2 — Enhanced with Chinese aesthetic
// Renders trip itineraries on a dark-themed interactive map.

const VP_MAP = {};

// Chinese-themed day colors (matching UI palette)
const DAY_COLORS = ['#dc4a3a', '#e8c56a', '#7dd3fc', '#4ade80', '#a78bfa', '#f472b6'];
const DAY_COLORS_FILL = ['rgba(220,74,58,.3)', 'rgba(232,197,106,.3)', 'rgba(125,211,252,.3)', 'rgba(74,222,128,.3)', 'rgba(167,139,250,.3)', 'rgba(244,114,182,.3)'];

VP_MAP.initMap = function(containerId, tripData) {
    const container = document.getElementById(containerId);
    if (!container) return null;
    if (container._vpMap) return container._vpMap;
    
    const map = L.map(containerId, {
        zoomControl: true,
        attributionControl: false,
        zoom: 5,
        center: [35, 110],
    });
    
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd',
    }).addTo(map);
    
    container._vpMap = map;
    container._vpLayers = {};
    container._vpAllMarkers = L.featureGroup().addTo(map);
    
    return map;
};

VP_MAP.loadItinerary = async function(containerId, tripData) {
    const map = VP_MAP.initMap(containerId, tripData);
    if (!map) return;
    
    const container = document.getElementById(containerId);
    if (!container) return;
    
    Object.values(container._vpLayers).forEach(g => {
        if (map.hasLayer(g)) map.removeLayer(g);
    });
    container._vpLayers = {};
    container._vpAllMarkers.clearLayers();
    
    const itin = tripData.current_itinerary || {};
    const cities = itin.cities || [];
    if (!cities.length) return;
    
    // Geocode cities
    let coords = {};
    try {
        const resp = await fetch('/api/geocode', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({places: cities}),
        });
        coords = await resp.json();
    } catch (e) {
        console.error('Geocode failed:', e);
        return;
    }
    
    const validCities = cities.filter(c => coords[c]).map(c => ({
        name: c,
        latlng: coords[c],
    }));
    if (!validCities.length) return;
    
    // ── All-day layer ──
    const allLayer = L.featureGroup();
    const markerLatLngs = [];
    
    const popupContent = validCities.map((city, i) => 
        `<div style="color:#e8c56a;font-weight:600;font-size:13px;margin-bottom:2px">📍 ${city.name}</div>` +
        `<div style="color:rgba(255,255,255,.5);font-size:11px">Stop ${i+1} of ${validCities.length}</div>`
    );
    
    validCities.forEach((city, i) => {
        const color = DAY_COLORS[i % DAY_COLORS.length];
        const fillColor = DAY_COLORS_FILL[i % DAY_COLORS_FILL.length];
        
        // Custom marker with tooltip
        const marker = L.circleMarker(city.latlng, {
            radius: 9,
            color: color,
            fillColor: color,
            fillOpacity: 0.35,
            weight: 2.5,
        })
        .bindTooltip(`<b>${city.name}</b>`, {
            direction: 'top',
            offset: [0, -12],
            className: 'vp-map-tooltip',
        })
        .bindPopup(popupContent[i], {
            className: 'vp-map-popup',
            closeButton: true,
        });
        
        markerLatLngs.push(city.latlng);
        allLayer.addLayer(marker);
        
        // Permanent city label below marker
        const label = L.tooltip({
            permanent: true,
            direction: 'bottom',
            offset: [0, 8],
            className: 'vp-map-label',
        }).setLatLng(city.latlng).setContent(
            `<span style="font-size:11px;font-weight:600">${city.name}</span>`
        );
        allLayer.addLayer(label);
    });
    
    // Route lines with gradient-like styling
    if (markerLatLngs.length > 1) {
        for (let i = 0; i < markerLatLngs.length - 1; i++) {
            const color = DAY_COLORS[i % DAY_COLORS.length];
            const line = L.polyline([markerLatLngs[i], markerLatLngs[i + 1]], {
                color: color,
                weight: 2.5,
                opacity: 0.5,
                dashArray: '6, 4',
            });
            allLayer.addLayer(line);
            
            // Dashed connector with arrow point
            const midLat = (markerLatLngs[i].lat + markerLatLngs[i + 1].lat) / 2;
            const midLng = (markerLatLngs[i].lng + markerLatLngs[i + 1].lng) / 2;
            const dot = L.circleMarker([midLat, midLng], {
                radius: 3,
                color: color,
                fillColor: color,
                fillOpacity: 0.6,
                weight: 1,
            });
            allLayer.addLayer(dot);
        }
    }
    
    map.fitBounds(allLayer.getBounds().pad(0.3));
    allLayer.addTo(map);
    container._vpLayers['all'] = allLayer;
    
    // ── Per-day layers ──
    const days = itin.days || [];
    if (days.length > 1) {
        days.forEach((day, idx) => {
            const dayLayer = L.featureGroup();
            const perDayCities = validCities.slice(0, Math.max(1, Math.ceil((idx + 1) * validCities.length / days.length)));
            
            perDayCities.forEach(city => {
                const color = DAY_COLORS[idx % DAY_COLORS.length];
                const m = L.circleMarker(city.latlng, {
                    radius: 7,
                    color: color,
                    fillColor: color,
                    fillOpacity: 0.25,
                    weight: 2,
                }).bindTooltip(`Day ${idx+1}: ${city.name}`, {direction: 'top'});
                dayLayer.addLayer(m);
            });
            
            if (perDayCities.length > 1) {
                for (let i = 0; i < perDayCities.length - 1; i++) {
                    const line = L.polyline([perDayCities[i].latlng, perDayCities[i + 1].latlng], {
                        color: DAY_COLORS[idx % DAY_COLORS.length],
                        weight: 3,
                        opacity: 0.8,
                    });
                    dayLayer.addLayer(line);
                }
            }
            
            container._vpLayers[`day${idx + 1}`] = dayLayer;
            dayLayer.addTo(map);
        });
        
        // Hide per-day layers, show all
        days.forEach((_, idx) => {
            const layer = container._vpLayers[`day${idx + 1}`];
            if (layer && map.hasLayer(layer)) map.removeLayer(layer);
        });
        if (!map.hasLayer(container._vpLayers['all'])) {
            container._vpLayers['all'].addTo(map);
        }
    }
    
    VP_MAP.setupDaySwitcher(container, days, validCities);
};

VP_MAP.switchDay = function(container, dayIndex) {
    const map = container._vpMap;
    if (!map) return;
    
    Object.values(container._vpLayers).forEach(g => {
        if (map.hasLayer(g)) map.removeLayer(g);
    });
    
    const key = dayIndex === 0 ? 'all' : `day${dayIndex}`;
    const layer = container._vpLayers[key];
    if (layer) {
        layer.addTo(map);
        if (layer.getBounds().isValid()) {
            map.fitBounds(layer.getBounds().pad(0.3));
        }
    }
    
    container.querySelectorAll('.vp-day-tab').forEach(tab => {
        const isActive = parseInt(tab.dataset.day) === dayIndex;
        tab.style.opacity = isActive ? '1' : '0.35';
        tab.style.borderBottom = isActive ? '2px solid #dc4a3a' : '2px solid transparent';
        tab.style.color = isActive ? '#e8c56a' : 'rgba(255,255,255,.5)';
    });
};

VP_MAP.setupDaySwitcher = function(container, days) {
    const existing = container.querySelector('.vp-day-tabs');
    if (existing) existing.remove();
    
    const tabs = document.createElement('div');
    tabs.className = 'vp-day-tabs';
    tabs.style.cssText = 'display:flex;gap:4px;padding:6px 12px;border-bottom:1px solid rgba(255,255,255,.06);overflow-x:auto;background:rgba(10,8,16,.4)';
    
    const allTab = document.createElement('button');
    allTab.className = 'vp-day-tab';
    allTab.dataset.day = '0';
    allTab.textContent = '📍 全览';
    allTab.style.cssText = 'background:none;border:none;color:#e8c56a;font-size:11px;cursor:pointer;padding:4px 10px;border-bottom:2px solid #dc4a3a;opacity:1;white-space:nowrap;flex-shrink:0;font-weight:600';
    allTab.onclick = () => VP_MAP.switchDay(container, 0);
    tabs.appendChild(allTab);
    
    days.forEach((day, idx) => {
        const tab = document.createElement('button');
        tab.className = 'vp-day-tab';
        tab.dataset.day = `${idx + 1}`;
        tab.textContent = `Day ${idx + 1}`;
        tab.style.cssText = 'background:none;border:none;color:rgba(255,255,255,.5);font-size:11px;cursor:pointer;padding:4px 10px;border-bottom:2px solid transparent;opacity:0.35;white-space:nowrap;flex-shrink:0';
        tab.onclick = () => VP_MAP.switchDay(container, idx + 1);
        tabs.appendChild(tab);
    });
    
    container.parentNode.insertBefore(tabs, container);
};

// Dynamic Leaflet CSS
if (!document.querySelector('link[href*="leaflet"]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(link);
}

// Tooltip/popup styling
const style = document.createElement('style');
style.textContent = `
.vp-map-tooltip { background:rgba(10,8,16,.9)!important; border:1px solid rgba(255,255,255,.1)!important; color:#fff!important; font-size:12px!important; border-radius:6px!important; padding:4px 10px!important; box-shadow:0 4px 12px rgba(0,0,0,.3)!important }
.vp-map-tooltip::before { border-top-color:rgba(10,8,16,.9)!important }
.vp-map-popup .leaflet-popup-content-wrapper { background:rgba(10,8,16,.95)!important; color:#fff!important; border-radius:8px!important; border:1px solid rgba(255,255,255,.08)!important; box-shadow:0 8px 24px rgba(0,0,0,.4)!important }
.vp-map-popup .leaflet-popup-tip { background:rgba(10,8,16,.95)!important; border:1px solid rgba(255,255,255,.08)!important }
.vp-map-popup .leaflet-popup-close-button { color:rgba(255,255,255,.4)!important }
`;
document.head.appendChild(style);
