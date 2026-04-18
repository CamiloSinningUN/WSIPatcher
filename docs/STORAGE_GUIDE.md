# GlassCut Storage Guide

## Overview

The StorageOrganizer manages the on-disk organization of datasets following PathoPatcher's proven structure. This ensures scalability, reproducibility, and easy downstream processing.

## Directory Structure

GlassCut organizes datasets as follows:

```
output_directory/
├── dataset_id/
│   ├── metadata.json              ← Dataset-level metadata
│   ├── processed.json             ← List of processed slides
│   │
│   ├── Slide_000/                 ← First slide directory
│   │   ├── slide_metadata.json    ← Per-slide metadata
│   │   ├── tiles/                 ← Extracted tile images
│   │   │   ├── tile_0000000.png
│   │   │   ├── tile_0000001.png
│   │   │   ├── tile_0000002.png
│   │   │   └── ...
│   │   ├── thumbnails/            ← Visualization images
│   │   │   ├── slide_thumbnail.png
│   │   │   └── mask_thumbnail.png
│   │   └── masks/                 ← Binary masks
│   │       └── tissue_mask.png
│   │
│   ├── Slide_001/
│   │   └── (same structure)
│   │
│   └── Slide_N/
│       └── (same structure)
```

## Using StorageOrganizer

### Basic Setup

```python
from glasscut.storage import StorageOrganizer

# Create organizer
organizer = StorageOrganizer(output_dir="./output")

# Initialize dataset
dataset_dir = organizer.init_dataset("my_dataset")
print(dataset_dir)  # ./output/my_dataset

# Initialize a slide
dirs = organizer.init_slide("my_dataset", "Slide_000")
print(dirs)
# {
#   'root': Path('./output/my_dataset/Slide_000'),
#   'tiles': Path('./output/my_dataset/Slide_000/tiles'),
#   'thumbnails': Path('./output/my_dataset/Slide_000/thumbnails'),
#   'masks': Path('./output/my_dataset/Slide_000/masks'),
# }
```

### Saving Files

```python
# Save a tile
tile_path = organizer.get_tile_path("my_dataset", "Slide_000", "tile_000000")
tile.image.save(tile_path)
# Saves to: ./output/my_dataset/Slide_000/tiles/tile_000000.png

# Save thumbnails
thumb_path = organizer.get_slide_thumbnail_path("my_dataset", "Slide_000")
slide.thumbnail.save(thumb_path)

mask_thumb_path = organizer.get_mask_thumbnail_path("my_dataset", "Slide_000")
mask_image.save(mask_thumb_path)

# Save masks
tissue_mask_path = organizer.get_tissue_mask_path("my_dataset", "Slide_000")
mask_array.save(tissue_mask_path)
```

## Metadata Files

### 1. Dataset-Level: `metadata.json`

Located at: `dataset_id/metadata.json`

Contains dataset-wide information and all slide metadata.

**Example structure:**
```json
{
  "dataset_id": "histopathology_study_v1",
  "created_at": "2024-01-15T10:30:00.123456",
  "total_slides": 2,
  "total_tiles": 12548,
  "config": {
    "tile_size": [512, 512],
    "magnification": 20,
    "tiler": "grid",
    "overlap": 50,
    "num_workers": 4
  },
  "slides": [
    {
      "slide_id": "Slide_000",
      "slide_name": "patient_001",
      "slide_path": "/data/slides/patient_001.svs",
      "total_tiles": 6200,
      "dimensions": [50000, 45000],
      "mpp": 0.499,
      "magnification": 20.0,
      "tile_size": [512, 512],
      "tiler_name": "GridTiler",
      "timestamp": "2024-01-15T10:30:05.123456",
      "tiles": [
        {
          "tile_id": "tile_0000000",
          "x": 0,
          "y": 0,
          "width": 512,
          "height": 512,
          "level": 0,
          "magnification": 20.0,
          "tissue_ratio": 0.95,
          "file_path": "histopathology_study_v1/Slide_000/tiles/tile_0000000.png"
        },
        ...
      ]
    },
    {
      "slide_id": "Slide_001",
      ...
    }
  ]
}
```

**Key fields:**
- `dataset_id`: Unique identifier for the dataset
- `created_at`: ISO timestamp of dataset generation
- `total_slides`: Number of slides processed
- `total_tiles`: Total tiles across all slides
- `config`: Configuration parameters used (for reproducibility)
- `slides`: Array of slide metadata (see below)

### 2. Per-Slide: `slide_metadata.json`

Located at: `dataset_id/Slide_XXX/slide_metadata.json`

Contains detailed information about a single slide.

**Example structure:**
```json
{
  "slide_id": "Slide_000",
  "slide_name": "patient_001",
  "slide_path": "/data/slides/patient_001.svs",
  "total_tiles": 6200,
  "dimensions": [50000, 45000],
  "mpp": 0.499,
  "magnification": 20.0,
  "tile_size": [512, 512],
  "tiler_name": "GridTiler",
  "timestamp": "2024-01-15T10:30:05.123456",
  "tiles": [
    {
      "tile_id": "tile_0000000",
      "x": 0,
      "y": 0,
      "width": 512,
      "height": 512,
      "level": 0,
      "magnification": 20.0,
      "tissue_ratio": 0.95,
      "file_path": "histopathology_study_v1/Slide_000/tiles/tile_0000000.png"
    },
    {
      "tile_id": "tile_0000001",
      "x": 512,
      "y": 0,
      "width": 512,
      "height": 512,
      "level": 0,
      "magnification": 20.0,
      "tissue_ratio": 0.87,
      "file_path": "histopathology_study_v1/Slide_000/tiles/tile_0000001.png"
    },
    ...
  ]
}
```

### 3. Processing Tracking: `processed.json`

Located at: `dataset_id/processed.json`

Simple file tracking which slides were successfully processed.

**Example structure:**
```json
{
  "processed_files": [
    "Slide_000",
    "Slide_001"
  ],
  "timestamp": "2024-01-15T10:35:00.123456",
  "total": 2
}
```

**Use case:** If dataset generation fails partway through, this file shows which slides were already processed.

## Reading Metadata

### Load and parse metadata:

```python
from glasscut.storage import StorageOrganizer
import json

organizer = StorageOrganizer("./output")

# Load dataset metadata
dataset_meta = organizer.load_dataset_metadata("my_dataset")
print(f"Total slides: {dataset_meta.total_slides}")
print(f"Total tiles: {dataset_meta.total_tiles}")

# Browse slides
for slide_meta in dataset_meta.slides:
    print(f"{slide_meta.slide_id}: {slide_meta.total_tiles} tiles")
    
    # Browse tiles in slide
    for tile_meta in slide_meta.tiles:
        print(f"  - {tile_meta.tile_id}: tissue_ratio={tile_meta.tissue_ratio:.2f}")
```

## File Naming Conventions

### Slide Directories
```
Slide_000  ← First slide
Slide_001  ← Second slide
Slide_002  ← Third slide
...
Slide_NNN  ← Nth slide (3-digit padding)
```

### Tile Files
```
tile_0000000.png   ← First tile
tile_0000001.png   ← Second tile
tile_0000002.png   ← Third tile
...
tile_NNNNNNN.png   ← Nth tile (7-digit padding)
```

**Benefits of zero-padding:**
- Consistent sorting: tiles sorted naturally by filename
- Easy to count: total files = highest number + 1
- Shell-friendly: Works with glob patterns and bash scripts

### Example counting:
```bash
# Count tiles in a slide easily
ls output/my_dataset/Slide_000/tiles | wc -l

# Display tile range
ls output/my_dataset/Slide_000/tiles | head -1
ls output/my_dataset/Slide_000/tiles | tail -1
```

## Storage Operations API

### Common StorageOrganizer Methods

```python
organizer = StorageOrganizer("./output")

# Initialization
dataset_dir = organizer.init_dataset("my_dataset")
dirs = organizer.init_slide("my_dataset", "Slide_000")

# Path generation
tile_path = organizer.get_tile_path("my_dataset", "Slide_000", "tile_000000")
thumb_path = organizer.get_slide_thumbnail_path("my_dataset", "Slide_000")
mask_path = organizer.get_tissue_mask_path("my_dataset", "Slide_000")

# Metadata operations
organizer.save_dataset_metadata("my_dataset", dataset_meta)
organizer.save_slide_metadata("my_dataset", "Slide_000", slide_meta)
organizer.save_processed_json("my_dataset", ["Slide_000", "Slide_001"])

# Reading
dataset_meta = organizer.load_dataset_metadata("my_dataset")
```

## Disk Space Considerations

### Typical storage usage per slide:

For a 50,000 × 45,000 pixel slide with 512×512 tiles, overlap=50:

| Component | Size | Count | Total |
|-----------|------|-------|-------|
| Tiles (PNG) | ~100 KB | ~6,000 | ~600 MB |
| Slide thumbnail | ~500 KB | 1 | 0.5 MB |
| Mask thumbnail | ~200 KB | 1 | 0.2 MB |
| Tissue mask | ~2 MB | 1 | 2 MB |
| Metadata JSON | ~2 MB | 1 | 2 MB |
| **Per-slide total** | | | **~605 MB** |

### For a 100-slide dataset:

```
100 slides × 605 MB/slide = ~60 GB total
+ 5 MB dataset-level metadata
≈ 60 GB
```

### Optimization strategies:

1. **Reduce tile size:** 256×256 instead of 512×512 reduces size by 4x
2. **JPEG compression:** Use JPEG instead of PNG (~90% smaller)
3. **Selective saving:** Don't save thumbnails/masks for all slides
4. **Archiving:** Compress dataset after generation with tar.gz

Example with smaller tiles:
```python
# 256x256 tiles use ~4x less space
config = DatasetConfig(
    tile_size=(256, 256),  # 4x smaller
    # ... rest of config
)
# → ~150 MB per slide instead of 605 MB
```

## Working with Generated Datasets

### Finding tiles programmatically:

```python
from pathlib import Path
import json

dataset_dir = Path("./output/my_dataset")

# Load dataset metadata
with open(dataset_dir / "metadata.json") as f:
    dataset_meta = json.load(f)

print(f"Dataset contains {dataset_meta['total_slides']} slides")
print(f"Total tiles: {dataset_meta['total_tiles']}")

# Find all tiles for a specific slide
for slide in dataset_meta['slides']:
    if slide['slide_id'] == 'Slide_000':
        print(f"Slide {slide['slide_id']} has {len(slide['tiles'])} tiles")
        for tile in slide['tiles'][:5]:  # First 5 tiles
            print(f"  - {tile['tile_id']}: {tile['file_path']}")
```

### Merging datasets:

```python
import shutil
from pathlib import Path

# Copy slides from one dataset to another
src_dataset = Path("./output/dataset_a")
dst_dataset = Path("./output/dataset_merged")

for slide_dir in src_dataset.glob("Slide_*"):
    dst_slide = dst_dataset / slide_dir.name
    if not dst_slide.exists():
        shutil.copytree(slide_dir, dst_slide)

# Note: You'll need to manually update metadata.json to merge metadata
```

## Compatibility with PathoPatcher

GlassCut's storage format is compatible with PathoPatcher-style processing:

✓ Directory structure matches  
✓ Metadata JSON format compatible  
✓ Tile file naming conventions match  
✓ Per-slide organization identical  

This means:
- PathoPatcher can read GlassCut-generated datasets
- Easy migration from PathoPatcher to GlassCut
- Familiar workflow for PathoPatcher users

---

## See Also

- [Tiler Guide](TILER_GUIDE.md) - How tiles are extracted
- [Dataset Generation Guide](DATASET_GENERATION.md) - Multi-slide processing
- [API Reference](LIBRARY_ARCHITECTURE.md) - Detailed class documentation
