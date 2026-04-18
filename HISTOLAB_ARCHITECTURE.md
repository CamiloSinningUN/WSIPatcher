# HistoLab Architecture Documentation

**Library**: HistoLab  
**Version**: Latest from `__legacy__/histolab`  
**Purpose**: Comprehensive histopathology image processing and tile extraction framework  
**License**: Apache 2.0  
**Status**: Actively documented  

---

## Table of Contents

1. [Overview](#overview)
2. [Core Architecture](#core-architecture)
3. [Module Breakdown](#module-breakdown)
4. [Design Patterns](#design-patterns)
5. [Module Communication](#module-communication)
6. [Key Differentiators](#key-differentiators)
7. [Processing Pipelines](#processing-pipelines)
8. [Extension Points](#extension-points)

---

## Overview

HistoLab is a sophisticated histopathology image processing library designed for automated slide analysis and tile extraction. It provides a protocol-based architecture emphasizing extensibility and clean separation of concerns.

### Key Characteristics

- **Protocol-Based Design**: Uses Python protocols for maximum flexibility
- **Strategy Pattern Implementation**: Supports pluggable strategies for masks, filters, scorers, and tilers
- **Factory Patterns**: Filter compositions generated via factory methods
- **Mixin Architecture**: Stain normalizers use transformer mixins
- **Mandatory Processed Path**: Output directory must be specified at initialization
- **Dual Backend Support**: OpenSlide primary, large_image as optional fallback
- **Comprehensive Filtering**: Extensive built-in filter system for image processing
- **Quality Scoring**: Built-in tile quality assessment mechanisms

---

## Core Architecture

### System Overview Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         HistoLab System                         │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
    ┌───▼────┐         ┌──────▼──────┐        ┌────▼─────┐
    │  Slide │         │   Tiler     │        │  Scorer   │
    │ (I/O)  │         │ (Strategy)  │        │(Strategy) │
    └────┬───┘         └──────┬──────┘        └────┬──────┘
         │                   │                     │
         ├─────┬──────┬──────┴────┬────────────────┤
         │     │      │           │                │
    ┌────▼─┐  │   ┌──▼──┐   ┌────▼────┐    ┌─────▼────┐
    │Tile  │  │   │Mask │   │ Filters │    │Stain Norm│
    └──────┘  │   └─────┘   └─────────┘    └──────────┘
              │
         ┌────▼────────┐
         │ Backend I/O │
         │ (OpenSlide/ │
         │ Large_Image)│
         └─────────────┘
```

### Module Dependency Graph

```
Slide (Main API)
  ├── Backend I/O (openslide_backend.py / largeimage_backend.py)
  ├── Types (CoordinatePair, Region)
  └── Utilities (util.py)
      ├── apply_mask_image()
      ├── np_to_pil()
      └── image utilities

Tiler (Protocol/Abstract)
  ├── Concrete Implementations
  │   ├── GridTiler
  │   ├── RandomTiler
  │   └── Custom implementations
  └── Uses Slide for token retrieval
      └── Produces Tile objects

Tile (Tile Representation)
  ├── Filters (applied in sequence)
  │   ├── ImageFilter (protocol)
  │   ├── MorphologicalFilter (protocol)
  │   ├── FilterComposition
  │   └── Lambda filters
  ├── Mask Application
  │   └── BinaryMask strategies
  ├── Scoring
  │   ├── RandomScorer
  │   └── CellularityScorer
  └── Properties
      ├── has_enough_tissue()
      ├── tissue_ratio
      └── coordinates

BinaryMask (Strategy)
  ├── BiggestTissueBoxMask
  ├── OtsuMask
  ├── Custom implementations
  └── Uses FiltersComposition for mask generation

Filters System
  ├── Protocols
  │   ├── Filter (base protocol)
  │   └── ImageFilter / MorphologicalFilter
  ├── Image Filters
  │   ├── RgbToGrayscale
  │   ├── OtsuThreshold
  │   ├── RedThreshold
  │   ├── GreenThreshold
  │   ├── BlueThreshold
  │   ├── Compose
  │   └── Lambda
  ├── Morphological Filters
  │   ├── RemoveSmallObjects
  │   ├── RemoveSmallHoles
  │   ├── Dilation
  │   ├── Erosion
  │   └── Binary operations
  └── Functional API
      ├── image_filters_functional.py
      └── morphological_filters_functional.py

StainNormalizer
  ├── TransformerStainMatrixMixin
  ├── Macenko normalization
  ├── fit() - Calculate reference matrix
  └── transform() - Apply normalization

Scorer (Protocol)
  ├── RandomScorer
  ├── CellularityScorer
  └── Custom implementations

Data Registry
  ├── Sample dataset registry
  ├── SHA256 hash validation
  ├── Legacy dataset support
  └── Remote URL mapping

Utilities
  ├── apply_mask_image()
  ├── np_to_pil()
  ├── Image format conversion
  ├── Mask operations
  └── Region calculations
```

---

## Module Breakdown

### 1. **Slide Module** (`slide.py`)

**Purpose**: Primary abstraction for whole-slide images (WSI)

**Key Responsibility**: Handle I/O with microscopy image files, manage backend switching

**Class: `Slide`**
```python
Slide(
    path: str,
    processed_path: str,  # REQUIRED - output directory
    use_largeimage: bool = False
)
```

**Key Features**:
- **Required Parameter**: `processed_path` (unlike GlassCut where it's internal)
- **Backend Management**: OpenSlide primary, large_image fallback
- **Resolution Access**: 
  - `base_mpp`: Microns-per-pixel at scan magnification
  - `properties`: Access to slide metadata

**Key Methods**:
- `slide.read_region(coordinates, level, size)` - Read image region
- `slide.get_thumbnail(size)` - Get thumbnail
- `slide.scaled_image(scale_factor)` - Generate scaled version
- `slide.thumbnail_from_mask(mask)` - Create thumbnail from mask
- `slide.has_valid_tissue_detection_level(level)` - Validate level

**Design Pattern**: 
- **Adapter Pattern** for backend switching
- **Lazy Loading** for expensive properties
- **Mandatory Initialization** parameter (processed_path)

**Usage**:
```python
from histolab.slides import Slide

# Must specify processed_path
slide = Slide(
    path="/path/to/slide.svs",
    processed_path="/path/to/output",
    use_largeimage=False  # Optional fallback
)

# Access properties
mpp = slide.base_mpp
region = slide.read_region((x, y), level, (width, height))
```

**Error Handling**:
- `TypeError` if `processed_path` is None
- `ModuleNotFoundError` if `use_largeimage=True` without large_image installed
- `ValueError` for invalid mpp resolution
- `MayNeedLargeImageError` for resolution issues

### 2. **Tile Module** (`tile.py`)

**Purpose**: Represent extracted tiles with filter application capability

**Class: `Tile`**
```python
Tile(
    image: PIL.Image.Image,
    coords: CoordinatePair,
    level: int,
    slide: Slide
)
```

**Key Features**:
- **Immutable Design**: `apply_filters()` returns new Tile
- **Filter Application**: Chain filters for preprocessing
- **Tissue Detection**: Quality assessment via tissue percentage
- **Lazy Properties**: Computed on-demand

**Key Methods**:
- `tile.apply_filters(filters)` - Apply filter(s) → new Tile
- `tile.has_enough_tissue(tissue_percent=80)` - Quality check
- `tile.tissue_ratio` - Current tissue percentage
- `tile.coords` - Coordinate pair (x, y)

**Key Properties**:
- `image` - PIL Image data
- `level` - Pyramid level
- `slide` - Reference to parent Slide

**Design Pattern**:
- **Immutable/Functional Design**: Filters create new instances
- **Quality Gate Pattern**: has_enough_tissue() as filter
- **Lazy Evaluation**: Properties computed when accessed

**Tissue Detection Parameters**:
- `tissue_percent` (default: 80%) - Minimum required tissue
- `near_zero_var_threshold` - Variance threshold for tissue detection

**Usage**:
```python
from histolab.tiles import Tile
from histolab.filters import RgbToGrayscale, OtsuThreshold

# Create with image and metadata
tile = Tile(
    image=pil_image,
    coords=(1000, 2000),
    level=0,
    slide=slide
)

# Apply filters (immutable - returns new Tile)
filters = [RgbToGrayscale(), OtsuThreshold()]
processed_tile = tile.apply_filters(filters)

# Check tissue quality
if tile.has_enough_tissue(tissue_percent=80):
    print("Tile has sufficient tissue")
```

### 3. **Tiler Module** (`tiler.py`)

**Purpose**: Define protocol for tile extraction strategies

**Protocol: `Tiler`**
```python
@runtime_checkable
class Tiler(Protocol):
    def extract(self, slide: Slide) -> Generator[Tile, None, None]:
        """Extract tiles from slide"""
        ...
    
    def locate_tiles(
        self, 
        slide: Slide, 
        scale_factor: float = 32,
        colors: Optional[List] = None,
        alpha: int = 128,
        linewidth: int = 1,
        tiles: Optional[Iterable[Tile]] = None
    ) -> PIL.Image.Image:
        """Visualize tile locations"""
        ...
```

**Key Features**:
- **Protocol-Based Abstraction**: No concrete base class
- **Generator Pattern**: Memory efficient streaming
- **Visualization Support**: Mark tile locations on slide
- **Flexible Colors**: RGB or named color support

**Concrete Implementations** (typically in tests/examples):
- `GridTiler` - Regular grid of tiles
- `RandomTiler` - Random sampling
- Custom implementations via protocol

**Design Pattern**:
- **Strategy Pattern**: Pluggable extraction algorithms
- **Protocol Pattern**: Composition over inheritance
- **Generator Pattern**: Memory efficiency for large slides

**Visualization Parameters**:
- `scale_factor` (default: 32) - Scale for visualization
- `colors` - Tile outline colors (list of colors or RGB tuples)
- `alpha` - Transparency (0-255)
- `linewidth` - Border thickness
- `tiles` - Pre-extracted tiles (optional, re-extracts if None)

**Usage**:
```python
from histolab.tiler import GridTiler  # Example implementation

tiler = GridTiler(tile_size=512, overlap=64)

# Extract tiles
for tile in tiler.extract(slide):
    if tile.has_enough_tissue():
        process(tile)

# Visualize
visualization = tiler.locate_tiles(
    slide,
    scale_factor=32,
    colors=['red', 'blue'],
    alpha=128
)
visualization.save("tiles_visualization.png")
```

### 4. **Masks Module** (`masks.py`)

**Purpose**: Define binary mask strategies for tissue detection

**Abstract Base Class: `BinaryMask`**
```python
class BinaryMask(ABC):
    @abstractmethod
    def get_mask(self, slide: Slide) -> np.ndarray:
        """Generate binary mask"""
        ...
    
    @cached_property
    def tissue_mask(self) -> np.ndarray:
        """Cached tissue mask"""
        ...
```

**Concrete Implementation: `BiggestTissueBoxMask`**
```python
class BiggestTissueBoxMask(BinaryMask):
    def __init__(self, slide: Slide):
        self._slide = slide
    
    def get_mask(self, slide: Slide) -> np.ndarray:
        """Get largest contiguous tissue region"""
        ...
```

**Key Features**:
- **ABC Pattern**: Enforce mask generation interface
- **Caching**: LRU cache for mask performance
- **Filter-Based Generation**: Uses filter compositions
- **Region Detection**: Find largest tissue box

**Design Pattern**:
- **Strategy Pattern**: Different mask generation strategies
- **Caching Pattern**: Avoid recomputation
- **Factory Integration**: Uses FiltersComposition

**Usage**:
```python
from histolab.masks import BiggestTissueBoxMask

mask_strategy = BiggestTissueBoxMask(slide)
tissue_mask = mask_strategy.get_mask(slide)

# Apply to image
from histolab.util import apply_mask_image
masked_image = apply_mask_image(image, tissue_mask)
```

### 5. **Filters System** (`filters/`)

**Package Structure**:
```
filters/
├── __init__.py                          # Public API
├── image_filters.py                     # Image filter protocols and classes
├── image_filters_functional.py          # Functional API
├── morphological_filters.py            # Morphological operations
├── morphological_filters_functional.py # Functional morphological
├── compositions.py                      # Filter composition factory
└── util.py                              # Filter utilities
```

#### **5a. Image Filters** (`image_filters.py`)

**Protocol: `Filter` (Base)**
```python
@runtime_checkable
class Filter(Protocol):
    def __call__(self, input_data) -> Any:
        """Apply filter to input"""
        ...
```

**Protocol: `ImageFilter`**
```python
@runtime_checkable
class ImageFilter(Filter, Protocol):
    def __call__(self, pil_image: PIL.Image.Image) -> PIL.Image.Image:
        """Apply filter to PIL Image"""
        ...
```

**Key Filter Classes**:

- **`Compose`**: Chain multiple filters
  ```python
  composed = Compose([
      RgbToGrayscale(),
      OtsuThreshold(),
      RemoveSmallObjects()
  ])
  result = composed(image)
  ```

- **`Lambda`**: Wrap arbitrary functions
  ```python
  custom_filter = Lambda(lambda img: img.convert('RGB'))
  ```

- **`RgbToGrayscale`**: Convert RGB to grayscale using specific channel
  ```python
  gray_filter = RgbToGrayscale()
  ```

- **`OtsuThreshold`**: Automatic threshold using Otsu's method
  ```python
  threshold = OtsuThreshold()
  ```

- **Threshold Filters**:
  - `RedThreshold(threshold=150)` - Red channel
  - `GreenThreshold(threshold=150)` - Green channel
  - `BlueThreshold(threshold=150)` - Blue channel

**Design Pattern**:
- **Composite Pattern**: Compose filters into pipelines
- **Protocol Pattern**: Any callable can act as filter
- **Decorator Pattern**: Wrap functionality with Lambda

#### **5b. Morphological Filters** (`morphological_filters.py`)

**Protocol: `MorphologicalFilter`**
```python
@runtime_checkable
class MorphologicalFilter(Filter, Protocol):
    def __call__(self, np_mask: np.ndarray) -> np.ndarray:
        """Apply morphological filter to mask"""
        ...
```

**Key Filter Classes**:

- **`RemoveSmallObjects`**: Remove tiny disconnected components
  ```python
  filter = RemoveSmallObjects(
      min_size=3000,
      avoid_overmask=True,
      overmask_thresh=95
  )
  ```

- **`RemoveSmallHoles`**: Fill small holes in mask
  ```python
  filter = RemoveSmallHoles(area_threshold=3000)
  ```

- **`Dilation`**: Expand white regions
  ```python
  filter = Dilation(kernel_size=5)
  ```

- **`Erosion`**: Shrink white regions
  ```python
  filter = Erosion(kernel_size=5)
  ```

#### **5c. Filter Compositions** (`compositions.py`)

**Factory Class: `FiltersComposition`**
```python
class FiltersComposition:
    @staticmethod
    def of(obj_type) -> List[Filter]:
        """Get filter composition for object type"""
        
        # Returns different chains based on input:
        # - Slide → comprehensive mask generation chain
        # - Tile → preprocessing chain
        # - Custom → user-defined
```

**Composition Strategies**:
- **Slide Composition**: Heavy filtering for mask generation
  ```python
  filters = FiltersComposition.of(slide)
  # Typically: RGB→Grayscale→Threshold→Morphological ops
  ```

- **Tile Composition**: Light filtering for preprocessing
  ```python
  filters = FiltersComposition.of(tile)
  # Typically: Format conversion→specific filters
  ```

**Design Pattern**:
- **Factory Pattern**: Generate filter chains
- **Strategy Pattern**: Different chains per type
- **Template Pattern**: Predefined composition recipes

**Usage**:
```python
from histolab.filters import FiltersComposition

# Get appropriate chain
filters = FiltersComposition.of(slide)

# Or compose manually
from histolab.filters import Compose, RgbToGrayscale, OtsuThreshold

pipeline = Compose([
    RgbToGrayscale(),
    OtsuThreshold(),
])
result = pipeline(image)
```

**Functional APIs**:
- `image_filters_functional.py`: Low-level image operations
- `morphological_filters_functional.py`: Low-level morphological ops

### 6. **Stain Normalizer Module** (`stain_normalizer.py`)

**Purpose**: Normalize color variations across slides

**Mixin Class: `TransformerStainMatrixMixin`**
```python
class TransformerStainMatrixMixin:
    def fit(self, target: np.ndarray) -> 'Normalizer':
        """Learn from reference slide"""
        ...
    
    def transform(self, source: np.ndarray) -> np.ndarray:
        """Normalize source to reference"""
        ...
```

**Key Features**:
- **Fit-Transform Pattern**: sklearn-like interface
- **Matrix-Based**: Uses stain color matrices
- **References**: Macenko, HistomicsTK, torchstain
- **Stateful**: Reference learned during fit

**Algorithm Overview**:
1. Extract stain vectors from image
2. Normalize stain matrix
3. Calculate transformation
4. Apply to source image

**Design Pattern**:
- **Mixin Pattern**: Compose with normalizer classes
- **Transformer Pattern**: fit() then transform()
- **Pipeline Integration**: Works with Compose

**Usage**:
```python
from histolab.stain_normalizer import StainNormalizer

normalizer = StainNormalizer()

# Learn from reference
normalizer.fit(reference_slide_array)

# Apply to other slides
normalized = normalizer.transform(source_slide_array)
```

### 7. **Scorer Module** (`scorer.py`)

**Purpose**: Assess tile quality for inclusion/filtering

**Protocol: `Scorer`**
```python
@runtime_checkable
class Scorer(Protocol):
    def score(self, tile: Tile) -> float:
        """Score tile quality (0-1 or arbitrary)"""
        ...
```

**Implementation: `RandomScorer`**
```python
class RandomScorer:
    def score(self, tile: Tile) -> float:
        """Return random scores for testing"""
        ...
```

**Implementation: `CellularityScorer`**
```python
class CellularityScorer:
    def score(self, tile: Tile) -> float:
        """Score based on tissue cellularity/density"""
        ...
```

**Design Pattern**:
- **Strategy Pattern**: Pluggable scoring algorithms
- **Protocol Pattern**: Composition over inheritance
- **Extensibility**: Easy to add custom scorers

**Usage**:
```python
from histolab.scorer import CellularityScorer

scorer = CellularityScorer()

for tile in tiler.extract(slide):
    score = scorer.score(tile)
    if score > 0.5:  # Keep high-quality tiles
        save_tile(tile)
```

### 8. **Types Module** (`types.py`)

**Purpose**: Define common type definitions

**NamedTuple: `CoordinatePair`**
```python
CoordinatePair = NamedTuple('CoordinatePair', [
    ('x', int),
    ('y', int)
])

CP = CoordinatePair  # Alias
```

**NamedTuple: `Region`**
```python
Region = NamedTuple('Region', [
    ('x', int),
    ('y', int),
    ('w', int),  # Width
    ('h', int)   # Height
])
```

**Design Pattern**:
- **Value Object Pattern**: Immutable coordinate representation
- **Type Safety**: Namedtuple with named fields
- **Utility Types**: Support for clean APIs

**Usage**:
```python
from histolab.types import CoordinatePair, Region

# Create coordinates
coords = CoordinatePair(x=1000, y=2000)

# Create region
region = Region(x=100, y=200, w=512, h=512)

# Access properties
print(coords.x, coords.y)
print(region.w, region.h)
```

### 9. **Exceptions Module** (`exceptions.py`)

**Purpose**: Define custom exceptions for error handling

**Exception Hierarchy**:
```
Exception
├── HistolabException (base)
│   ├── FilterCompositionError
│   ├── LevelError
│   ├── MayNeedLargeImageError
│   ├── SlidePropertyError
│   └── TileSizeOrCoordinatesError
```

**Key Exceptions**:

- **`HistolabException`**: Base exception class
  ```python
  try:
      ...
  except HistolabException as e:
      handle_histolab_error(e)
  ```

- **`FilterCompositionError`**: Invalid filter chain
  ```python
  # Raised when filter composition fails
  ```

- **`LevelError`**: Invalid pyramid level
  ```python
  # Raised for invalid level access
  ```

- **`MayNeedLargeImageError`**: large_image might help
  ```python
  # Raised when OpenSlide insufficient
  ```

- **`SlidePropertyError`**: Property access issue
  ```python
  # Raised for invalid slide properties
  ```

- **`TileSizeOrCoordinatesError`**: Invalid tile specs
  ```python
  # Raised for invalid tile region
  ```

**Design Pattern**:
- **Hierarchy Pattern**: Specific exceptions for catch
- **Context Pattern**: Descriptive error messages
- **Guidance Pattern**: Suggests use of large_image when needed

**Usage**:
```python
from histolab.exceptions import (
    HistolabException,
    MayNeedLargeImageError,
    FilterCompositionError
)

try:
    tile = extract_tile(slide)
except MayNeedLargeImageError:
    slide = Slide(path, processed_path, use_largeimage=True)
except FilterCompositionError as e:
    print(f"Filter error: {e}")
```

### 10. **Mixins Module** (`mixins.py`)

**Purpose**: Shared functionality for stain normalizers

**Mixin Class: `LinalgMixin`**
```python
class LinalgMixin:
    @staticmethod
    def normalize_columns(matrix: np.ndarray) -> np.ndarray:
        """L2 normalize matrix columns"""
        ...
    
    @staticmethod
    def principal_components(matrix: np.ndarray, k: int = 2) -> np.ndarray:
        """Extract principal components via SVD"""
        ...
```

**Key Methods**:
- `normalize_columns()`: L2 normalization for each column
- `principal_components()`: PCA via Singular Value Decomposition

**Design Pattern**:
- **Mixin Pattern**: Compose into normalizer classes
- **Static Method Pattern**: Utility functions
- **Linear Algebra Pattern**: Matrix operations

**Usage**:
```python
from histolab.mixins import LinalgMixin

# Use in custom normalizer
class CustomNormalizer(LinalgMixin):
    def normalize(self, matrix: np.ndarray) -> np.ndarray:
        return self.normalize_columns(matrix)
```

### 11. **Utilities Module** (`util.py`)

**Purpose**: Common utility functions

**Key Functions**:

- **`apply_mask_image(image, mask)`**: Apply binary mask to image
  ```python
  masked = apply_mask_image(pil_image, binary_mask)
  ```

- **`np_to_pil(np_array)`**: Convert NumPy array to PIL Image
  ```python
  # Handles dtype conversion (bool, float64, uint8)
  pil_image = np_to_pil(numpy_array)
  ```

- **`refine_thumbnail_size_preserving_aspect_ratio()`**: Resize maintaining aspect
  ```python
  new_size = refine_thumbnail_size_preserving_aspect_ratio(
      thumbnail_size=(150, 150),
      original_size=(2000, 3000)
  )
  ```

- **Region calculations**: Properties and measurements

**Design Pattern**:
- **Utility Pattern**: Static helper functions
- **Format Conversion**: Data type transformations
- **Image Processing**: Mask and region utilities

**Usage**:
```python
from histolab.util import apply_mask_image, np_to_pil

# Convert arrays to PIL
pil_img = np_to_pil(numpy_array)

# Apply masks
masked_img = apply_mask_image(pil_img, mask_array)

# Maintain aspect ratio
new_dims = refine_thumbnail_size_preserving_aspect_ratio(
    (200, 200), 
    (4000, 6000)
)
```

### 12. **Data Registry** (`data/_registry.py`)

**Purpose**: Manage sample datasets for testing/examples

**Registry Contents**:
```python
registry = {
    "histolab/broken.svs": "sha256_hash",
    "histolab/kidney.png": "sha256_hash",
    "data/cmu_small_region.svs": "sha256_hash",
    "aperio/JP2K-33003-1.svs": "sha256_hash",
    # ... TCGA, IDR datasets
}

registry_urls = {
    "histolab/broken.svs": "https://raw.github...",
    # ... URLs for each dataset
}
```

**Features**:
- SHA256 validation for integrity
- Legacy dataset support
- Multiple data sources (Aperio, TCGA, IDR)
- Automatic download capability

**Design Pattern**:
- **Registry Pattern**: Central dataset catalog
- **Hash Validation**: Integrity checking
- **URL Mapping**: Flexible data sources

**Usage**:
```python
from histolab.data import registry

# Access sample data
test_file = registry["histolab/kidney.png"]

# Verify integrity
from histolab.data import registry_urls
url = registry_urls[test_file]
```

---

## Design Patterns

### 1. **Protocol Pattern**
Used extensively for maximum flexibility:
- `Filter`, `ImageFilter`, `MorphologicalFilter`
- `Tiler`, `Scorer`
- `@runtime_checkable` enables duck typing

**Benefit**: Add new implementations without base class inheritance

### 2. **Strategy Pattern**
Different implementations of same interface:
- **Masks**: `BiggestTissueBoxMask`, custom implementations
- **Scorers**: `RandomScorer`, `CellularityScorer`
- **Tilers**: `GridTiler`, `RandomTiler`, custom

**Benefit**: Plugin architecture without modification

### 3. **Factory Pattern**
`FiltersComposition.of()` generates filter chains:
- Different chains for Slide vs Tile
- Encapsulates composition logic
- Easy to extend with new types

**Benefit**: Centralized creation logic

### 4. **Composite Pattern**
`Compose` chains filters:
- Treats single filter and composed pipeline uniformly
- Recursive composition possible
- Clean API

**Benefit**: Flexible filter pipelines

### 5. **Mixin Pattern**
`TransformerStainMatrixMixin` provides shared functionality:
- Stain normalizers inherit to get fit/transform
- `LinalgMixin` provides matrix operations
- Composition over inheritance

**Benefit**: Clean code without deep hierarchies

### 6. **Adapter Pattern**
Slide class adapts between OpenSlide and large_image:
- Unified interface for both backends
- Backend switching transparent
- Error handling for compatibility

**Benefit**: Seamless backend switching

### 7. **Lazy Evaluation Pattern**
Properties computed on-demand:
- `@lazyproperty` decorator
- `@cached_property` for expensive operations
- Performance optimization

**Benefit**: Fast startup, compute on access

### 8. **Generator Pattern**
`Tiler.extract()` yields tiles:
- Memory efficient for large slides
- Streaming processing
- Can stop extraction early

**Benefit**: Handle massive datasets

---

## Module Communication

### Data Flow Diagram

```
User Code
    │
    ├─► Slide  ◄──────────────┐
    │    │                    │
    │    ├─► Read WSI         │
    │    ├─► Get metadata     │
    │    └─► Provide regions  │
    │                         │
    │                    Backend I/O
    │                   (OpenSlide or
    │                    large_image)
    │
    ├─► Tiler ◄──────────────┐
    │    │                   │
    │    ├─► Ask Slide for   │
    │    │   regions         │
    │    │                   │
    │    └─► Yield Tiles ────┼─► Users
    │                        │
    │                    (Extract
    │                     Tiles)
    │
    ├─► Tile ◄──────────────────────┐
    │    │                          │
    │    ├─► apply_filters()        │
    │    │   │                      │
    │    │   ├─► ImageFilter        │
    │    │   └─► MorphologicalFilter│
    │    │       (from Filters      │
    │    │        System)           │
    │    │                          │
    │    ├─► has_enough_tissue()    │
    │    │                          │
    │    └─► score() ◄──────┐       │
    │                       │    (Quality
    │                    Scorer   Check)
    │                       │
    │        ┌──────────────┘
    │        │
    ├─► BinaryMask ◄──────────────┐
    │    │                        │
    │    ├─► Uses                │
    │    │   FiltersComposition  │
    │    │   (Slide-specific     │
    │    │    filter chain)      │
    │    │                       │
    │    └─► get_mask()          │
    │        (Returns             │
    │         np.ndarray)         │
    │                            │
    └────────────────────────────┘


Preprocessing Pipeline:
────────────────────────

Image File
    │
    ├─► Slide.read_region()
    │    │
    │    └─► PIL.Image
    │
    ├─► Tile (wraps image)
    │    │
    │    ├─► apply_filters(FiltersComposition.of(Slide))
    │    │    │
    │    │    ├─► RgbToGrayscale()
    │    │    ├─► OtsuThreshold()
    │    │    ├─► RemoveSmallObjects()
    │    │    └─► RemoveSmallHoles()
    │    │
    │    └─► Result: Binary Mask
    │
    ├─► BinaryMask.get_mask()
    │    │
    │    └─► Largest tissue region
    │
    ├─► Tile.apply_filters(user_filters)
    │    │
    │    ├─► RGB normalization
    │    ├─► Stain normalization
    │    └─► Custom preprocessing
    │
    └─► Quality checks
         │
         ├─► has_enough_tissue()
         ├─► Scorer.score()
         └─► Custom filtering
```

### Typical Workflow

```
1. Load Slide
   ├─ Slide(path, processed_path)
   ├─ Initialize backend (OpenSlide or large_image)
   └─ Cache metadata

2. Generate Tissue Mask
   ├─ BinaryMask strategy selection
   ├─ Apply filter composition
   └─ Get binary tissue map

3. Extract Tiles via Tiler
   ├─ Ask Slide for region coordinates
   ├─ Read region from WSI
   ├─ Create Tile object with image
   └─ Yield to caller

4. Process Tile
   ├─ Apply preprocessing filters
   ├─ Check tissue percentage
   ├─ Score quality
   └─ Accept/reject

5. Output
   ├─ Save to processed_path
   ├─ Store metadata
   └─ Generate statistics
```

---

## Key Differentiators

### HistoLab vs GlassCut

| Feature | HistoLab | GlassCut |
|---------|----------|----------|
| **Mandatory Output Path** | Yes (required parameter) | No (internal) |
| **Backend Strategy** | OpenSlide primary, large_image fallback | cuCIM first, OpenSlide fallback |
| **Filter System** | Built-in comprehensive filters | Injected via properties |
| **Scoring** | Built-in (RandomScorer, CellularityScorer) | Not built-in |
| **Mask Strategy** | BinaryMask ABC with implementations | TissueDetector protocol |
| **Tiler** | Protocol-based (strategy pattern) | Not explicitly exposed |
| **Architecture** | Protocol-heavy | Backend-focused |
| **Extensibility** | Protocol composition | Backend abstraction |
| **Use Case** | Multi-strategy preprocessing | Simple, fast tile extraction |

### HistoLab vs PathoPatcher

| Feature | HistoLab | PathoPatcher |
|---------|----------|-------------|
| **Architecture** | Protocol-based, clean separation | Production pipeline, all-in-one |
| **Configuration** | Python API primarily | YAML configuration |
| **Backend** | Bundled (OpenSlide/large_image) | Bundled (multiple WSI interfaces) |
| **Preprocessing** | Strategy-based (masks, filters) | Fixed pipeline |
| **Scale** | Single slide focus | Batch processing oriented |
| **Threading** | Not built-in | Multiprocessing support |
| **Output** | File-based | Formatted patches (PNG, HDF5, etc.) |
| **Interfaces** | Library API | CLI + Python API |

---

## Processing Pipelines

### Pipeline 1: Basic Tile Extraction

```python
# Setup
slide = Slide(path="/slide.svs", processed_path="/output")
tiler = GridTiler(tile_size=512, overlap=50)

# Extract
for tile in tiler.extract(slide):
    # Tile is raw extraction
    if tile.has_enough_tissue(tissue_percent=80):
        tile.image.save(f"/output/tile_{tile.coords.x}_{tile.coords.y}.png")
```

### Pipeline 2: Preprocessing + Quality Check

```python
from histolab.filters import FiltersComposition

slide = Slide(path="/slide.svs", processed_path="/output")
tiler = GridTiler(tile_size=512)
scorer = CellularityScorer()
filters = FiltersComposition.of(Tile)  # Tile preprocessing

tiles_to_save = []
for tile in tiler.extract(slide):
    # Preprocess
    processed = tile.apply_filters(filters)
    
    # Check quality
    if processed.has_enough_tissue() and scorer.score(tile) > 0.5:
        tiles_to_save.append(tile)

# Save high-quality tiles
for i, tile in enumerate(tiles_to_save):
    tile.image.save(f"/output/tile_{i}.png")
```

### Pipeline 3: Stain Normalization

```python
from histolab.stain_normalizer import StainNormalizer
import numpy as np

# Load reference and target
ref_slide = Slide(ref_path, proc_path)
target_slide = Slide(target_path, proc_path)

# Get reference region
ref_region = ref_slide.read_region((0, 0), level=0, size=(1000, 1000))
ref_array = np.array(ref_region)

# Initialize and fit normalizer
normalizer = StainNormalizer()
normalizer.fit(ref_array)

# Extract and normalize tiles
tiler = GridTiler(tile_size=512)
for tile in tiler.extract(target_slide):
    tile_array = np.array(tile.image)
    normalized = normalizer.transform(tile_array)
    
    # Convert back to PIL and save
    from histolab.util import np_to_pil
    normalized_img = np_to_pil(normalized)
    normalized_img.save(f"/output/normalized_{tile.coords}.png")
```

### Pipeline 4: Custom Mask + Advanced Filtering

```python
from histolab.masks import BinaryMask

class CustomTissueMask(BinaryMask):
    def get_mask(self, slide: Slide) -> np.ndarray:
        # Custom tissue detection logic
        region = slide.read_region((0, 0), level=2, size=(1024, 1024))
        # Process and return binary mask
        ...

mask_strategy = CustomTissueMask()
tissue_mask = mask_strategy.get_mask(slide)

# Use for tile filtering
verified_tiles = []
for tile in tiler.extract(slide):
    # Check if tile overlaps with valid tissue
    if verify_tissue_overlap(tile, tissue_mask):
        verified_tiles.append(tile)
```

---

## Extension Points

### 1. Custom Mask Strategy

```python
from histolab.masks import BinaryMask
import numpy as np

class AdaptiveThresholdMask(BinaryMask):
    """Custom mask using adaptive thresholding"""
    
    def __init__(self, window_size: int = 11):
        self.window_size = window_size
    
    def get_mask(self, slide: Slide) -> np.ndarray:
        # Get reference image
        region = slide.read_region((0, 0), level=2, size=(512, 512))
        
        # Apply adaptive threshold
        from skimage.filters import threshold_local
        mask = threshold_local(np.array(region.convert('L')), self.window_size) > 0
        
        return mask.astype(np.uint8)
```

### 2. Custom Scorer

```python
from histolab.scorer import Scorer

class EdgeDensityScorer:
    """Score tiles based on edge content"""
    
    def score(self, tile: Tile) -> float:
        from skimage.filter import sobel
        edges = sobel(np.array(tile.image.convert('L')))
        return float(np.mean(edges) / 255.0)
```

### 3. Custom Filter

```python
from histolab.filters import Filter
import PIL.ImageFilter as ImageFilter

class MedianBlur:
    """Simple median blur filter"""
    
    def __init__(self, radius: int = 3):
        self.radius = radius
    
    def __call__(self, pil_image: PIL.Image.Image) -> PIL.Image.Image:
        return pil_image.filter(ImageFilter.MedianFilter(self.radius))

# Use in pipeline
filters = [
    RgbToGrayscale(),
    MedianBlur(radius=5),
    OtsuThreshold()
]
```

### 4. Custom Tiler

```python
from histolab.tiler import Tiler
from typing import Generator

class Spiral Tiler:
    """Extract tiles in spiral pattern"""
    
    def __init__(self, tile_size: int = 512, start_center: bool = True):
        self.tile_size = tile_size
        self.start_center = start_center
    
    def extract(self, slide: Slide) -> Generator[Tile, None, None]:
        # Generate spiral coordinates
        for x, y in self._spiral_coordinates(slide):
            region = slide.read_region((x, y), level=0, (self.tile_size, self.tile_size))
            yield Tile(
                image=region,
                coords=(x, y),
                level=0,
                slide=slide
            )
    
    def _spiral_coordinates(self, slide):
        # Spiral algorithm
        ...
    
    def locate_tiles(self, slide, ...):
        # Visualization
        ...
```

### 5. Custom Filter Composition

```python
from histolab.filters import Compose

class HistopathologyPreprocessing(Compose):
    """Specialized preprocessing pipeline"""
    
    def __init__(self):
        filters = [
            RgbToGrayscale(),
            OtsuThreshold(),
            RemoveSmallObjects(min_size=5000),
            RemoveSmallHoles(area_threshold=2000),
            MedianBlur(radius=3)
        ]
        super().__init__(filters)

# Use
preprocessor = HistopathologyPreprocessing()
mask = preprocessor(slide_region)
```

---

## Performance Considerations

### Memory Efficiency
- **Generator-based extraction**: Tiles not held in memory simultaneously
- **Lazy properties**: Expensive computations on-demand
- **Cached operations**: Repeated accesses use cache

### Computation Optimization
- **Backend selection**: large_image for specific formats
- **Level selection**: Use lower levels for thumbnails
- **Mask caching**: BinaryMask uses `@cached_property`

### Scaling Considerations
- **Batch Processing**: No built-in, layer on PathoPatcher
- **Multiprocessing**: Implement custom worker pattern
- **Network I/O**: Consider data locality

---

## Error Handling

### Common Errors and Solutions

**1. TypeError: processed_path cannot be None**
```python
# Wrong
slide = Slide(path="/slide.svs")  # TypeError!

# Right
slide = Slide(path="/slide.svs", processed_path="/out")
```

**2. ModuleNotFoundError: large_image not installed**
```python
# If catching
try:
    slide = Slide(path, proc_path, use_largeimage=True)
except ModuleNotFoundError:
    # Install large_image or use OpenSlide
    slide = Slide(path, proc_path, use_largeimage=False)
```

**3. ValueError: Unknown scan resolution**
```python
# Large_image might have metadata OpenSlide lacks
try:
    mpp = slide.base_mpp
except ValueError:
    # Try with large_image
    slide2 = Slide(path, proc_path, use_largeimage=True)
    mpp = slide2.base_mpp
```

---

## Summary

HistoLab is a sophisticated, protocol-driven histopathology image processing library that emphasizes:

1. **Extensibility**: Protocol-based design for custom implementations
2. **Clean Architecture**: Clear separation of concerns across modules
3. **Preprocessing**: Comprehensive filter system for image manipulation
4. **Strategy Flexibility**: Pluggable masks, scorers, and tilers
5. **Quality Assurance**: Built-in tissue and quality metrics
6. **Backend Flexibility**: Support for multiple WSI backends

The library is ideal for research pipelines requiring:
- Multiple preprocessing strategies
- Custom quality assessment
- Complex tile filtering
- Extensible architecture

It pairs well with PathoPatcher for production batch processing and with GlassCut for simpler use cases.
