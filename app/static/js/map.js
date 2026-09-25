/**
 * TENALI AI - Complete Spatial Context Map for AGPYP
 * Features: Satellite basemap, AOI selection, footprint rendering, evidence overlays
 */

class TenaliMap {
  constructor() {
    this.map = null;
    this.mapContainer = document.getElementById('map-container');
    this.mapSection = document.getElementById('map-section');
    this.currentBasemap = 'satellite-labels'; // satellite, satellite-labels, streets
    this.initialized = false;
    this.currentFootprint = null;
    this.currentAOI = null;
    this.isDrawingAOI = false;
    this.aoiStartPoint = null;

    // Store references to UI controls
    this.controls = {
      basemapBtn: null,
      resetBtn: null,
      fullscreenBtn: null,
      clearAOI: null,
      analyzeAOI: null
    };

    // Initialize when map section is visible
    if (this.mapSection) {
      this.initializeMap();
      this.setupEventListeners();
    }
  }

  /**
   * Initialize MapLibre GL map with draw controls
   */
  initializeMap() {
    if (this.initialized || !this.mapContainer) return;

    try {
      // Create map instance
      this.map = new maplibregl.Map({
        container: 'map-container',
        style: this.getSatelliteStyle(),
        center: [78.9629, 20.5937], // Center of India
        zoom: 4,
        attributionControl: true
      });

      // Add fullscreen control
      this.map.addControl(new maplibregl.FullscreenControl(), 'top-right');

      // Setup custom controls (includes zoom buttons)
      this.addCustomControls();

      // Setup AOI rectangle drawing
      this.setupRectangleDraw();

      this.initialized = true;
      console.log('[TenaliMap] Map initialized with rectangle AOI selection');

    } catch (error) {
      console.error('[TenaliMap] Map initialization failed:', error);
    }
  }

  /**
   * Get style object for satellite basemap
   */
  getSatelliteStyle() {
    const sources = {
      'satellite': {
        type: 'raster',
        tiles: [
          'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        ],
        tileSize: 256,
        attribution: '© Esri'
      },
      'labels': {
        type: 'raster',
        tiles: [
          'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}'
        ],
        tileSize: 256,
        attribution: '© Esri'
      },
      'osm': {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '© OpenStreetMap'
      }
    };

    let layers = [];

    if (this.currentBasemap === 'satellite') {
      layers = [
        {
          id: 'satellite-layer',
          type: 'raster',
          source: 'satellite'
        }
      ];
    } else if (this.currentBasemap === 'satellite-labels') {
      layers = [
        {
          id: 'satellite-layer',
          type: 'raster',
          source: 'satellite'
        },
        {
          id: 'labels-layer',
          type: 'raster',
          source: 'labels'
        }
      ];
    } else if (this.currentBasemap === 'streets') {
      layers = [
        {
          id: 'osm-layer',
          type: 'raster',
          source: 'osm'
        }
      ];
    }

    return {
      version: 8,
      sources: sources,
      layers: layers
    };
  }

  /**
   * Add custom control buttons
   */
  addCustomControls() {
    // Zoom controls
    const zoomControl = document.createElement('div');
    zoomControl.className = 'maplibregl-ctrl maplibregl-ctrl-group';
    zoomControl.innerHTML = `
      <button id="map-zoom-in" class="maplibregl-ctrl-icon" title="Zoom In" style="width: 32px; height: 32px; font-size: 20px; font-weight: 600; line-height: 1;">+</button>
      <button id="map-zoom-out" class="maplibregl-ctrl-icon" title="Zoom Out" style="width: 32px; height: 32px; font-size: 20px; font-weight: 600; line-height: 1;">−</button>
    `;
    this.map.getContainer().appendChild(zoomControl);
    zoomControl.querySelector('#map-zoom-in').addEventListener('click', () => this.map.zoomIn());
    zoomControl.querySelector('#map-zoom-out').addEventListener('click', () => this.map.zoomOut());

    // Basemap toggle control
    const basemapControl = document.createElement('div');
    basemapControl.className = 'maplibregl-ctrl maplibregl-ctrl-group';
    basemapControl.innerHTML = `
      <button id="map-basemap-toggle" class="maplibregl-ctrl-icon" title="Basemap: Satellite + Labels" style="width: 32px; height: 32px;">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10 0L0 6v8l10 6 10-6V6L10 0zm8 12.5l-8 4.8-8-4.8V7.5l8 4.8 8-4.8v5z"/>
        </svg>
      </button>
    `;
    this.map.getContainer().appendChild(basemapControl);
    this.controls.basemapBtn = basemapControl.querySelector('#map-basemap-toggle');
    this.controls.basemapBtn.addEventListener('click', () => this.toggleBasemap());

    // Reset view control
    const resetControl = document.createElement('div');
    resetControl.className = 'maplibregl-ctrl maplibregl-ctrl-group';
    resetControl.innerHTML = `
      <button id="map-reset-view" class="maplibregl-ctrl-icon" title="Reset View (Center on India)" style="width: 32px; height: 32px;">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10 3v2a5 5 0 000 10v2a7 7 0 010-14zM8.5 11l-2.5 2.5L3.5 11H8.5z"/>
        </svg>
      </button>
    `;
    this.map.getContainer().appendChild(resetControl);
    this.controls.resetBtn = resetControl.querySelector('#map-reset-view');
    this.controls.resetBtn.addEventListener('click', () => this.resetView());

    // Draw rectangle button
    const drawControl = document.createElement('div');
    drawControl.className = 'maplibregl-ctrl maplibregl-ctrl-group';
    drawControl.innerHTML = `
      <button id="map-draw-aoi" class="maplibregl-ctrl-icon" title="Select Area of Interest (Click and Drag)" style="width: 32px; height: 32px;">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="14" height="14" rx="1"/>
        </svg>
      </button>
    `;
    this.map.getContainer().appendChild(drawControl);
    const drawBtn = drawControl.querySelector('#map-draw-aoi');
    drawBtn.addEventListener('click', () => this.startDrawingAOI());

    // Clear AOI button
    const clearControl = document.createElement('div');
    clearControl.className = 'maplibregl-ctrl maplibregl-ctrl-group';
    clearControl.style.display = 'none';
    clearControl.innerHTML = `
      <button id="map-clear-aoi" class="maplibregl-ctrl-icon" title="Clear Area of Interest" style="width: 32px; height: 32px; background-color: #dc2626 !important;">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="white" stroke-width="2">
          <path d="M4 4l12 12M16 4L4 16"/>
        </svg>
      </button>
    `;
    this.map.getContainer().appendChild(clearControl);
    this.controls.clearAOI = clearControl.querySelector('#map-clear-aoi');
    this.controls.clearAOI.addEventListener('click', () => this.clearAOI());

    // Store reference to the control div for show/hide
    this.controls.clearAOIControl = clearControl;

    // Position custom controls
    const controlPositions = this.map.getContainer().querySelectorAll('.maplibregl-ctrl-group');
    controlPositions.forEach((ctrl, idx) => {
      ctrl.style.position = 'absolute';
      if (idx === controlPositions.length - 5) { // Zoom
        ctrl.style.top = '10px';
        ctrl.style.left = '10px';
      } else if (idx === controlPositions.length - 4) { // Basemap
        ctrl.style.top = '90px';
        ctrl.style.left = '10px';
      } else if (idx === controlPositions.length - 3) { // Reset
        ctrl.style.top = '130px';
        ctrl.style.left = '10px';
      } else if (idx === controlPositions.length - 2) { // Draw
        ctrl.style.top = '170px';
        ctrl.style.left = '10px';
      } else if (idx === controlPositions.length - 1) { // Clear
        ctrl.style.top = '210px';
        ctrl.style.left = '10px';
      }
    });
  }

  /**
   * Toggle basemap between satellite, satellite+labels, and streets
   */
  toggleBasemap() {
    const modes = ['satellite-labels', 'satellite', 'streets'];
    const currentIndex = modes.indexOf(this.currentBasemap);
    const nextIndex = (currentIndex + 1) % modes.length;
    this.currentBasemap = modes[nextIndex];

    // Update button tooltip
    const modeNames = {
      'satellite-labels': 'Satellite + Labels',
      'satellite': 'Satellite',
      'streets': 'Streets'
    };
    if (this.controls.basemapBtn) {
      this.controls.basemapBtn.title = `Basemap: ${modeNames[this.currentBasemap]}`;
    }

    // Update map style
    this.map.setStyle(this.getSatelliteStyle());

    // Re-add footprint and evidence after style change
    this.map.once('styledata', () => {
      if (this.currentFootprint) {
        this.renderFootprint(this.currentFootprint);
      }
      if (this.currentAOI) {
        this.renderAOI(this.currentAOI);
      }
    });

    console.log(`[TenaliMap] Basemap switched to: ${this.currentBasemap}`);
  }

  /**
   * Reset view to default
   */
  resetView() {
    this.map.flyTo({
      center: [78.9629, 20.5937],
      zoom: 4,
      duration: 1000
    });
  }

  /**
   * Setup click-and-drag rectangle drawing
   */
  setupRectangleDraw() {
    this.map.on('mousedown', (e) => {
      if (!this.isDrawingAOI) return;

      this.aoiStartPoint = e.lngLat;
      this.map.getCanvas().style.cursor = 'crosshair';

      const onMouseMove = (e) => {
        if (!this.aoiStartPoint) return;

        const currentPoint = e.lngLat;
        this.renderTempAOI(this.aoiStartPoint, currentPoint);
      };

      const onMouseUp = (e) => {
        if (!this.aoiStartPoint) return;

        const endPoint = e.lngLat;
        this.finishAOI(this.aoiStartPoint, endPoint);

        this.map.off('mousemove', onMouseMove);
        this.map.off('mouseup', onMouseUp);
        this.aoiStartPoint = null;
        this.isDrawingAOI = false;
        this.map.getCanvas().style.cursor = '';
      };

      this.map.on('mousemove', onMouseMove);
      this.map.on('mouseup', onMouseUp);
    });
  }

  /**
   * Render temporary AOI rectangle while dragging
   */
  renderTempAOI(start, end) {
    const coords = this.getRectangleCoords(start, end);

    if (this.map.getSource('temp-aoi')) {
      this.map.getSource('temp-aoi').setData({
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [coords]
        }
      });
    } else {
      this.map.addSource('temp-aoi', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: [coords]
          }
        }
      });

      this.map.addLayer({
        id: 'temp-aoi-fill',
        type: 'fill',
        source: 'temp-aoi',
        paint: {
          'fill-color': '#06b6d4',
          'fill-opacity': 0.15
        }
      });

      this.map.addLayer({
        id: 'temp-aoi-outline',
        type: 'line',
        source: 'temp-aoi',
        paint: {
          'line-color': '#06b6d4',
          'line-width': 3
        }
      });
    }
  }

  /**
   * Finish drawing AOI
   */
  finishAOI(start, end) {
    const coords = this.getRectangleCoords(start, end);

    this.currentAOI = {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [coords]
      },
      properties: {
        type: 'aoi'
      }
    };

    // Remove temp layer
    if (this.map.getLayer('temp-aoi-fill')) {
      this.map.removeLayer('temp-aoi-fill');
      this.map.removeLayer('temp-aoi-outline');
      this.map.removeSource('temp-aoi');
    }

    // Reset draw button style
    const drawBtn = document.getElementById('map-draw-aoi');
    if (drawBtn) {
      drawBtn.style.backgroundColor = '';
      drawBtn.style.color = '';
    }

    // Render final AOI
    if (this.map.getSource('aoi')) {
      this.map.getSource('aoi').setData(this.currentAOI);
    } else {
      this.map.addSource('aoi', {
        type: 'geojson',
        data: this.currentAOI
      });

      this.map.addLayer({
        id: 'aoi-fill',
        type: 'fill',
        source: 'aoi',
        paint: {
          'fill-color': '#06b6d4',
          'fill-opacity': 0.2
        }
      });

      this.map.addLayer({
        id: 'aoi-outline',
        type: 'line',
        source: 'aoi',
        paint: {
          'line-color': '#06b6d4',
          'line-width': 3,
          'line-dasharray': [2, 2]
        }
      });
    }

    // Show clear button
    if (this.controls.clearAOIControl) {
      this.controls.clearAOIControl.style.display = 'block';
    }

    // Dispatch event
    this.updateAnalyzeButton(true);

    console.log('[TenaliMap] AOI created:', this.currentAOI);
  }

  /**
   * Get rectangle coordinates from two points
   */
  getRectangleCoords(start, end) {
    return [
      [start.lng, start.lat],
      [end.lng, start.lat],
      [end.lng, end.lat],
      [start.lng, end.lat],
      [start.lng, start.lat] // close the ring
    ];
  }

  /**
   * Start drawing rectangle AOI
   */
  startDrawingAOI() {
    this.isDrawingAOI = true;
    this.map.getCanvas().style.cursor = 'crosshair';

    // Visual feedback: highlight the draw button
    const drawBtn = document.getElementById('map-draw-aoi');
    if (drawBtn) {
      drawBtn.style.backgroundColor = '#0891b2';
      drawBtn.style.color = '#ffffff';
    }

    console.log('[TenaliMap] Click and drag to draw rectangle AOI');
  }

  /**
   * Clear AOI
   */
  clearAOI() {
    this.currentAOI = null;
    this.isDrawingAOI = false;
    this.aoiStartPoint = null;

    // Reset cursor
    this.map.getCanvas().style.cursor = '';

    // Reset draw button style
    const drawBtn = document.getElementById('map-draw-aoi');
    if (drawBtn) {
      drawBtn.style.backgroundColor = '';
      drawBtn.style.color = '';
    }

    // Remove AOI layers
    if (this.map.getLayer('aoi-fill')) {
      this.map.removeLayer('aoi-fill');
      this.map.removeLayer('aoi-outline');
      this.map.removeSource('aoi');
    }

    // Remove temp AOI layers if present
    if (this.map.getLayer('temp-aoi-fill')) {
      this.map.removeLayer('temp-aoi-fill');
      this.map.removeLayer('temp-aoi-outline');
      this.map.removeSource('temp-aoi');
    }

    if (this.controls.clearAOIControl) {
      this.controls.clearAOIControl.style.display = 'none';
    }

    this.map.getCanvas().style.cursor = '';
    this.updateAnalyzeButton(false);
    console.log('[TenaliMap] AOI cleared');
  }

  /**
   * Get current AOI as GeoJSON
   */
  getAOI() {
    return this.currentAOI;
  }

  /**
   * Update analyze button state
   */
  updateAnalyzeButton(enabled) {
    // This will be called by app.js to enable/disable analyze button
    const event = new CustomEvent('aoi-changed', {
      detail: {
        hasAOI: enabled,
        geojson: this.currentAOI
      }
    });
    document.dispatchEvent(event);
  }

  /**
   * Render image footprint on map
   */
  renderFootprint(footprintGeoJSON) {
    if (!this.map || !footprintGeoJSON) return;

    try {
      // Store footprint for re-rendering after style changes
      this.currentFootprint = footprintGeoJSON;

      // Remove existing footprint
      if (this.map.getLayer('footprint-fill')) {
        this.map.removeLayer('footprint-fill');
      }
      if (this.map.getLayer('footprint-outline')) {
        this.map.removeLayer('footprint-outline');
      }
      if (this.map.getSource('footprint')) {
        this.map.removeSource('footprint');
      }

      // Add footprint source
      this.map.addSource('footprint', {
        type: 'geojson',
        data: footprintGeoJSON
      });

      // Add footprint fill layer
      this.map.addLayer({
        id: 'footprint-fill',
        type: 'fill',
        source: 'footprint',
        paint: {
          'fill-color': '#22d3ee',
          'fill-opacity': 0.2
        }
      });

      // Add footprint outline layer
      this.map.addLayer({
        id: 'footprint-outline',
        type: 'line',
        source: 'footprint',
        paint: {
          'line-color': '#22d3ee',
          'line-width': 3
        }
      });

      // Fit map to footprint bounds
      const bbox = this.getBBoxFromGeoJSON(footprintGeoJSON);
      if (bbox) {
        this.map.fitBounds(bbox, {
          padding: 50,
          duration: 1000
        });
      }

      console.log('[TenaliMap] Footprint rendered');
    } catch (error) {
      console.error('[TenaliMap] Failed to render footprint:', error);
    }
  }

  /**
   * Render evidence overlays on map
   */
  renderEvidence(evidenceGeoJSON) {
    if (!this.map || !evidenceGeoJSON) return;

    try {
      // Remove existing evidence
      if (this.map.getLayer('evidence-layer')) {
        this.map.removeLayer('evidence-layer');
      }
      if (this.map.getSource('evidence')) {
        this.map.removeSource('evidence');
      }

      // Add evidence source
      this.map.addSource('evidence', {
        type: 'geojson',
        data: evidenceGeoJSON
      });

      // Add evidence layer (points or polygons)
      const geometryType = evidenceGeoJSON.type === 'FeatureCollection'
        ? evidenceGeoJSON.features[0]?.geometry.type
        : evidenceGeoJSON.geometry?.type;

      if (geometryType === 'Point') {
        this.map.addLayer({
          id: 'evidence-layer',
          type: 'circle',
          source: 'evidence',
          paint: {
            'circle-radius': 6,
            'circle-color': '#f59e0b',
            'circle-stroke-width': 2,
            'circle-stroke-color': '#fff'
          }
        });
      } else if (geometryType === 'Polygon' || geometryType === 'MultiPolygon') {
        this.map.addLayer({
          id: 'evidence-layer',
          type: 'fill',
          source: 'evidence',
          paint: {
            'fill-color': '#f59e0b',
            'fill-opacity': 0.3,
            'fill-outline-color': '#f59e0b'
          }
        });
      }

      console.log('[TenaliMap] Evidence rendered');
    } catch (error) {
      console.error('[TenaliMap] Failed to render evidence:', error);
    }
  }

  /**
   * Show map section
   */
  show() {
    if (this.mapSection) {
      this.mapSection.style.display = 'block';
      if (this.map) {
        this.map.resize();
      }
    }
  }

  /**
   * Hide map section
   */
  hide() {
    if (this.mapSection) {
      this.mapSection.style.display = 'none';
    }
  }

  /**
   * Get bounding box from GeoJSON
   */
  getBBoxFromGeoJSON(geojson) {
    try {
      let coords = [];

      if (geojson.type === 'Feature') {
        coords = geojson.geometry.coordinates;
      } else if (geojson.type === 'Polygon') {
        coords = geojson.coordinates;
      } else if (geojson.type === 'FeatureCollection') {
        coords = geojson.features[0]?.geometry.coordinates;
      }

      if (!coords || coords.length === 0) return null;

      // Flatten coordinates
      const flatCoords = this.flattenCoordinates(coords);

      const lngs = flatCoords.map(c => c[0]);
      const lats = flatCoords.map(c => c[1]);

      return [
        [Math.min(...lngs), Math.min(...lats)], // southwest
        [Math.max(...lngs), Math.max(...lats)]  // northeast
      ];
    } catch (error) {
      console.error('[TenaliMap] Failed to calculate bbox:', error);
      return null;
    }
  }

  /**
   * Flatten nested coordinate arrays
   */
  flattenCoordinates(coords) {
    const flat = [];
    for (const item of coords) {
      if (Array.isArray(item[0])) {
        flat.push(...this.flattenCoordinates(item));
      } else {
        flat.push(item);
      }
    }
    return flat;
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Listen for result updates to render footprints
    document.addEventListener('analysis-complete', (e) => {
      if (e.detail && e.detail.footprint) {
        this.renderFootprint(e.detail.footprint);
        this.show();
      }
      if (e.detail && e.detail.evidence) {
        this.renderEvidence(e.detail.evidence);
      }
    });
  }
}

// Initialize map when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.tenaliMap = new TenaliMap();
  });
} else {
  window.tenaliMap = new TenaliMap();
}
