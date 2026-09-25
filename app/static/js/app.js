/**
 * TENALI AI - Frontend Client Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  setupModeSwitching();
  setupDragAndDrop();
  setupExampleChips();
});

function setupModeSwitching() {
  const modeInputs = document.querySelectorAll('input[name="mode_selector"]');
  const hiddenMode = document.getElementById('input-mode-hidden');
  const singleZone = document.getElementById('zone-single');
  const bitemporalZone = document.getElementById('zone-bitemporal');
  const opticalSarZone = document.getElementById('zone-optical-sar');

  function updateZoneInputs(mode) {
    if (singleZone) singleZone.classList.toggle('hidden', mode !== 'single');
    if (bitemporalZone) bitemporalZone.classList.toggle('hidden', mode !== 'bi_temporal');
    if (opticalSarZone) opticalSarZone.classList.toggle('hidden', mode !== 'optical_sar');
  }

  // Initial call
  updateZoneInputs(hiddenMode ? hiddenMode.value : 'single');

  modeInputs.forEach(radio => {
    radio.addEventListener('change', (e) => {
      const mode = e.target.value;
      if (hiddenMode) hiddenMode.value = mode;

      updateZoneInputs(mode);

      // Update active styling
      document.querySelectorAll('.mode-tab-label').forEach(lbl => {
        const isSelected = lbl.dataset.mode === mode;
        lbl.classList.toggle('bg-cyan-950', isSelected);
        lbl.classList.toggle('text-cyan-400', isSelected);
        lbl.classList.toggle('border-cyan-500', isSelected);
        lbl.classList.toggle('text-slate-400', !isSelected);
        lbl.classList.toggle('border-slate-800', !isSelected);
      });
    });
  });

  // Global HTMX error interceptor to ensure error messages are always rendered
  document.body.addEventListener('htmx:responseError', (evt) => {
    const resultContainer = document.getElementById('result-container');
    if (resultContainer) {
      let msg = 'Analysis request could not be processed.';
      try {
        const data = JSON.parse(evt.detail.xhr.responseText);
        if (data.detail) msg = data.detail;
      } catch (e) {
        if (evt.detail.xhr.responseText) {
          msg = evt.detail.xhr.responseText;
        }
      }
      resultContainer.innerHTML = `
        <div class="bg-red-950/80 border border-red-800 rounded-2xl p-6 shadow-xl space-y-3 animate-fade-in">
          <div class="flex items-start gap-3">
            <div class="w-8 h-8 rounded-lg bg-red-900/80 border border-red-700 flex items-center justify-center text-red-400 shrink-0">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
            </div>
            <div class="space-y-1">
              <h3 class="text-sm font-bold text-red-200 uppercase tracking-wide">Analysis Error</h3>
              <p class="text-sm text-red-300 leading-relaxed font-medium">${msg}</p>
            </div>
          </div>
        </div>
      `;
      resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  });

  // Client-side form pre-validation
  const form = document.getElementById('analyze-form');
  if (form) {
    form.addEventListener('htmx:configRequest', (evt) => {
      const mode = hiddenMode ? hiddenMode.value : 'single';
      let missingMsg = '';

      if (mode === 'single') {
        const input = document.querySelector('#zone-single input[type="file"]');
        if (!input || !input.files || input.files.length === 0) {
          missingMsg = 'Please select a satellite image to analyze in Single Image mode.';
        }
      } else if (mode === 'bi_temporal') {
        const t1 = document.querySelector('input[name="t1"]');
        const t2 = document.querySelector('input[name="t2"]');
        if (!t1?.files?.length || !t2?.files?.length) {
          missingMsg = 'Bi-Temporal Change analysis requires both Time 1 (T1) and Time 2 (T2) images.';
        }
      } else if (mode === 'optical_sar') {
        const opt = document.querySelector('input[name="optical"]');
        const sar = document.querySelector('input[name="sar"]');
        if (!opt?.files?.length || !sar?.files?.length) {
          missingMsg = 'Optical + SAR analysis requires both Optical and SAR images.';
        }
      }

      if (missingMsg) {
        evt.preventDefault();
        const resultContainer = document.getElementById('result-container');
        if (resultContainer) {
          resultContainer.innerHTML = `
            <div class="bg-red-950/80 border border-red-800 rounded-2xl p-6 shadow-xl space-y-3 animate-fade-in">
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-lg bg-red-900/80 border border-red-700 flex items-center justify-center text-red-400 shrink-0">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                </div>
                <div class="space-y-1">
                  <h3 class="text-sm font-bold text-red-200 uppercase tracking-wide">Image Input Required</h3>
                  <p class="text-sm text-red-300 leading-relaxed font-medium">${missingMsg}</p>
                </div>
              </div>
            </div>
          `;
          resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }
    });
  }
}

function setupDragAndDrop() {
  const dropzones = document.querySelectorAll('.dropzone-container');

  dropzones.forEach(zone => {
    const input = zone.querySelector('input[type="file"]');
    const previewContainer = zone.querySelector('.dropzone-preview');
    const promptContainer = zone.querySelector('.dropzone-prompt');

    if (!input) return;

    ['dragenter', 'dragover'].forEach(eventName => {
      zone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.add('border-cyan-400', 'bg-cyan-950/20');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      zone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove('border-cyan-400', 'bg-cyan-950/20');
      });
    });

    zone.addEventListener('drop', (e) => {
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        try {
          const dt = new DataTransfer();
          dt.items.add(file);
          input.files = dt.files;
        } catch (err) {
          input.files = e.dataTransfer.files;
        }
        handleFileSelection(file, previewContainer, promptContainer);
      }
    });

    input.addEventListener('change', () => {
      if (input.files && input.files.length > 0) {
        handleFileSelection(input.files[0], previewContainer, promptContainer);
      }
    });
  });
}

function handleFileSelection(file, previewContainer, promptContainer) {
  if (!file || !previewContainer || !promptContainer) return;

  const fileName = file.name;
  const fileSizeKb = (file.size / 1024).toFixed(1);
  const ext = fileName.split('.').pop().toUpperCase();

  if (file.type.startsWith('image/') || fileName.endsWith('.png') || fileName.endsWith('.jpg') || fileName.endsWith('.jpeg')) {
    const reader = new FileReader();
    reader.onload = (e) => {
      previewContainer.innerHTML = `
        <div class="relative w-full h-36 rounded-lg bg-space-950 overflow-hidden flex flex-col items-center justify-center border border-cyan-700/60 p-1 group">
          <img src="${e.target.result}" class="max-h-24 max-w-full object-contain rounded" alt="Preview" />
          <div class="mt-1 w-full bg-space-900/90 rounded px-2 py-0.5 flex items-center justify-between text-[11px] font-mono">
            <span class="text-cyan-300 truncate max-w-[130px]" title="${fileName}">${fileName}</span>
            <span class="text-slate-400 text-[10px] shrink-0">${fileSizeKb} KB</span>
          </div>
          <div class="text-[10px] text-cyan-400/80 font-mono mt-0.5">Click to replace</div>
        </div>
      `;
      previewContainer.classList.remove('hidden');
      promptContainer.classList.add('hidden');
    };
    reader.readAsDataURL(file);
  } else {
    // GeoTIFF or non-browser standard raster
    previewContainer.innerHTML = `
      <div class="w-full h-36 rounded-lg bg-space-950 border border-cyan-700/60 flex flex-col items-center justify-center p-3 text-center">
        <svg class="w-8 h-8 text-cyan-400 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
        <span class="text-xs font-mono font-semibold text-slate-200 truncate w-full" title="${fileName}">${fileName}</span>
        <div class="flex items-center gap-1.5 mt-1">
          <span class="px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-400 font-mono text-[10px] font-bold">${ext}</span>
          <span class="text-[11px] text-slate-400">${fileSizeKb} KB</span>
        </div>
        <span class="text-[10px] text-slate-500 mt-1">Click to replace</span>
      </div>
    `;
    previewContainer.classList.remove('hidden');
    promptContainer.classList.add('hidden');
  }
}

function setupExampleChips() {
  document.querySelectorAll('.query-example-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const queryText = chip.dataset.query;
      const targetMode = chip.dataset.mode;
      const queryInput = document.getElementById('query-input');

      if (queryInput && queryText) {
        queryInput.value = queryText;
        queryInput.focus();
      }

      if (targetMode) {
        const radio = document.querySelector(`input[name="mode_selector"][value="${targetMode}"]`);
        if (radio) {
          radio.checked = true;
          radio.dispatchEvent(new Event('change'));
        }
      }
    });
  });
}

// AOI (Area of Interest) handling
let currentAOI = null;

document.addEventListener('aoi-changed', (e) => {
  currentAOI = e.detail.hasAOI ? e.detail.geojson : null;
  console.log('[App] AOI changed:', currentAOI ? 'AOI selected' : 'AOI cleared');

  // Could add visual indicator that AOI is selected
  // Could enable a special "Analyze Selected Area" button
  // For now, AOI is just stored for potential future use
});

// Export for map to access if needed
window.getCurrentAOI = function() {
  return currentAOI;
};
