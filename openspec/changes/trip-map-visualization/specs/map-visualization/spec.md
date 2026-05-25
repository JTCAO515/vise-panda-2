## ADDED Requirements

### Requirement: Geocode Proxy API
The backend SHALL provide a geocoding proxy that converts city/POI names to coordinates via Nominatim with caching.

#### Scenario: Basic geocode request
- **WHEN** POST /api/geocode {"places": ["Xi'an", "Chengdu"]}
- **THEN** returns {"Xi'an": [34.3416, 108.9398], "Chengdu": [30.5728, 104.0668]}

#### Scenario: Cache hit
- **WHEN** same place queried twice
- **THEN** second request returns from cache, no Nominatim call

#### Scenario: Rate limiting
- **WHEN** 5 places queried simultaneously
- **THEN** each request SHALL be spaced >= 1.2s

#### Scenario: Error tolerance
- **WHEN** Nominatim returns empty for a place
- **THEN** returns null for that place, others unaffected

### Requirement: Leaflet Interactive Map
The map component SHALL be based on Leaflet + OpenStreetMap with dark theme.

#### Scenario: Map initialization
- **WHEN** initMap() called on a container div
- **THEN** CartoDB Dark Matter map renders with zoom/pan

#### Scenario: City markers
- **WHEN** addCityMarkers() with city coordinates
- **THEN** markers with city name labels appear on map

#### Scenario: Route lines
- **WHEN** addRouteLine() with city coordinates
- **THEN** polyline connections shown between cities

#### Scenario: Day switching
- **WHEN** user clicks Day 1 / Day 2 / All tab
- **THEN** map SHALL show only the selected day's route

#### Scenario: Mobile touch
- **WHEN** user touches and drags on mobile
- **THEN** map pans and zooms correctly

### Requirement: Chat Page Integration
The chat page SHALL auto-display the map when a structured itinerary is detected.

#### Scenario: Auto-map on itinerary
- **WHEN** LLM returns structured itinerary (trip_update SSE event)
- **THEN** map appears below the chat bubble

#### Scenario: No map for non-itinerary
- **WHEN** user sends non-travel message
- **THEN** map container stays hidden

### Requirement: Share Page Integration
The share page SHALL display a map with the full itinerary.

#### Scenario: Share page map
- **WHEN** user visits /share/{share_id}
- **THEN** map with full itinerary shown at page bottom
