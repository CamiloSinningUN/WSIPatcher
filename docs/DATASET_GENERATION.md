# GlassCut Dataset Generation Guide

Complete guide to using `DatasetGenerator` for multi-slide batch processing with parallel extraction, metadata tracking, and organized storage.

## Quick Start (5 minutes)

### Minimal Example

```python
from glasscut import DatasetGenerator, DatasetConfig

# Configure
config = DatasetConfig(
    dataset_id="my_first_dataset",
    output_dir="./datasets",
    tiler="grid",
)

# Process
generator = DatasetGenerator(config)
dataset_meta = generator.process_dataset([
    "slide_001.svs",
    "slide_002.svs",
])

print(f"✓ Generated {dataset_meta.total_tiles} tiles")
```

**Output structure:**
```
datasets/
└── my_first_dataset/
    ├── metadata.json
    ├── processed.json
    ├── Slide_000/
    │   ├── tiles/          (PNG tile images)
    │   ├── thumbnails/     (Visualization images)
    │   ├── masks/          (Binary masks)
    │   └── slide_metadata.json
    └── Slide_001/
        └── (same structure)
```

---

## Configuration

### DatasetConfig Parameters

```python
from glasscut import DatasetConfig

config = DatasetConfig(
    # Required
    dataset_id="study_v1",           # Unique dataset name
    output_dir="./datasets",         # Where to save output
    
    # Tile extraction
    tile_size=(512, 512),            # Tile dimensions
    magnification=20,                # Extraction magnification
    overlap=50,                      # For GridTiler (pixels)
    
    # Tiling strategy
    tiler="grid",                    # "grid", "random", or "conditional"
    tiler_params={                   # Strategy-specific parameters
        "min_tissue_ratio": 0.5,
    },
    
    # Output artifacts
    save_thumbnails=True,            # Generate slide thumbnails
    save_masks=True,                 # Generate tissue masks
    save_processed_json=True,        # Track processed slides
    
    # Processing
    num_workers=4,                   # Parallelism level (1=sequential)
    verbose=True,                    # Enable logging
)
```

### Tiler-Specific Parameters

#### GridTiler
```python
config = DatasetConfig(
    tiler="grid",
    tiler_params={
        "overlap": 50,              # Overlap between tiles
        "min_tissue_ratio": 0.3,    # Minimum tissue to keep tile
        "save_empty": False,        # Skip empty tiles
    }
)
```

#### RandomTiler
```python
config = DatasetConfig(
    tiler="random",
    tiler_params={
        "num_tiles": 100,           # Tiles per slide
        "seed": 42,                 # Reproducibility
        "min_tissue_ratio": 0.5,
        "max_attempts": 1000,       # Attempts to find valid tiles
    }
)
```

#### ConditionalTiler
```python
config = DatasetConfig(
    tiler="conditional",
    tiler_params={
        "overlap": 50,
        "min_tissue_in_tile": 0.7,  # Min tissue coverage
        "mask_level": 4,            # Pyramid level for mask
    }
)
```

---

## Usage Patterns

### Pattern 1: Basic Single-Run Dataset

```python
from glasscut import DatasetGenerator, DatasetConfig
from pathlib import Path

# Configuration
config = DatasetConfig(
    dataset_id="biopsy_cohort",
    output_dir="./datasets",
    tile_size=(512, 512),
    magnification=20,
    tiler="grid",
    num_workers=1,  # Sequential for reproducibility
    verbose=True,
)

# Generate dataset
generator = DatasetGenerator(config)
dataset_meta = generator.process_dataset([
    "data/slide_001.svs",
    "data/slide_002.svs",
    "data/slide_003.svs",
])

# Inspect results
print(f"Slides: {dataset_meta.total_slides}")
print(f"Tiles: {dataset_meta.total_tiles}")
for slide in dataset_meta.slides:
    print(f"  {slide.slide_id}: {slide.total_tiles} tiles, "
          f"mpp={slide.mpp:.3f}")
```

### Pattern 2: Parallel Processing with Many Slides

```python
from pathlib import Path
from glasscut import DatasetGenerator, DatasetConfig

# Find all slides
slide_dir = Path("data/slides")
slide_paths = sorted(slide_dir.glob("*.svs"))

# Large-scale configuration
config = DatasetConfig(
    dataset_id="large_study_v1",
    output_dir="./datasets",
    tile_size=(512, 512),
    magnification=20,
    tiler="grid",
    tiler_params={"overlap": 50, "min_tissue_ratio": 0.3},
    num_workers=8,      # Use 8 parallel workers
    save_masks=True,
    verbose=True,
)

generator = DatasetGenerator(config)
dataset_meta = generator.process_dataset(slide_paths)

print(f"✓ Processed {dataset_meta.total_slides} slides")
print(f"✓ Total tiles: {dataset_meta.total_tiles}")
print(f"✓ Output: datasets/large_study_v1")
```

### Pattern 3: Random Sampling for Initial Exploration

```python
from glasscut import DatasetGenerator, DatasetConfig

# Get representative samples without processing entire slides
config = DatasetConfig(
    dataset_id="exploratory_sample",
    output_dir="./datasets",
    tile_size=(256, 256),       # Smaller tiles for sampling
    magnification=40,            # Higher magnification
    tiler="random",
    tiler_params={
        "num_tiles": 20,        # Just 20 tiles per slide
        "seed": 42,             # Reproducible
    },
    num_workers=4,
)

generator = DatasetGenerator(config)
dataset_meta = generator.process_dataset([
    "slide_001.svs",
    "slide_002.svs",
    "slide_003.svs",
])

# Use for quick QC before large processing
print(f"Sample: {dataset_meta.total_tiles} representative tiles")
```

### Pattern 4: Tissue-Aware Processing Only

```python
from glasscut import DatasetGenerator, DatasetConfig

# Extract only tissue-containing tiles
config = DatasetConfig(
    dataset_id="tissue_only_study",
    output_dir="./datasets",
    tile_size=(512, 512),
    magnification=20,
    tiler="conditional",
    tiler_params={
        "min_tissue_in_tile": 0.8,  # >= 80% tissue
    },
    num_workers=4,
    verbose=True,
)

generator = DatasetGenerator(config)
dataset_meta = generator.process_dataset(slide_paths)

print(f"Processed {dataset_meta.total_tiles} tissue tiles")
```

### Pattern 5: Incremental Dataset Building

Add new slides to existing dataset:

```python
from glasscut import DatasetGenerator, DatasetConfig
from pathlib import Path
import json

dataset_dir = Path("./datasets/my_dataset")
existing_meta_path = dataset_dir / "metadata.json"

# Load existing metadata
with open(existing_meta_path) as f:
    existing_meta = json.load(f)

# Get existing slide count
existing_slides = len(existing_meta['slides'])
next_index = existing_slides

# Process new slides
config = DatasetConfig(
    dataset_id="my_dataset",
    output_dir="./datasets",
    # ... rest of config
)

generator = DatasetGenerator(config)
new_slides = ["new_slide_001.svs", "new_slide_002.svs"]
new_dataset_meta = generator.process_dataset(new_slides)

# Merge metadata
# Note: Currently requires manual merging of JSON files
```

---

## Processing Steps

### What DatasetGenerator Does

1. **Initialization**
   - Create output directory structure
   - Initialize StorageOrganizer
   - Setup logging

2. **For Each Slide**
   - Load WSI file
   - Initialize slide directories (tiles/, thumbnails/, masks/)
   - Generate tile coordinates using Tiler
   - Extract each tile image
   - Calculate tissue ratio for each tile
   - Save tile PNG files
   - Generate slide thumbnail
   - Generate tissue mask
   - Create metadata JSON

3. **Dataset Completion**
   - Aggregate all slide metadata
   - Create dataset-level metadata.json
   - Write processed.json
   - Close all resources

### Parallelism Model

```
With num_workers=4:

Process 1: Slide 0
Process 2: Slide 1
Process 3: Slide 2
Process 4: Slide 3
Process 1: Slide 4 (Slide 0 complete)
Process 2: Slide 5 (Slide 1 complete)
...
```

**Note:** Each worker processes one complete slide before starting the next. The tile extraction within a slide remains single-threaded for reproducibility.

---

## Error Handling and Robustness

### What happens if a slide fails?

```python
# If one slide fails to process:
# - Error is logged
# - Processing continues with remaining slides
# - Other slides in dataset are unaffected
# - processed.json contains only successful slides

dataset_meta = generator.process_dataset(slides)
# If Slide_002 fails:
# - Slide_000 and Slide_001 are in dataset_meta
# - Slide_002 is skipped with error logged
# - processed.json lists only Slide_000, Slide_001
```

### Handling partial failures:

```python
try:
    dataset_meta = generator.process_dataset(large_slide_list)
except RuntimeError as e:
    # Raised only if ALL slides fail
    print("All slides failed to process")

# Check which slides succeeded
successful = [s.slide_id for s in dataset_meta.slides]
print(f"Successfully processed: {successful}")

# Retry failed slides separately
processed_path = dataset_dir / "processed.json"
with open(processed_path) as f:
    processed = json.load(f)

failed = [s for s in slide_paths if s not in processed['processed_files']]
if failed:
    print(f"Retrying {len(failed)} failed slides...")
    dataset_meta2 = generator.process_dataset(failed)
```

---

## Monitoring Progress

### Console Output

```
2024-01-15 14:30:00 - DatasetGenerator[my_dataset] - INFO - \
  Starting dataset generation: my_dataset
2024-01-15 14:30:00 - DatasetGenerator[my_dataset] - INFO - \
  Processing 3 slides with 4 workers
2024-01-15 14:30:05 - DatasetGenerator[my_dataset] - INFO - \
  [1/3] Processed slide_001.svs (2145 tiles)
2024-01-15 14:30:12 - DatasetGenerator[my_dataset] - INFO - \
  [2/3] Processed slide_002.svs (1987 tiles)
2024-01-15 14:30:18 - DatasetGenerator[my_dataset] - INFO - \
  [3/3] Processed slide_003.svs (2268 tiles)
2024-01-15 14:30:18 - DatasetGenerator[my_dataset] - INFO - \
  Dataset complete! Generated 6400 tiles from 3 slides
```

### Disable verbose logging:

```python
config = DatasetConfig(
    # ...
    verbose=False  # Quieter execution
)
```

### Custom progress tracking:

```python
dataset_meta = generator.process_dataset(slides)

# Access results after completion
print(f"Total slides: {dataset_meta.total_slides}")
print(f"Total tiles: {dataset_meta.total_tiles}")

for slide in dataset_meta.slides:
    avg_tissue = sum(t.tissue_ratio for t in slide.tiles) / len(slide.tiles)
    print(f"{slide.slide_id}: {slide.total_tiles} tiles, "
          f"avg tissue: {avg_tissue:.1%}")
```

---

## Performance & Optimization

### Choosing num_workers

| Scenario | num_workers | Comment |
|----------|-------------|---------|
| Testing/debugging | 1 | Sequential, easier debugging |
| Small datasets (1-10 slides) | 1-2 | Overhead not worth it |
| Medium datasets (10-100 slides) | 4 | Good balance |
| Large datasets (100+ slides) | 8-16 | Maximize throughput |
| Large slides (>100K × 100K) | 2-4 | Each slide memory intensive |

```python
import os

# Auto-tune based on CPU count
num_cpus = os.cpu_count()
config = DatasetConfig(
    num_workers=max(1, num_cpus - 1),  # Leave 1 CPU free
    # ...
)
```

### Speed optimization:

```python
# Fastest configuration
config = DatasetConfig(
    tile_size=(256, 256),     # Smaller tiles
    magnification=5,          # Lower magnification (faster to read)
    tiler="random",           # Very fast sampling
    tiler_params={"num_tiles": 50},
    num_workers=8,
    save_thumbnails=False,    # Skip expensive artifact generation
    save_masks=False,
    verbose=False,
)
```

### Quality optimization:

```python
# Most thorough configuration
config = DatasetConfig(
    tile_size=(512, 512),
    magnification=40,         # High magnification
    tiler="conditional",      # Tissue-aware filtering
    tiler_params={"min_tissue_in_tile": 0.9},
    num_workers=4,
    save_thumbnails=True,     # All artifacts
    save_masks=True,
    verbose=True,
)
```

### Memory considerations:

- Each worker loads one slide in memory
- For 100K × 100K slides: ~500MB per worker × num_workers
- Use `num_workers=1` if memory is constrained
- Use smaller `tile_size` to reduce memory per tile

---

## Metadata Access

### After generation:

```python
from glasscut import DatasetGenerator, DatasetConfig
import json

config = DatasetConfig(
    dataset_id="study",
    output_dir="./datasets"
)
generator = DatasetGenerator(config)

# Generate dataset
dataset_meta = generator.process_dataset(slides)

# Access programmatically
print(f"Dataset ID: {dataset_meta.dataset_id}")
print(f"Created: {dataset_meta.created_at}")
print(f"Config: {dataset_meta.config}")

for slide in dataset_meta.slides:
    print(f"\n{slide.slide_id}:")
    print(f"  Original file: {slide.slide_path}")
    print(f"  Tiles: {slide.total_tiles}")
    print(f"  Dimensions: {slide.dimensions}")
    print(f"  MPP: {slide.mpp}")
    
    # First 3 tiles
    for tile in slide.tiles[:3]:
        print(f"    - {tile.tile_id}: ({tile.x}, {tile.y}), "
              f"tissue={tile.tissue_ratio:.1%}")
```

### Direct JSON access:

```python
import json
from pathlib import Path

dataset_meta_path = Path("./datasets/my_dataset/metadata.json")
with open(dataset_meta_path) as f:
    metadata = json.load(f)

print(json.dumps(metadata, indent=2))
```

---

## Best Practices

### 1. Always validate configuration

```python
try:
    config = DatasetConfig(
        tile_size=(512, 512),
        num_workers=0,  # ERROR: must be >= 1
    )
except ValueError as e:
    print(f"Invalid config: {e}")
```

### 2. Use meaningful dataset IDs

```python
# Good
config = DatasetConfig(dataset_id="cohort_A_baseline_V2")

# Bad
config = DatasetConfig(dataset_id="dataset1")
```

### 3. Document your configuration

```python
config = DatasetConfig(
    dataset_id="study_phase1",
    output_dir="./datasets",
    tile_size=(512, 512),
    magnification=20,
    tiler="grid",
    tiler_params={
        "overlap": 50,
        "min_tissue_ratio": 0.5,  # Skip mostly empty tiles
    },
    num_workers=4,
    # Note: Using GridTiler with 50px overlap for smooth region coverage
)
```

### 4. Keep slides and output separate

```python
# Recommended structure
project/
├── data/
│   └── slides/              # Original WSI files
│       ├── slide_001.svs
│       └── slide_002.svs
├── datasets/                # Generated datasets
│   └── dataset_v1/
└── code/
    └── pipeline.py
```

### 5. Backup metadata after generation

```python
from pathlib import Path
import shutil
from datetime import datetime

dataset_dir = Path("./datasets/my_dataset")
backup_dir = Path("./backups") / f"my_dataset_{datetime.now().isoformat()}"

# Backup metadata
shutil.copy(dataset_dir / "metadata.json", backup_dir)
shutil.copy(dataset_dir / "processed.json", backup_dir)
```

---

## Troubleshooting

### Issue: "No module named 'openslide'"

```
ModuleNotFoundError: No module named 'openslide'
```

**Solution:** Install OpenSlide:
```bash
pip install openslide-python
# Or on Ubuntu/Debian:
apt-get install libopenslide0 openslide-tools
```

### Issue: Out of memory errors

```python
# Solutions:
# 1. Use fewer workers
config = DatasetConfig(num_workers=1)

# 2. Use smaller tiles
config = DatasetConfig(tile_size=(256, 256))

# 3. Lower magnification
config = DatasetConfig(magnification=10)
```

### Issue: Very slow processing

```python
# Try:
# 1. Increase workers (if CPU is bottleneck)
config = DatasetConfig(num_workers=8)

# 2. Reduce metadata overhead
config = DatasetConfig(
    save_masks=False,
    save_thumbnails=False,
    verbose=False,
)

# 3. Use faster tiler
config = DatasetConfig(tiler="random")
```

### Issue: Incomplete dataset

If processing fails partway through:

```python
# Check which slides were processed
import json
processed_path = Path("./datasets/my_dataset/processed.json")
with open(processed_path) as f:
    processed = json.load(f)

print(f"Processed: {processed['processed_files']}")
print(f"Total: {processed['total']}")

# Continue with remaining slides
remaining = [s for s in all_slides if s not in processed['processed_files']]
generator.process_dataset(remaining)
```

---

## See Also

- [Tiler Guide](TILER_GUIDE.md) - Detailed tiling strategies
- [Storage Guide](STORAGE_GUIDE.md) - Output organization
- [API Reference](LIBRARY_ARCHITECTURE.md) - Class documentation
