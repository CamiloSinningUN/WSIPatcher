# PathoPatcher Library Architecture

## Overview

PathoPatcher is a comprehensive pipeline for preprocessing whole slide images (WSIs) to extract patches for machine learning tasks. It's a production-grade tool designed for digital pathology workflows with support for multiple WSI formats, annotation systems, and stain normalization techniques.

**Main Goal**: Convert large WSI files → organized dataset of image patches with metadata, annotations, and quality filtering

---

## Core Modules

### 1. **Configuration System** (`glasscut/config/`)

**Purpose**: Manage preprocessing configuration parameters and validation

#### Key Components:

##### `config.py` - Internal Constants
- `WSI_EXT`: Supported WSI formats (svs, tiff, tif, bif, scn, ndpi, vms, vmu, dcm)
- `ANNOTATION_EXT`: Supported annotation formats (json)
- `LOGGING_EXT`: Logging levels
- `COLOR_DEFINITIONS`: 30+ color palette for annotations
- `COLOR_CODES_LOGGING`: Terminal color codes for log messages

##### `PreProcessingConfig` (Pydantic BaseModel)
- **Role**: Main configuration object for pipeline
- **Responsibilities**:
  - Validates all parameters
  - Converts string paths to `pathlib.Path` objects
  - Manages 50+ preprocessing options

**Key Configuration Groups**:

1. **Dataset Paths**:
   - `wsi_paths`: Location of WSI files
   - `output_path`: Output dataset directory
   - `annotation_paths`: Location of annotation files

2. **Patch Extraction**:
   - `patch_size`: Pixel size of extracted patches (e.g., 256)
   - `patch_overlap`: Percentage overlap between adjacent patches (0-100)
   - `target_mpp` / `target_mag` / `downsample` / `level`: Resolution selection
   - `context_scales`: Multi-scale context patches

3. **Annotation Handling**:
   - `annotation_paths`: Path to annotations
   - `incomplete_annotations`: Allow partial slide coverage
   - `label_map_file`: Map class names to indices
   - `save_only_annotated_patches`: Only extract within annotated regions
   - `overlapping_labels`: Handle overlapping annotations

4. **Tissue Detection**:
   - `masked_otsu`: Use masked Otsu thresholding
   - `otsu_annotation`: Annotation label for masking
   - `filter_patches`: Remove background patches
   - `apply_prefilter`: Pre-filter before thresholding

5. **Stain Normalization** (Macenko):
   - `normalize_stains`: Enable stain normalization
   - `normalization_vector_json`: Reference stain vectors
   - `adjust_brightness`: Post-normalize brightness

6. **Hardware & Logging**:
   - `hardware_selection`: "cucim" (GPU) or "openslide" (CPU)
   - `log_level`: Verbosity level
   - `processes`: Number of parallel workers

---

### 2. **CLI & Entry Points** (`cli.py`, `wsi_extraction.py`, `macenko_vector_generation.py`)

**Purpose**: Command-line interfaces for different workflows

#### Main Entry Points:

##### `wsi_extraction.py` - Main Pipeline
```
Command: python -m pathopatch.wsi_extraction \
  --wsi_paths /path/to/wsi \
  --output_path /path/to/output \
  --config config.yaml
```

**Workflow**:
1. Parse CLI arguments + YAML config
2. Create `PreProcessor` instance
3. Call `slide_processor.sample_patches_dataset()`
4. Output: Structured dataset with patches + metadata

##### `macenko_vector_generation.py` - Stain Vector Computation
```
Command: python -m pathopatch.macenko_vector_generation \
  --wsi_paths slide.svs \
  --save_json_path macenko_vectors.json
```

**Purpose**: Pre-compute stain normalization vectors from a reference slide

##### Configuration Hierarchy:
```
CLI args
  ↓ overrides
YAML config
  ↓ defaults to
PreProcessingConfig (Pydantic model)
```

---

### 3. **WSI Interfaces** (`wsi_interfaces/`)

**Purpose**: Abstraction layer for different slide reading backends

#### Backend Architecture

All backends provide a **DeepZoomGenerator** interface:

##### `DeepZoomGeneratorOS` (OpenSlide Backend)
- **Library**: OpenSlide (CPU-based)
- **Formats**: SVS, TIFF, NDPI, BIF, SCN, VMS, VMU
- **Wrapper**: Extends OpenSlide's DeepZoomGenerator with compatible API
- **Key method**: `get_tile(level, address) → PIL.Image`

```python
dzg = DeepZoomGeneratorOS(openslide_obj, tile_size=254, overlap=1)
tile = dzg.get_tile(level=3, address=(10, 20))
```

##### `DeepZoomGeneratorCucim` (cuCim GPU Backend)
- **Library**: NVIDIA cuCim (GPU-accelerated)
- **Performance**: 5-10x faster than OpenSlide
- **Requirements**: NVIDIA GPU + cuCIM installation
- **Metadata**: Uses OpenSlide for metadata, cuCIM for image data

**Key Features**:
- `preferred_memory_capacity()`: Optimize GPU memory usage
- `cache`: Per-process GPU memory cache
- `get_tile()`: Returns cached tiles from GPU

```python
dzg = DeepZoomGeneratorCucim(
    meta_loader=openslide_obj,
    image_loader=cucim_obj,
    tile_size=254
)
```

##### `DeepZoomGeneratorDicom` (DICOM Backend)
- **Library**: wsidicomizer (converts DICOM to OpenSlide format)
- **Use case**: DICOM format WSIs
- **Implementation**: Wraps DICOM slides with OpenSlide interface

#### Backend Selection Logic:
```python
# In PreProcessor._set_hardware()
if hardware_selection == "cucim":
    Try: Load CuImage + OpenSlide metadata
    Fallback: Use OpenSlide if cuCIM not available
else:
    Use OpenSlide only
```

---

### 4. **Patch Extraction** (`patch_extraction/`)

**Purpose**: Core logic for extracting patches from WSI with quality filtering

#### Main Class: `PreProcessor`

**Initialization**:
- Loads configuration
- Sets up WSI paths
- Loads annotations
- Initializes backends
- Sets up tissue detector (if needed)

**Key Attributes**:
```python
slide_processor_config          # PreProcessingConfig instance
wsi_paths                       # List[Path] to WSI files
annotation_files_dict           # Dict[str, List[Path]] by slide name
output_path                     # Path for output dataset
storage                         # Storage instance
deep_zoom_generator             # DeepZoomGenerator (OS or cuCIM)
detector_device                 # "cpu" or "cuda"
detector_model                  # Tissue detection model (if used)
curr_wsi_level                  # Current pyramid level
```

**Main Methods**:

##### `sample_patches_dataset()`
Main entry point that orchestrates the complete pipeline:

```
For each WSI:
  1. _prepare_wsi()
     ├─ Open slide with backend
     ├─ Generate tissue mask
     ├─ Generate annotation masks
     └─ Generate thumbnails
  
  2. process_queue()
     ├─ Extract patch coordinates
     ├─ Filter by tissue
     ├─ Filter by annotations
     └─ Queue for saving
  
  3. Save to Storage
     ├─ Apply stain normalization
     ├─ Extract context patches
     └─ Save patch + metadata
```

##### `_prepare_wsi() → (dimensions, masks, generator, annotations)`
Prepares a WSI for patch extraction:
1. Opens WSI with appropriate backend
2. Computes tissue mask (Otsu or masked)
3. Computes annotation masks
4. Creates thumbnail
5. Returns all masks and Deep Zoom generator

##### `process_queue(batch, wsi_file, metadata, level, ...)`
Processes a batch of patch coordinates:
1. Validates coordinates
2. Checks tissue intersection
3. Checks annotation intersection
4. Computes patch statistics
5. Queues for storage with metadata

**Parallel Processing**:
```
Main process:
  Generate patch coordinates
  ↓
  Queue patches to workers
  
Workers (queue_worker):
  Dequeue patch
  Resize if needed
  Apply stain normalization
  Save to disk with metadata
```

#### Helper Module: `process_batch.py`
Contains batch processing utilities for multi-slide datasets.

---

### 5. **Storage** (`patch_extraction/storage.py`)

**Purpose**: Manage organized output directory structure

#### Output Structure:
```
output_path/
├── wsi_name_1/
│   ├── metadata.yaml           # WSI metadata
│   ├── patches/
│   │   ├── wsi_name_1_0_0.png
│   │   ├── wsi_name_1_0_1.png
│   │   └── ...
│   ├── metadata/               # Per-patch metadata
│   │   ├── wsi_name_1_0_0.yaml
│   │   ├── wsi_name_1_0_1.yaml
│   │   └── ...
│   ├── tissue_masks/
│   │   ├── tissue_mask.png
│   │   └── otsu_mask.png
│   ├── thumbnails/
│   │   ├── thumbnail.png
│   │   └── ...
│   ├── annotation_masks/       # (if annotations provided)
│   │   ├── class_1.png
│   │   ├── class_2.png
│   │   └── ...
│   ├── context/                # (if context_scales provided)
│   │   ├── scale_2x/
│   │   ├── scale_4x/
│   │   └── ...
│   └── masks/                  # (if store_masks=True)
│       ├── wsi_name_1_0_0.npy
│       ├── wsi_name_1_0_1.npy
│       └── ...
└── wsi_name_2/
    └── ...
```

**Key Methods**:

- `save_meta_data()`: Save WSI-level metadata
- `save_masks(mask_images)`: Save tissue masks
- `save_annotation_mask()`: Save annotation masks
- `save_thumbnails()`: Save slide thumbnails
- `save_elem_to_disk(patch_result)`: Save single patch + metadata
- `save_neighbourhood_patch()`: Save context patches
- `clean_up()`: Final cleanup and statistics

**Patch Metadata** (YAML format):
```yaml
coordinates: [x, y]
magnification: 20
patch_size: 256
tissue_ratio: 0.85
annotated: true
annotation_labels: [1, 2]
context_scales:
  2x: [...]
  4x: [...]
```

---

### 6. **Utils Module** (`utils/`)

**Purpose**: Shared utility functions for image processing, annotation handling, and dataset management

#### Key Submodules:

##### `masking.py` - Tissue Detection
```python
generate_tissue_mask(
    tissue_tile: np.ndarray,
    mask_otsu: bool = False,
    polygons: List[Polygon] = None,
    otsu_annotation: str = "object",
    downsample: int = 1,
    apply_prefilter: bool = False
) → np.ndarray
```

**Algorithm**:
1. If `mask_otsu=True`: Apply annotation mask first
2. Convert to grayscale
3. (Optional) Apply prefilter to remove markers
4. Apply Otsu thresholding
5. Return binary mask

**Usage**: Called during `_prepare_wsi()` to generate tissue masks

##### `filters.py` - Image Filtering (from histolab)
Pre-built filters for image quality:
- `RedPenFilter`: Remove red pen annotations
- `GreenPenFilter`: Remove green pen annotations
- `BluePenFilter`: Remove blue pen annotations
- `apply_mask_image()`: Apply binary mask to image

**Purpose**: Clean up tissue before Otsu thresholding

##### `patch_util.py` - Patch Utilities
Core patch-related computations:

```python
get_files_from_dir(file_path, file_type) → List[Path]
    # Find all WSI files matching extension

patch_to_tile_size(patch_size, tile_size) → int
    # Convert patch pixels to tile coordinates

target_mag_to_downsample(target_mag, base_mag)
target_mpp_to_downsample(target_mpp, slide_mpp)
    # Convert magnification/mpp to pyramid level

get_regions_json(annotation_path) → List[Polygon]
get_regions_xml(annotation_path) → List[Polygon]
    # Parse annotation formats

macenko_normalization(image_list, normalization_vector_path)
    # Apply stain normalization to batch

calculate_background_ratio(image) → float
    # Compute white background percentage

generate_thumbnails(slide, sizes) → dict
    # Create slide thumbnails at different sizes

compute_interesting_patches(tissue_mask, patch_size, patch_overlap)
    # Find coordinates of tissue-rich patches
```

##### `patch_dataset.py` - PyTorch Dataset
```python
class TissueDetectionDataset(Dataset):
    """Dataset for loading extracted patches for tissue detection inference"""
    
    def __init__(self, patched_wsi_path: str, transforms: Callable)
    def __getitem__(idx) → (image_tensor, filename)

def load_tissue_detection_dl(path, transforms) → DataLoader
    """Load patches into DataLoader for inference"""
```

**Purpose**: Bridge extracted patches → PyTorch training/inference

##### `plotting.py` - Visualization
- `generate_polygon_overview()`: Visualize annotations on slide thumbnail

##### `logger.py` - Logging
- Custom logger with color-coded output
- Terminal colors via `colorama`

##### `file_handling.py` - File Operations
- Generic file operations (reading, writing, validation)

##### `tools.py` - General Utilities
- `start_timer()`, `end_timer()`: Performance monitoring
- `module_exists()`: Check if optional dependencies available

##### `exceptions.py` - Custom Exceptions
```python
class WrongParameterException(Exception)      # Invalid config
class UnalignedDataException(Exception)       # Annotation/image mismatch
```

---

### 7. **Annotation Conversion** (`annotation_conversion.py`)

**Purpose**: Convert annotation formats to standardized JSON

#### Main Function: `convert_geojson_to_json()`
- Input: GeoJSON file (from annotation tools like QuPath)
- Output: JSON file with standardized format

**Additional Utility**: `merge_outlines(geojson)`
- Merges multiple annotation outlines into single tissue mask
- Creates "Tissue-Outline" feature

**Use Case**: Prepare annotations before patch extraction

#### Supported Annotation Formats:
- GeoJSON (QuPath, Aperio, etc.)
- XML (some proprietary formats)
- JSON (custom)

---

### 8. **Macenko Stain Normalization** (`macenko_vector_generation.py`)

**Purpose**: Pre-compute stain normalization vectors

#### Entry Point: `MacenkoParser` + `PreProcessor.save_normalization_vector()`

**Workflow**:
```
Reference slide
    ↓
Extract sample patches
    ↓
Fit Macenko normalizer to patches
    ↓
Save stain vectors to JSON
    ↓
Use in patch extraction pipeline (normalize_stains=True)
```

**Output JSON Format**:
```json
{
  "hematoxylin": [0.65, 0.70, 0.29],
  "eosin": [0.07, 0.99, 0.11],
  "dab": [0.27, 0.57, 0.78]
}
```

---

### 9. **Base ML** (`base_ml/`)

**Purpose**: Base classes for machine learning workflows

#### `ABCParser` (Abstract Base Class)
Blueprint for configuration parsers:
- `__init__()`: Initialize argument parser
- `get_config()`: Load config and return (config, logger)
- `store_config()`: Save config to disk for reproducibility

#### `ExperimentBaseParser`
Base for ML experiment parsers (for future extensions)

---

### 10. **Data Module** (`data/`)

**Purpose**: PyTorch dataset utilities

Currently minimal, expands base ML dataset classes for the pipeline.

---

## Module Communication Flow

### Flow 1: Main Preprocessing Pipeline

```
wsi_extraction.py
    ↓
PreProcessingParser.get_config()
    ├─ Parse YAML config
    ├─ Parse CLI args
    ├─ Create PreProcessingConfig
    └─ Set up logger
    ↓
PreProcessor.__init__(config)
    ├─ _set_wsi_paths()
    ├─ _set_annotations_paths()
    ├─ _set_hardware() → Select backend (cuCIM/OpenSlide)
    └─ _set_tissue_detector() (if needed)
    ↓
PreProcessor.sample_patches_dataset()
    ├─ For each WSI:
    │   ├─ _prepare_wsi()
    │   │   ├─ Open with backend (DeepZoomGenerator)
    │   │   ├─ generate_tissue_mask() [masking.py]
    │   │   ├─ get_regions_json() [patch_util.py]
    │   │   └─ create Storage instance
    │   │
    │   ├─ compute_interesting_patches() [patch_util.py]
    │   │   → Find tissue-rich coordinates
    │   │
    │   ├─ process_queue()
    │   │   ├─ For each patch:
    │   │   │   ├─ Get coordinates
    │   │   │   ├─ dzg.get_tile() → PIL.Image
    │   │   │   ├─ Check tissue ratio
    │   │   │   ├─ Check annotation intersection
    │   │   │   └─ Queue for saving
    │   │
    │   ├─ queue_worker() [multiprocessing]
    │   │   ├─ Dequeue patch
    │   │   ├─ (Optional) macenko_normalization() [patch_util.py]
    │   │   ├─ Extract context patches (if needed)
    │   │   └─ storage.save_elem_to_disk()
    │   │
    │   └─ storage.clean_up()
    │       ├─ Save metadata.yaml
    │       ├─ Save tissue masks
    │       ├─ Save annotation masks
    │       └─ Save thumbnails
    │
    └─ Logger: Finished Preprocessing
```

### Flow 2: Per-Patch Processing

```
DST coordinates (row, col)
    ↓
DeepZoomGenerator.get_tile(level, address)
    ↓ (if cuCIM)
CuImage.read_region()    [GPU acceleration]
    ↓ (else OpenSlide)
OpenSlide.read_region()  [CPU]
    ↓
PIL.Image (RGB)
    ├─ Check tissue_ratio > threshold
    ├─ Check annotation intersection
    └─ Queue for saving
    ↓
queue_worker()
    ├─ (Optional) macenko_normalization()
    ├─ (Optional) extract context patches
    └─ storage.save_elem_to_disk()
        ├─ Save patch PNG
        └─ Save metadata YAML
```

### Flow 3: Stain Normalization

```
macenko_vector_generation.py
    ↓
MacenkoParser.get_config()
    ↓
PreProcessor.save_normalization_vector(wsi_file, save_path)
    ├─ Extract sample patches
    ├─ Fit MacenkoNormalizer
    ├─ Save vectors to JSON
    └─ Output: normalization_vectors.json
    
Later in preprocessing:
    if normalize_stains=True:
        Load vectors from JSON
            ↓
        queue_worker()
            ├─ macenko_normalization(patch, vector_path)
            └─ Save normalized patch
```

---

## Design Patterns Used

### 1. **Backend Strategy Pattern**
- `DeepZoomGenerator` base interface
- Implementations: OpenSlide, cuCIM, DICOM
- Allows seamless GPU/CPU switching

### 2. **Configuration as Object Pattern**
- `PreProcessingConfig`: Pydantic model with validation
- Type-safe, serializable configuration

### 3. **Multiprocessing Worker Pattern**
```
Main thread: Generate work (patch coordinates)
    ↓
Queue: Distribute work
    ↓
Workers: Process work (save patches)
```

### 4. **Storage Abstraction**
- `Storage` class encapsulates directory structure
- Centralizes all file I/O operations

### 5. **Parser Chain Pattern**
- CLI args → YAML config → Config object
- Flexible parameter specification

---

## Key Data Structures

### Patch Coordinate Tuple
```python
(patch_center_x, patch_center_y, magnification)
```

### Patch Result (Queue Item)
```python
(
    patch_image: np.ndarray,
    coords: (x, y),
    path: str,
    context_patches: dict,  # {scale: image}
    target_patch_size: int
)
```

### Patch Metadata (Saved YAML)
```yaml
coordinates: [x, y]
magnification: 20
patch_size: 256
tissue_ratio: 0.92
annotation_labels: [1, 2]
context:
  2x: <image_data>
  4x: <image_data>
```

---

## Dependency Injection & Configuration

### Hardware Selection
```python
config.hardware_selection = "cucim"  # Try GPU first
    ↓
PreProcessor._set_hardware()
    └─ Attempts CuImageBackend
       ├─ Success: Use cuCIM + OpenSlide metadata
       └─ Failure: Fallback to OpenSlide only
```

### Tissue Detector Injection
```python
if config.masked_otsu:
    detector_config = {
        'mask_otsu': True,
        'otsu_annotation': config.otsu_annotation,
        'apply_prefilter': config.apply_prefilter
    }
    ↓
generate_tissue_mask(..., **detector_config)
```

### Annotation Loading
```python
config.annotation_paths
    ↓
_set_annotations_paths()
    ├─ Find JSON/XML files
    ├─ Parse with get_regions_json/xml()
    └─ Store as List[Polygon]
```

---

## Extension Points

### 1. Custom Tissue Detector
Modify `generate_tissue_mask()` in `utils/masking.py` to implement custom algorithm

### 2. Custom Annotation Format
Add support in `utils/patch_util.py`:
- `get_regions_custom()` function
- Parse in `_set_annotations_paths()`

### 3. Custom Backend
Create new DeepZoomGenerator wrapper in `wsi_interfaces/` for new WSI format

### 4. Custom Filtering
Add filters in `utils/filters.py` before Otsu thresholding

### 5. Custom Stain Normalizer
Add in `utils/patch_util.py` (similar to `macenko_normalization`)

---

## Performance Characteristics

### Computation Bottlenecks:
1. **Tissue detection**: O(WSI size), parallelizable across patches
2. **Stain normalization**: O(patches), parallelizable via queue workers
3. **I/O**: Often dominant; optimized with multiprocessing
4. **Backend speed**:
   - cuCIM (GPU): 5-10x faster than OpenSlide
   - OpenSlide (CPU): Baseline

### Optimization Strategies:
1. Use `hardware_selection="cucim"` for large datasets
2. Increase `processes` for CPU-bound filtering
3. Cache tissue mask for multiple patch extractions
4. Batch normalize stains with same vector

---

## Error Handling

**Custom Exceptions**:
- `WrongParameterException`: Invalid configuration
- `UnalignedDataException`: Mismatch between annotations and images

**Validation Checkpoints**:
1. Config validation in `PreProcessingConfig`
2. Path existence checks
3. WSI resolution consistency checks
4. Coordinate boundary checks

---

## Logging & Monitoring

**Logger Levels**:
- DEBUG: Detailed processing steps
- INFO: Major milestones
- WARNING: Potential issues
- ERROR: Processing failures
- CRITICAL: Fatal errors

**Color-coded Output**: Terminal colors via `colorama`

**Performance Metrics**:
- Timer functions: `start_timer()`, `end_timer()`
- Per-slide statistics stored in metadata

---

## Configuration Hierarchy

```
Defaults (in PreProcessingConfig)
    ↑ overridden by ↓
YAML config file
    ↑ overridden by ↓
CLI arguments
    ↓
Final PreProcessingConfig instance
```

Example Priority:
```bash
# YAML specifies:
normalize_stains: false

# CLI overrides:
--normalize_stains

# Result: normalize_stains = True (from CLI)
```

