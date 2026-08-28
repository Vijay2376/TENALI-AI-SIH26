/**
 * TENALI AI - Earth Observation Layer Inspector & Evidence Viewer
 * Clean, high-performance tabbed raster visualizer and comparative grid.
 */

window.initEvidenceViewer = function(containerId) {
  const root = document.getElementById(containerId);
  if (!root) return;

  const mainImg = root.querySelector('.viewer-main-image');
  const layerTabs = root.querySelectorAll('.layer-tab-btn');
  const layerTitleBadge = root.querySelector('.viewer-active-layer-title');
  const layerDescBadge = root.querySelector('.viewer-active-layer-desc');
  const stage = root.querySelector('.evidence-stage');
  const stageWrapper = root.querySelector('.viewer-stage-wrapper');
  const gridContainer = root.querySelector('.evidence-grid-view');
  const modeFocusBtn = root.querySelector('.viewer-mode-focus');
  const modeGridBtn = root.querySelector('.viewer-mode-grid');
  const openNewTabBtn = root.querySelector('.viewer-open-newtab');

  // Zoom & Pan state
  let zoomLevel = 1.0;
  let panX = 0;
  let panY = 0;
  let isPanning = false;
  let startX = 0;
  let startY = 0;

  function updateTransform() {
    if (mainImg) {
      mainImg.style.transform = `scale(${zoomLevel}) translate(${panX}px, ${panY}px)`;
      mainImg.style.transformOrigin = 'center center';
    }
    const zoomText = root.querySelector('.viewer-zoom-indicator');
    if (zoomText) {
      zoomText.textContent = `${Math.round(zoomLevel * 100)}%`;
    }
    if (stage) {
      if (zoomLevel > 1.0) {
        stage.classList.add('viewer-pan-grab');
      } else {
        stage.classList.remove('viewer-pan-grab', 'viewer-pan-grabbing');
      }
    }
  }

  function resetZoom() {
    zoomLevel = 1.0;
    panX = 0;
    panY = 0;
    updateTransform();
  }

  // 1. Layer Tab Switching
  layerTabs.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetUrl = btn.dataset.url;
      const layerName = btn.dataset.layerName || 'Satellite Layer';
      const layerDesc = btn.dataset.desc || '';

      if (!targetUrl || !mainImg) return;

      // Switch active tab styling
      layerTabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Update image with smooth transition
      mainImg.style.opacity = '0.2';
      const tempImg = new Image();
      tempImg.onload = () => {
        mainImg.src = targetUrl;
        mainImg.style.opacity = '1';
        resetZoom();
      };
      tempImg.src = targetUrl;

      // Update badges
      if (layerTitleBadge) layerTitleBadge.textContent = layerName;
      if (layerDescBadge) layerDescBadge.textContent = layerDesc;
      if (openNewTabBtn) openNewTabBtn.href = targetUrl;

      // Ensure we are in focused view
      if (stageWrapper && gridContainer && stageWrapper.classList.contains('hidden')) {
        stageWrapper.classList.remove('hidden');
        gridContainer.classList.add('hidden');
        if (modeFocusBtn) {
          modeFocusBtn.classList.add('bg-cyan-600', 'text-white');
          modeFocusBtn.classList.remove('bg-slate-800', 'text-slate-300');
        }
        if (modeGridBtn) {
          modeGridBtn.classList.remove('bg-cyan-600', 'text-white');
          modeGridBtn.classList.add('bg-slate-800', 'text-slate-300');
        }
      }
    });
  });

  // 2. View Mode Toggle (Focused Inspector vs Side-by-Side Multi-Grid)
  if (modeFocusBtn && modeGridBtn && stageWrapper && gridContainer) {
    modeFocusBtn.addEventListener('click', () => {
      stageWrapper.classList.remove('hidden');
      gridContainer.classList.add('hidden');
      modeFocusBtn.classList.add('bg-cyan-600', 'text-white');
      modeFocusBtn.classList.remove('bg-slate-800', 'text-slate-300');
      modeGridBtn.classList.remove('bg-cyan-600', 'text-white');
      modeGridBtn.classList.add('bg-slate-800', 'text-slate-300');
    });

    modeGridBtn.addEventListener('click', () => {
      stageWrapper.classList.add('hidden');
      gridContainer.classList.remove('hidden');
      modeGridBtn.classList.add('bg-cyan-600', 'text-white');
      modeGridBtn.classList.remove('bg-slate-800', 'text-slate-300');
      modeFocusBtn.classList.remove('bg-cyan-600', 'text-white');
      modeFocusBtn.classList.add('bg-slate-800', 'text-slate-300');
    });
  }

  // 3. Zoom Controls
  const zoomInBtn = root.querySelector('.viewer-zoom-in');
  const zoomOutBtn = root.querySelector('.viewer-zoom-out');
  const zoomResetBtn = root.querySelector('.viewer-zoom-reset');

  if (zoomInBtn) {
    zoomInBtn.addEventListener('click', () => {
      zoomLevel = Math.min(zoomLevel + 0.35, 4.0);
      updateTransform();
    });
  }

  if (zoomOutBtn) {
    zoomOutBtn.addEventListener('click', () => {
      zoomLevel = Math.max(zoomLevel - 0.35, 0.7);
      if (zoomLevel <= 1.0) {
        panX = 0;
        panY = 0;
      }
      updateTransform();
    });
  }

  if (zoomResetBtn) {
    zoomResetBtn.addEventListener('click', () => {
      resetZoom();
    });
  }

  // 4. Pan by Dragging when Zoomed
  if (stage) {
    stage.addEventListener('mousedown', (e) => {
      if (zoomLevel > 1.0) {
        isPanning = true;
        startX = e.clientX - panX;
        startY = e.clientY - panY;
        stage.classList.add('viewer-pan-grabbing');
        e.preventDefault();
      }
    });

    window.addEventListener('mouseup', () => {
      if (isPanning) {
        isPanning = false;
        if (stage) stage.classList.remove('viewer-pan-grabbing');
      }
    });

    window.addEventListener('mousemove', (e) => {
      if (isPanning && zoomLevel > 1.0) {
        panX = e.clientX - startX;
        panY = e.clientY - startY;
        updateTransform();
      }
    });

    // Touch support for Pan
    stage.addEventListener('touchstart', (e) => {
      if (zoomLevel > 1.0 && e.touches.length === 1) {
        isPanning = true;
        startX = e.touches[0].clientX - panX;
        startY = e.touches[0].clientY - panY;
      }
    }, { passive: true });

    window.addEventListener('touchend', () => {
      isPanning = false;
    });

    window.addEventListener('touchmove', (e) => {
      if (isPanning && zoomLevel > 1.0 && e.touches.length === 1) {
        panX = e.touches[0].clientX - startX;
        panY = e.touches[0].clientY - startY;
        updateTransform();
      }
    }, { passive: true });
  }

  // 5. Grid Card Click to Focus
  root.querySelectorAll('.grid-card-select-btn').forEach(cardBtn => {
    cardBtn.addEventListener('click', () => {
      const targetLayer = cardBtn.dataset.layerKey;
      if (targetLayer) {
        const correspondingTab = root.querySelector(`.layer-tab-btn[data-layer-key="${targetLayer}"]`);
        if (correspondingTab) {
          correspondingTab.click();
        }
      }
    });
  });

  // 6. Region Cluster Click to Highlight Grounded Layer
  root.querySelectorAll('.cluster-jump-btn').forEach(clusterBtn => {
    clusterBtn.addEventListener('click', () => {
      const targetTab = root.querySelector('.layer-tab-btn[data-layer-key="change_map"]') ||
                        root.querySelector('.layer-tab-btn[data-layer-key="annotated"]');
      if (targetTab) {
        targetTab.click();
        root.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    });
  });
};

