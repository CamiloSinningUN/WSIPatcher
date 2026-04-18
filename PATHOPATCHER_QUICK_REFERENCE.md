# PathoPatcher - Quick Reference Guide

## Module Quick Reference

### 🎯 Main PreProcessor (`patch_extraction/patch_extraction.py`)

**What it does**: Orchestrates entire WSI-to-patches pipeline

**Key Responsibilities**:
- Loads and validates configuration
- Manages WSI file discovery
- Handles annotation loading
- Selects hardware backend (cuCIM/OpenSlide)
- Generates tissue masks
- Extracts patches in parallel
- Manages output storage

**Key Methods**:
- `__init__(slide_processor_config)` - Initialize
- `sample_patches_dataset()` - Main entry point
- `_prepare_wsi()` - Prepare single WSI
- `process_queue()` - Process batch of patches
- `save_normalization_vector()` - Generate Macenko vectors

**Usage**:
```python
from pathopatch.cli import PreProcessingParser
from pathopatch.patch_extraction.patch_extraction import PreProcessor

# Load config
parser = PreProcessingParser()
config, logger = parser.get_config()

# Run preprocessing
processor = PreProcessor(slide_processor_config=config)
processor.sample_patches_dataset()
```

---

### ⚙️ Configuration System (`config/config.py` + `cli.py`)

**Key Types**:

1. **PreProcessingConfig** (Pydantic BaseModel)
   - `wsi_paths`: Path to WSI files
   - `output_path`: Output dataset location
   - `patch_size`: Patch dimensions (pixels)
   - `patch_overlap`: Percentage overlap (0-100)
   - `target_mpp` / `target_mag`: Resolution selection
   - `hardware_selection`: "cucim" or "openslide"
   - `normalize_stains`: Enable Macenko normalization
   - `processes`: Number of parallel workers

2. **Constants** (config.py):
   - `WSI_EXT`: [svs, tiff, tif, bif, scn, ndpi, vms, vmu, dcm]
   - `ANNOTATION_EXT`: [json]
   - `COLOR_DEFINITIONS`: 30+ colors for visualization
   - `COLOR_CODES_LOGGING`: Terminal colors

**Configuration Hierarchy**:
```
Default values
  ↓ overridden by
YAML config file
  ↓ overridden by  
CLI arguments
  ↓
Final configuration
```

---

### 🌍 WSI Interfaces (`wsi_interfaces/`)

**What they do**: Abstract slide reading backends

**Backends**:

| Backend | Library | Speed | Use Case |
|---------|---------|-------|----------|
| `DeepZoomGeneratorOS` | OpenSlide | Baseline | CPU-only, always available |
| `DeepZoomGeneratorCucim` | cuCIM | 5-10x faster | GPU acceleration, large datasets |
| `DeepZoomGeneratorDicom` | wsidicomizer | Variable | DICOM WSI format |

**Common Interface**:
```python
dzg.get_tile(level: int, address: tuple[int, int]) → PIL.Image
```

**Hardware Auto-Selection**:
```python
if hardware_selection == "cucim":
    Try: CuImage + OpenSlide metadata
    Fallback: OpenSlide only (if cuCIM unavailable)
else:
    Use OpenSlide exclusively
```

---

### 🔍 Patch Extraction Pipeline

**Key Steps** (in `sample_patches_dataset()`):

1. **Load WSI**: Open with backend (cuCIM/OpenSlide)
2. **Generate Tissue Mask**: Otsu thresholding on tissue
3. **Load Annotations**: Parse GeoJSON/XML polygons
4. **Find Patches**: Grid of tissue-rich coordinates
5. **Filter Patches**: By tissue ratio, annotation overlap
6. **Queue Patches**: Send to multiprocessing workers
7. **Save Patches**: Apply normalization, save with metadata

**Filtering Chain**:
```
All patch coordinates
  ↓
Filter: Tissue ratio > threshold
  ↓
Filter: Annotation intersection (if provided)
  ↓
Filter: Background ratio < max
  ↓
Queue for saving
```

---

### 📦 Storage (`patch_extraction/storage.py`)

**Output Directory Structure**:
```
output_path/
├── wsi_name_1/
│   ├── metadata.yaml              # WSI-level metadata
│   ├── patches/
│   │   ├── wsi_name_1_0_0.png     # Patch images
│   │   ├── wsi_name_1_0_1.png
│   │   └── ...
│   ├── metadata/                  # Per-patch metadata
│   │   ├── wsi_name_1_0_0.yaml    # Coordinates, tissue ratio, etc.
│   │   ├── wsi_name_1_0_1.yaml
│   │   └── ...
│   ├── tissue_masks/
│   │   ├── tissue_mask.png
│   │   └── otsu_mask.png
│   ├── thumbnails/
│   │   ├── thumbnail_256x256.png
│   │   └── ...
│   ├── annotation_masks/          # One mask per class
│   │   ├── class_tumor.png
│   │   ├── class_normal.png
│   │   └── ...
│   ├── context/                   # Multi-scale context
│   │   ├── scale_2x/
│   │   │   ├── context_0_0_2x.png
│   │   │   └── ...
│   │   └── scale_4x/
│   └── masks/                     # Segmentation masks
│       ├── wsi_name_1_0_0.npy
│       └── ...
└── wsi_name_2/
    └── ...
```

**Key Methods**:
- `save_meta_data()` - Save WSI metadata
- `save_masks()` - Save tissue masks
- `save_annotation_mask()` - Save class masks
- `save_thumbnails()` - Save thumbnails
- `save_elem_to_disk()` - Save patch + metadata
- `clean_up()` - Final cleanup

---

### 🧬 Tissue Detection & Masking (`utils/masking.py`)

**Main Function**: `generate_tissue_mask()`

**Parameters**:
- `tissue_tile`: Image as numpy array
- `mask_otsu`: Apply annotation mask before Otsu (default: False)
- `apply_prefilter`: Remove pen/marker artifacts (default: False)
- `otsu_annotation`: Which annotation to use for masking
- `polygons`: List of annotation polygons
- `region_labels`: Labels for polygons

**Algorithm** (when mask_otsu=False):
1. Convert to grayscale
2. (Optional) Apply prefilter
3. Apply Otsu thresholding
4. Return binary mask

**Algorithm** (when mask_otsu=True):
1. Filter polygons by `otsu_annotation` label
2. Create mask from filtered polygons
3. Apply mask to tissue tile
4. Apply Otsu on masked image
5. Return binary mask

---

### 🖼️ Image Filters (`utils/filters.py`)

**Available Filters**:
- `RedPenFilter` - Remove red pen markings
- `GreenPenFilter` - Remove green pen markings
- `BluePenFilter` - Remove blue pen markings
- `apply_mask_image()` - Apply binary mask to image

**Purpose**: Clean artifacts before tissue detection

---

### 🎲 Patch Utilities (`utils/patch_util.py`)

**Key Functions**:

```python
get_files_from_dir(path, file_type="svs")
    → List[Path] of WSI files

patch_to_tile_size(patch_size, tile_size)
    → Convert pixel coordinates to tile indices

target_mag_to_downsample(target_mag, base_mag)
target_mpp_to_downsample(target_mpp, slide_mpp)
    → Get pyramid level for magnification/mpp

get_regions_json(annotation_path)
get_regions_xml(annotation_path)
    → Parse annotations → List[Polygon]

macenko_normalization(image_list, vector_path)
    → Apply stain normalization to batch

calculate_background_ratio(image)
    → Percentage of white pixels

generate_thumbnails(slide, sizes)
    → Create thumbnails at multiple sizes

compute_interesting_patches(tissue_mask, patch_size, overlap)
    → Find tissue-rich patch coordinates
```

---

### 📊 PyTorch Dataset (`utils/patch_dataset.py`)

**Class**: `TissueDetectionDataset`

**Purpose**: Load extracted patches for PyTorch training/inference

**Usage**:
```python
from pathopatch.utils.patch_dataset import load_tissue_detection_dl
from torchvision.transforms import Compose

transforms = Compose([...])  # Your transforms
dataloader = load_tissue_detection_dl(
    patched_wsi_path="/path/to/patches",
    transforms=transforms
)

for image_batch, filenames in dataloader:
    # image_batch: torch.Tensor
    # filenames: list of str
    ...
```

---

### 🎨 Annotation Conversion (`annotation_conversion.py`)

**Main Function**: `convert_geojson_to_json()`

**Purpose**: Convert GeoJSON (QuPath, etc.) → Standardized JSON

**Features**:
- Parse GeoJSON FeatureCollections
- Extract polygon geometries
- Optional: merge outlines into tissue mask

**Usage**:
```python
from pathopatch.annotation_conversion import convert_geojson_to_json

convert_geojson_to_json(
    file_path="annotations.geojson",
    output_path="annotations.json",
    generate_tissue_outline=True
)
```

---

### 🧪 Stain Normalization Vectors (`macenko_vector_generation.py`)

**Purpose**: Pre-compute Macenko stain vectors for normalization

**Entry Point**: `MacenkoParser` CLI

**Workflow**:
1. Open reference WSI
2. Extract sample patches
3. Fit Macenko normalizer
4. Save vectors to JSON
5. Use in preprocessing pipeline

**Output Format**:
```json
{
  "hematoxylin": [0.65, 0.70, 0.29],
  "eosin": [0.07, 0.99, 0.11],
  "dab": [0.27, 0.57, 0.78]
}
```

**Usage in Pipeline**:
```yaml
normalize_stains: true
normalization_vector_json: "/path/to/macenko_vectors.json"
```

---

### 🔧 Base ML Classes (`base_ml/base_cli.py`)

**ABCParser** - Abstract base for configuration parsers

**Methods**:
- `get_config()` → (config_obj, logger)
- `store_config()` → Save config to disk

**Purpose**: Standardize parser interface for reproducibility

---

## Common Workflows

### Workflow 1: Basic Preprocessing (No Annotations)

```bash
python -m pathopatch.wsi_extraction \
  --wsi_paths /path/to/slides \
  --output_path /path/to/output \
  --patch_size 256 \
  --patch_overlap 0 \
  --target_mag 20 \
  --hardware_selection cucim \
  --processes 8
```

### Workflow 2: With Annotations

```yaml
# config.yaml
wsi_paths: /path/to/slides
output_path: /path/to/output
annotation_paths: /path/to/annotations
patch_size: 512
target_mag: 20
save_only_annotated_patches: true
store_masks: true
```

```bash
python -m pathopatch.wsi_extraction --config config.yaml
```

### Workflow 3: Stain Normalization

```bash
# Step 1: Generate normalization vectors
python -m pathopatch.macenko_vector_generation \
  --wsi_paths reference_slide.svs \
  --save_json_path macenko_vectors.json

# Step 2: Use in preprocessing
python -m pathopatch.wsi_extraction \
  --wsi_paths /path/to/slides \
  --output_path /path/to/output \
  --normalize_stains \
  --normalization_vector_json macenko_vectors.json
```

### Workflow 4: Context Patches (Multi-scale)

```yaml
wsi_paths: /path/to/slides
output_path: /path/to/output
patch_size: 256
context_scales: [2, 4, 8]  # 2x, 4x, 8x context
```

Output will include:
- `context/scale_2x/` - 512x512 patches
- `context/scale_4x/` - 1024x1024 patches
- `context/scale_8x/` - 2048x2048 patches

### Workflow 5: Annotation-Based Masking

```yaml
wsi_paths: /path/to/slides
output_path: /path/to/output
annotation_paths: /path/to/annotations
masked_otsu: true
otsu_annotation: "tissue"  # Use tissue annotation for masking
```

---

## Parameter Priority & Overrides

### Resolution Selection (Priority Order)
1. `target_mpp` (microns per pixel) - Highest priority
2. `target_mag` (magnification)
3. `downsample` (pyramid level divisor)
4. `level` (absolute pyramid level) - Lowest priority

```python
# If multiple specified, target_mpp wins
if target_mpp is set:
    Use target_mpp (overrides all others)
elif target_mag is set:
    Use target_mag
elif downsample is set:
    Use downsample
elif level is set:
    Use level
```

### Tissue Detection
- If `masked_otsu=True`: Annotation-based masking → Otsu
- If `masked_otsu=False`: Direct Otsu on tissue
- If `apply_prefilter=True`: Remove pen artifacts before Otsu

---

## Multiprocessing Architecture

**Main Thread** (PreProcessor):
- Generate patch coordinates
- Load images from backend
- Queue patches with metadata

**Worker Processes** (queue_worker):
- Dequeue patches
- Resize if size mismatch
- Apply stain normalization (if enabled)
- Extract context patches (if enabled)
- Save to disk

**Queue Flow**:
```
(image_array, coords, path, context_patches, target_size)
    ↓
queue_worker()
    ├─ Resize to target_size
    ├─ macenko_normalization() [if enabled]
    ├─ Extract context [if enabled]
    └─ storage.save_elem_to_disk()
```

---

## Performance Tuning

| Parameter | Impact | Recommendation |
|-----------|--------|-----------------|
| `hardware_selection="cucim"` | Speed ↑↑↑ | Use for large datasets |
| `processes=8+` | Speed ↑ | Adjust to CPU core count |
| `normalize_stains=True` | Speed ↓, Quality ↑ | Use for stain variation |
| `context_scales=[2,4,8]` | Storage ↑↑, Quality ↑ | Optional, increases disk/RAM |
| `patch_overlap=0` | Speed ↑, Coverage ↓ | Trade: speed vs. overlap |
| `masked_otsu=True` | Speed ↓, Accuracy ↑ | Use with good annotations |

---

## Error Handling

**Custom Exceptions**:
- `WrongParameterException` - Invalid configuration
- `UnalignedDataException` - Annotation/image mismatch

**Common Issues**:

| Issue | Cause | Solution |
|-------|-------|----------|
| Out of memory | Too many workers | Reduce `processes` |
| Slow processing | CPU bottleneck + cuCIM unavailable | Install cuCIM for GPU |
| Missing annotations | Mismatched naming/paths | Verify annotation filenames |
| Uneven intensity | No stain normalization | Enable `normalize_stains` |
| Low tissue patches | Otsu threshold too high | Use `masked_otsu` |
| Memory spike during normalization | Large batch normalization | Reduce batch size in config |

---

## Metadata Output

**Per-Patch YAML** (`metadata/wsi_name_0_0.yaml`):
```yaml
coordinates: [1024, 2048]          # (x, y) at level 0
magnification: 20
patch_size: 256
tissue_ratio: 0.92                 # Percentage of tissue
annotated: true
annotation_labels: [1, 2, 3]       # Class indices
background_ratio: 0.08
context:
  scale_2x: [...]                  # 512x512 image
  scale_4x: [...]                  # 1024x1024 image
```

**WSI-Level YAML** (`metadata.yaml`):
```yaml
wsi_name: slide_name
patch_count: 1250
magnification: 20
mpp: 0.5
dimensions: [40000, 50000]
tissue_coverage: 0.65
```

---

## Configuration Examples

### Example 1: Standard 20x Extraction
```yaml
patch_size: 512
target_mag: 20
hardware_selection: cucim
processes: 8
filter_patches: true
```

### Example 2: Annotated Tumor Dataset
```yaml
patch_size: 256
target_mag: 40
annotation_paths: /data/annotations
save_only_annotated_patches: true
store_masks: true
label_map_file: /data/label_map.json
```

### Example 3: Multi-scale with Normalization
```yaml
patch_size: 256
target_mag: 20
context_scales: [2, 4]
normalize_stains: true
normalization_vector_json: /data/macenko.json
```

### Example 4: Tissue-Masked Otsu
```yaml
patch_size: 512
masked_otsu: true
otsu_annotation: tissue
apply_prefilter: true
filter_patches: true
```

---

## Integration with PyTorch

```python
from torch.utils.data import DataLoader
from pathopatch.utils.patch_dataset import TissueDetectionDataset
from torchvision.transforms import Compose, ToTensor, Normalize

# Define transforms
transforms = Compose([
    ToTensor(),
    Normalize(mean=[0.485, 0.456, 0.406],
              std=[0.229, 0.224, 0.225])
])

# Load dataset
dataset = TissueDetectionDataset(
    patched_wsi_path="/path/to/extracted_patches",
    transforms=transforms
)

# Create DataLoader
dataloader = DataLoader(
    dataset,
    batch_size=32,
    shuffle=True,
    num_workers=4
)

# Train
for image_batch, filenames in dataloader:
    # image_batch: [B, C, H, W]
    # filenames: list of B strings
    predictions = model(image_batch)
```

