# GlassCut Library - Usage Examples

This document shows practical examples of how GlassCut modules work together.

---

## Example 1: Basic Slide Loading and Tile Extraction

```python
from glasscut.slides import Slide
from pathlib import Path

# Load a slide (automatically attempts GPU backend, falls back to CPU)
slide_path = Path("data/sample_slide.svs")

with Slide(slide_path, use_cucim=True) as slide:
    # Access slide metadata
    print(f"Slide name: {slide.name}")
    print(f"Dimensions: {slide.dimensions}")  # (width, height)
    print(f"Available magnifications: {slide.magnifications}")
    print(f"Microns per pixel: {slide.mpp}")
    
    # Extract a single tile
    tile = slide.extract_tile(
        coords=(5000, 5000),        # x, y at level 0
        tile_size=(512, 512),       # width, height
        magnification=20            # magnification level
    )
    
    print(f"Tile extracted: {tile}")
    print(f"Tile image size: {tile.image.size}")
    
    # Get thumbnail for preview
    thumbnail = slide.thumbnail
    thumbnail.save("slide_preview.png")
```

**Module Communication**:
1. `Slide.__init__()` → attempts `CuCimBackend` → falls back to `OpenSlideBackend`
2. Properties like `magnifications`, `mpp` are lazy-evaluated
3. `extract_tile()` creates a `Tile` object with validated coordinates

---

## Example 2: Tissue Detection in Tiles

```python
from glasscut.slides import Slide
from glasscut.tissue_detectors import OtsuTissueDetector
import numpy as np

slide_path = "data/sample_slide.svs"

with Slide(slide_path) as slide:
    # Extract multiple tiles
    coordinates = [
        (2000, 2000),
        (4000, 4000),
        (6000, 6000),
        (2000, 4000),
    ]
    
    # Method 1: Extract one by one with tissue analysis
    tissue_tiles = []
    for coords in coordinates:
        tile = slide.extract_tile(
            coords=coords,
            tile_size=(512, 512),
            magnification=20
        )
        
        # Check tissue content (lazily computed on first access)
        if tile.has_enough_tissue(tissue_threshold=0.8):
            print(f"Tile at {coords} has {tile.tissue_ratio:.1%} tissue ✓")
            tissue_tiles.append(tile)
        else:
            print(f"Slide at {coords} has only {tile.tissue_ratio:.1%} tissue (skipped)")
    
    # Method 2: Extract multiple tiles in parallel
    tiles = slide.extract_tiles(
        coords_list=coordinates,
        tile_size=(512, 512),
        magnification=20,
        num_workers=4  # Parallel workers
    )
    
    # Filter by tissue content
    filtered_tiles = [
        t for t in tiles 
        if t.has_enough_tissue(tissue_threshold=0.8)
    ]
    
    print(f"Selected {len(filtered_tiles)}/{len(tiles)} tiles with sufficient tissue")
```

**Module Communication Chain**:
```
Slide.extract_tile() 
  → creates Tile
  
User calls tile.has_enough_tissue()
  → Tile accesses self.tissue_mask (lazyproperty)
  → First access triggers OtsuTissueDetector.detect()
  → Cached for subsequent accesses
  
tile.tissue_ratio calculation
  → Uses cached tissue_mask
  → Fast computation without re-detection
```

---

## Example 3: Custom Tissue Detector

```python
from glasscut.tissue_detectors import TissueDetector
from glasscut.slides import Slide
import numpy as np
from PIL import Image
from skimage import filters

class CustomCNNTissueDetector(TissueDetector):
    """Custom tissue detector using your own algorithm."""
    
    def detect(self, image: Image.Image) -> np.ndarray:
        """Custom tissue detection logic."""
        # Implement your CNN or custom algorithm here
        # Example: simple threshold
        img_array = np.array(image.convert("L"))
        threshold = filters.threshold_niblack(img_array, window_size=51)
        tissue_mask = (img_array > threshold).astype(np.uint8)
        return tissue_mask

# Use custom detector with tiles
with Slide("data/sample_slide.svs") as slide:
    tile = slide.extract_tile(
        coords=(5000, 5000),
        tile_size=(512, 512),
        magnification=20
    )
    
    # Replace detector
    tile.tissue_detector = CustomCNNTissueDetector()
    
    # Now uses custom detector
    if tile.has_enough_tissue(tissue_threshold=0.75):
        print("Tile has sufficient tissue (custom detector)")
        print(f"Tissue mask shape: {tile.tissue_mask.shape}")

```

**Key Point**: `TissueDetector` strategy pattern allows seamless swapping of detection methods.

---

## Example 4: Stain Normalization

```python
from glasscut.slides import Slide
from glasscut.stain_normalizers import MacenkoStainNormalizer
from PIL import Image
import os

# Load reference slide for normalization
reference_path = "data/reference_slide.svs"
test_path = "data/test_slide.svs"

# Create normalizer
normalizer = MacenkoStainNormalizer()

# Fit on reference image
with Slide(reference_path) as ref_slide:
    ref_tile = ref_slide.extract_tile(
        coords=(0, 0),
        tile_size=(512, 512),
        magnification=20
    )
    normalizer.fit(ref_tile.image)
    print("Normalizer fitted to reference slide")

# Apply normalization to test slide
with Slide(test_path) as test_slide:
    tiles = test_slide.extract_tiles(
        coords_list=[
            (2000, 2000),
            (4000, 4000),
            (6000, 6000),
        ],
        tile_size=(512, 512),
        magnification=20,
        num_workers=4
    )
    
    # Normalize all tiles
    normalized_tiles = []
    output_dir = "data/normalized_tiles"
    os.makedirs(output_dir, exist_ok=True)
    
    for i, tile in enumerate(tiles):
        normalized_image = normalizer.transform(tile.image)
        
        # Save normalized tile
        normalized_path = f"{output_dir}/tile_{i:03d}.png"
        normalized_image.save(normalized_path)
        
        print(f"Normalized tile {i} saved to {normalized_path}")
```

**Stain Normalizer Workflow**:
```
MacenkoStainNormalizer.fit(reference)
  → Analyzes stain vectors in reference
  → Stores parameters internally
  
normalizer.transform(image)
  → Applies learned parameters to new image
  → Returns normalized PIL Image
```

---

## Example 5: Complete Pipeline - Extraction + Tissue Analysis + Normalization

```python
from glasscut.slides import Slide
from glasscut.tissue_detectors import OtsuTissueDetector
from glasscut.stain_normalizers import MacenkoStainNormalizer
from pathlib import Path
import json

def process_slide_complete(slide_path: str, output_dir: str, magnification: int = 20):
    """Complete pipeline: extract → filter → normalize → save."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "slide_path": str(slide_path),
        "magnification": magnification,
        "tiles": []
    }
    
    # Step 1: Initialize normalizer (fit to first tile)
    normalizer = MacenkoStainNormalizer()
    normalizer_fitted = False
    
    # Step 2: Process slide
    with Slide(slide_path) as slide:
        print(f"Processing {slide.name}")
        print(f"Dimensions: {slide.dimensions}")
        print(f"Magnifications: {slide.magnifications}")
        
        # Generate tile coordinates on a grid
        tile_size = 512
        step_size = 512  # No overlap
        
        coords_list = []
        width, height = slide.dimensions
        
        for y in range(0, height - tile_size, step_size):
            for x in range(0, width - tile_size, step_size):
                coords_list.append((x, y))
        
        print(f"Extracting {len(coords_list)} tiles...")
        
        # Step 3: Extract tiles in parallel
        tiles = slide.extract_tiles(
            coords_list=coords_list,
            tile_size=(tile_size, tile_size),
            magnification=magnification,
            num_workers=8
        )
        
        print(f"Extracted {len(tiles)} tiles")
        
        # Step 4: Fit normalizer on first tissue-rich tile
        for tile in tiles:
            if tile.has_enough_tissue(threshold=0.8):
                normalizer.fit(tile.image)
                normalizer_fitted = True
                print(f"Normalizer fitted on tile at {tile.coords}")
                break
        
        if not normalizer_fitted:
            print("Warning: No tile with sufficient tissue found for normalization")
        
        # Step 5: Process and save tiles
        processed_count = 0
        
        for i, tile in enumerate(tiles):
            # Check tissue content
            if not tile.has_enough_tissue(tissue_threshold=0.8):
                continue
            
            # Get tissue mask for visualization
            tissue_mask = tile.tissue_mask  # Cached after first access
            tissue_ratio = tile.tissue_ratio
            
            # Normalize stain
            normalized_image = normalizer.transform(tile.image)
            
            # Save results
            tile_name = f"tile_{i:06d}"
            normalized_path = output_path / f"{tile_name}_normalized.png"
            normalized_image.save(normalized_path)
            
            # Save tissue mask visualization
            mask_img = Image.fromarray(tissue_mask * 255)
            mask_path = output_path / f"{tile_name}_tissue_mask.png"
            mask_img.save(mask_path)
            
            # Record metadata
            metadata["tiles"].append({
                "index": i,
                "coords": tile.coords,
                "tissue_ratio": float(tissue_ratio),
                "normalized_image": str(normalized_path),
                "tissue_mask": str(mask_path)
            })
            
            processed_count += 1
            
            if processed_count % 10 == 0:
                print(f"Processed {processed_count} tiles...")
        
        # Save metadata
        metadata_path = output_path / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\nProcessing complete!")
        print(f"Processed tiles: {processed_count}")
        print(f"Output directory: {output_dir}")
        print(f"Metadata: {metadata_path}")

# Run the pipeline
if __name__ == "__main__":
    process_slide_complete(
        slide_path="data/sample_slide.svs",
        output_dir="output/processed_tiles",
        magnification=20
    )
```

**Complete Data Flow**:
```
Slide.extract_tiles() 
  ↓
For each tile:
  tile.has_enough_tissue()
    ↓ (first access)
    tissue_detector.detect()
    ↓ (cached)
  
  normalizer.transform(tile.image)
    ↓
  normalized PIL.Image
  
  Save + record metadata
```

---

## Example 6: Error Handling

```python
from glasscut.slides import Slide
from glasscut.exceptions import (
    MagnificationError,
    TileSizeOrCoordinatesError,
    SlidePropertyError
)

slide_path = "data/sample_slide.svs"

try:
    with Slide(slide_path) as slide:
        print(f"Available magnifications: {slide.magnifications}")
        
        # ❌ This will raise MagnificationError
        try:
            tile = slide.extract_tile(
                coords=(1000, 1000),
                tile_size=(512, 512),
                magnification=99  # Not available!
            )
        except MagnificationError as e:
            print(f"Error: {e}")
            print(f"Please use one of: {slide.magnifications}")
        
        # ❌ This will raise TileSizeOrCoordinatesError
        width, height = slide.dimensions
        try:
            tile = slide.extract_tile(
                coords=(width, height),  # Outside boundaries!
                tile_size=(512, 512),
                magnification=20
            )
        except TileSizeOrCoordinatesError as e:
            print(f"Error: {e}")
            print(f"Slide dimensions: {slide.dimensions}")
        
        # ✅ Valid extraction
        tile = slide.extract_tile(
            coords=(5000, 5000),
            tile_size=(512, 512),
            magnification=20
        )
        print("Tile extracted successfully!")
        
except SlidePropertyError as e:
    print(f"Slide property error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Example 7: Batch Processing Multiple Slides

```python
from glasscut.slides import Slide
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_single_slide(slide_path: str) -> dict:
    """Process a single slide (can run in separate process)."""
    
    result = {
        "slide_path": slide_path,
        "tiles_extracted": 0,
        "tiles_with_tissue": 0,
        "average_tissue_ratio": 0.0
    }
    
    try:
        with Slide(slide_path) as slide:
            # Extract grid of tiles
            tiles = slide.extract_tiles(
                coords_list=[
                    (x, y) 
                    for x in range(0, 10000, 1000)
                    for y in range(0, 10000, 1000)
                ],
                tile_size=(512, 512),
                magnification=20,
                num_workers=4
            )
            
            result["tiles_extracted"] = len(tiles)
            
            tissue_ratios = []
            for tile in tiles:
                if tile.has_enough_tissue():
                    result["tiles_with_tissue"] += 1
                    tissue_ratios.append(tile.tissue_ratio)
            
            if tissue_ratios:
                result["average_tissue_ratio"] = sum(tissue_ratios) / len(tissue_ratios)
    
    except Exception as e:
        logger.error(f"Error processing {slide_path}: {e}")
        result["error"] = str(e)
    
    return result

# Process multiple slides in parallel
slides = list(Path("data/slides").glob("*.svs"))

with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_single_slide, [str(s) for s in slides]))

for result in results:
    print(f"{result['slide_path']}: {result['tiles_with_tissue']}/{result['tiles_extracted']} tiles with tissue")
```

---

## Module Interaction Summary

| Operation | Modules Involved | Flow |
|-----------|------------------|------|
| Load slide | Slide, SlideBackend | Slide → tries CuCim → falls back to OpenSlide |
| Extract tile | Slide, Backend, Tile | Slide validates → Backend reads → Tile created |
| Tissue analysis | Tile, TissueDetector | Tile → TissueDetector (lazy, cached) |
| Save tile | Tile, utils | Tile.image → PIL save |
| Stain normalize | StainNormalizer, utils | Normalizer.fit() → transform() → PIL Image |
| Error handling | exceptions | All modules raise custom exceptions |

