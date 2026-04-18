# HistoLab Quick Reference Guide

**Last Updated**: Current Session  
**Purpose**: Quick lookup for common HistoLab operations  
**Target Audience**: Developers already familiar with histopathology image processing

---

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Core API Reference](#core-api-reference)
3. [Common Workflows](#common-workflows)
4. [Configuration](#configuration)
5. [Cheat Sheet](#cheat-sheet)
6. [Troubleshooting](#troubleshooting)

---

## Installation & Setup

### Basic Installation

```bash
# Via pip
pip install histolab

# With optional large_image backend
pip install histolab[large_image]

# Development
git clone https://github.com/histolab/histolab.git
cd histolab
pip install -e ".[dev]"
```

### Imports

```python
# Core
from histolab.slides import Slide
from histolab.tiles import Tile
from histolab.tiler import Tiler

# Filters
from histolab.filters import (
    Compose,
    RgbToGrayscale,
    OtsuThreshold,
    Lambda
)
from histolab.filters.morphological_filters import (
    RemoveSmallObjects,
    RemoveSmallHoles,
    Dilation,
    Erosion
)
from histolab.filters.compositions import FiltersComposition

# Masks
from histolab.masks import BinaryMask, BiggestTissueBoxMask

# Scoring
from histolab.scorer import RandomScorer, CellularityScorer

# Stain normalization
from histolab.stain_normalizer import StainNormalizer

# Types
from histolab.types import CoordinatePair, Region, CP

# Utilities
from histolab.util import apply_mask_image, np_to_pil

# Exceptions
from histolab.exceptions import (
    HistolabException,
    MayNeedLargeImageError,
    FilterCompositionError
)
```

### First Steps

```python
from histolab.slides import Slide

# 1. Create Slide object (REQUIRES processed_path)
slide = Slide(
    path="/path/to/slide.svs",
    processed_path="/path/to/output"  # MANDATORY
)

# 2. Access basic properties
print(f"MPP: {slide.base_mpp}")  # Microns per pixel
print(f"Size: {slide.size}")  # (width, height)
print(f"Properties: {slide.properties}")  # Slide metadata

# 3. Read a region
region = slide.read_region(
    coordinates=(0, 0),
    level=0,
    size=(512, 512)
)
# Returns PIL.Image.Image
```

---

## Core API Reference

### Slide Class

```python
from histolab.slides import Slide

# Create
slide = Slide(
    path: str,                    # Path to .svs, .tif, etc.
    processed_path: str,          # OUTPUT PATH (REQUIRED!)
    use_largeimage: bool = False  # Fallback backend
)

# Properties
slide.base_mpp              # float - Microns per pixel
slide.size                  # (width, height) at level 0
slide.level_dimensions      # Dimensions at each pyramid level
slide.level_downsamples     # Downsampling factors
slide.properties            # dict - Slide metadata

# Methods
slide.read_region(            # Read image region
    coordinates=(x, y),
    level=0,
    size=(width, height)
) -> PIL.Image.Image

slide.get_thumbnail(          # Get slide thumbnail
    size=(width, height)
) -> PIL.Image.Image

slide.scaled_image(           # Scaled version for display
    scale_factor=32
) -> PIL.Image.Image

slide.has_valid_tissue_detection_level(level) -> bool
```

### Tile Class

```python
from histolab.tiles import Tile

# Create (usually via Tiler)
tile = Tile(
    image: PIL.Image.Image,
    coords: CoordinatePair,
    level: int,
    slide: Slide
)

# Properties
tile.image                  # PIL.Image.Image
tile.coords                 # CoordinatePair(x, y)
tile.level                  # Pyramid level
tile.slide                  # Reference to parent Slide
tile.tissue_ratio           # float 0-1, tissue percentage

# Methods
processed = tile.apply_filters(      # Returns NEW Tile
    filters: List[Filter]
) -> Tile

is_valid = tile.has_enough_tissue(   # Check quality
    tissue_percent: float = 80
) -> bool
```

### Tiler Protocol

```python
from histolab.tiler import Tiler
from typing import Generator

# Implement custom tiler
class CustomTiler:
    def extract(self, slide: Slide) -> Generator[Tile, None, None]:
        """Yield tiles from slide"""
        # Implementation
        yield tile
    
    def locate_tiles(
        self,
        slide: Slide,
        scale_factor: float = 32,
        colors: List = None,
        alpha: int = 128,
        linewidth: int = 1,
        tiles: Iterable[Tile] = None
    ) -> PIL.Image.Image:
        """Visualize tile locations"""
```

### Filters - Quick Reference

```python
from histolab.filters import (
    Compose, RgbToGrayscale, OtsuThreshold, Lambda
)

# Single filter
filter = RgbToGrayscale()
gray_img = filter(pil_image)

# Compose pipeline
pipeline = Compose([
    RgbToGrayscale(),
    OtsuThreshold(),
    RemoveSmallObjects(min_size=5000)
])
result = pipeline(pil_image)

# Custom filter (Lambda)
custom = Lambda(lambda img: img.rotate(90))
rotated = custom(pil_image)

# Get default for object type
from histolab.filters.compositions import FiltersComposition
filters = FiltersComposition.of(Slide)  # or Tile
```

### Available Filters

```python
# Image Filters
RgbToGrayscale()
OtsuThreshold()
RedThreshold(threshold=150)
GreenThreshold(threshold=150)
BlueThreshold(threshold=150)
Compose(filters_list)
Lambda(function)

# Morphological Filters
RemoveSmallObjects(
    min_size=3000,
    avoid_overmask=True,
    overmask_thresh=95
)

RemoveSmallHoles(area_threshold=3000)

Dilation(kernel_size=5)

Erosion(kernel_size=5)

# Functional API (low-level)
from histolab.filters import image_filters_functional as F
from histolab.filters import morphological_filters_functional as MF

F.rgb_to_grayscale(pil_image)
MF.remove_small_objects(np_mask, min_size=3000)
```

### BinaryMask

```python
from histolab.masks import BinaryMask, BiggestTissueBoxMask

# Use concrete implementation
mask_strategy = BiggestTissueBoxMask(slide)
tissue_mask = mask_strategy.get_mask(slide)

# Custom implementation
class CustomMask(BinaryMask):
    def get_mask(self, slide: Slide) -> np.ndarray:
        # Your logic
        return binary_mask_array

# Apply mask to image
from histolab.util import apply_mask_image
masked_image = apply_mask_image(pil_image, tissue_mask)
```

### Scorer

```python
from histolab.scorer import RandomScorer, CellularityScorer

# Use built-in
scorer = CellularityScorer()
score = scorer.score(tile)  # 0-1 or arbitrary

# Custom scorer
class MyScorer:
    def score(self, tile: Tile) -> float:
        # Your scoring logic
        return score_value

scorer = MyScorer()
for tile in tiles:
    if scorer.score(tile) > threshold:
        keep(tile)
```

### Stain Normalization

```python
from histolab.stain_normalizer import StainNormalizer
import numpy as np

# Initialize
normalizer = StainNormalizer()

# Learn from reference
ref_image = np.array(ref_slide.read_region(...))
normalizer.fit(ref_image)

# Apply to source
source_image = np.array(source_slide.read_region(...))
normalized = normalizer.transform(source_image)

# Convert back to PIL
from histolab.util import np_to_pil
result_image = np_to_pil(normalized)
```

### Types

```python
from histolab.types import CoordinatePair, Region, CP

# Create coordinates
coords = CoordinatePair(x=1000, y=2000)
# or alias
coords = CP(x=1000, y=2000)

# Create region
region = Region(x=100, y=200, w=512, h=512)

# Access
print(coords.x, coords.y)
print(region.w, region.h)
print(region.x + region.w)  # Right edge
```

### Utilities

```python
from histolab.util import apply_mask_image, np_to_pil
import numpy as np

# Convert NumPy to PIL (handles dtype)
np_array = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
pil_image = np_to_pil(np_array)

# Apply binary mask
mask = np.ones((512, 512), dtype=bool)
masked_image = apply_mask_image(pil_image, mask)

# Size refining (aspect ratio)
from histolab.util import refine_thumbnail_size_preserving_aspect_ratio
new_size = refine_thumbnail_size_preserving_aspect_ratio(
    thumbnail_size=(100, 100),
    original_size=(2000, 4000)
)
```

---

## Common Workflows

### Workflow 1: Extract Tiles and Save

```python
from histolab.slides import Slide
from histolab.tiler import GridTiler  # Example, implement or import

slide = Slide(
    path="/data/slide.svs",
    processed_path="/output/tiles"
)

# Assuming GridTiler is available or use custom
tiler = GridTiler(tile_size=512, overlap=50)

counter = 0
for tile in tiler.extract(slide):
    if tile.has_enough_tissue(tissue_percent=75):
        tile.image.save(f"/output/tiles/tile_{counter:05d}.png")
        counter += 1

print(f"Extracted {counter} tiles")
```

### Workflow 2: Preprocessing Pipeline

```python
from histolab.slides import Slide
from histolab.filters import Compose, RgbToGrayscale, OtsuThreshold
from histolab.filters.morphological_filters import RemoveSmallObjects

slide = Slide(path="/data/slide.svs", processed_path="/output")

# Define preprocessing
preprocessing = Compose([
    RgbToGrayscale(),
    OtsuThreshold(),
    RemoveSmallObjects(min_size=5000),
])

# Read region and preprocess
region = slide.read_region((0, 0), 0, (2048, 2048))
processed_region = preprocessing(region)

# Result is PIL.Image or np.ndarray
processed_region.save("/output/preprocessed.png")
```

### Workflow 3: Quality Filtering

```python
from histolab.slides import Slide
from histolab.scorer import CellularityScorer
from histolab.filters.compositions import FiltersComposition

slide = Slide(path="/data/slide.svs", processed_path="/output")
scorer = CellularityScorer()
preprocessor = FiltersComposition.of(Tile)

tiles_to_keep = []

for tile in tiler.extract(slide):
    # Preprocess
    processed = tile.apply_filters(preprocessor)
    
    # Multiple quality checks
    if (processed.has_enough_tissue(tissue_percent=80) and 
        scorer.score(tile) > 0.6):
        tiles_to_keep.append(tile)

print(f"Kept {len(tiles_to_keep)} high-quality tiles")

# Save
for i, tile in enumerate(tiles_to_keep):
    tile.image.save(f"/output/quality_tiles/tile_{i:05d}.png")
```

### Workflow 4: Stain Normalization

```python
from histolab.slides import Slide
from histolab.stain_normalizer import StainNormalizer
from histolab.util import np_to_pil
import numpy as np

# Load reference slide
ref_slide = Slide(path="/data/ref.svs", processed_path="/tmp")
ref_region = ref_slide.read_region((0, 0), 2, (1024, 1024))

# Load target slide
target_slide = Slide(path="/data/target.svs", processed_path="/output")

# Train normalizer
normalizer = StainNormalizer()
normalizer.fit(np.array(ref_region))

# Normalize tiles
normalized_tiles = []
for tile in tiler.extract(target_slide):
    tile_array = np.array(tile.image)
    normalized_array = normalizer.transform(tile_array)
    normalized_image = np_to_pil(normalized_array)
    normalized_tiles.append(normalized_image)

# Save
for i, img in enumerate(normalized_tiles):
    img.save(f"/output/normalized/tile_{i:05d}.png")
```

### Workflow 5: Batch Processing Multiple Slides

```python
from histolab.slides import Slide
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

slides_dir = Path("/data/slides")
output_dir = Path("/output/processed")

for slide_file in slides_dir.glob("*.svs"):
    try:
        slide = Slide(
            path=str(slide_file),
            processed_path=str(output_dir / slide_file.stem)
        )
        
        logger.info(f"Processing {slide_file.name}")
        
        extracted = 0
        for tile in tiler.extract(slide):
            if tile.has_enough_tissue():
                tile.image.save(f"{output_dir / slide_file.stem}/tile_{extracted:05d}.png")
                extracted += 1
        
        logger.info(f"  Extracted {extracted} tiles")
        
    except Exception as e:
        logger.error(f"Failed to process {slide_file.name}: {e}")
        continue
```

### Workflow 6: Custom Mask + Filtering

```python
from histolab.masks import BinaryMask
from histolab.slides import Slide
import numpy as np

class ThresholdBasedMask(BinaryMask):
    def __init__(self, threshold: int = 150):
        self.threshold = threshold
    
    def get_mask(self, slide: Slide) -> np.ndarray:
        # Get low-res overview
        region = slide.read_region((0, 0), 4, (512, 512))
        
        # Simple thresholding
        gray = region.convert('L')
        mask = np.array(gray) > self.threshold
        
        return mask.astype(np.uint8)

# Use custom mask
mask_strategy = ThresholdBasedMask(threshold=180)
tissue_mask = mask_strategy.get_mask(slide)

# Filter tiles using mask
from histolab.util import apply_mask_image

for tile in tiler.extract(slide):
    # Check overlap with tissue
    tile_masked = apply_mask_image(tile.image, tissue_mask)
    if np.array(tile_masked).mean() > 50:  # Rough check
        process(tile)
```

### Workflow 7: Visualization

```python
from histolab.slides import Slide
from pathlib import Path

slide = Slide(path="/data/slide.svs", processed_path="/tmp")

# Get thumbnail with tiles marked
tiles_vis = tiler.locate_tiles(
    slide,
    scale_factor=32,
    colors=['red', 'blue', 'green'],  # or RGB tuples
    alpha=128,
    linewidth=2
)

tiles_vis.save("/output/tiles_visualization.png")

# Or get thumbnail individually
thumb = slide.get_thumbnail((500, 500))
thumb.save("/output/thumbnail.png")
```

---

## Configuration

### Slide Configuration

```python
from histolab.slides import Slide

# Basic
slide = Slide(
    path="/path/to/slide.svs",
    processed_path="/path/to/output"
)

# With large_image backend
slide = Slide(
    path="/path/to/slide.tif",
    processed_path="/path/to/output",
    use_largeimage=True  # For formats OpenSlide doesn't support
)

# Error handling
from histolab.exceptions import MayNeedLargeImageError

try:
    mpp = slide.base_mpp
except MayNeedLargeImageError:
    slide = Slide(path, processed_path, use_largeimage=True)
    mpp = slide.base_mpp
```

### Filter Configuration

```python
from histolab.filters import Compose
from histolab.filters.morphological_filters import RemoveSmallObjects

# Configurable pipeline
pipeline = Compose([
    RgbToGrayscale(),
    OtsuThreshold(),
    RemoveSmallObjects(
        min_size=3000,           # Size threshold
        avoid_overmask=True,     # Prevent over-masking
        overmask_thresh=95       # Max tissue percentage
    ),
    RemoveSmallHoles(area_threshold=2000)
])

# Store configuration
config = {
    "min_object_size": 3000,
    "avoid_overmask": True,
    "overmask_threshold": 95,
    "min_hole_size": 2000
}
```

### Memory Configuration

```python
# For large-scale processing
import gc

# Process in chunks
batch_size = 100
tiles_batch = []

for i, tile in enumerate(tiler.extract(slide)):
    tiles_batch.append(tile)
    
    if (i + 1) % batch_size == 0:
        # Process batch
        for tile in tiles_batch:
            save(tile)
        
        tiles_batch.clear()
        gc.collect()  # Force garbage collection
```

---

## Cheat Sheet

### Quick Imports

```python
# Minimal setup
from histolab.slides import Slide
from histolab.tiler import GridTiler  # or custom
from histolab.filters import Compose, RgbToGrayscale, OtsuThreshold

# Full setup
from histolab.slides import Slide
from histolab.filters import *
from histolab.filters.compositions import FiltersComposition
from histolab.masks import BiggestTissueBoxMask
from histolab.scorer import CellularityScorer
from histolab.stain_normalizer import StainNormalizer
from histolab.util import apply_mask_image, np_to_pil
from histolab.types import CoordinatePair, Region
from histolab.exceptions import MayNeedLargeImageError
```

### Basic Operations

```python
# Create slide (MUST have processed_path)
s = Slide(path, out_path)

# Get slide properties
s.base_mpp           # Resolution
s.size               # Dimensions
s.properties         # Metadata

# Read region
img = s.read_region((x, y), level, (w, h))

# Tile operations
tile.apply_filters([filter1, filter2])
tile.has_enough_tissue()

# Scoring
score = scorer.score(tile)

# Masks
mask = BiggestTissueBoxMask(slide).get_mask(slide)

# Stain norm
normalizer = StainNormalizer()
normalizer.fit(ref_array)
normalized = normalizer.transform(src_array)
```

### Common Parameters

```python
# Tissue detection
tissue_percent=80          # Minimum tissue %
near_zero_var_threshold    # Variance threshold

# Morphological ops
min_size=3000             # Min object size
area_threshold=2000       # Hole size
kernel_size=5             # Dilation/erosion

# Visualization
scale_factor=32           # Display scale
colors=['red']            # Tile colors
alpha=128                 # Transparency

# Filters
avoid_overmask=True       # Prevent over-masking
overmask_thresh=95        # Max masked %
```

### Error Patterns

```python
# Missing processed_path
try:
    Slide(path)
except TypeError:
    slide = Slide(path, processed_path)

# Large_image not installed
try:
    Slide(path, out, use_largeimage=True)
except ModuleNotFoundError:
    pip install large-image

# Resolution issues
try:
    mpp = slide.base_mpp
except ValueError:
    # Try large_image
    slide = Slide(path, out, use_largeimage=True)

# Filter errors
try:
    result = pipeline(image)
except FilterCompositionError:
    # Check filter compatibility
    pass
```

---

## Troubleshooting

### Issue: "processed_path cannot be None"

**Solution**:
```python
# Wrong
slide = Slide("/slide.svs")

# Right
slide = Slide(
    path="/slide.svs",
    processed_path="/output/directory"
)
```

---

### Issue: "ModuleNotFoundError: large_image"

**Solution**:
```bash
# Install large_image with all dependencies
pip install large-image[all]

# Or specific backends
pip install large-image[gdal,jp2k]
```

**In code**:
```python
try:
    slide = Slide(path, proc_path, use_largeimage=True)
except ModuleNotFoundError:
    print("Install large_image or use OpenSlide")
    slide = Slide(path, proc_path, use_largeimage=False)
```

---

### Issue: "ValueError: Unknown scan resolution"

**Cause**: OpenSlide cannot determine magnification  
**Solution**:
```python
# Try large_image
slide = Slide(
    path=slide_path,
    processed_path=out_path,
    use_largeimage=True  # Large_image may have metadata
)

# Or manually set
if slide.properties.get("aperio.MPP"):
    mpp = float(slide.properties["aperio.MPP"])
else:
    # Set default or prompt user
    mpp = 0.25  # Typical value
```

---

### Issue: Memory usage too high

**Solution**:
```python
# Process in batches
import gc

batch_size = 50
for i, tile in enumerate(tiler.extract(slide)):
    process(tile)
    
    if i % batch_size == 0:
        gc.collect()

# Or use lower resolution levels
region = slide.read_region(
    (0, 0),
    level=3,  # Lower level = smaller image
    size=(1024, 1024)
)
```

---

### Issue: Slow tile extraction

**Solutions**:
```python
# 1. Use lower resolution level for mask
mask = mask_strategy.get_mask(slide)  # May use level 6 internally

# 2. Skip expensive scoring
# Don't score every tile, sample instead

tiles = list(tiler.extract(slide))
samples = tiles[::10]  # Every 10th
scored = [scorer.score(t) for t in samples]

# 3. Pre-filter by tissue first
for tile in tiler.extract(slide):
    if tile.has_enough_tissue():  # Fast check first
        if scorer.score(tile) > threshold:  # Slower check
            keep(tile)
```

---

### Issue: Tiles have artifacts at edges

**Solution**:
```python
# Use overlap in tiler
class CustomTiler:
    def __init__(self, tile_size=512, overlap=64):
        self.tile_size = tile_size
        self.overlap = overlap

# Remove edge artifacts with morphology
from histolab.filters.morphological_filters import Dilation

# Clean up borders
post_process = Compose([
    original_filters,
    Dilation(kernel_size=5),
    RemoveSmallObjects()
])
```

---

### Issue: Color appearance differs between slides

**Solution**: Use stain normalization
```python
from histolab.stain_normalizer import StainNormalizer

# Normalize all slides to reference
normalizer = StainNormalizer()
normalizer.fit(reference_image)

# Apply to all
for slide in slides:
    region = slide.read_region(...)
    normalized = normalizer.transform(np.array(region))
```

---

### Issue: Can't determine which level to use

**Solution**:
```python
# Check available levels
slide = Slide(path, processed_path)

print(f"Number of levels: {len(slide.level_dimensions)}")
print(f"Dimensions: {slide.level_dimensions}")
print(f"Downsamples: {slide.level_downsamples}")

# Level 0 = full resolution
# Higher levels = downsampled

# For mask generation, often use level 5-6
# For tiles, use level 0
```

---

## Tips & Tricks

1. **Always specify processed_path** - It's required, not optional
2. **Use protocols** - Works with any object that implements the interface
3. **Cache masks** - BinaryMask already caches, but profile if slow
4. **Batch process** - Use generators to avoid loading all tiles at once
5. **Test with small regions** - Always test pipeline on subset first
6. **Profile performance** - Use cProfile for bottlenecks
7. **Log progress** - Easy to forget how many tiles you'll get
8. **Validate output** - Check a few tiles manually before full run

---

## Related Resources

- **Main Library**: [HistoLab GitHub](https://github.com/histolab/histolab)
- **Documentation**: Main README and examples
- **Paper**: Check citations in repository
- **Similar Libraries**: GlassCut (simpler), PathoPatcher (production pipeline)
