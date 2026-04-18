# GlassCut - Quick Reference Guide

## Module Quick Reference

### 🖼️ Slides Module (`glasscut/slides/`)

**What it does**: Manages whole slide images and tile extraction

**Key Classes**:
- **`Slide`** - Main API class
  - Properties: `name`, `dimensions`, `magnifications`, `mpp`, `properties`, `thumbnail`
  - Methods: `extract_tile()`, `extract_tiles()`, `close()`
  - Context manager: Use with `with` statement for auto cleanup

- **`SlideBackend`** - Abstract base
  - Concrete implementations: `OpenSlideBackend`, `CuCimBackend`
  - Interface: `open()`, `close()`, `read_region()`, `properties`, `dimensions`, `mpp`, etc.

**Dependencies**: 
- Uses `utils.lazyproperty` for caching
- Raises exceptions for validation errors
- Injects `TissueDetector` into created `Tile` objects

**When to use**:
```python
with Slide("path/to/slide.svs") as slide:
    tile = slide.extract_tile(coords=(1000, 1000), tile_size=(512, 512), magnification=20)
```

---

### 🎯 Tile Module (`glasscut/tile.py`)

**What it does**: Represents extracted image region with metadata and tissue analysis

**Key Class**: `Tile`
- **Attributes**: 
  - `image` - PIL.Image (RGB)
  - `coords` - (x, y) tuple
  - `magnification` - extraction level
  - `tissue_detector` - TissueDetector strategy

- **Methods**:
  - `has_enough_tissue(threshold=0.8)` - Returns bool
  - `save(path)` - Saves image to disk

- **Properties** (lazy-evaluated & cached):
  - `tissue_mask` - Binary mask (0=background, 1=tissue)
  - `tissue_ratio` - Float (0.0-1.0)

**Dependencies**:
- Depends on `utils.lazyproperty` for caching
- Uses `tissue_detectors.TissueDetector` strategy (injected)
- Uses `utils.np_to_pil` for conversion

**When to use**:
```python
tile = slide.extract_tile(...)
if tile.has_enough_tissue(threshold=0.8):
    print(f"Tissue ratio: {tile.tissue_ratio}")
    tile.save("output.png")
    mask = tile.tissue_mask  # Gets cached value on subsequent accesses
```

---

### 🔍 Tissue Detectors Module (`glasscut/tissue_detectors/`)

**What it does**: Provides strategies for tissue detection

**Base Class**: `TissueDetector` (ABC)
- **Method**: `detect(image: PIL.Image) -> np.ndarray`
  - Input: RGB PIL Image
  - Output: Binary mask (0 or 1)

**Concrete Implementation**: `OtsuTissueDetector`
- **Algorithm**: Otsu thresholding with optional morphological ops
- **Parameters**: `apply_prefilter`, `apply_morphology`, `morphology_disk_size`

**How it connects**:
- `Tile` receives `TissueDetector` instance (default: `OtsuTissueDetector`)
- Accessed lazily via `tile.tissue_mask`
- Result cached automatically

**How to extend**:
```python
class CustomDetector(TissueDetector):
    def detect(self, image: Image.Image) -> np.ndarray:
        # Your detection logic here
        return binary_mask

tile.tissue_detector = CustomDetector()
```

---

### 🧬 Stain Normalizers Module (`glasscut/stain_normalizers/`)

**What it does**: Normalizes stain color variations in histology images

**Base Class**: `StainNormalizer` (ABC)
- **Methods**:
  - `fit(target_image)` - Learn normalization from reference
  - `transform(image) -> PIL.Image` - Apply normalization

**Concrete Implementations**:
- **`MacenkoStainNormalizer`** - Unsupervised color deconvolution, best for H&E
- **`ReinhardtStainNormalizer`** - Color transfer, fast and interactive

**How to use**:
```python
normalizer = MacenkoStainNormalizer()
with Slide("reference.svs") as ref_slide:
    ref_tile = ref_slide.extract_tile(...)
    normalizer.fit(ref_tile.image)

with Slide("test.svs") as test_slide:
    test_tile = test_slide.extract_tile(...)
    normalized = normalizer.transform(test_tile.image)
```

**How it connects**:
- Independent module
- Works with `Tile.image` (PIL.Image)
- Returns PIL.Image for further processing

---

### 🛠️ Utils Module (`glasscut/utils.py`)

**What it does**: Shared utilities and decorators

**Components**:

1. **`lazyproperty` decorator**
   - Purpose: Lazy evaluation with automatic caching
   - Uses: `functools.lru_cache(maxsize=100)`
   - Used in: `Slide` properties, `Tile` properties
   - Benefit: Expensive computations computed only once

   ```python
   @lazyproperty
   def tissue_mask(self) -> np.ndarray:
       # Computed once, cached thereafter
       return self.tissue_detector.detect(self.image)
   ```

2. **`np_to_pil(np_img)` function**
   - Purpose: Convert NumPy arrays to PIL Images
   - Handles: Bool, float64, uint8 conversion
   - Used in: Stain normalizers, mask visualization

**When to use**:
- Use `lazyproperty` for expensive properties that might not always be accessed
- Use `np_to_pil` when converting algorithm outputs to displayable images

---

### ⚠️ Exceptions Module (`glasscut/exceptions.py`)

**Exception Hierarchy**:
```
GlassCutException (base)
├── SlidePropertyError      - Property unavailable
├── BackendError           - Backend failure
├── MagnificationError     - Invalid magnification
├── TileSizeOrCoordinatesError - Invalid tile params
└── FilterCompositionError - Filter issue
```

**When raised**:
```python
# MagnificationError
tile = slide.extract_tile(..., magnification=99)  # Not available!

# TileSizeOrCoordinatesError
tile = slide.extract_tile(coords=(999999, 999999), ...)  # Out of bounds!

# SlidePropertyError
mpp = slide.mpp  # Property missing in metadata
```

**How to handle**:
```python
from glasscut.exceptions import MagnificationError, TileSizeOrCoordinatesError

try:
    tile = slide.extract_tile(...)
except MagnificationError:
    print(f"Use magnifications: {slide.magnifications}")
except TileSizeOrCoordinatesError:
    print(f"Slide size: {slide.dimensions}")
```

---

## Communication Patterns

### Pattern 1: Lazy Evaluation & Caching
```
First access:  property → computation → cache
Second access: property → return from cache
```
Used for: `tissue_mask`, `tissue_ratio`, slide `magnifications`, etc.

### Pattern 2: Strategy Injection
```
User creates: Tile(..., tissue_detector=CustomDetector())
At runtime:   tile.method(...) → uses injected strategy
```
Used for: `TissueDetector`, `StainNormalizer`, `SlideBackend`

### Pattern 3: Backend Fallback
```
Try:    CuCimBackend() 
Fallback: OpenSlideBackend()
```
Transparent to user, automatic failover

### Pattern 4: Context Manager
```
with Slide(...) as slide:
    # Resources allocated
    ...
# Resources freed automatically
```
Ensures proper cleanup

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────┐
│                  Application Code                   │
└────────┬────────────────────────────────────────────┘
         │
         ├──> Slide(path)
         │      ├─> Backend selection (cuCim/OpenSlide)
         │      └─> Metadata calculation (magnifications, mpp)
         │
         ├──> slide.extract_tile(coords, size, mag)
         │      ├─> Validation (magnification, coords)
         │      ├─> Backend.read_region() → PIL.Image
         │      └─> Tile creation
         │
         ├──> tile.has_enough_tissue()
         │      ├─> First access: tissue_detector.detect()
         │      ├─> Cache result
         │      └─> Calculate ratio → return bool
         │
         ├──> normalizer.fit(ref_image)
         │      └─> Learn stain vectors
         │
         └──> normalizer.transform(image)
              └─> Apply normalization → Normalized PIL.Image
```

---

## When Each Module is Involved

| Task | Modules | Method |
|------|---------|--------|
| Load WSI | Slide, Backend | `Slide(path)` |
| Get metadata | Slide | `slide.magnifications`, `slide.dimensions` |
| Extract single tile | Slide, Backend, Tile | `slide.extract_tile()` |
| Extract multiple | Slide, Backend, Tile | `slide.extract_tiles()` with parallelization |
| Detect tissue | Tile, TissueDetector | `tile.has_enough_tissue()` |
| Get tissue ratio | Tile, TissueDetector | `tile.tissue_ratio` |
| Visualize tissue | Tile, utils | `tile.tissue_mask` → `np_to_pil()` |
| Normalize stain | StainNormalizer, utils | `normalizer.fit()` → `normalizer.transform()` |
| Save output | Tile, PIL | `tile.save()` |
| Handle errors | exceptions | Catch specific exceptions |

---

## Dependency Graph (Simplified)

```
Application
    │
    ├─→ Slide ←─ utils(lazyproperty)
    │   ├─→ Backend (OpenSlide/cuCim)
    │   └─→ Tile
    │
    ├─→ Tile ←─ utils(lazyproperty)
    │   └─→ TissueDetector(strategy)
    │
    ├─→ TissueDetector
    │   └─→ OtsuTissueDetector
    │       └─→ scikit-image
    │
    ├─→ StainNormalizer
    │   ├─→ MacenkoStainNormalizer
    │   └─→ ReinhardtStainNormalizer
    │       └─→ utils(np_to_pil)
    │
    └─→ exceptions
        └─→ GlassCutException (base)
```

---

## Extension Points

### 1. Custom Tissue Detector
**File**: Create new class inheriting from `TissueDetector`
```python
class MyDetector(TissueDetector):
    def detect(self, image: Image.Image) -> np.ndarray:
        # Your logic
        return mask
```

### 2. Custom Backend
**File**: Create new class inheriting from `SlideBackend`
```python
class MyBackend(SlideBackend):
    def open(self, path):
        # Your logic
    def read_region(self, location, level, size):
        # Your logic
        return image
```

### 3. Custom Stain Normalizer
**File**: Create new class inheriting from `StainNormalizer`
```python
class MyNormalizer(StainNormalizer):
    def fit(self, target_image, **kwargs):
        # Learn parameters
    def transform(self, image, **kwargs):
        # Apply normalization
        return normalized_image
```

---

## Performance Considerations

1. **Lazy Properties**: First access is slow, subsequent accesses are fast (cached)
   - Use `tile.tissue_mask` multiple times efficiently

2. **Parallel Extraction**: `extract_tiles()` is faster than sequential `extract_tile()`
   - Use `num_workers=4+` for optimal performance

3. **Backend Selection**: cuCim (GPU) >> OpenSlide (CPU) for large-scale extraction
   - Default behavior: try cuCim, fallback to OpenSlide

4. **Caching**: Tissue detection is cached per tile
   - Don't recreate tiles unnecessarily

5. **Stain Normalization**: Fit once, transform many times
   - Reuse normalizer instance for batch processing

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `MagnificationError` | Requested magnification unavailable | Check `slide.magnifications` |
| `TileSizeOrCoordinatesError` | Tile outside slide bounds | Verify coords with `slide.dimensions` |
| Slow extraction | Sequential tile extraction | Use `extract_tiles()` with parallelization |
| Out of memory | Too many tiles in memory | Process in batches |
| Tissue detection variable | Different detector behavior | Use consistent `TissueDetector` |
| Stain variation | Normalizer not fitted | Call `normalizer.fit()` before transform |

---

## Example: All Modules Working Together

```python
from glasscut.slides import Slide
from glasscut.stain_normalizers import MacenkoStainNormalizer
import json

# Step 1: Load slide (Slide module + Backend)
with Slide("slide.svs") as slide:
    print(f"Magnifications: {slide.magnifications}")
    
    # Step 2: Extract tiles (Slide + Backend + Tile)
    tiles = slide.extract_tiles(
        coords_list=[(i*512, j*512) for i in range(5) for j in range(5)],
        tile_size=(512, 512),
        magnification=20,
        num_workers=4
    )
    
    # Step 3: Initialize normalizer (StainNormalizer)
    normalizer = MacenkoStainNormalizer()
    normalizer.fit(tiles[0].image)
    
    # Step 4: Process tiles (Tile + TissueDetector + StainNormalizer + utils)
    results = []
    for i, tile in enumerate(tiles):
        # Check tissue (Tile + TissueDetector)
        if tile.has_enough_tissue(threshold=0.8):
            # Normalize stain (StainNormalizer)
            normalized = normalizer.transform(tile.image)
            
            # Save (Tile + utils)
            tile.save(f"output/{i}_original.png")
            normalized.save(f"output/{i}_normalized.png")
            
            # Record metadata (utils for calculations)
            results.append({
                "index": i,
                "tissue_ratio": tile.tissue_ratio,
                "coords": tile.coords
            })
    
    # Step 5: Save metadata
    with open("output/metadata.json", "w") as f:
        json.dump(results, f)
```

