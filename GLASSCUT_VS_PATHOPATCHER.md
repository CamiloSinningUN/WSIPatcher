# GlassCut vs PathoPatcher: Comparison & Integration

## High-Level Comparison

### GlassCut: Minimal, Focused Library
**Purpose**: Simple slide access and tile extraction  
**Scope**: Core WSI operations  
**Complexity**: Low  
**Use Case**: Research, exploration, quick prototyping  

### PathoPatcher: Production Pipeline
**Purpose**: Complete preprocessing for ML datasets  
**Scope**: Full end-to-end pipeline with quality control  
**Complexity**: High  
**Use Case**: Dataset creation, clinical workflows, production  

---

## Feature Comparison

| Feature | GlassCut | PathoPatcher |
|---------|----------|--------------|
| **Core Reading** | ✓ | ✓ |
| Tile Extraction | Simple API | Grid-based with filtering |
| Annotation Support | Via external tools | Built-in (GeoJSON/XML) |
| Tissue Detection | Otsu only | Otsu + masked + prefilter |
| Stain Normalization | Via injected normalizer | Macenko built-in |
| Multiprocessing | No | Yes (queue workers) |
| Output Organization | None | Structured dataset format |
| Thumbnails | Via property | Automatic per slide |
| Context Patches | Manual | Automatic multi-scale |
| Configuration | Minimal | Comprehensive (50+ params) |
| CLI | None | Full CLI + YAML support |
| Logging | Basic | Production-grade |
| Error Handling | Exceptions | Exceptions + validation |
| PyTorch Integration | Via manual dataset | TissueDetectionDataset |
| GPU Support | Via backend | Auto-fallback |
| Batch Processing | No | Yes, with queue |
| Metadata Management | Per-tile manual | Automatic YAML per patch |

---

## Architecture Comparison

### GlassCut Architecture
```
User Code
  ↓
Slide → Backend (cuCIM/OpenSlide)
  ↓
Tile → TissueDetector → Properties (tissue_mask, tissue_ratio)
  ↓
Stain Normalizer (external)
```

**Focus**: Single slide, single tile  
**API Style**: Object-oriented, property-based

### PathoPatcher Architecture
```
CLI/Parser → Config
  ↓
PreProcessor → Hardware selection
  ↓
For each WSI:
  → Backend (cuCIM/OpenSlide)
  → Generate tissue mask
  → Load annotations
  → Find patch coordinates
  → Queue patches
  ↓
Multiprocessing Workers:
  → Normalize stains
  → Extract context
  → Save with metadata
  ↓
Structured Dataset
```

**Focus**: Batch of slides, organized dataset  
**API Style**: Imperative, pipeline-based

---

## Code Examples: Same Task, Different Approaches

### Task: Extract 256x256 patches at 20x from a slide

#### Using GlassCut:
```python
from glasscut.slides import Slide
from PIL import Image
import os

slide_path = "slide.svs"
output_dir = "patches"
os.makedirs(output_dir, exist_ok=True)

with Slide(slide_path) as slide:
    # Manually define coordinates
    coords_list = [(x, y) for x in range(0, 10000, 256) 
                          for y in range(0, 10000, 256)]
    
    # Extract in parallel
    tiles = slide.extract_tiles(
        coords_list=coords_list,
        tile_size=(256, 256),
        magnification=20,
        num_workers=4
    )
    
    # Manual organization
    for i, tile in enumerate(tiles):
        if tile.has_enough_tissue(threshold=0.8):
            patch_path = f"{output_dir}/patch_{i:06d}.png"
            tile.save(patch_path)
```

**Responsibility**: User handles organization, filtering, metadata

#### Using PathoPatcher:
```yaml
# config.yaml
wsi_paths: /data/slides
output_path: /data/output
patch_size: 256
target_mag: 20
filter_patches: true
processes: 8
```

```bash
python -m pathopatch.wsi_extraction --config config.yaml
```

**Result**:
```
output/
├── slide_name/
│   ├── patches/
│   │   ├── slide_name_0_0.png
│   │   └── ...
│   ├── metadata/
│   │   ├── slide_name_0_0.yaml
│   │   └── ...
│   ├── tissue_masks/
│   ├── thumbnails/
│   └── metadata.yaml
```

**Responsibility**: Library handles organization, filtering, metadata

---

## When to Use Each

### Use **GlassCut** when you:
- Need programmatic WSI access
- Want light-weight dependencies
- Build custom preprocessing
- Do research or exploration
- Extract specific tiles from a slide
- Implement custom filtering logic
- Don't need scale to many slides

### Use **PathoPatcher** when you:
- Create ML training datasets
- Process multiple slides
- Need annotation support
- Want standardized output
- Require quality filtering
- Need batch processing
- Want automatic metadata
- Need production-grade logging

---

## Integration: Using Both Together

### Scenario 1: Custom Tissue Detection via GlassCut

```python
# Use GlassCut for custom tissue detection
from glasscut.slides import Slide
from glasscut.tile import Tile
from glasscut.tissue_detectors import TissueDetector
import numpy as np
from PIL import Image

class CustomDLTissueDetector(TissueDetector):
    """Custom detector using your model"""
    def __init__(self, model):
        self.model = model
    
    def detect(self, image: Image.Image) -> np.ndarray:
        # Your detection logic
        return mask  # Binary mask

# Then use with PathoPatcher by configuring masking
# PathoPatcher would need to call this custom detector
# Requires extending PathoPatcher's masking module
```

### Scenario 2: Post-Processing PathoPatcher Output

```python
# PathoPatcher generates patches
# Use GlassCut for further analysis

from pathlib import Path
from glasscut.utils import np_to_pil
import numpy as np
from PIL import Image
import yaml

output_dir = Path("/data/pathopatcher_output")

for slide_dir in output_dir.iterdir():
    # Load slide metadata
    meta_path = slide_dir / "metadata.yaml"
    with open(meta_path) as f:
        slide_meta = yaml.safe_load(f)
    
    # Open original slide with GlassCut for verification
    # slide_path = ...
    # with Slide(slide_path) as slide:
    #     tile = slide.extract_tile(...)
    
    patches_dir = slide_dir / "patches"
    for patch_file in patches_dir.glob("*.png"):
        patch = Image.open(patch_file)
        # Further analysis with GlassCut utilities
        # e.g., custom filtering, stain analysis
```

### Scenario 3: Advanced Preprocessing Pipeline

```python
# Use PathoPatcher for batch extraction
# Use GlassCut for verification/QA

from pathopatch.cli import PreProcessingParser
from pathopatch.patch_extraction.patch_extraction import PreProcessor
from glasscut.slides import Slide
import random

# Step 1: Bulk extract with PathoPatcher
parser = PreProcessingParser()
config, logger = parser.get_config()
preprocessor = PreProcessor(slide_processor_config=config)
preprocessor.sample_patches_dataset()
logger.info("PathoPatcher extraction complete")

# Step 2: Verification with GlassCut
output_paths = list(Path(config.output_path).glob("*/metadata.yaml"))
samples_to_verify = random.sample(output_paths, min(5, len(output_paths)))

for meta_path in samples_to_verify:
    # Load patch and verify against original slide
    patch_data = yaml.safe_load(open(meta_path))
    coords = patch_data['coordinates']
    mag = patch_data['magnification']
    
    # Verify by reading from original slide with GlassCut
    slide_name = meta_path.parent.name
    original_slide = find_slide_by_name(slide_name)
    
    with Slide(original_slide) as slide:
        verification_tile = slide.extract_tile(
            coords=coords,
            tile_size=(256, 256),
            magnification=mag
        )
        # Compare checksums or visual properties
        logger.info(f"Verified patch: tissue ratio = {verification_tile.tissue_ratio}")
```

---

## Module Overlap Analysis

### Modules in Common:

| Module | GlassCut | PathoPatcher | Notes |
|--------|----------|--------------|-------|
| `utils.np_to_pil` | ✓ | ✓ | Both implement same function |
| `utils.lazyproperty` | ✓ | ✗ | GlassCut uses for caching |
| Tissue Detection | Basic | Advanced | PathoPatcher has masked Otsu |
| Stain Normalization | Via injection | Built-in | Different integration |
| WSI Backend Abstraction | ✓ | ✓ | Similar but different APIs |
| Exceptions | ✓ | ✓ | Different exception types |

### Potential Code Sharing:

1. **np_to_pil function**: Could be unified in a shared utils
2. **WSI Backend interface**: Could standardize DeepZoomGenerator usage
3. **Tissue detection**: GlassCut's TissueDetector could be used in PathoPatcher
4. **Stain normalizers**: GlassCut's classes could be reused in PathoPatcher

---

## Data Flow: Using Both Libraries

```
Original WSI File
    ↓
[PathoPatcher Extraction]
    ├─ Automatic tissue detection
    ├─ Bulk patch extraction
    ├─ Stain normalization
    ├─ Metadata generation
    └─ Structured dataset output
    ↓
Organized Dataset
    ├── patches/
    ├── metadata/
    └── tissue_masks/
    ↓
[GlassCut Verification/Analysis]
    ├─ Load original slide
    ├─ Verify specific patches
    ├─ Custom filtering
    └─ Research/exploration
    ↓
Final Analysis Results
```

---

## Code Organization Suggestions

If merging or sharing code:

```
glasscut/
├── core/
│   ├── slide.py              # Core slide reading
│   ├── tile.py               # Tile representation
│   └── backends/             # WSI backends
├── preprocessing/            # Shared with PathoPatcher
│   ├── tissue_detection/
│   │   ├── base.py
│   │   ├── otsu.py          # Could be shared
│   │   └── masked_otsu.py
│   ├── stain_normalization/
│   │   ├── base.py
│   │   └── macenko.py
│   └── annotation/
│       └── converter.py      # Could be shared
├── utils/
│   ├── np_to_pil.py         # Shared
│   ├── lazyproperty.py      # GlassCut-specific
│   └── filters.py           # Shared
├── exceptions.py
└── ...

pathopatch/
├── pipeline.py               # Main PreProcessor
├── config/
├── wsi_interfaces/
├── patch_extraction/
├── storage/
├── utils/
│   ├── masking.py           # Uses glasscut.preprocessing
│   ├── patch_util.py        # Uses glasscut.preprocessing
│   └── ...
└── ...
```

---

## Performance Characteristics

### GlassCut:
- Single-threaded per tile
- Fast for small-scale tile extraction
- GPU support via backend selection
- Memory efficient

### PathoPatcher:
- Multi-threaded (queue workers)
- Optimized for bulk dataset creation
- Better utilizes GPU with batch operations
- Higher memory overhead but faster throughput

**Benchmark** (hypothetical):
```
Task: Extract 5000 patches from 10 slides
GlassCut: 2 hours (manual parallelization needed)
PathoPatcher: 20 minutes (automatic multiprocessing)
```

---

## Ecosystem Positioning

```
Low-Level        GlassCut           PathoPatcher        High-Level
APIs             (Core)             (Pipeline)          Abstractions
                                    
Raw slides  →  Tile reading  →  Patch extraction  →  ML Datasets
             (with filtering) (with organization)
```

**GlassCut**: "How do I read and work with slides?"  
**PathoPatcher**: "How do I create training datasets?"

---

## Recommendation Matrix

| Use Case | Recommendation | Why |
|----------|---|---|
| Research project | GlassCut | Lightweight, flexible |
| Prototype ML | GlassCut initially, then PathoPatcher | Start simple, scale up |
| Production pipeline | PathoPatcher + GlassCut for QA | Scalable + verification |
| Custom preprocessing | GlassCut foundation | More control |
| Standard dataset creation | PathoPatcher | Out-of-the-box solution |
| Mixed workflows | Both in same project | Each tool for its purpose |

---

## Future Integration Opportunities

1. **Unify exceptions**: Single exception hierarchy
2. **Shared utilities**: Common utils module
3. **Tissue detection**: GlassCut detectors in PathoPatcher
4. **Backend abstraction**: Standardized interface
5. **CLI for GlassCut**: Add command-line interface
6. **Modular PathoPatcher**: Make components reusable as GlassCut plugins

