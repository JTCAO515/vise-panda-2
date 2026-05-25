// VisePanda Trip Map — Leaflet + OpenStreetMap
// Renders trip itineraries on a dark-themed interactive map.

const VP_MAP = {};

const DAY_COLORS = ['#7dd3fc', '#fbbf24', '#f87171', '#4ade80', '#a78bfa', '#f472b6', '#fb923c'];

VP_MAP.initMap = function(containerId, tripData) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Only init once
    if (container._vpMap) return;
    
    const map = L.map(containerId, {
        zoomControl: true,
        attributionControl: false,
        zoom: 5,
        center: [35, 110],
    });
    
    // Dark tile layer (CartoDB Dark Matter)
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
    const map = VP_MAP.initMap(containerId);
    if (!map) return;
    
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Clear previous layers
    Object.values(container._vpLayers).forEach(g => map.removeLayer(g));
    container._vpLayers = {};
    container._vpAllMarkers.clearLayers();
    
    // Get itinerary data
    const itin = tripData.current_itinerary || {};
    const cities = itin.cities || [];
    const dayCount = itin.day_count || 0;
    
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
    
    // All-day layer (full route)
    const allLayer = L.featureGroup();
    const markerLatLngs = [];
    
    validCities.forEach((city, i) => {
        const color = DAY_COLORS[i % DAY_COLORS.length];
        const marker = L.circleMarker(city.latlng, {
            radius: 8,
            color: color,
            fillColor: color,
            fillOpacity: 0.3,
            weight: 2,
        }).bindTooltip(city.name, {direction: 'top', offset: [0, -10]});
        
        markerLatLngs.push(city.latlng);
        allLayer.addLayer(marker);
        
        // City name label
        const label = L.tooltip({
            permanent: true,
            direction: 'bottom',
            offset: [0, 8],
            className: 'vp-map-label',
        }).setLatLng(city.latlng).setContent(city.name);
        allLayer.addLayer(label);
    });
    
    // Route lines between cities
    if (markerLatLngs.length > 1) {
        for (let i = 0; i < markerLatLngs.length - 1; i++) {
            const color = DAY_COLORS[i % DAY_COLORS.length];
            const line = L.polyline([markerLatLngs[i], markerLatLngs[i + 1]], {
                color: color,
                weight: 2,
                opacity: 0.6,
                dashArray: '8, 6',
            });
            allLayer.addLayer(line);
        }
    }
    
    map.fitBounds(allLayer.getBounds().pad(0.3));
    allLayer.addTo(map);
    container._vpLayers['all'] = allLayer;
    
    // Per-day layers (if trip has day data)
    const days = itin.days || [];
    if (days.length > 1) {
        // Create per-day layers (just show subset of cities for each day)
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
                }).bindTooltip(city.name, {direction: 'top'});
                dayLayer.addLayer(m);
            });
            
            if (perDayCities.length > 1) {
                for (let i = 0; i < perDayCities.length - 1; i++) {
                    const line = L.polyline([perDayCities[i].latlng, perDayCities[i + 1].latlng], {
                        color: DAY_COLORS[idx % DAY_COLORS.length],
                        weight: 2.5,
                        opacity: 0.8,
                    });
                    dayLayer.addLayer(line);
                }
            }
            
            container._vpLayers[`day${idx + 1}`] = dayLayer;
            dayLayer.addTo(map);
        });
        
        // Hide all per-day layers initially (show "all" first)
        days.forEach((_, idx) => {
            container._vpLayers[`day${idx + 1}`].setStyle({opacity: 0});
            map.removeLayer(container._vpLayers[`day${idx + 1}`]);
        });
        container._vpLayers['all'].addTo(map);
    }
    
    // Set up day switcher UI
    VP_MAP.setupDaySwitcher(container, days);
};

VP_MAP.switchDay = function(container, dayIndex) {
    const map = container._vpMap;
    if (!map) return;
    
    // Hide all layers
    Object.values(container._vpLayers).forEach(g => {
        if (map.hasLayer(g)) map.removeLayer(g);
    });
    
    const key = dayIndex === 0 ? 'all' : `day${dayIndex}`;
    const layer = container._vpLayers[key];
    if (layer) {
        layer.addTo(map);
        map.fitBounds(layer.getBounds().pad(0.3));
    }
    
    // Update tab styles
    container.querySelectorAll('.vp-day-tab').forEach(tab => {
        tab.style.opacity = parseInt(tab.dataset.day) === dayIndex ? '1' : '0.4';
        tab.style.borderBottom = parseInt(tab.dataset.day) === dayIndex ? '2px solid #7dd3fc' : '2px solid transparent';
    });
};

VP_MAP.setupDaySwitcher = function(container, days) {
    const existing = container.querySelector('.vp-day-tabs');
    if (existing) existing.remove();
    
    const tabs = document.createElement('div');
    tabs.className = 'vp-day-tabs';
    tabs.style.cssText = 'display:flex;gap:6px;padding:8px 12px;border-bottom:1px solid rgba(255,255,255,.08);overflow-x:auto';
    
    // "All" tab
    const allTab = document.createElement('button');
    allTab.className = 'vp-day-tab';
    allTab.dataset.day = '0';
    allTab.textContent = '📍 All';
    allTab.style.cssText = 'background:none;border:none;color:rgba(255,255,255,.9);font-size:12px;cursor:pointer;padding:4px 10px;border-bottom:2px solid #7dd3fc;opacity:1;white-space:nowrap;flex-shrink:0';
    allTab.onclick = () => VP_MAP.switchDay(container, 0);
    tabs.appendChild(allTab);
    
    // Day tabs
    days.forEach((day, idx) => {
        const tab = document.createElement('button');
        tab.className = 'vp-day-tab';
        tab.dataset.day = `${idx + 1}`;
        tab.textContent = `Day ${idx + 1}`;
        tab.style.cssText = 'background:none;border:none;color:rgba(255,255,255,.6);font-size:12px;cursor:pointer;padding:4px 10px;border-bottom:2px solid transparent;opacity:0.4;white-space:nowrap;flex-shrink:0';
        tab.onclick = () => VP_MAP.switchDay(container, idx + 1);
        tabs.appendChild(tab);
    });
    
    container.parentNode.insertBefore(tabs, container);
};

// Add Leaflet CSS dynamically
if (!document.querySelector('link[href*="leaflet"]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(link);
}
