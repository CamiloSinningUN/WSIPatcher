# HistoLab vs GlassCut vs PathoPatcher - Comprehensive Comparison

**Purpose**: Understand differences, similarities, and when to use each library  
**Scope**: Architecture, features, use cases, integration patterns  
**Audience**: Developers choosing between the three libraries

---

## Table of Contents

1. [Quick Comparison Matrix](#quick-comparison-matrix)
2. [Architecture Overview](#architecture-overview)
3. [Module Breakdown](#module-breakdown)
4. [Feature Comparison](#feature-comparison)
5. [Use Case Recommendations](#use-case-recommendations)
6. [Integration Scenarios](#integration-scenarios)
7. [API Comparison](#api-comparison)
8. [Performance](#performance)
9. [Migration Paths](#migration-paths)

---

## Quick Comparison Matrix

| Feature | GlassCut | HistoLab | PathoPatcher |
|---------|----------|----------|-------------|
| **Primary Use** | Simple tile extraction | Flexible preprocessing | Batch production pipeline |
| **Architecture Style** | Backend-focused | Protocol-based | Monolithic pipeline |
| **Configuration** | Python API only | Python API | YAML + Python |
| **WSI Backends** | cuCIM (primary), OpenSlide | OpenSlide (primary), large_image | Multiple (user selects) |
| **Tile Extraction** | Built-in (simple) | Protocol extensible | Built-in (fixed) |
| **Filtering** | External (via Slide) | Built-in comprehensive | Built-in (fixed chain) |
| **Stain Normalization** | No | Built-in | Integrated |
| **Quality Scoring** | Tissue ratio only | Multiple scorers | No scoring |
| **Batch Processing** | Manual loops | Manual loops | Native support |
| **Multiprocessing** | Not built-in | Not built-in | Built-in |
| **Output Formats** | PNG/TIFF (user) | PNG/TIFF (user) | PNG, HDF5, Zarr |
| **Typical Workflow** | Research > single slide | Research > preprocessing | Production > batch |
| **Learning Curve** | Easiest | Moderate | Steepest |
| **Extensibility** | Backend swap | Add strategies | Modify config |
| **Mandatory Config** | Very minimal | processed_path | YAML required |

---

## Architecture Overview

### Design Philosophy Comparison

```
GlassCut
  └─ Philosophy: Backend abstraction + data types
     Architecture: Factory pattern + property injection
     Emphasis: I/O abstraction, simplicity
     
HistoLab
  └─ Philosophy: Strategy composition + protocols
     Architecture: Protocol-based + multiple patterns
     Emphasis: Flexibility, extensibility
     
PathoPatcher
  └─ Philosophy: Complete processing pipeline
     Architecture: Orchestration + configuration
     Emphasis: Production efficiency, batch processing
```

### Core Module Comparison

```
┌────────────────┬──────────────┬────────────────┬────────────────┐
│     Layer      │  GlassCut    │    HistoLab    │ PathoPatcher   │
├────────────────┼──────────────┼────────────────┼────────────────┤
│ I/O            │ Slide        │ Slide          │ WsiInterface   │
│ (Backend)      │ (Adapter)    │ (Adapter)      │ (Multiple)     │
├────────────────┼──────────────┼────────────────┼────────────────┤
│ Representation │ Tile         │ Tile           │ InMemoryPatch  │
│                │ (Simple)     │ (Rich)         │ (Complex)      │
├────────────────┼──────────────┼────────────────┼────────────────┤
│ Extraction     │ Implicit     │ Tiler          │ PatchExtractor │
│ Strategy       │ (Simple grid)│ (Protocol)     │ (Fixed)        │
├────────────────┼──────────────┼────────────────┼────────────────┤
│ Preprocessing  │ External     │ Filters        │ FilterChain    │
│                │ (No built-in)│ (Rich system)  │ (Predefined)   │
├────────────────┼──────────────┼────────────────┼────────────────┤
│ Quality Gate   │ tissue_ratio │ BinaryMask +   │ None           │
│                │              │ Scorers        │                │
├────────────────┼──────────────┼────────────────┼────────────────┤
│ Output         │ PIL Image    │ PNG/file       │ Multiple       │
│ Format         │ (User saves) │ (Configurable) │ (HDF5, etc)    │
├────────────────┼──────────────┼────────────────┼────────────────┤
│ Orchestration  │ None         │ None           │ PreProcessor   │
│                │ (User code)  │ (User code)    │ (Built-in)     │
└────────────────┴──────────────┴────────────────┴────────────────┘
```

---

## Module Breakdown

### GlassCut Architecture

```
glasscut/
├── slides/
│   ├── slide.py (Main API)
│   ├── base.py (BaseSlide)
│   └── backends/ (cuCIM, OpenSlide)
├── tile.py (Tile representation)
├── tissue_detectors/ (Strategy)
├── stain_normalizers/ (Strategy)
└── utils.py (Utilities)

Key Characteristics:
- Minimal but complete
- Backend-focused design
- Property-based configuration
- No built-in orchestration
```

### HistoLab Architecture

```
histolab/
├── slides/
│   ├── slide.py (Main API)
│   └── data/ (Registry)
├── tiles/
│   └── tile.py (Rich Tile)
├── tiler.py (Protocol)
├── masks.py (BinaryMask strategy)
├── filters/ (Comprehensive system)
│   ├── image_filters.py
│   ├── morphological_filters.py
│   ├── compositions.py
│   └── functional/ (Low-level)
├── scorer.py (Quality scoring)
├── stain_normalizer.py (Normalization)
├── mixins.py (Shared functionality)
├── types.py (Type definitions)
├── exceptions.py (Error hierarchy)
└── util.py (Utilities)

Key Characteristics:
- Protocol-heavy
- Rich filter system
- Built-in quality metrics
- Highly extensible
```

### PathoPatcher Architecture

```
pathopatch/
├── cli.py (CLI interface)
├── config/ (Configuration)
├── patch_extraction/ (Main)
├── wsi_interfaces/ (Backends)
├── storage.py (Output mgmt)
├── annotation_conversion.py (GeoJSON)
├── utils/ (Masking, filtering)
├── base_ml/ (ML utilities)
└── data/ (Sample data)

Key Characteristics:
- Configuration-driven
- Complete batch pipeline
- Multiple output formats
- Production-focused
```

---

## Feature Comparison

### 1. Slide Loading

**GlassCut**
```python
from glasscut.slides import Slide

slide = Slide(path="/slide.svs")  # No output path needed
# Optional: specify backend
slide = Slide(path, backend="openslide")  # cuCIM is default
```

**HistoLab**
```python
from histolab.slides import Slide

# Requires processed_path (MANDATORY)
slide = Slide(
    path="/slide.svs",
    processed_path="/output"  # REQUIRED
)
```

**PathoPatcher**
```python
from pathopatch.wsi_interfaces import OpenSlideInterface

slide = OpenSlideInterface(path="/slide.svs")
# User selects backend upfront in config
```

**Comparison**:
- **GlassCut**: Minimal, optional backend selection
- **HistoLab**: Mandatory output path, optional fallback backend
- **PathoPatcher**: Upfront backend selection via config

### 2. Tile Extraction

**GlassCut**
```python
# Simple grid extraction (built-in)
tiles = slide.extract_tiles(
    tile_size=512,
    overlap=0,
    filter_tissue=True
)
```

**HistoLab**
```python
# Protocol-based (extensible)
from histolab.tiler import Tiler

tiler = CustomTiler()  # Implement protocol
for tile in tiler.extract(slide):
    ...
```

**PathoPatcher**
```python
# Fixed pipeline
from pathopatch.patch_extraction import PreProcessor

processor = PreProcessor(config)
patches = processor.extract(...)
```

**Comparison**:
- **GlassCut**: Built-in simple grid, no customization
- **HistoLab**: Protocol allows custom extraction strategies
- **PathoPatcher**: Fixed extraction with config options

### 3. Filtering & Preprocessing

**GlassCut**
```python
# No built-in filters
# User applies external packages
from skimage import filters as ski_filters

# Or use properties
slide = Slide(path, detect_tissue_fn=custom_fn)
```

**HistoLab**
```python
# Rich built-in filter system
from histolab.filters import Compose, RgbToGrayscale, OtsuThreshold

pipeline = Compose([
    RgbToGrayscale(),
    OtsuThreshold(),
    RemoveSmallObjects()
])
result = pipeline(image)
```

**PathoPatcher**
```python
# Fixed predefined chains
from pathopatch.utils import FilterComposition

filters = FilterComposition.of(slide)
# Chain determined by config
```

**Comparison**:
- **GlassCut**: No filtering, user responsibility
- **HistoLab**: Comprehensive, composable filters
- **PathoPatcher**: Predefined chains via config

### 4. Tissue Detection

**GlassCut**
```python
# Simple tissue detection
from glasscut.tissue_detectors import OtsuTissueDetector

detector = OtsuTissueDetector()
tissue_map = detector.get_tissue_mask(slide)
```

**HistoLab**
```python
# Multiple strategies
from histolab.masks import BiggestTissueBoxMask, BinaryMask

mask = BiggestTissueBoxMask(slide)
tissue_map = mask.get_mask(slide)

# Or custom implementation
class CustomMask(BinaryMask):
    def get_mask(self, slide): ...
```

**PathoPatcher**
```python
# Built-in to pipeline
from pathopatch.utils import masking

tissue_map = masking.get_tissue_mask(slide)
```

**Comparison**:
- **GlassCut**: OtsuTissueDetector, simple
- **HistoLab**: Multiple strategies via BinaryMask protocol
- **PathoPatcher**: Fixed masking integrated in pipeline

### 5. Stain Normalization

**GlassCut**
```python
# No built-in normalization
# User must implement or use external
from my_stain_normalizer import StainNormalizer

# Or use GlassCut's stain normalizer strategy
from glasscut.stain_normalizers import MacenkoNormalizer

normalizer = MacenkoNormalizer()
normalized = normalizer.transform(image, reference)
```

**HistoLab**
```python
# Built-in
from histolab.stain_normalizer import StainNormalizer

normalizer = StainNormalizer()
normalizer.fit(reference_image)
normalized = normalizer.transform(source_image)
```

**PathoPatcher**
```python
# Integrated in pipeline
# Optional via config
# Based on HistoLab's implementation
```

**Comparison**:
- **GlassCut**: Strategy-based, multiple implementations
- **HistoLab**: Built-in transformer pattern
- **PathoPatcher**: Optional, integrated

### 6. Quality Scoring

**GlassCut**
```python
# Only tissue ratio available
tile = Tile(...)
tissue_ratio = calculate_tissue_ratio(tile)
if tissue_ratio > 0.7:
    keep_tile(tile)
```

**HistoLab**
```python
# Multiple built-in scorers
from histolab.scorer import CellularityScorer, RandomScorer

scorer = CellularityScorer()
score = scorer.score(tile)

# Custom scorer
class MyScorer:
    def score(self, tile): ...
```

**PathoPatcher**
```python
# No quality scoring
# Filter via config parameters
```

**Comparison**:
- **GlassCut**: Tissue ratio only
- **HistoLab**: Multiple scorers, extensible
- **PathoPatcher**: None

### 7. Batch Processing

**GlassCut**
```python
# Manual loop
from pathlib import Path

for slide_file in Path("/slides").glob("*.svs"):
    slide = Slide(str(slide_file))
    tiles = slide.extract_tiles(...)
    for tile in tiles:
        save_tile(tile)
```

**HistoLab**
```python
# Manual loop
for slide_file in Path("/slides").glob("*.svs"):
    slide = Slide(str(slide_file), processed_path=str(output))
    for tile in tiler.extract(slide):
        process_tile(tile)
```

**PathoPatcher**
```python
# Built-in batch support
from pathopatch.patch_extraction import PreProcessor

processor = PreProcessor(config)
processor.process_batch(
    slides_dir="/slides",
    output_dir="/output"
)
```

**Comparison**:
- **GlassCut**: User implements loops
- **HistoLab**: User implements loops
- **PathoPatcher**: Built-in batch orchestration

### 8. Output Formats

**GlassCut**
```python
# User saves via PIL
tile_image = tile.image
tile_image.save("/output/tile.png")
```

**HistoLab**
```python
# User saves via PIL or np_to_pil
from histolab.util import np_to_pil

pil_image = np_to_pil(numpy_array)
pil_image.save("/output/tile.png")
```

**PathoPatcher**
```python
# Multiple formats built-in
from pathopatch.storage import TileStorage

storage = TileStorage(
    format="hdf5"  # or png, zarr, etc.
)
storage.save(patch, metadata)
```

**Comparison**:
- **GlassCut**: PNG/TIFF via user code
- **HistoLab**: PNG/TIFF via user code
- **PathoPatcher**: PNG, HDF5, Zarr, custom

---

## Use Case Recommendations

### Use GlassCut When:

1. **Quick Prototyping**
   - Need simple tile extraction fast
   - Minimal configuration needed
   
2. **Research (Single Slide)**
   - Processing one slide at a time
   - Focus on exploration
   
3. **Simple Requirements**
   - No complex filtering needed
   - Basic tissue detection sufficient
   
4. **GPU Acceleration Needed**
   - cuCIM backend (primary)
   - RAPIDS ecosystem integration
   
5. **Minimal Dependencies**
   - Want lightweight solution
   - Clean, simple API

**Ideal Workflow**:
```python
from glasscut.slides import Slide

# One slide exploration
slide = Slide("/path/to/slide.svs")
for tile in slide.extract_tiles(tile_size=512):
    analyze_tile(tile)
```

---

### Use HistoLab When:

1. **Complex Preprocessing**
   - Multiple filter options needed
   - Custom mask strategies
   - Stain normalization important
   
2. **Quality Control**
   - Multiple scoring strategies
   - Selective tile extraction
   - Tissue quality metrics
   
3. **Extensibility**
   - Need custom tilers
   - Custom scorers
   - Custom filters
   
4. **Research + Preprocessing**
   - Exploratory with full preprocessing
   - Multiple slides, varying quality
   - Algorithm development
   
5. **Educational**
   - Learn image processing patterns
   - Protocol-based design study

**Ideal Workflow**:
```python
from histolab.slides import Slide
from histolab.filters import Compose, RgbToGrayscale, OtsuThreshold
from histolab.scorer import CellularityScorer

# Complex preprocessing with quality control
slide = Slide("/slide.svs", processed_path="/output")
scorer = CellularityScorer()

for tile in tiler.extract(slide):
    processed = tile.apply_filters([RgbToGrayscale(), OtsuThreshold()])
    if tile.has_enough_tissue() and scorer.score(tile) > 0.7:
        save_high_quality_tile(tile)
```

---

### Use PathoPatcher When:

1. **Production Batch Processing**
   - Processing 100+ slides
   - Enterprise deployment needed
   - Consistent, reproducible results
   
2. **Multiple Output Formats**
   - Need HDF5, Zarr outputs
   - Complex metadata storage
   - Downstream ML pipeline
   
3. **Multiprocessing**
   - Parallel extraction needed
   - CPU-bound operations
   - Time-critical processing
   
4. **Fixed Pipeline**
   - Standard preprocessing acceptable
   - No custom filtering
   - Configuration via YAML
   
5. **Integration with ML**
   - PyTorch dataset loading
   - HDF5 compatibility
   - ML pipeline integration

**Ideal Workflow**:
```yaml
# config.yaml
tile_size: 512
batch_size: 100
output_format: hdf5
num_workers: 8
```

```python
from pathopatch.patch_extraction import PreProcessor

processor = PreProcessor("config.yaml")
processor.process_batch(
    slides_dir="/slides",
    output_dir="/output"
)
```

---

## Integration Scenarios

### Scenario 1: Research to Production

**Phase 1: Exploration (GlassCut)**
```python
# Quick understanding of slide
slide = Slide("/slide.svs")
for tile in slide.extract_tiles(tile_size=512):
    preview_tile(tile)
```

**Phase 2: Preprocessing Development (HistoLab)**
```python
# Develop preprocessing pipeline
slide = Slide("/slide.svs", processed_path="/tmp")

filters = Compose([
    RgbToGrayscale(),
    OtsuThreshold(),
    RemoveSmallObjects(),
])

# Test on samples
for tile in sample_tiles:
    processed = tile.apply_filters(filters)
```

**Phase 3: Production (PathoPatcher)**
```yaml
# config.yaml - replicate HistoLab pipeline in config
tile_size: 512
preprocess: true
num_workers: 8
output_format: hdf5
```

```python
# Deploy at scale
processor = PreProcessor("config.yaml")
processor.process_batch("/slides", "/output")
```

---

### Scenario 2: Multi-Library Pipeline

**Stage 1: Load with GlassCut (Fast I/O)**
```python
from glasscut.slides import Slide as GlassCutSlide

slide = GlassCutSlide("/slide.svs")
thumbnail = slide.get_thumbnail((500, 500))
```

**Stage 2: Preprocess with HistoLab (Rich Filters)**
```python
from histolab.slides import Slide as HistolabSlide
from histolab.filters import Compose, OtsuThreshold

slide = HistolabSlide("/slide.svs", processed_path="/tmp")
# Use HistoLab's filtering
```

**Stage 3: Extract with PathoPatcher (Batch)**
```python
from pathopatch.patch_extraction import PreProcessor

processor = PreProcessor(config)
processor.extract("/slide.svs", "/output")
```

---

### Scenario 3: Custom Tile Scoring

**Using GlassCut + HistoLab Scorer**
```python
from glasscut.slides import Slide as GlassCutSlide
from histolab.scorer import CellularityScorer
from histolab.types import CoordinatePair
from histolab.tiles import Tile

glass_slide = GlassCutSlide("/slide.svs")
scorer = CellularityScorer()

for i, tile_img in enumerate(glass_slide.extract_tiles()):
    # Create HistoLab Tile for scoring
    tile = Tile(
        image=tile_img,
        coords=CoordinatePair(i*512, 0),
        level=0,
        slide=glass_slide  # May not work directly
    )
    score = scorer.score(tile)
    if score > 0.7:
        save_tile(tile_img)
```

---

## API Comparison

### Initialize Slide

```python
# GlassCut
from glasscut.slides import Slide as GCSlide
slide = GCSlide(path="/slide.svs")
# Optional: backend, detect_tissue_fn, etc.

# HistoLab
from histolab.slides import Slide as HLSlide
slide = HLSlide(
    path="/slide.svs",
    processed_path="/output"  # REQUIRED
)

# PathoPatcher
from pathopatch.wsi_interfaces import OpenSlideInterface
interface = OpenSlideInterface(path="/slide.svs")
```

### Extract Tiles

```python
# GlassCut
for tile in slide.extract_tiles(tile_size=512, overlap=50):
    process(tile)

# HistoLab
from histolab.tiler import GridTiler  # User implements
tiler = GridTiler(tile_size=512, overlap=50)
for tile in tiler.extract(slide):
    process(tile)

# PathoPatcher
processor = PreProcessor(config)
patches = list(processor.extract_patches(slide))
for patch in patches:
    process(patch)
```

### Get Tissue Mask

```python
# GlassCut
from glasscut.tissue_detectors import OtsuTissueDetector
detector = OtsuTissueDetector()
mask = detector.get_tissue_mask(slide)

# HistoLab
from histolab.masks import BiggestTissueBoxMask
mask_strategy = BiggestTissueBoxMask(slide)
mask = mask_strategy.get_mask(slide)

# PathoPatcher
from pathopatch.utils import masking
mask = masking.get_tissue_mask(slide)
```

### Apply Filters

```python
# GlassCut
# No built-in filters
# Use external packages

# HistoLab
from histolab.filters import Compose, RgbToGrayscale
pipeline = Compose([RgbToGrayscale()])
result = pipeline(image)

# PathoPatcher
# Fixed pipeline via config
# No direct filter API
```

---

## Performance

### Extraction Speed (Relative)

```
GlassCut:     ████████ (Fast - simple extraction)
HistoLab:     ██████░░ (Moderate - more features)
PathoPatcher: ██░░░░░░ (Slow - full pipeline, multiprocessing)
```

### Memory Usage

```
GlassCut:     ███░░░░░░░ (Lightweight)
HistoLab:     █████░░░░░ (Moderate)
PathoPatcher: ████████░░ (Heavy - batch processing)
```

### Customization Options

```
GlassCut:     ██░░░░░░░░ (Limited)
HistoLab:     █████████░ (Extensive)
PathoPatcher: ████░░░░░░ (Configuration-only)
```

### Scale

```
GlassCut:     Single slide (1-50 slides)
HistoLab:     Multiple slides (manual batching)
PathoPatcher: Large batches (100+)
```

---

## Migration Paths

### GlassCut → HistoLab

**Reason**: Need more filtering/preprocessing

```python
# GlassCut
from glasscut.slides import Slide

slide = Slide("/slide.svs")
for tile in slide.extract_tiles():
    ...

# HistoLab equivalent
from histolab.slides import Slide
from histolab.filters import Compose, RgbToGrayscale

slide = Slide("/slide.svs", processed_path="/output")
filters = Compose([RgbToGrayscale()])
for tile in tiler.extract(slide):
    processed = tile.apply_filters(filters)
    ...
```

**Migration Steps**:
1. Add `processed_path` parameter
2. Move filter logic to HistoLab filters
3. Use Tile.apply_filters() instead of external filtering

---

### GlassCut → PathoPatcher

**Reason**: Need production batch processing

```python
# GlassCut
for slide_file in slides_dir.glob("*.svs"):
    slide = Slide(slide_file)
    for tile in slide.extract_tiles():
        save_tile(tile)

# PathoPatcher equivalent
from pathopatch.patch_extraction import PreProcessor

processor = PreProcessor(config)
processor.process_batch(slides_dir, output_dir)
```

**Migration Steps**:
1. Create configuration YAML
2. Switch to PathoPatcher's batch interface
3. Update output format (HDF5, etc.)

---

### HistoLab → PathoPatcher

**Reason**: Need multiprocessing/batch

```python
# HistoLab
for slide_file in slides_dir.glob("*.svs"):
    slide = Slide(str(slide_file), processed_path=str(output_dir / slide_file.stem))
    for tile in tiler.extract(slide):
        if tile.has_enough_tissue():
            save_tile(tile)

# PathoPatcher (batched)
from pathopatch.patch_extraction import PreProcessor

config = {
    "tile_size": 512,
    "num_workers": 8,
    "output_format": "hdf5"
}
processor = PreProcessor(config)
processor.process_batch(slides_dir, output_dir)
```

**Migration Steps**:
1. Port filter pipeline to PathoPatcher config
2. Use PathoPatcher's batch API
3. Switch to HDF5 or Zarr output
4. Implement parallel processing

---

## Detailed Feature Matrix

| Feature | GlassCut | HistoLab | PathoPatcher |
|---------|----------|----------|-------------|
| Slide Loading | ✓ | ✓ | ✓ |
| Multiple Backends | ✓ (2) | ✓ (2) | ✓ (3+) |
| Tile Extraction | ✓ (grid) | ✓ (protocol) | ✓ (fixed) |
| Custom Extractors | ✗ | ✓ | ✗ |
| Built-in Filters | ✗ | ✓ (rich) | ✓ (fixed) |
| Custom Filters | ✗ | ✓ | ✗ |
| Tissue Detection | ✓ (Otsu) | ✓ (multiple) | ✓ (fixed) |
| Custom Masks | ✗ | ✓ | ✗ |
| Stain Norm | ✓ (strategy) | ✓ (built-in) | ✓ (integrated) |
| Quality Scoring | ✓ (ratio) | ✓ (multiple) | ✗ |
| Custom Scorers | ✗ | ✓ | ✗ |
| Batch Processing | ✗ (manual) | ✗ (manual) | ✓ (built-in) |
| Multiprocessing | ✗ | ✗ | ✓ |
| Config Files | ✗ | ✗ | ✓ (YAML) |
| CLI Interface | ✗ | ✗ | ✓ |
| Output Formats | 1 (PIL) | 1 (PIL) | 3+ (HDF5, etc) |
| Type Hints | ✓ | ✓ | ✓ |
| Documentation | Good | Excellent | Moderate |
| Test Coverage | Good | Excellent | Good |

---

## Summary Decision Tree

```
START: "I need to process WSI files"
  │
  ├─ "Just quick exploration?" → GlassCut
  │
  ├─ "Need custom preprocessing?" → HistoLab
  │   │
  │   ├─ "One slide at a time?" → HistoLab
  │   │
  │   └─ "Batch processing with HistoLab's features?" → Use HistoLab + custom batch
  │
  ├─ "Need production batch processing?" → PathoPatcher
  │
  ├─ "Need GPU acceleration?" → GlassCut (cuCIM) or HistoLab (RAPIDS compatible)
  │
  └─ "Need ML pipeline integration?" → PathoPatcher (HDF5 output)
```

---

## Conclusion

- **GlassCut**: Best for simple, fast tile extraction
- **HistoLab**: Best for flexible, extensible preprocessing
- **PathoPatcher**: Best for production batch processing

The three libraries complement each other and can be used together in multi-stage pipelines.
