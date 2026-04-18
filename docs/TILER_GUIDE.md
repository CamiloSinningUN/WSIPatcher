# GlassCut Tiler Guide

## Overview

Tilers are pluggable tile extraction strategies that determine which regions of a slide to extract as tiles. GlassCut provides several built-in tilers and supports custom implementations.

## Available Tilers

### 1. GridTiler (Regular Grid)

Extracts tiles in a regular grid pattern across the slide.

**Best for:**
- Systematic, complete coverage of slide
- Non-overlapping or slightly overlapping regions
- Reproducible, deterministic tiling

**Parameters:**
- `tile_size` (tuple): Size of each tile (width, height) in pixels. Default: (512, 512)
- `overlap` (int): Overlap between adjacent tiles in pixels. Default: 0
- `min_tissue_ratio` (float): Minimum tissue ratio to include tile (0.0-1.0). Default: 0.0
- `save_empty` (bool): Whether to include empty tiles. Default: False

**Example:**
```python
from glasscut import Slide, GridTiler

slide = Slide("biopsy_sample.svs")

# Extract non-overlapping tiles
tiler = GridTiler(
    tile_size=(512, 512),
    overlap=0,
    min_tissue_ratio=0.5
)

for tile in tiler.extract(slide, magnification=20):
    tile.save(f"tiles/tile_{tile.coords}.png")

# Or with large overlap for smooth viewing
tiler_overlap = GridTiler(
    tile_size=(512, 512),
    overlap=100  # 100-pixel overlap with neighbors
)
```

**How it works:**
```
Step size = tile_size - overlap = 512 - 0 = 512 pixels

Grid layout (each box is a tile):
┌─────────────────┬─────────────────┬─────────────────┐
│   tile (0, 0)   │   tile (512, 0) │  tile (1024, 0) │
├─────────────────┼─────────────────┼─────────────────┤
│   tile (0, 512) │  tile (512, 512)│ tile (1024, 512)│
├─────────────────┼─────────────────┼─────────────────┤
│  tile (0, 1024) │ tile (512, 1024)│tile (1024, 1024)│
└─────────────────┴─────────────────┴─────────────────┘

With overlap=100:
Step size = 512 - 100 = 412 pixels

Grid becomes denser (tiles overlap):
┌──────────────────────┬──────────────────────┐
│  tile (0, 0)         │  tile (412, 0)       │
│  ┌────────────────────────────────────┐    │
│  │  overlap region  │  overlap region │    │
│  └────────────────────────────────────┘    │
└──────────────────────┴──────────────────────┘
```

---

### 2. RandomTiler (Random Sampling)

Extracts tiles randomly from the slide without regard to position.

**Best for:**
- Creating representative samples
- Reducing bias towards certain regions
- Non-systematic sampling requirements
- Speed (doesn't need to cover entire slide)

**Parameters:**
- `num_tiles` (int): Number of tiles to extract. Default: 100
- `tile_size` (tuple): Size of each tile (width, height). Default: (512, 512)
- `seed` (int, optional): Random seed for reproducibility. Default: None
- `min_tissue_ratio` (float): Minimum tissue ratio to include tile. Default: 0.0
- `max_attempts` (int): Max attempts to find valid tiles. Default: 1000

**Example:**
```python
from glasscut import Slide, RandomTiler

slide = Slide("biopsy_sample.svs")

# Reproducible random sampling
tiler = RandomTiler(
    num_tiles=50,
    seed=42,
    min_tissue_ratio=0.5
)

for tile in tiler.extract(slide, magnification=20):
    print(f"Extracted tile at {tile.coords}")

# Without seed for non-deterministic sampling
tiler_nondeterministic = RandomTiler(
    num_tiles=100,
    seed=None  # Different tiles each time
)
```

**How it works:**
```
Random coordinate selection:
- Valid range: (0 to slide_width-tile_size, 0 to slide_height-tile_size)
- For each of num_tiles iterations:
  - Generate random x = randint(0, max_x)
  - Generate random y = randint(0, max_y)
  - Extract tile at (x, y)

Example distribution across slide:
●   ●     ●        ○○ = tissue tiles
   ●         ●      ● = sampled tiles
●              ●    ○ = background (not sampled)
      ●      ●    ○ (mostly random, some clustering)
   ●    ●              possible due to chance
```

---

### 3. ConditionalTiler (Tissue-Aware)

Extracts tiles only from regions containing sufficient tissue content.

**Best for:**
- Maximizing tissue coverage
- Eliminating completely empty tiles automatically
- Research on tissue morphology and distribution
- Quality control (only tissue-containing tiles)

**Parameters:**
- `tissue_detector` (TissueDetector): Strategy for tissue detection. Default: OtsuTissueDetector
- `tile_size` (tuple): Size of each tile. Default: (512, 512)
- `overlap` (int): Overlap between adjacent tiles. Default: 0
- `min_tissue_in_tile` (float): Min tissue ratio to include tile (0.0-1.0). Default: 0.5
- `mask_level` (int): Pyramid level for mask computation (lower=faster). Default: 4

**Example:**
```python
from glasscut import Slide, ConditionalTiler
from glasscut.tissue_detectors import OtsuTissueDetector

slide = Slide("biopsy_sample.svs")

# Use standard Otsu tissue detection
detector = OtsuTissueDetector()
tiler = ConditionalTiler(
    tissue_detector=detector,
    tile_size=(512, 512),
    min_tissue_in_tile=0.7  # At least 70% tissue
)

for tile in tiler.extract(slide, magnification=20):
    print(f"Tissue-containing tile at {tile.coords}")
```

**How it works:**
```
1. Generate tissue binary mask (1=tissue, 0=background)
2. Generate grid coordinates (like GridTiler)
3. For each grid position:
   - Check tissue coverage in that region
   - Only include if tissue_ratio >= min_tissue_in_tile

Before (all tiles):      After (filtered):
┌─┬─┬─┬─┬─┐            ┌─┬─┬─┐
├─┼─┼─┼─┼─┤            ├─┼─┼─┤
├─┼─┼─┼─┼─┤     →      ├─┼─┼─┤
├─┼─┼─┼─┼─┤            ├─┼─┼─┤
└─┴─┴─┴─┴─┘            └─┴─┴─┘
                 (Empty regions removed)
```

---

## Comparison Table

| Aspect | GridTiler | RandomTiler | ConditionalTiler |
|--------|-----------|-------------|-----------------|
| **Coverage** | Complete, systematic | Sparse, may miss regions | Selected (tissue-only) |
| **Reproducibility** | Always same tiles | Only with seed | Always same tiles |
| **Speed** | Fast | Very fast | Medium (mask gen) |
| **Use Case** | Comprehensive analysis | Sampling, statistics | Quality control |
| **Configuration** | overlap, min_tissue | num_tiles, seed | min_tissue_in_tile |
| **Best for** | Disease detection | Epidemiology | Tissue analysis |

---

## Creating Custom Tilers

Extend the `Tiler` abstract base class to create custom extraction strategies.

**Example: Diagonal Tiler (extract along diagonal)**
```python
from glasscut.tiler import Tiler
from glasscut.slides import Slide
from glasscut.tile import Tile
from typing import Generator, List, Tuple

class DiagonalTiler(Tiler):
    """Extract tiles along the slide diagonal."""
    
    def __init__(self, tile_size: Tuple[int, int] = (512, 512), spacing: int = 256):
        self.tile_size = tile_size
        self.spacing = spacing
    
    def extract(
        self,
        slide: Slide,
        magnification: int | float,
        tile_size: Tuple[int, int] = (512, 512),
    ) -> Generator[Tile, None, None]:
        """Extract tiles along diagonal."""
        w, h = tile_size
        
        # Diagonal direction: from (0,0) to (width, height)
        for i in range(0, min(slide.dimensions), self.spacing):
            x, y = i, i
            
            # Skip if out of bounds
            if x + w > slide.dimensions[0] or y + h > slide.dimensions[1]:
                continue
            
            tile = slide.extract_tile(
                coords=(x, y),
                tile_size=(w, h),
                magnification=magnification
            )
            yield tile
    
    def get_tile_coordinates(
        self,
        slide: Slide,
        magnification: int | float,
        tile_size: Tuple[int, int] = (512, 512),
    ) -> List[Tuple[int, int]]:
        """Get diagonal coordinates."""
        w, h = tile_size
        coords = []
        
        for i in range(0, min(slide.dimensions), self.spacing):
            x, y = i, i
            if x + w <= slide.dimensions[0] and y + h <= slide.dimensions[1]:
                coords.append((x, y))
        
        return coords

# Usage
tiler = DiagonalTiler(tile_size=(512, 512), spacing=500)
for tile in tiler.extract(slide, magnification=20):
    print(f"Diagonal tile at {tile.coords}")
```

---

## Visualizing Tiles

Before extracting, visualize where tiles will be placed on the slide.

```python
from glasscut import Slide, GridTiler

slide = Slide("biopsy_sample.svs")
tiler = GridTiler(tile_size=(512, 512), overlap=50)

# Generate visualization
viz_image = tiler.visualize(
    slide,
    magnification=5,      # Low mag for visualization
    scale_factor=32,
    colors=[(0, 255, 0), (255, 0, 0)],  # Green, red
    alpha=200,
    linewidth=2
)

viz_image.save("tile_visualization.png")
viz_image.show()
```

---

## Performance Considerations

### Extraction Speed
- **GridTiler**: Fastest (~1000 tiles/min on single thread)
- **RandomTiler**: Very fast (~5000 tiles/min, no I/O)
- **ConditionalTiler**: Slowest (~500 tiles/min, includes mask generation)

### Memory Usage
- **GridTiler**: Constant, minimal overhead
- **RandomTiler**: Minimal, seed-based RNG
- **ConditionalTiler**: Requires tissue mask (~50MB for 50K×50K slide at level 4)

### Recommendation for Large Datasets
```python
# For speed: Use RandomTiler or GridTiler with num_workers=4+
config = DatasetConfig(
    tiler="grid",
    num_workers=8,  # Parallel slide processing
    verbose=False   # Reduce logging overhead
)

# For quality: Use ConditionalTiler with tissue filtering
config = DatasetConfig(
    tiler="conditional",
    tiler_params={"min_tissue_in_tile": 0.7},
    num_workers=4
)

# For balance: GridTiler with moderate settings
config = DatasetConfig(
    tiler="grid",
    tiler_params={"overlap": 50, "min_tissue_ratio": 0.3},
    num_workers=4
)
```

---

## Common Issues & Solutions

**Issue: Too many empty tiles**
```python
# Solution: Use ConditionalTiler or filter with GridTiler
tiler = GridTiler(min_tissue_ratio=0.5)  # Skip tiles <50% tissue
```

**Issue: Tiles too small at slide boundaries**
```python
# Solution: GridTiler automatically skips small edge tiles
# Or manually control with overlap parameter
tiler = GridTiler(overlap=100)  # Larger overlap avoids small tiles
```

**Issue: Not enough tiles extracted**
```python
# Solution: Reduce min_tissue_ratio or use RandomTiler with more samples
tiler = GridTiler(min_tissue_ratio=0.1)  # Lower threshold
tiler = RandomTiler(num_tiles=500)       # Increase sample size
```

**Issue: Slow extraction with large datasets**
```python
# Solution: Use parallel processing
config = DatasetConfig(
    tiler="grid",
    num_workers=8,  # Increase workers
    tile_size=(256, 256),  # Reduce tile size (fewer bytes/tile)
)
```

---

## See Also

- [StorageOrganizer Guide](STORAGE_GUIDE.md) - How tiles are organized
- [DatasetGenerator Guide](DATASET_GENERATION.md) - Batch processing
- [API Reference](LIBRARY_ARCHITECTURE.md) - Detailed class documentation
