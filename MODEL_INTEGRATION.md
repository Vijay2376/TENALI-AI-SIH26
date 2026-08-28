# TENALI AI — Model Integration Guide

> **Developer Guide for Upgrading Demo Adapters to Real Remote-Sensing Deep Learning Foundation Models**

---

## 1. Overview & Integration Philosophy

TENALI AI enforces a strict architectural boundary between **Tool Interfaces** (`app/tools/`) and **Model Implementations** (`app/adapters/`). The agent orchestrator and web frontend interact exclusively through tool contracts. 

Replacing a lightweight demo adapter with a GPU-accelerated deep learning model requires **zero changes** to the agent or frontend.

---

## 2. Integration Specifications

### 🛰️ Capability 1: Visual Question Answering (VQA / VLM)

| Parameter | Specification |
|---|---|
| **Current Implementation** | `DemoVQAAdapter` (`app/adapters/demo_vqa.py`) + `RemoteSensingAdaptationService` |
| **Execution Mode** | `REAL EO ADAPTED MODEL` |
| **Adapter Target File** | `app/adapters/real/vlm_adapter.py` |
| **Target Class** | `RealRemoteSensingVLMAdapter` |
| **Recommended Models** | **GeoChat-7B**, **SkyEyeGPT**, **RSGPT**, **EarthGPT** |
| **Input Signature** | `rgb_arr: np.ndarray (H, W, 3)`, `query: str`, `metadata: dict` |
| **Output Signature** | `{"answer": str, "confidence_estimate": float, "adapter": str, "execution_mode": str}` |

#### Step-by-Step Integration Steps:
1. Install `transformers`, `torch`, `accelerate`:
   ```bash
   pip install torch torchvision transformers accelerate
   ```
2. Download model checkpoint (e.g. `MBZUAI/geochat-7b` from Hugging Face).
3. In `app/adapters/real/vlm_adapter.py`, implement `load_model()`:
   ```python
   from transformers import AutoModelForCausalLM, AutoTokenizer
   import torch

   class RealRemoteSensingVLMAdapter(BaseAdapter):
       def load_model(self):
           self.tokenizer = AutoTokenizer.from_pretrained("MBZUAI/geochat-7b")
           self.model = AutoModelForCausalLM.from_pretrained(
               "MBZUAI/geochat-7b",
               torch_dtype=torch.float16,
               device_map="auto"
           )
           self.is_loaded = True
   ```
4. Register the new adapter in `app/agent/registry.py`:
   ```python
   from app.adapters.real.vlm_adapter import RealRemoteSensingVLMAdapter
   self.register(VQATool(adapter=RealRemoteSensingVLMAdapter()))
   ```

---

### 🎯 Capability 2: Text-Guided Region Grounding

| Parameter | Specification |
|---|---|
| **Current Implementation** | `DemoGroundingAdapter` (`app/adapters/demo_grounding.py`) |
| **Execution Mode** | `IMAGE PROCESSING` |
| **Adapter Target File** | `app/adapters/real/grounding_dino.py` |
| **Target Class** | `RealGroundingDINOAdapter` |
| **Recommended Models** | **Grounding DINO** (fine-tuned on DIOR / DOTA / RSOD datasets) |
| **Input Signature** | `rgb_arr: np.ndarray (H, W, 3)`, `target_query: str`, `metadata: dict` |
| **Output Signature** | `{"mask": np.ndarray (H, W), "boxes": list[RegionBox], "adapter": str}` |

#### Step-by-Step Integration Steps:
1. Install Grounding DINO dependencies:
   ```bash
   pip install groundingdino-py
   ```
2. Load checkpoint weights in `RealGroundingDINOAdapter.load_model()`.
3. In `run()`, tokenize `target_query`, run object detection forward pass, filter boxes by box threshold (e.g., 0.35), and format into `RegionBox` instances.

---

### 🔄 Capability 3: Bi-Temporal Change Detection

| Parameter | Specification |
|---|---|
| **Current Implementation** | `DemoChangeDetectionAdapter` (`app/adapters/demo_change.py`) |
| **Execution Mode** | `IMAGE PROCESSING` |
| **Adapter Target File** | `app/adapters/real/change_former.py` |
| **Target Class** | `RealChangeFormerAdapter` |
| **Recommended Models** | **ChangeFormerV6**, **SNUNet-CD**, **BIT (Bitemporal Image Transformer)** |
| **Input Signature** | `t1_rgb: np.ndarray`, `t2_rgb: np.ndarray`, `query: str`, `metadata_t1: dict`, `metadata_t2: dict` |
| **Output Signature** | `{"change_mask": np.ndarray (H, W), "diff_magnitude": np.ndarray, "regions": list[RegionBox], "statistics": ChangeStatistics}` |

#### Step-by-Step Integration Steps:
1. Package Siamese transformer architecture into PyTorch module.
2. Feed normalized $(T_1, T_2)$ tensor pair of shape `(1, 6, H, W)` or `((1, 3, H, W), (1, 3, H, W))`.
3. Apply Sigmoid activation on predicted logits $\to$ binary change mask thresholded at 0.5.

---

### 🛰️ Capability 4: Optical + SAR Cross-Modal Fusion

| Parameter | Specification |
|---|---|
| **Current Implementation** | `DemoOpticalSARAdapter` (`app/adapters/demo_optical_sar.py`) |
| **Execution Mode** | `HEURISTIC` |
| **Recommended Architecture** | **Dual-Stream Cross-Attention Multimodal Transformer** |
| **Input Signature** | `optical_rgb: np.ndarray (H, W, 3)`, `sar_rgb: np.ndarray (H, W, 1)`, `query: str` |
| **Output Signature** | `{"optical_processed": True, "sar_processed": True, "fused_thematic_map": np.ndarray, "fusion_summary": dict}` |

---

## 📊 3. Benchmark Dataset Evaluation Integration Points

TENALI AI is architecturally structured to plug into standard remote-sensing benchmarks:

1. **BigEarthNet**: Multi-spectral land-cover evaluation across Sentinel-2 and Sentinel-1 patches.
2. **VRSBench / RSVQA**: Visual Question Answering accuracy metrics on high-resolution satellite imagery.
3. **CDVQA**: Change Detection Visual Question Answering benchmarks.
4. **ISRO Cartosat-2S & RISAT Evaluation**: High-resolution Indian space mission optical and C-band SAR datasets.

To add benchmark evaluation scripts, implement evaluation runners under `tests/benchmarks/` calling `orchestrator.analyze()` on benchmark test splits.
