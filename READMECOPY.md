<<<<<<< HEAD
# TENALI AI

> **"Ask the Earth. Understand the Change."**  
> **Smart India Hackathon 2026 (SIH 26167)** &bull; **Theme:** Space Technology &bull; **Category:** Software  
> *An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Natural Language Text Queries*

---

## 🛰️ 1. What is TENALI AI?

Traditional remote-sensing AI systems operate in silos: users must manually choose sensor types, decide on pre-processing pipelines, pick GIS algorithms, configure radiometric thresholds, and select isolated task models (classification, change detection, VQA, or segmentation).

**TENALI AI** introduces a **Query-Driven Agentic Orchestration Pipeline** that abstracts this complexity behind natural language. Users simply upload satellite imagery (Single Scene, Bi-Temporal Pair, or Optical + SAR Pair) and ask questions in plain English. TENALI AI validates the input, extracts geospatial metadata, dynamically routes the query to specialist tools, executes domain-adapted remote-sensing analysis, renders multi-layer visual evidence, estimates confidence, and synthesizes a grounded answer with an auditable execution trace.

```
USER
  ↓
IMAGE INPUT (GeoTIFF / TIFF / PNG / JPG)
  ↓
INPUT VALIDATION & GEOSPATIAL INGESTION (Rasterio / Tifffile / Shapely)
  ↓
QUERY UNDERSTANDING & DUAL-ENGINE ROUTING (Gemini API / Local Pattern Router)
  ↓
AGENTIC TASK PLANNING & SPECIALIST TOOL SELECTION
  ↓
SPECIALIST REMOTE-SENSING ANALYSIS (Adapters & Real Image Processing)
  ↓
DOMAIN ADAPTATION (BigEarthNet-19 Multi-Spectral Classifier)
  ↓
MULTI-LAYER EVIDENCE GENERATION (Masks, Heatmaps, Bounding Boxes, Collages)
  ↓
ANSWER SYNTHESIS + CONFIDENCE ESTIMATE + AUDITABLE EXECUTION TRACE
  ↓
INTERACTIVE EARTH OBSERVATION CONSOLE (FastAPI + Jinja2 + HTMX + Tailwind)
```

---

## ⚡ 2. Key Capabilities & Innovations

1. **Strictly Python-First**: Built entirely with FastAPI, Jinja2, HTMX, Tailwind CSS, and Vanilla JS for interactive canvas raster manipulation. Zero React/Node dependencies.
2. **Real Remote-Sensing Domain Adaptation**: Implements a concrete, active domain adaptation classifier trained on the **BigEarthNet-19 nomenclature** (Sentinel-2 / CORINE Land Cover taxonomy) and multi-spectral spectral-spatial distributions.
3. **Multi-Input Configurations**:
   - **Single Image**: Visual Question Answering (VQA), Scene Description, and Text-Guided Region Grounding.
   - **Bi-Temporal Pair ($T_1 + T_2$)**: Differential change detection, structural texture shifts, change statistics (pixel percentage, hectares, trends), and change heatmaps.
   - **Optical + SAR Pair**: Genuine dual-stream cross-modal fusion combining optical spectral reflectance with SAR radar backscatter (specular reflection, double-bounce structures, and volume scattering).
4. **Interactive Multi-Layer Visualizer**: Built-in split-screen swipe comparison slider, opacity cross-fader, pan/zoom controls, and bounding box cluster inspector.
5. **Auditable Execution Trace**: Granular millisecond telemetry logging every pipeline step, tool dispatched, and adapter used.
6. **Zero-Key Offline Demo Mode**: Fully functional deterministic demo adapters and local rule-based routing when `GEMINI_API_KEY` is not provided (`TENALI_DEMO_MODE=true`).
7. **Comprehensive Audit Reports**: One-click generation of printable HTML and downloadable JSON telemetry reports.

---

## 🛠️ 3. Technology Stack

- **Backend Framework**: FastAPI 0.136.3, Uvicorn, Pydantic v2, Pydantic Settings
- **Frontend / UI**: Jinja2 Templates, HTMX 1.9.12, Tailwind CSS, Vanilla JavaScript
- **Remote Sensing & Computer Vision**: `tifffile`, `Pillow`, `OpenCV` (Headless), `NumPy`, `Shapely`
- **Domain Adaptation & Machine Learning**: `scikit-learn` (ExtraTrees / Random Forest on BigEarthNet spectral-spatial distributions)
- **Generative AI / LLM Reasoning**: Google Gemini API (`google-genai` SDK) with offline fallback
- **Testing & Verification**: `pytest`, `httpx`

---

## 🚀 4. Quick Start & Installation

### Prerequisites
- Python 3.11+ (tested on Python 3.13)
- Windows, Linux, or macOS

### Step 1: Clone and Create Virtual Environment
```bash
# Navigate to project directory
cd d:/agpyp

# Create isolated virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*Note: If you have a Google Gemini API Key, set `GEMINI_API_KEY=your_key_here`. If left empty, TENALI AI automatically operates in deterministic local routing and demo adapter mode.*

### Step 4: Run the Application
```bash
python run.py
```
Open your browser and navigate to: **`http://127.0.0.1:8000`**

---

## 🎯 5. The 5 Mandatory SIH Demonstrations

TENALI AI includes pre-packaged synthetic remote-sensing datasets in `demo_data/` accessible via the **One-Click SIH Demonstrations** panel on the dashboard:

| # | Demo Title | Input Modality | Query | Workflow Executed |
|---|---|---|---|---|
| **1** | **Single Image VQA** | Optical / Multispectral GeoTIFF | *"Describe the land-cover and major objects visible in this image."* | `Input Validation` $\to$ `BigEarthNet Domain Adaptation` $\to$ `Spectral Metrics` $\to$ `Grounded Answer` $\to$ `Trace` |
| **2** | **Text-Guided Grounding** | Optical GeoTIFF | *"Highlight the water body."* | `Input Validation` $\to$ `Spectral Index Thresholding` $\to$ `Morphological Contours` $\to$ `Bounding Boxes` $\to$ `Overlay Mask` |
| **3** | **Bi-Temporal Change** | $T_1 + T_2$ Pair | *"What changed between these two dates?"* | `Co-Registration` $\to$ `Differential Magnitude` $\to$ `Adaptive Thresholding` $\to$ `Connected Components` $\to$ `Change Map` |
| **4** | **Built-up Structural Trend** | $T_1 + T_2$ Pair | *"Has the built-up area increased, decreased, or remained unchanged?"* | `Bi-Temporal Alignment` $\to$ `Texture Gradient Shift` $\to$ `Luminance Differential` $\to$ `Approximate Trend Inference` |
| **5** | **Optical + SAR Fusion** | Optical + SAR Co-registered Pair | *"Use the optical and SAR images together to identify built-up and water-covered regions."* | `Optical Feature Stream` $\to$ `SAR Radar Backscatter Stream` $\to$ `Synergistic Cross-Modal Fusion` $\to$ `Thematic Map` |

---

## 📡 6. API Documentation

Interactive OpenAPI documentation is available at **`/docs`** or **`/redoc`**.

### Key Endpoints:
- `GET /health`: System readiness, active adapters, and telemetry.
- `GET /capabilities`: Supported modalities, task taxonomy, and registered tool list.
- `POST /analyze`: Primary multimodal analysis endpoint supporting multipart file uploads (`query`, `mode`, `images` / `t1` / `t2` / `optical` / `sar`).
- `GET /demo/presets`: Returns list of pre-configured demo scenarios.
- `POST /demo/run-preset`: Executes a demo preset with synthetic sample data.
- `GET /reports/{report_id}`: Printable HTML audit report.
- `GET /reports/{report_id}/json`: Full JSON telemetry export.

---

## ⚖️ 7. Technical Honesty & Scientific Disclaimers

In accordance with strict hackathon scientific integrity standards:
- **Confidence Estimates**: Confidence scores are clearly presented as *heuristic/uncalibrated confidence estimates*.
- **Domain Adaptation Attribution**: The domain adaptation module is attributed explicitly to the *BigEarthNet-19 empirical spectral-spatial distribution model*.
- **Built-up Change Inference**: Labeled as *Approximate Built-up Inference (Heuristic)*.
- **Execution Mode Badges**: Every result prominently displays its execution mode: `REAL EO ADAPTED MODEL`, `IMAGE PROCESSING`, `HEURISTIC`, or `DEMO ADAPTER`.

---

## 🧪 8. Automated Test Suite

Run the automated test suite with pytest:
```bash
.venv\Scripts\pytest -v
```
The suite tests:
1. Application startup and health check endpoints
2. GeoTIFF parsing and metadata extraction
3. BigEarthNet domain adaptation classification
4. Single-image VQA and text-guided grounding
5. Bi-temporal change detection and change statistics
6. Dual-stream Optical + SAR cross-modal fusion
7. Error handling (invalid modes, missing second images, unsupported formats)
8. End-to-end execution of all 5 demo workflows.
=======
# TENALI-AI-SIH26
>>>>>>> 39be49f7d45bd21811f652253d8504a83ad2c67b
