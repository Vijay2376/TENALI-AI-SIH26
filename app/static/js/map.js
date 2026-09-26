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
    this.aoiCapture = null;
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
        attributionControl: true,
        canvasContextAttributes: {
          preserveDrawingBuffer: true
        }
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
      <button id="map-zoom-in" class="maplibregl-ctrl-icon tenali-control-button" title="Zoom In" style="width: 32px; height: 32px; font-size: 20px; font-weight: 600; line-height: 1;">+</button>
      <button id="map-zoom-out" class="maplibregl-ctrl-icon tenali-control-button" title="Zoom Out" style="width: 32px; height: 32px; font-size: 20px; font-weight: 600; line-height: 1;">−</button>
    `;
    this.map.getContainer().appendChild(zoomControl);
    zoomControl.querySelector('#map-zoom-in').addEventListener('click', () => this.map.zoomIn());
    zoomControl.querySelector('#map-zoom-out').addEventListener('click', () => this.map.zoomOut());

    // Basemap toggle control
    const basemapControl = document.createElement('div');
    basemapControl.className = 'maplibregl-ctrl maplibregl-ctrl-group';
    basemapControl.innerHTML = `
      <button id="map-basemap-toggle" class="maplibregl-ctrl-icon tenali-control-button" title="Basemap: Satellite + Labels" style="width: 32px; height: 32px;">
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
      <button id="map-reset-view" class="maplibregl-ctrl-icon tenali-control-button" title="Reset View (Center on India)" style="width: 32px; height: 32px;">
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
      <button id="map-draw-aoi" class="maplibregl-ctrl-icon tenali-control-button" title="Select Area of Interest (Click and Drag)" style="width: 32px; height: 32px;">
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
      <button id="map-clear-aoi" class="maplibregl-ctrl-icon tenali-control-button" title="Clear Area of Interest" style="width: 32px; height: 32px; background-color: #dc2626 !important;">
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

    // Capture AOI button — enabled only after a rectangle is completed.
    const captureControl = document.createElement('div');
    captureControl.className = 'maplibregl-ctrl maplibregl-ctrl-group';
    captureControl.style.display = 'none';
    captureControl.innerHTML = `
      <button id="map-capture-aoi"
              class="maplibregl-ctrl-icon tenali-control-button"
              title="Capture AOI Snapshot"
              aria-label="Capture AOI Snapshot">
        <svg width="20" height="20" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 7h3l2-2h6l2 2h3v11H4z"/>
          <circle cx="12" cy="12" r="3.5"/>
        </svg>
      </button>
    `;
    this.map.getContainer().appendChild(captureControl);
    this.controls.captureAOIControl = captureControl;
    this.controls.captureAOIBtn =
      captureControl.querySelector('#map-capture-aoi');
    this.controls.captureAOIBtn.addEventListener('click', (event) => {
      event.stopPropagation();
      this.captureAOI();
    });

    captureControl.style.position = 'absolute';
    captureControl.style.top = '250px';
    captureControl.style.left = '10px';

    // Explicit positions: do not depend on MapLibre's internal control order.
    const positions = [
      [zoomControl, '10px'],
      [basemapControl, '50px'],
      [resetControl, '90px'],
      [drawControl, '130px'],
      [clearControl, '170px'],
      [captureControl, '210px']
    ];

    positions.forEach(([control, top]) => {
      control.style.position = 'absolute';
      control.style.top = top;
      control.style.left = '10px';
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
      if (this.controls.captureAOIControl) {
        this.controls.captureAOIControl.style.display =
          this.currentAOI ? 'block' : 'none';
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
      this.map.dragPan.disable();
      this.map.boxZoom.disable();
      this.map.doubleClickZoom.disable();
      this.map.touchZoomRotate.disable();
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
        this.map.dragPan.enable();
        this.map.boxZoom.enable();
        this.map.doubleClickZoom.enable();
        this.map.touchZoomRotate.enable();
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
      drawBtn.classList.remove('aoi-active');
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

    // Show AOI actions.
    if (this.controls.clearAOIControl) {
      this.controls.clearAOIControl.style.display = 'block';
    }
    if (this.controls.captureAOIControl) {
      this.controls.captureAOIControl.style.display = 'block';
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
    this.removeAOICapture();

    // If an older rectangle exists, remove it before drawing a new one.
    if (this.currentAOI) {
      this.clearAOI();
    }

    this.isDrawingAOI = true;
    this.map.getCanvas().style.cursor = 'crosshair';

    // Visual feedback: highlight the draw button
    const drawBtn = document.getElementById('map-draw-aoi');
    if (drawBtn) {
      drawBtn.classList.add('aoi-active');
    }

    console.log('[TenaliMap] Click and drag to draw rectangle AOI');
  }

  /**
   * Cancel an interrupted AOI drag.
   */
  cancelAOIDrawing() {
    this.isDrawingAOI = false;
    this.aoiStartPoint = null;

    if (this.map) {
      this.map.getCanvas().style.cursor = '';
      this.map.dragPan.enable();
      this.map.boxZoom.enable();
      this.map.doubleClickZoom.enable();
      this.map.touchZoomRotate.enable();
    }

    if (this.map?.getLayer('temp-aoi-fill')) this.map.removeLayer('temp-aoi-fill');
    if (this.map?.getLayer('temp-aoi-outline')) this.map.removeLayer('temp-aoi-outline');
    if (this.map?.getSource('temp-aoi')) this.map.removeSource('temp-aoi');

    document.getElementById('map-draw-aoi')?.classList.remove('aoi-active');
  }

  /**
   * Convert the current geographic AOI into map-canvas pixel bounds.
   */
  getAOIScreenBounds() {
    if (!this.currentAOI || !this.map) return null;

    const ring = this.currentAOI.geometry?.coordinates?.[0];
    if (!ring || ring.length < 4) return null;

    const points = ring.map(([lng, lat]) => this.map.project([lng, lat]));
    return {
      left: Math.min(...points.map(p => p.x)),
      top: Math.min(...points.map(p => p.y)),
      right: Math.max(...points.map(p => p.x)),
      bottom: Math.max(...points.map(p => p.y))
    };
  }

  /**
   * Capture the selected AOI from the rendered MapLibre canvas as a real PNG.
   * This is a visual map snapshot; the AOI GeoJSON remains the spatial record.
   */
  captureAOI() {
    if (!this.map || !this.currentAOI) return;

    const button = this.controls.captureAOIBtn;
    if (button) {
      button.disabled = true;
      button.title = 'Capturing…';
    }

    this.map.redraw();

    window.requestAnimationFrame(() => {
      try {
        const source = this.map.getCanvas();
        const bounds = this.getAOIScreenBounds();
        if (!bounds) throw new Error('Unable to calculate AOI pixel bounds.');

        const rect = source.getBoundingClientRect();
        const scaleX = source.width / Math.max(rect.width, 1);
        const scaleY = source.height / Math.max(rect.height, 1);

        let sx = Math.floor(bounds.left * scaleX);
        let sy = Math.floor(bounds.top * scaleY);
        let sw = Math.ceil((bounds.right - bounds.left) * scaleX);
        let sh = Math.ceil((bounds.bottom - bounds.top) * scaleY);

        sx = Math.max(0, Math.min(sx, source.width - 1));
        sy = Math.max(0, Math.min(sy, source.height - 1));
        sw = Math.max(1, Math.min(sw, source.width - sx));
        sh = Math.max(1, Math.min(sh, source.height - sy));

        // Prevent oversized output canvases on high-DPI displays.
        const maxDimension = 4096;
        const scale = Math.min(1, maxDimension / Math.max(sw, sh));
        const width = Math.max(1, Math.round(sw * scale));
        const height = Math.max(1, Math.round(sh * scale));

        const output = document.createElement('canvas');
        output.width = width;
        output.height = height;

        const ctx = output.getContext('2d');
        if (!ctx) throw new Error('Could not create snapshot canvas.');

        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(source, sx, sy, sw, sh, 0, 0, width, height);

        output.toBlob((blob) => {
          if (!blob) throw new Error('PNG encoding failed.');

          const file = new File(
            [blob],
            `tenali-aoi-${new Date().toISOString().replace(/[:.]/g, '-')}.png`,
            {type: 'image/png', lastModified: Date.now()}
          );

          if (this.aoiCapture?.url) URL.revokeObjectURL(this.aoiCapture.url);

          this.aoiCapture = {
            file,
            url: URL.createObjectURL(blob),
            width,
            height,
            geojson: this.currentAOI
          };

          this.renderAOICaptureCard();

          document.dispatchEvent(new CustomEvent('aoi-capture-ready', {
            detail: {
              file,
              url: this.aoiCapture.url,
              width,
              height,
              geojson: this.currentAOI
            }
          }));

          console.log('[TenaliMap] AOI snapshot captured:', file.name, file.size);

          if (button) {
            button.disabled = false;
            button.title = 'Recapture AOI Snapshot';
          }
        }, 'image/png');
      } catch (error) {
        console.error('[TenaliMap] AOI capture failed:', error);
        if (button) {
          button.disabled = false;
          button.title = 'Capture AOI Snapshot';
        }
        this.showAOICaptureError();
      }
    });
  }

  /**
   * Create a draggable thumbnail containing the actual PNG File.
   */
  renderAOICaptureCard() {
    if (!this.aoiCapture || !this.mapSection) return;

    document.getElementById('aoi-capture-card')?.remove();

    const card = document.createElement('div');
    card.id = 'aoi-capture-card';
    card.className = 'tenali-aoi-capture-card';
    card.draggable = true;

    card.innerHTML = `
      <div class="tenali-aoi-capture-preview-wrap">
        <img class="tenali-aoi-capture-preview"
             src="${this.aoiCapture.url}"
             alt="Captured AOI map snapshot">
      </div>
      <div class="tenali-aoi-capture-info">
        <div class="tenali-aoi-capture-title">AOI Snapshot</div>
        <div class="tenali-aoi-capture-meta">
          ${this.aoiCapture.width} × ${this.aoiCapture.height} · PNG
        </div>
        <div class="tenali-aoi-capture-hint">
          Drag into any image upload slot
        </div>
      </div>
      <button type="button"
              class="tenali-aoi-capture-download"
              title="Download AOI snapshot"
              aria-label="Download AOI snapshot">↓</button>
    `;

    card.querySelector('.tenali-aoi-capture-download')
      .addEventListener('click', (event) => {
        event.stopPropagation();
        this.downloadAOICapture();
      });

    card.addEventListener('dragstart', (event) => {
      if (!this.aoiCapture?.file || !event.dataTransfer) return;

      // File payload MUST be added synchronously during dragstart.
      event.dataTransfer.effectAllowed = 'copy';
      event.dataTransfer.items.add(this.aoiCapture.file);
      event.dataTransfer.setData('text/plain', 'TENALI_AOI_SNAPSHOT');
      card.classList.add('is-dragging');
    });

    card.addEventListener('dragend', () => {
      card.classList.remove('is-dragging');
    });

    this.mapSection.appendChild(card);
  }

  showAOICaptureError() {
    document.getElementById('aoi-capture-card')?.remove();

    if (!this.mapSection) return;
    const card = document.createElement('div');
    card.id = 'aoi-capture-card';
    card.className = 'tenali-aoi-capture-card tenali-aoi-capture-error';
    card.textContent =
      'AOI capture failed. Try a smaller selection and capture again.';
    this.mapSection.appendChild(card);
    window.setTimeout(() => card.remove(), 5000);
  }

  downloadAOICapture() {
    if (!this.aoiCapture?.url) return;
    const a = document.createElement('a');
    a.href = this.aoiCapture.url;
    a.download = this.aoiCapture.file?.name || 'tenali-aoi.png';
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  removeAOICapture() {
    document.getElementById('aoi-capture-card')?.remove();

    if (this.aoiCapture?.url) {
      URL.revokeObjectURL(this.aoiCapture.url);
    }

    this.aoiCapture = null;

    if (this.controls.captureAOIControl) {
      this.controls.captureAOIControl.style.display =
        this.currentAOI ? 'block' : 'none';
    }
  }

  /**
   * Clear AOI
   */
  clearAOI() {
    this.removeAOICapture();
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
    this.map.dragPan.enable();
    this.map.boxZoom.enable();
    this.map.doubleClickZoom.enable();
    this.map.touchZoomRotate.enable();

    if (this.controls.captureAOIControl) {
      this.controls.captureAOIControl.style.display = 'none';
    }

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
    // Highlight existing upload/drop areas while the real AOI PNG is dragged.
    const uploadSelectors = [
      'input[type="file"]',
      '[data-upload-slot]',
      '.upload-dropzone',
      '.drop-zone',
      '.upload-area',
      '.file-dropzone'
    ].join(',');

    document.addEventListener('dragover', (event) => {
      if (!this.aoiCapture?.file) return;
      if (!event.dataTransfer?.types?.includes('Files')) return;

      const target = event.target instanceof Element
        ? event.target.closest(uploadSelectors)
        : null;

      document.querySelectorAll('.tenali-aoi-drop-target')
        .forEach(el => el.classList.remove('tenali-aoi-drop-target'));

      if (target) {
        target.classList.add('tenali-aoi-drop-target');
      }
    });

    document.addEventListener('drop', (event) => {
      document.querySelectorAll('.tenali-aoi-drop-target')
        .forEach(el => el.classList.remove('tenali-aoi-drop-target'));
    }, true);

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
