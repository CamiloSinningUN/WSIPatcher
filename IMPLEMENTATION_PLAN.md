# GlassCut Enhancement: Tiler + Storage System

## Strategic Plan for Integration

**Objective**: Add HistoLab-style Tilers + PathoPatcher-style Storage to GlassCut  
**Timeline**: Multi-phase implementation  
**Scope**: New module `glasscut.tiler`, storage organization, Dataset orchestrator  

---

## Part 1: Requirements Analysis

### 1.1 Storage Structure (from PathoPatcher model)

**Current PathoPatcher Organization**:
```
output/
├── Dataset_Metadata.csv
├── Slide_001/
│   ├── tile_0000.png
│   ├── tile_0001.png
│   ├── ...
│   ├── thumbnail.png
│   ├── mask.png
│   ├── mask_thumbnail.png
│   ├── metadata.json
│   └── slides.csv
├── Slide_002/
│   └── (same structure)
```

**GlassCut Target Organization** (similar but simpler):
```
output/
├── metadata.json                    # Dataset-level metadata
├── slides_index.csv                 # Index of all slides
├── Slide_001/
│   ├── tiles/
│   │   ├── tile_0000000.png
│   │   ├── tile_0000001.png
│   │   └── ...
│   ├── thumbnails/
│   │   ├── slide_thumbnail.png
│   │   └── mask_thumbnail.png
│   ├── masks/
│   │   └── tissue_mask.png
│   └── slide_metadata.json          # Per-slide metadata
├── Slide_002/
│   └── (same structure)
```

### 1.2 Tiler Interface (from HistoLab model)

**HistoLab Tiler Protocol**:
```python
class Tiler(Protocol):
    def extract(self, slide: Slide) -> Generator[Tile]:
        """Generate tiles"""
    def locate_tiles(self, slide: Slide) -> PIL.Image:
        """Visualize tiles"""
```

**GlassCut Target - Tiler ABC**:
```python
class Tiler(ABC):
    """Base class for tile extraction strategies"""
    
    def extract(self, slide: Slide) -> Generator[Tile]:
        """Generate tiles from slide"""
    
    def get_tile_coordinates(self, slide: Slide) -> List[Tuple[int, int, int, int]]:
        """Get all (x, y, w, h) without extracting"""
    
    def visualize(self, slide: Slide) -> PIL.Image:
        """Show tiles on slide thumbnail"""
```

**Concrete Implementations Needed**:
1. `GridTiler` - Regular grid tiling
2. `RandomTiler` - Random sampling
3. `ConditionalTiler` - Tissue-masked tiling
4. `CustomTiler` - User-defined pattern

### 1.3 Dataset Orchestrator (class)

```python
class DatasetGenerator:
    """Orchestrate multi-slide processing"""
    
    def __init__(self, config: DatasetConfig):
        """Initialize with configuration"""
    
    def process(self, slides_list: List[str]) -> DatasetMetadata:
        """Process multiple WSI files"""
```

---

## Part 2: Architecture Design

### 2.1 New Module Structure

```
glasscut/
├── tiler/                           # NEW
│   ├── __init__.py
│   ├── base.py                      # Tiler ABC
│   ├── grid.py                      # GridTiler
│   ├── random.py                    # RandomTiler
│   ├── conditional.py               # ConditionalTiler
│   └── utils.py                     # Coordinate generation
├── storage/                         # NEW
│   ├── __init__.py
│   ├── manager.py                   # StorageOrganizer
│   ├── metadata.py                  # MetadataManager
│   └── structures.py                # Data models (dataclasses)
├── dataset/                         # NEW
│   ├── __init__.py
│   ├── generator.py                 # DatasetGenerator
│   ├── config.py                    # Configuration models
│   └── utils.py                     # Dataset utilities
├── tiles/
│   └── tile.py                      # Modify: Add metadata tracking
```

### 2.2 Data Flow Architecture

```
User Code
    │
    ├─ DatasetGenerator
    │   │
    │   ├─ DatasetConfig (configuration)
    │   ├─ StorageOrganizer (directory setup)
    │   └─ For each slide:
    │       │
    │       ├─ Slide (load WSI)
    │       ├─ Tiler (select extraction strategy)
    │       │   ├─ GridTiler
    │       │   ├─ RandomTiler
    │       │   └─ ConditionalTiler
    │       │
    │       ├─ For each tile:
    │       │   ├─ Extract tile image
    │       │   ├─ Generate metadata
    │       │   ├─ Save to storage/{slide}/{tiles}/
    │       │   └─ Accumulate metadata
    │       │
    │       ├─ Generate artifacts:
    │       │   ├─ Slide thumbnail
    │       │   ├─ Tissue mask thumbnail
    │       │   └─ Save to storage/{slide}/{thumbnails}/
    │       │
    │       └─ Write slide-level metadata
    │
    └─ Output
        └─ Structured dataset with index
```

### 2.3 Data Models (Dataclasses)

```python
# In storage/structures.py

@dataclass
class TileMetadata:
    """Single tile information"""
    tile_id: str
    x: int
    y: int
    width: int
    height: int
    level: int
    tissue_ratio: float
    file_path: str

@dataclass
class SlideMetadata:
    """Single slide information"""
    slide_id: str
    slide_path: str
    slide_name: str
    total_tiles: int
    dimension: Tuple[int, int]
    mpp: float
    tiles: List[TileMetadata]
    timestamp: str

@dataclass
class DatasetMetadata:
    """Complete dataset information"""
    dataset_id: str
    created_at: str
    total_slides: int
    total_tiles: int
    slides: List[SlideMetadata]
    config: Dict  # Configuration used
```

---

## Part 3: Phase-by-Phase Implementation

### Phase 1: Tiler Base Class ✓ (Week 1: 2-3 days)

**Goal**: Implement `glasscut/tiler/base.py`

```python
# File: glasscut/tiler/base.py

from abc import ABC, abstractmethod
from typing import Generator, List, Tuple
from ..slides import Slide
from ..tiles import Tile

class Tiler(ABC):
    """Abstract base class for tile extraction strategies"""
    
    @abstractmethod
    def extract(self, slide: Slide) -> Generator[Tile, None, None]:
        """
        Extract tiles from slide.
        
        Args:
            slide: Slide object
            
        Yields:
            Tile objects in order
        """
        pass
    
    @abstractmethod
    def get_tile_coordinates(self, slide: Slide) -> List[Tuple[int, int, int, int]]:
        """
        Get all tile coordinates without extracting.
        
        Args:
            slide: Slide object
            
        Returns:
            List of (x, y, width, height) tuples
        """
        pass
    
    def visualize(self, slide: Slide, scale: int = 32) -> PIL.Image:
        """
        Visualize tile grid on slide thumbnail.
        
        Args:
            slide: Slide object
            scale: Scale factor for thumbnail
            
        Returns:
            PIL Image with tile grid drawn
        """
        pass  # Optional implementation
```

**Tasks**:
1. Create `glasscut/tiler/__init__.py`
2. Create `glasscut/tiler/base.py` with Tiler ABC
3. Add type hints, docstrings
4. Create `glasscut/tiler/utils.py` for coordinate utilities

**Tests**:
- Verify ABC prevents direct instantiation
- Test abstract method enforcement

**Output**: Base Tiler class ready for inheritance

---

### Phase 2: GridTiler Implementation ✓ (Week 1: 2-3 days)

**Goal**: Implement `glasscut/tiler/grid.py`

```python
# File: glasscut/tiler/grid.py

from typing import Tuple, Optional
from .base import Tiler

class GridTiler(Tiler):
    """Regular grid tiling strategy"""
    
    def __init__(
        self,
        tile_size: int = 512,
        overlap: int = 0,
        min_tissue_ratio: float = 0.0
    ):
        """
        Initialize grid tiler.
        
        Args:
            tile_size: Size of tiles
            overlap: Overlap between tiles (0-tile_size)
            min_tissue_ratio: Minimum tissue to keep tile
        """
        self.tile_size = tile_size
        self.overlap = overlap
        self.min_tissue_ratio = min_tissue_ratio
    
    def get_tile_coordinates(self, slide: Slide) -> List[Tuple]:
        """Generate grid coordinates"""
        coordinates = []
        step = self.tile_size - self.overlap
        
        for y in range(0, slide.size[1], step):
            for x in range(0, slide.size[0], step):
                w = min(self.tile_size, slide.size[0] - x)
                h = min(self.tile_size, slide.size[1] - y)
                
                # Skip edges smaller than min tile
                if w < self.tile_size // 2 or h < self.tile_size // 2:
                    continue
                
                coordinates.append((x, y, w, h))
        
        return coordinates
    
    def extract(self, slide: Slide) -> Generator[Tile, None, None]:
        """Extract tiles in grid"""
        for x, y, w, h in self.get_tile_coordinates(slide):
            tile_image = slide.read_region((x, y), 0, (w, h))
            tile = Tile(image=tile_image, x=x, y=y, level=0)
            
            # Apply tissue filter
            if self.min_tissue_ratio > 0:
                # Calculate tissue ratio
                tissue_ratio = calculate_tissue_ratio(tile_image)
                if tissue_ratio < self.min_tissue_ratio:
                    continue
            
            yield tile
```

**Tasks**:
1. Implement GridTiler class
2. Implement coordinate generation logic
3. Add validation (overlap bounds, etc.)
4. Add docstrings and type hints
5. Create unit tests

**Tests**:
- Test various tile sizes
- Test overlap handling
- Test edge case (small slides, large tiles)
- Test coordinate generation

**Output**: GridTiler ready for production

---

### Phase 3: Additional Tilers (Week 2: 2-3 days)

**Goal**: Implement RandomTiler and ConditionalTiler

```python
# File: glasscut/tiler/random.py

class RandomTiler(Tiler):
    """Random sampling strategy"""
    
    def __init__(
        self,
        tile_size: int = 512,
        num_tiles: int = 100,
        seed: Optional[int] = None,
        min_tissue_ratio: float = 0.5
    ):
        self.tile_size = tile_size
        self.num_tiles = num_tiles
        self.seed = seed
        self.min_tissue_ratio = min_tissue_ratio
    
    def get_tile_coordinates(self, slide: Slide) -> List[Tuple]:
        """Random sampling"""
        np.random.seed(self.seed)
        coordinates = []
        
        while len(coordinates) < self.num_tiles:
            x = np.random.randint(0, slide.size[0] - self.tile_size)
            y = np.random.randint(0, slide.size[1] - self.tile_size)
            coordinates.append((x, y, self.tile_size, self.tile_size))
        
        return coordinates
```

```python
# File: glasscut/tiler/conditional.py

class ConditionalTiler(Tiler):
    """Tissue-aware tiling"""
    
    def __init__(
        self,
        tile_size: int = 512,
        tissue_detector = None,
        min_tissue_in_tile: float = 0.5
    ):
        self.tile_size = tile_size
        self.tissue_detector = tissue_detector
        self.min_tissue_in_tile = min_tissue_in_tile
    
    def get_tile_coordinates(self, slide: Slide) -> List[Tuple]:
        """Generate coordinates only in tissue regions"""
        # Get tissue mask
        tissue_mask = self.tissue_detector.get_tissue_mask(slide)
        
        # Generate grid and filter by tissue
        coordinates = []
        for y in range(0, slide.size[1], self.tile_size):
            for x in range(0, slide.size[0], self.tile_size):
                # Check tissue coverage
                tissue_in_region = np.mean(
                    tissue_mask[y:y+self.tile_size, x:x+self.tile_size]
                )
                
                if tissue_in_region >= self.min_tissue_in_tile:
                    coordinates.append((x, y, self.tile_size, self.tile_size))
        
        return coordinates
```

**Tasks**:
1. Implement RandomTiler
2. Implement ConditionalTiler
3. Add tests for each
4. Performance testing

**Output**: Multiple Tiler strategies available

---

### Phase 4: Storage Organization (Week 2: 3-4 days)

**Goal**: Implement `glasscut/storage/` module

```python
# File: glasscut/storage/structures.py

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from datetime import datetime

@dataclass
class TileMetadata:
    tile_id: str
    x: int
    y: int
    width: int
    height: int
    level: int
    tissue_ratio: float
    file_path: str

@dataclass
class SlideMetadata:
    slide_id: str
    slide_name: str
    slide_path: str
    total_tiles: int
    dimensions: Tuple[int, int]
    mpp: float
    timestamp: str
    tiles: List[TileMetadata] = field(default_factory=list)

@dataclass
class DatasetMetadata:
    dataset_id: str
    created_at: str
    total_slides: int
    total_tiles: int
    config: Dict = field(default_factory=dict)
    slides: List[SlideMetadata] = field(default_factory=list)
```

```python
# File: glasscut/storage/manager.py

from pathlib import Path
import json
from typing import Optional
from .structures import DatasetMetadata, SlideMetadata

class StorageOrganizer:
    """Manage dataset directory structure"""
    
    def __init__(self, output_dir: str):
        """Initialize storage"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def init_dataset(self, dataset_id: str) -> Path:
        """Initialize dataset structure"""
        dataset_path = self.output_dir / dataset_id
        dataset_path.mkdir(exist_ok=True)
        return dataset_path
    
    def init_slide(self, dataset_id: str, slide_id: str) -> Dict[str, Path]:
        """Initialize slide subdirectories"""
        slide_dir = self.output_dir / dataset_id / slide_id
        
        dirs = {
            'root': slide_dir,
            'tiles': slide_dir / 'tiles',
            'thumbnails': slide_dir / 'thumbnails',
            'masks': slide_dir / 'masks',
        }
        
        for dir_path in dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        return dirs
    
    def get_tile_path(self, dataset_id: str, slide_id: str, tile_id: str) -> Path:
        """Get path for tile"""
        return self.output_dir / dataset_id / slide_id / 'tiles' / f'{tile_id}.png'
    
    def save_metadata(self, metadata: DatasetMetadata):
        """Save dataset metadata as JSON"""
        metadata_path = self.output_dir / metadata.dataset_id / 'metadata.json'
        
        # Convert dataclass to dict
        data = asdict(metadata)
        
        with open(metadata_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_metadata(self, dataset_id: str) -> DatasetMetadata:
        """Load dataset metadata"""
        metadata_path = self.output_dir / dataset_id / 'metadata.json'
        
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        
        # Convert dict back to dataclass
        return DatasetMetadata(**data)
```

**Tasks**:
1. Create `glasscut/storage/structures.py` with dataclasses
2. Create `glasscut/storage/manager.py` with StorageOrganizer
3. Create `glasscut/storage/metadata.py` for metadata utilities
4. Add JSON serialization/deserialization
5. Add indexing utilities (CSV generation)

**Tests**:
- Directory structure creation
- Metadata serialization
- Path resolution

**Output**: Storage system ready for use

---

### Phase 5: DatasetGenerator Orchestrator (Week 3: 3-4 days)

**Goal**: Implement `glasscut/dataset/` module

```python
# File: glasscut/dataset/config.py

from dataclasses import dataclass
from typing import Optional, List, Type

@dataclass
class DatasetConfig:
    """Dataset generation configuration"""
    dataset_id: str
    output_dir: str
    tile_size: int = 512
    tiler: str = "grid"  # grid, random, conditional
    tiler_params: dict = None
    save_thumbnails: bool = True
    save_masks: bool = True
    mask_level: int = 4
    num_workers: int = 1
    verbose: bool = True
```

```python
# File: glasscut/dataset/generator.py

from pathlib import Path
from typing import List, Optional
import logging
from ..slides import Slide
from ..tiler.base import Tiler
from ..storage.manager import StorageOrganizer
from ..storage.structures import DatasetMetadata, SlideMetadata, TileMetadata
from .config import DatasetConfig

class DatasetGenerator:
    """Orchestrate multi-slide dataset generation"""
    
    def __init__(self, config: DatasetConfig):
        """Initialize with configuration"""
        self.config = config
        self.storage = StorageOrganizer(config.output_dir)
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger("DatasetGenerator")
        if self.config.verbose:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)
        return logger
    
    def process_dataset(self, slide_paths: List[str]) -> DatasetMetadata:
        """
        Process multiple slides into dataset.
        
        Args:
            slide_paths: List of paths to WSI files
            
        Returns:
            DatasetMetadata with all information
        """
        self.logger.info(f"Starting dataset generation: {self.config.dataset_id}")
        self.logger.info(f"Processing {len(slide_paths)} slides")
        
        # Initialize dataset
        self.storage.init_dataset(self.config.dataset_id)
        
        # Initialize tiler
        tiler = self._get_tiler()
        
        # Process each slide
        slides_metadata = []
        total_tiles = 0
        
        for i, slide_path in enumerate(slide_paths):
            self.logger.info(f"[{i+1}/{len(slide_paths)}] Processing {Path(slide_path).name}")
            
            try:
                slide_meta = self._process_slide(
                    slide_path=slide_path,
                    slide_index=i,
                    tiler=tiler
                )
                slides_metadata.append(slide_meta)
                total_tiles += slide_meta.total_tiles
                
            except Exception as e:
                self.logger.error(f"Failed to process {slide_path}: {e}")
                continue
        
        # Create dataset metadata
        dataset_meta = DatasetMetadata(
            dataset_id=self.config.dataset_id,
            created_at=datetime.now().isoformat(),
            total_slides=len(slides_metadata),
            total_tiles=total_tiles,
            config=asdict(self.config),
            slides=slides_metadata
        )
        
        # Save metadata
        self.storage.save_metadata(dataset_meta)
        
        self.logger.info(f"Dataset complete: {total_tiles} tiles from {len(slides_metadata)} slides")
        return dataset_meta
    
    def _get_tiler(self) -> Tiler:
        """Get configured tiler"""
        if self.config.tiler == "grid":
            from ..tiler.grid import GridTiler
            return GridTiler(**(self.config.tiler_params or {}))
        elif self.config.tiler == "random":
            from ..tiler.random import RandomTiler
            return RandomTiler(**(self.config.tiler_params or {}))
        elif self.config.tiler == "conditional":
            from ..tiler.conditional import ConditionalTiler
            return ConditionalTiler(**(self.config.tiler_params or {}))
        else:
            raise ValueError(f"Unknown tiler: {self.config.tiler}")
    
    def _process_slide(
        self,
        slide_path: str,
        slide_index: int,
        tiler: Tiler
    ) -> SlideMetadata:
        """Process single slide"""
        slide_name = Path(slide_path).stem
        slide_id = f"Slide_{slide_index:03d}"
        
        # Initialize storage for this slide
        dirs = self.storage.init_slide(self.config.dataset_id, slide_id)
        
        # Load slide
        slide = Slide(slide_path)
        
        # Extract tiles
        tile_list = []
        for tile_index, tile in enumerate(tiler.extract(slide)):
            tile_id = f"tile_{tile_index:07d}"
            
            # Save tile
            tile_path = dirs['tiles'] / f"{tile_id}.png"
            tile.image.save(tile_path)
            
            # Record metadata
            tile_meta = TileMetadata(
                tile_id=tile_id,
                x=tile.x,
                y=tile.y,
                width=tile.image.width,
                height=tile.image.height,
                level=tile.level,
                tissue_ratio=self._calculate_tissue_ratio(tile),
                file_path=str(tile_path.relative_to(self.storage.output_dir))
            )
            tile_list.append(tile_meta)
        
        # Generate artifacts (thumbnails, masks)
        if self.config.save_thumbnails:
            self._save_thumbnails(slide, dirs)
        
        if self.config.save_masks:
            self._save_masks(slide, dirs)
        
        # Create slide metadata
        slide_meta = SlideMetadata(
            slide_id=slide_id,
            slide_name=slide_name,
            slide_path=slide_path,
            total_tiles=len(tile_list),
            dimensions=slide.size,
            mpp=slide.base_mpp if hasattr(slide, 'base_mpp') else 0.0,
            timestamp=datetime.now().isoformat(),
            tiles=tile_list
        )
        
        return slide_meta
    
    def _save_thumbnails(self, slide: Slide, dirs: Dict[str, Path]):
        """Save slide thumbnail"""
        thumb = slide.get_thumbnail((512, 512))
        thumb.save(dirs['thumbnails'] / 'slide_thumbnail.png')
    
    def _save_masks(self, slide: Slide, dirs: Dict[str, Path]):
        """Save tissue mask"""
        # Use slide's tissue detector
        from ..tissue_detectors import OtsuTissueDetector
        detector = OtsuTissueDetector()
        mask = detector.get_tissue_mask(slide)
        
        # Save as image
        mask_img = Image.fromarray((mask * 255).astype(np.uint8))
        mask_img.save(dirs['masks'] / 'tissue_mask.png')
    
    def _calculate_tissue_ratio(self, tile) -> float:
        """Calculate tissue ratio for tile"""
        # Simple implementation - can be extended
        return 0.8  # Placeholder
```

**Tasks**:
1. Create `glasscut/dataset/config.py` with DatasetConfig
2. Create `glasscut/dataset/generator.py` with DatasetGenerator
3. Implement single-slide processor
4. Implement artifact generation (thumbnails, masks)
5. Add progress tracking and logging
6. Create CSV index generation

**Tests**:
- Single slide processing
- Multi-slide processing
- Config validation
- Metadata generation

**Output**: Complete dataset generator

---

### Phase 6: Integration & Public API (Week 3: 2-3 days)

**Goal**: Make everything accessible from main `glasscut` module

```python
# File: glasscut/__init__.py (modify)

from .tiler import Tiler, GridTiler, RandomTiler, ConditionalTiler
from .storage import StorageOrganizer, DatasetMetadata, SlideMetadata
from .dataset import DatasetGenerator, DatasetConfig

# Update __all__
__all__ = [
    # Existing
    'Slide',
    'Tile',
    'OtsuTissueDetector',
    'MacenkoNormalizer',
    
    # New
    'Tiler',
    'GridTiler',
    'RandomTiler',
    'ConditionalTiler',
    'StorageOrganizer',
    'DatasetGenerator',
    'DatasetConfig',
]
```

**Tasks**:
1. Update `__init__.py` files for new modules
2. Create comprehensive docstrings
3. Add type hints everywhere
4. Create integration examples

**Output**: Clean public API

---

### Phase 7: Documentation & Examples (Week 4: 2-3 days)

**Goal**: Document new features with examples

**Files to create**:
1. `docs/TILER_GUIDE.md` - Tiler usage guide
2. `docs/STORAGE_GUIDE.md` - Storage organization
3. `docs/DATASET_GENERATION.md` - Complete examples
4. `examples/example_dataset_generation.py` - Working example

**Example Code**:
```python
# Example: Simple dataset generation

from glasscut import DatasetGenerator, DatasetConfig

config = DatasetConfig(
    dataset_id="my_dataset_v1",
    output_dir="/data/output",
    tile_size=512,
    tiler="grid",
    tiler_params={
        "overlap": 50,
        "min_tissue_ratio": 0.5
    }
)

generator = DatasetGenerator(config)

slide_paths = [
    "/data/slides/slide_001.svs",
    "/data/slides/slide_002.svs",
    "/data/slides/slide_003.svs",
]

dataset_meta = generator.process_dataset(slide_paths)
print(f"Generated {dataset_meta.total_tiles} tiles")
```

**Tasks**:
1. Write comprehensive guides
2. Create working examples
3. Add API documentation
4. Add troubleshooting guide

**Output**: Production-ready documentation

---

### Phase 8: Testing & Optimization (Week 4: 2-4 days)

**Goal**: Comprehensive testing and performance tuning

**Unit Tests** (~50-70 tests):
- Tiler coordinate generation
- Storage directory structure
- Metadata serialization
- Dataset generation workflow

**Integration Tests** (~10-15 tests):
- End-to-end dataset generation
- Multiple slide processing
- Error handling

**Performance Tests**:
- Single slide extraction speed
- Multi-slide throughput
- Memory usage
- Storage efficiency

**Tasks**:
1. Write unit tests for each module
2. Write integration tests
3. Performance benchmarking
4. Memory profiling
5. Optimization based on metrics

**Output**: Test suite with 80%+ coverage

---

## Part 4: Architecture Decisions & Justifications

### Decision 1: Why ABC instead of Protocol (HistoLab style)?

**Choice**: Use ABC for Tiler  
**Rationale**:
- GlassCut's style uses inheritance (not protocols)
- Easier for users to extend
- Can include default implementations
- More explicit than protocols for beginners

### Decision 2: Storage organization (PathoPatcher-inspired)?

**Choice**: Similar structure but simplified  
**Rationale**:
- Familiar to PathoPatcher users
- Organized for downstream processing
- Easy to index programmatically
- Extensible for future features

### Decision 3: Dataclasses for metadata?

**Choice**: Use dataclasses with JSON serialization  
**Rationale**:
- Type-safe
- Serializable
- Immutable-friendly
- Easy to extend

### Decision 4: Synchronous vs Asynchronous?

**Choice**: Synchronous with optional multiprocessing hook  
**Rationale**:
- Matches GlassCut's current style
- Simpler debugging
- Can add multiprocessing in Phase 9 (optional)
- Easier for beginners

---

## Part 5: Implementation Timeline

### Week 1 (6 days)
- **Days 1-3**: Phase 1 (Tiler ABC) + Phase 2 (GridTiler)
- **Days 4-6**: Phase 3 (RandomTiler, ConditionalTiler)

### Week 2 (6 days)
- **Days 1-3**: Phase 4 (Storage organization)
- **Days 4-6**: Phase 5 (DatasetGenerator) - initial implementation

### Week 3 (6 days)
- **Days 1-3**: Phase 5 (DatasetGenerator) - complete
- **Days 4-6**: Phase 6 (Integration & API)

### Week 4 (6 days)
- **Days 1-3**: Phase 7 (Documentation & Examples)
- **Days 4-6**: Phase 8 (Testing & Optimization)

**Total**: ~4 weeks for Phase 1-8

---

## Part 6: Future Enhancements (Phase 9+)

### Post-MVP Features:
1. **Multiprocessing** - Parallel slide processing
2. **Streaming** - Large batch processing with generators
3. **Caching** - Smart tile cache to avoid recomputation
4. **Visualization** - Interactive tile browser
5. **Validation** - Dataset integrity checks
6. **Export** - HDF5, Zarr formats (like PathoPatcher)
7. **ML Integration** - PyTorch DataLoader support
8. **Distributed** - Dask support for clusters

---

## Part 7: Risk Assessment & Mitigation

### Risk 1: API Stability
**Concern**: Changes to Tile class might break existing code  
**Mitigation**:
- Add new fields as optional, not required
- Keep backward compatibility
- Version the storage format

### Risk 2: Performance
**Concern**: Large datasets might be slow  
**Mitigation**:
- Profile early
- Optimize hot paths
- Add caching layer
- Plan multiprocessing for Phase 9

### Risk 3: Storage Efficiency
**Concern**: PNG storage might be large  
**Mitigation**:
- Use compression
- Add optional format conversion to JPEG
- Plan for HDF5 in Phase 9

### Risk 4: User Adoption
**Concern**: Complex API might overwhelm users  
**Mitigation**:
- Start with sensible defaults
- Excellent documentation
- Working examples
- Progressive disclosure (advanced features optional)

---

## Part 8: Success Criteria

### Functional Requirements
- [ ] Tiler generates correct coordinates
- [ ] Tiles extracted match expected sizes
- [ ] Storage structure matches spec
- [ ] Metadata accurately captured
- [ ] Multiple slides processed without errors

### Performance Requirements
- [ ] Single slide: <5 min (1000 tiles, 512x512)
- [ ] Memory: <2GB for typical dataset
- [ ] Throughput: >200 tiles/min on single thread

### Quality Requirements
- [ ] Test coverage >80%
- [ ] All code documented
- [ ] Examples run without modification
- [ ] 0 linting errors (pylint, mypy)

### Usability Requirements
- [ ] API is intuitive
- [ ] Error messages are helpful
- [ ] Documentation is complete
- [ ] Examples cover common use cases

---

## Part 9: Dependencies & Prerequisites

### New Dependencies to Add:
- None required (use existing PIL, numpy, etc.)
- Optional: `pandas` for CSV handling (consider using CSV module)
- Optional: `tqdm` for progress bars

### Code Dependencies:
- Uses existing: `Slide`, `Tile` from glasscut
- Uses existing: `OtsuTissueDetector` from tissue_detectors
- Builds on existing caching patterns

---

## Part 10: File Structure Summary

```
glasscut/
├── tiler/
│   ├── __init__.py
│   ├── base.py                  # Tiler ABC
│   ├── grid.py                  # GridTiler
│   ├── random.py                # RandomTiler
│   ├── conditional.py           # ConditionalTiler
│   └── utils.py                 # Helpers
├── storage/
│   ├── __init__.py
│   ├── structures.py            # Dataclasses
│   ├── manager.py               # StorageOrganizer
│   ├── metadata.py              # MetadataManager
│   └── utils.py                 # Indexing
├── dataset/
│   ├── __init__.py
│   ├── config.py                # DatasetConfig
│   ├── generator.py             # DatasetGenerator
│   └── utils.py                 # Utilities
├── tests/
│   ├── test_tiler/
│   │   ├── test_grid.py
│   │   ├── test_random.py
│   │   └── test_conditional.py
│   ├── test_storage/
│   │   ├── test_structures.py
│   │   └── test_manager.py
│   ├── test_dataset/
│   │   └── test_generator.py
│   └── test_integration.py
├── docs/
│   ├── TILER_GUIDE.md
│   ├── STORAGE_GUIDE.md
│   └── DATASET_GENERATION.md
├── examples/
│   └── example_dataset_generation.py
```

---

## Part 11: Getting Started - Immediate Next Steps

### For the User Now:
1. **Review this plan** - Feedback on architecture?
2. **Prioritize** - Any phases to tackle first?
3. **Timeline** - Does 4 weeks seem reasonable?
4. **Dependencies** - Any changes needed?

### Recommended First Action:
**Phase 1 + Phase 2 (Week 1)**: Get GridTiler working
- Simplest to implement
- Validates the overall approach
- Provides foundation for others

---

## Reference: How This Combines the Three Libraries

### From GlassCut:
- Clean, minimal API
- Backend abstraction pattern
- Property-based configuration
- Lazy evaluation

### From HistoLab:
- Tiler as pluggable strategy (GridTiler, RandomTiler, ConditionalTiler)
- Protocol-like extensibility
- Rich metadata tracking
- Filter composition patterns

### From PathoPatcher:
- Storage organization (slide folders, tile subfolders, artifacts)
- Metadata JSON per slide
- Indexing and cataloguing
- Batch processing orchestration

**Result**: Best of all three, GlassCut style!

---

## Questions for User Clarification

1. **Timeline**: Is 4 weeks realistic for your needs?
2. **Phase ordering**: Start with GridTiler first?
3. **Naming**: Content with "Tiler", "DatasetGenerator", "StorageOrganizer"?
4. **Metadata**: Should we include more fields (e.g., image statistics)?
5. **Multiprocessing**: Should we include in Phase 5 or leave for Phase 9?
6. **Formats**: PNG only, or also JPEG as option?
7. **Compatibility**: Should we support loading PathoPatcher datasets?
8. **Configuration**: YAML config file or Python API only?
