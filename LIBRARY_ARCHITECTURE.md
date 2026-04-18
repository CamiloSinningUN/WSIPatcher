# GlassCut Library Architecture

## Overview

GlassCut is a Python library for working with whole slide images (WSI) in digital pathology. It provides a clean, modular interface for loading, extracting tiles, and performing image processing tasks on histopathology slides.

---

## Core Modules

### 1. **Slides Module** (`glasscut/slides/`)
**Purpose**: Manage WSI file access and tile extraction

#### Key Classes:

##### `Slide` (Main API)
- **Role**: Primary interface for working with WSI files
- **Responsibilities**:
  - Opens slide files (delegates to backends)
  - Provides access to slide metadata (dimensions, magnifications, properties)
  - Extracts individual tiles or multiple tiles in parallel
  - Manages resource lifecycle (context manager support)

```python
with Slide("path/to/slide.svs") as slide:
    tile = slide.extract_tile(
        coords=(1000, 1000),
        tile_size=(512, 512),
        magnification=20
    )
```

- **Key Properties**:
  - `dimensions`: Slide size at base magnification
  - `magnifications`: Available magnification levels
  - `mpp`: Microns per pixel
  - `thumbnail`: Slide preview image
  - `name`: Slide filename without extension

- **Key Methods**:
  - `extract_tile()`: Extract single tile
  - `extract_tiles()`: Extract multiple tiles in parallel using ThreadPoolExecutor
  - `close()`: Free resources

#### Backend Architecture

The `Slide` class uses a **Strategy Pattern** with pluggable backends:

##### `SlideBackend` (Abstract Base)
Defines interface that all backends must implement:
- `open()` / `close()`: Manage resources
- `read_region()`: Extract pixel data at specific coordinates
- `properties`, `dimensions`, `num_levels`: Metadata access
- `mpp`, `base_magnification`: Image properties

##### Concrete Backends:

**`CuCimBackend`**
- Uses NVIDIA cuCIM library for GPU acceleration
- Better performance for large-scale tile extraction
- Falls back to OpenSlide if not available

**`OpenSlideBackend`**
- CPU-based tile reading
- Supports common WSI formats (SVS, TIFF, etc.)
- Fallback option, always available

**Backend Selection Logic**:
```
If use_cucim=True:
  Try cuCim → Success: use cuCim
           → Fail: fallback to OpenSlide
Else:
  Use OpenSlide directly
```

---

### 2. **Tile Module** (`glasscut/tile.py`)
**Purpose**: Represents extracted image regions with tissue analysis

#### `Tile` Class
- **Role**: Encapsulates a single extracted tile and its metadata
- **Dependencies**: 
  - Imports from `tissue_detectors` (uses TissueDetector strategy)
  - Imports from `utils` (uses lazyproperty decorator)

#### Key Attributes:
- `image`: PIL.Image object (RGB format)
- `coords`: (x, y) coordinates at level 0
- `magnification`: Extraction magnification level
- `tissue_detector`: Strategy for tissue detection

#### Key Methods:
- `has_enough_tissue(tissue_threshold=0.8)`: Check tissue percentage
- `save(path)`: Save tile to disk

#### Key Properties (Lazy-Evaluated):
- `tissue_mask`: Binary mask of tissue (computed once, cached)
- `tissue_ratio`: Percentage of tissue in tile (computed once, cached)

**Flow Example**:
```
Tile extracted → tissue_mask accessed → computed via tissue_detector.detect()
              → result cached in lazyproperty → subsequent accesses use cached value
```

---

### 3. **Tissue Detectors Module** (`glasscut/tissue_detectors/`)
**Purpose**: Strategy for identifying tissue regions in images

#### `TissueDetector` (Abstract Base)
- **Pattern**: Strategy pattern for pluggable detection methods
- **Method**: `detect(image: Image) -> np.ndarray`
  - Input: RGB PIL Image
  - Output: Binary mask (0=background, 1=tissue)

#### `OtsuTissueDetector` (Concrete Implementation)
- **Algorithm**: Otsu thresholding with optional morphological operations
- **Pipeline**:
  1. Convert RGB to grayscale
  2. (Optional) Apply pre-filtering for marker removal
  3. Apply Otsu thresholding
  4. (Optional) Apply morphological dilation & hole filling
  
**Configuration**:
```python
detector = OtsuTissueDetector(
    apply_prefilter=False,
    apply_morphology=False,
    morphology_disk_size=2
)
```

**Usage in Tile**:
```python
tile.tissue_detector = OtsuTissueDetector()
mask = tile.tissue_mask  # Lazily computed
```

---

### 4. **Stain Normalizers Module** (`glasscut/stain_normalizers/`)
**Purpose**: Reduce color variations in histopathology images

#### `StainNormalizer` (Abstract Base)
- **Pattern**: Strategy pattern + mixin pattern
- **Methods**:
  - `fit(target_image)`: Learn normalization parameters from reference
  - `transform(image)`: Apply normalization

#### Concrete Implementations:

##### `MacenkoStainNormalizer`
- **Algorithm**: Unsupervised color deconvolution
- **Best for**: H&E stained images
- **Performance**: Fast and robust

**Pipeline**:
1. Convert RGB to optical density (OD) space
2. PCA analysis on OD values
3. Angular decomposition to identify stain vectors
4. Normalize concentrations to reference

**Stain Map**:
```python
{
    "hematoxylin": [0.65, 0.70, 0.29],  # Purple stain
    "eosin": [0.07, 0.99, 0.11],        # Pink stain
    "dab": [0.27, 0.57, 0.78],          # Brown DAB marker
}
```

##### `ReinhardtStainNormalizer`
- **Algorithm**: Color transfer-based
- **Performance**: Computationally efficient
- **Use case**: Interactive normalization

**Using with Tiles**:
```python
normalizer = MacenkoStainNormalizer()
reference_image = Image.open("reference.png")
normalizer.fit(reference_image)

# Apply to multiple tiles
for tile in tiles:
    normalized = normalizer.transform(tile.image)
    normalized_tile = Tile(normalized, tile.coords, tile.magnification)
```

---

### 5. **Utils Module** (`glasscut/utils.py`)
**Purpose**: Shared utility functions and decorators

#### Key Components:

##### `lazyproperty` Decorator
- **Purpose**: Lazy evaluation with automatic caching
- **Behavior**:
  - First access: Computes value
  - Subsequent accesses: Returns cached value
  - Read-only (no setter)
- **Implementation**: Uses `functools.lru_cache(maxsize=100)`

**Used extensively for expensive computations**:
```python
@lazyproperty
def tissue_mask(self) -> np.ndarray:
    # Computed only once per Tile instance
    return self.tissue_detector.detect(self.image)
```

##### `np_to_pil(np_img)` Function
- **Purpose**: Convert NumPy arrays to PIL Images
- **Handles**:
  - Bool arrays → uint8 (0-255)
  - Float arrays → uint8 (normalized)
  - Already uint8 → pass-through

**Type conversions**:
- Bool: `array * 255`
- Float: Uses `skimage.img_as_ubyte`
- Default: Force to uint8

---

### 6. **Exceptions Module** (`glasscut/exceptions.py`)
**Purpose**: Custom exception hierarchy for clear error handling

#### Exception Hierarchy:
```
Exception
└── GlassCutException (base for all custom exceptions)
    ├── SlidePropertyError: Missing/unavailable slide properties
    ├── BackendError: Backend-level failures
    ├── MagnificationError: Requested magnification unavailable
    ├── TileSizeOrCoordinatesError: Invalid tile extraction parameters
    └── FilterCompositionError: Filter composition issues
```

**Usage**:
```python
try:
    tile = slide.extract_tile(coords, size, magnification=99)
except MagnificationError:
    print("Magnification not available")
```

---

## Module Communication Flow

### Scenario 1: Loading and Extracting a Tile

```
User Application
    ↓
Slide.__init__(path) 
    ├→ Attempts CuCimBackend
    └→ Falls back to OpenSlideBackend
    
User calls: slide.extract_tile(coords, size, magnification)
    ↓
Slide validates magnification against available_mags
    ├→ Raises MagnificationError if invalid
    └→ Continues with valid magnification
    
Slide validates coordinates & size
    ├→ Raises TileSizeOrCoordinatesError if invalid
    └→ Continues
    
Slide.magnification_to_level(magnification, available_mags) 
    → Returns pyramid level
    
Backend.read_region(location, level, size)
    → Returns PIL.Image (RGB)
    
Tile created with image + metadata
    ↓
User receives Tile object
```

### Scenario 2: Tissue Analysis Workflow

```
Tile object with tissue_detector = OtsuTissueDetector()
    
User calls: tile.has_enough_tissue(threshold=0.8)
    ↓
First access to tile.tissue_mask (lazyproperty)
    ├→ tissue_detector.detect(tile.image)
    ├→ Result cached in instance
    └→ Returns cached result
    
tissue_ratio = np.mean(tissue_mask)
    ↓
Comparison: tissue_ratio > threshold
    ↓
Boolean result returned
```

### Scenario 3: Stain Normalization Workflow

```
images = [PIL.Image for each tile]
    
normalizer = MacenkoStainNormalizer()
normalizer.fit(reference_image)
    → Learns stain vectors from reference
    
For each image:
    normalized = normalizer.transform(image)
    → Applies learned normalization
    → Returns PIL.Image
    
Update tiles:
    normalized_tiles = [
        Tile(norm_img, coords, magnification) 
        for norm_img in normalized_images
    ]
```

---

## Design Patterns Used

### 1. **Strategy Pattern**
- **Examples**: 
  - `SlideBackend` (OpenSlide vs cuCim)
  - `TissueDetector` (different detection algorithms)
  - `StainNormalizer` (different normalization methods)
- **Benefit**: Easy to extend without modifying existing code

### 2. **Decorator Pattern**
- **Example**: `lazyproperty` - adds caching to methods
- **Benefit**: Transparent lazy evaluation

### 3. **Mixin Pattern**
- **Example**: `TransformerStainMatrixMixin` in stain normalizers
- **Benefit**: Shared functionality across multiple classes

### 4. **Context Manager**
- **Example**: `Slide.__enter__()`, `Slide.__exit__()`
- **Benefit**: Automatic resource cleanup

### 5. **Factory Pattern (Implicit)**
- **Example**: Backend selection in `Slide.__init__()`
- **Benefit**: Automatic fallback mechanism

---

## Dependency Graph

```
Slide
  ├── depends on → SlideBackend (OpenSlide or cuCim)
  ├── depends on → exceptions (MagnificationError, TileSizeOrCoordinatesError)
  ├── depends on → utils (lazyproperty)
  └── returns → Tile

Tile
  ├── depends on → utils (lazyproperty)
  ├── depends on → tissue_detectors (TissueDetector)
  └── uses → Exception (TileSizeOrCoordinatesError)

tissue_detectors
  ├── OtsuTissueDetector implements TissueDetector
  └── uses → PIL, numpy, scikit-image

stain_normalizers
  ├── MacenkoStainNormalizer implements StainNormalizer
  ├── ReinhardtStainNormalizer implements StainNormalizer
  └── uses → numpy, PIL, scipy/skimage

utils
  └── Used by Slide, Tile, stain_normalizers
```

---

## Data Flow Summary

### Input Path
```
.svs/.tiff file → Backend.open() → Slide object ready
```

### Tile Extraction Path
```
(coords, size, magnification) → Slide.extract_tile()
  → magnification_to_level() 
  → Backend.read_region()
  → Tile object created
```

### Processing Path
```
Tile
  → tissue_mask (lazy, cached)
  → tissue_ratio (lazy, cached)
  → pass to StainNormalizer
  → or save to disk
```

### Extension Points
Where you can add custom implementations:
1. **Custom Tissue Detector**: Inherit from `TissueDetector`
2. **Custom Backend**: Inherit from `SlideBackend`
3. **Custom Stain Normalizer**: Inherit from `StainNormalizer`

---

## Key Design Decisions

1. **Lazy Properties**: Expensive computations (tissue detection) computed on-demand
2. **Abstraction Layers**: Backends abstract file format differences
3. **Strategy Pattern**: Multiple algorithms pluggable without code changes
4. **Parallelization**: `extract_tiles()` uses ThreadPoolExecutor for multi-tile extraction
5. **Resource Management**: Context manager for proper cleanup
6. **Graceful Fallback**: cuCim → OpenSlide when GPU unavailable
