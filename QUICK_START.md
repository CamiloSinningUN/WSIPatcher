# GlassCut Quick Start: Tilers & Datasets

## Installation

GlassCut is already in your workspace. Just import it:

```python
from glasscut import (
    # Slide loading
    Slide,
    
    # Tiling strategies  
    GridTiler, RandomTiler, ConditionalTiler,
    
    # Dataset generation
    DatasetGenerator, DatasetConfig,
    
    # Storage
    StorageOrganizer,
)
```

## 60-Second Example

```python
from glasscut import DatasetGenerator, DatasetConfig

# Configure
config = DatasetConfig(
    dataset_id="my_dataset",
    output_dir="./output",
    tiler="grid",
    num_workers=4,
)

# Generate
generator = DatasetGenerator(config)
dataset = generator.process_dataset([
    "slide_001.svs",
    "slide_002.svs",
])

# Done! ✓
print(f"Generated {dataset.total_tiles} tiles")
# Output: ./output/my_dataset/Slide_000/tiles/*.png
```

## Three Tiling Strategies

### 1. GridTiler - Systematic Grid

```python
from glasscut import Slide, GridTiler

slide = Slide("slide.svs")
tiler = GridTiler(tile_size=(512, 512), overlap=50)

for tile in tiler.extract(slide, magnification=20):
    tile.save(f"tile_{tile.coords}.png")
```

**Best for:** Complete coverage, reproducible, systematic analysis

### 2. RandomTiler - Random Sampling

```python
tiler = RandomTiler(num_tiles=100, seed=42)

for tile in tiler.extract(slide, magnification=20):
    print(f"Tile at {tile.coords}")
```

**Best for:** Representative sampling, fast screening, initial QC

### 3. ConditionalTiler - Tissue-Aware

```python
tiler = ConditionalTiler(min_tissue_in_tile=0.7)

for tile in tiler.extract(slide, magnification=20):
    print(f"Tissue tile at {tile.coords}")
```

**Best for:** Quality control, tissue-only extraction, morphology studies

## Choices by Use Case

### Use Case: Process 100 slides quickly
```python
config = DatasetConfig(
    tiler="grid",
    num_workers=8,      # Parallel processing
    tile_size=(256, 256),  # Smaller tiles
    verbose=False,      # Quiet mode
)
```

### Use Case: Research study with quality control
```python
config = DatasetConfig(
    tiler="conditional",
    tiler_params={"min_tissue_in_tile": 0.8},
    save_thumbnails=True,
    save_masks=True,
    num_workers=4,
)
```

### Use Case: Initial exploration/screening
```python
config = DatasetConfig(
    tiler="random",
    tiler_params={"num_tiles": 25},
    num_workers=2,
    save_masks=False,    # Skip expensive operations
)
```

### Use Case: Full analysis at high magnification
```python
config = DatasetConfig(
    tile_size=(768, 768),
    magnification=40,    # High detail
    tiler="grid",
    tiler_params={"overlap": 200},
    num_workers=4,
)
```

## Output Structure

After processing, you get:

```
./output/my_dataset/
├── metadata.json                    # All dataset info
├── processed.json                   # Which slides succeeded
├── Slide_000/
│   ├── tiles/                       # 🖼️ Tile images
│   │   ├── tile_0000000.png
│   │   ├── tile_0000001.png
│   │   └── ...
│   ├── thumbnails/                  # 📸 Preview images
│   ├── masks/                       # 🎭 Tissue masks
│   └── slide_metadata.json
└── Slide_001/ (etc)
```

All JSON files are properly formatted and queryable:

```python
import json
from pathlib import Path

with open("./output/my_dataset/metadata.json") as f:
    metadata = json.load(f)

print(f"Total slides: {metadata['total_slides']}")
print(f"Total tiles: {metadata['total_tiles']}")

for slide in metadata['slides']:
    print(f"{slide['slide_id']}: {slide['total_tiles']} tiles")
```

## Configuration Options

### Tile Extraction
| Option | Default | Description |
|--------|---------|-------------|
| `tile_size` | (512, 512) | Tile dimensions (w, h) |
| `magnification` | 20 | Extraction magnification |
| `tiler` | "grid" | "grid" \| "random" \| "conditional" |
| `overlap` | 0 | For grid tiler (pixels) |

### Processing
| Option | Default | Description |
|--------|---------|-------------|
| `num_workers` | 4 | Parallel workers (1=sequential) |
| `save_thumbnails` | True | Generate preview images |
| `save_masks` | True | Generate tissue masks |
| `verbose` | True | Detailed logging |

## Common Configurations

### Fast & Simple (5 min)
```python
DatasetConfig(
    tiler="grid",
    num_workers=1,
    save_masks=False,
    verbose=False,
)
```

### Balanced (15 min)
```python
DatasetConfig(
    tiler="grid",
    tiler_params={"overlap": 50},
    num_workers=4,
)
```

### Thorough (30+ min)
```python
DatasetConfig(
    tiler="conditional",
    tiler_params={"min_tissue_in_tile": 0.8},
    tile_size=(768, 768),
    magnification=40,
    num_workers=2,
    save_masks=True,
    save_thumbnails=True,
)
```

## Advanced: Single Slide

Extract tiles from one slide manually:

```python
from glasscut import Slide, GridTiler

slide = Slide("path/to/slide.svs")
tiler = GridTiler(tile_size=(512, 512), overlap=50)

# Get all coordinates first
coords = tiler.get_tile_coordinates(slide, magnification=20)
print(f"Will extract {len(coords)} tiles")

# Visualize before extracting
viz = tiler.visualize(slide)
viz.save("tile_visualization.png")

# Now extract
for i, tile in enumerate(tiler.extract(slide, magnification=20)):
    if i % 100 == 0:
        print(f"Extracted {i} tiles...")
    tile.save(f"tiles/tile_{i:06d}.png")

print("✓ Done!")
```

## Troubleshooting

### Slow processing?
```python
# Use these settings:
config = DatasetConfig(
    tiler="random",            # Fastest
    tile_size=(256, 256),      # Smaller
    num_workers=8,             # More workers
    save_masks=False,          # Skip expensive
    verbose=False,             # Reduce overhead
)
```

### Out of memory?
```python
config = DatasetConfig(
    num_workers=1,             # Sequential
    tile_size=(256, 256),      # Smaller
    magnification=10,          # Lower mag
)
```

### Need only tissue regions?
```python
config = DatasetConfig(
    tiler="conditional",
    tiler_params={"min_tissue_in_tile": 0.5},
)
```

### Want reproducible results?
```python
if tiler == "random":
    config = DatasetConfig(
        tiler="random",
        tiler_params={"seed": 42},  # Fixed seed
    )
else:
    # Grid and Conditional are always deterministic
    config = DatasetConfig(tiler="grid")
```

## Reading the Output

### Get all tiles for a slide:
```python
import json

with open("./output/my_dataset/metadata.json") as f:
    meta = json.load(f)

slide_0 = meta['slides'][0]
print(f"Slide: {slide_0['slide_id']}")
print(f"Tiles: {slide_0['total_tiles']}")

for tile in slide_0['tiles'][:10]:  # First 10
    print(f"  {tile['tile_id']}: ({tile['x']}, {tile['y']}), "
          f"tissue={tile['tissue_ratio']:.1%}")
```

### Check which slides processed successfully:
```python
import json

with open("./output/my_dataset/processed.json") as f:
    processed = json.load(f)

print(f"Processed {processed['total']} slides")
for slide_id in processed['processed_files']:
    print(f"  ✓ {slide_id}")
```

## Next Steps

1. **Read the guides:**
   - `docs/DATASET_GENERATION.md` - Full reference
   - `docs/TILER_GUIDE.md` - Strategy details
   - `docs/STORAGE_GUIDE.md` - Output organization

2. **Try the examples:**
   - `examples/example_dataset_generation.py`
   
3. **Process your data:**
   ```python
   config = DatasetConfig(...)
   generator = DatasetGenerator(config)
   dataset = generator.process_dataset(your_slides)
   ```

## API Reference

### DatasetGenerator
```python
generator = DatasetGenerator(config)
dataset_meta = generator.process_dataset(slide_paths)

# dataset_meta.total_slides : int
# dataset_meta.total_tiles : int
# dataset_meta.slides : List[SlideMetadata]
```

### StorageOrganizer
```python
organizer = StorageOrganizer("./output")
organizer.init_dataset("my_dataset")
dirs = organizer.init_slide("my_dataset", "Slide_000")

tile_path = organizer.get_tile_path("my_dataset", "Slide_000", "tile_0")
thumbnail_path = organizer.get_slide_thumbnail_path("my_dataset", "Slide_000")
```

### Tilers
```python
tiler = GridTiler(tile_size=(512, 512), overlap=50)
tiler = RandomTiler(num_tiles=100, seed=42)
tiler = ConditionalTiler(min_tissue_in_tile=0.7)

for tile in tiler.extract(slide, magnification=20):
    # tile.image : PIL.Image
    # tile.coords : (x, y)
    # tile.magnification : float
    pass

coords = tiler.get_tile_coordinates(slide, magnification=20)
viz = tiler.visualize(slide)
```

---

**Ready to start?** Try the 60-second example above! 🚀
