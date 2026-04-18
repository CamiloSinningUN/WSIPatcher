"""GlassCut: Fast and flexible histopathology image tiling library.

A lightweight, extensible library for extracting tiles from whole slide images (WSI)
with support for multiple tiling strategies, parallel processing, and comprehensive
metadata tracking.

Core Components:
    Slide I/O:
        - Slide: WSI reader with backend abstraction
        - Tile: Individual tile image with metadata

    Tiling Strategies (pluggable):
        - Tiler: Abstract base class for tiling strategies
        - GridTiler: Regular grid tiling with optional overlap
        - RandomTiler: Random sampling-based tiling
        - ConditionalTiler: Tissue-aware conditional tiling

    Dataset Generation:
        - DatasetGenerator: Multi-slide orchestrator with parallel processing
        - DatasetConfig: Configuration for dataset generation

    Storage Organization:
        - StorageOrganizer: Directory structure management
        - DatasetMetadata, SlideMetadata, TileMetadata: Metadata classes

    Tissue Detection:
        - OtsuTissueDetector: Otsu method tissue detection

    Stain Normalization:
        - MacenkoNormalizer: Stain color normalization

Quick Start:
    >>> from glasscut import Slide, GridTiler
    >>> slide = Slide("path/to/slide.svs")
    >>> tiler = GridTiler(tile_size=(512, 512), overlap=50)
    >>> for tile in tiler.extract(slide, magnification=20):
    ...     tile.save(f"tile_{tile.coords}.png")

For multi-slide datasets:
    >>> from glasscut import DatasetGenerator, DatasetConfig
    >>> config = DatasetConfig(
    ...     dataset_id="my_dataset",
    ...     output_dir="./output",
    ...     tiler="grid",
    ...     num_workers=4
    ... )
    >>> generator = DatasetGenerator(config)
    >>> dataset = generator.process_dataset(["slide1.svs", "slide2.svs"])

See documentation at: https://github.com/yourusername/glasscut
"""

__version__ = "0.2.0"  # Bumped for tiler/storage features
__author__ = "GlassCut Contributors"

# Core slide classes
from .slides import Slide
from .tile import Tile

# Tiling strategies
from .tiler import (
    Tiler,
    GridTiler,
    RandomTiler,
    ConditionalTiler,
)

# Dataset generation
from .dataset import (
    DatasetGenerator,
    DatasetConfig,
)

# Storage
from .storage import (
    StorageOrganizer,
    DatasetMetadata,
    SlideMetadata,
    TileMetadata,
)

# Tissue detection
from .tissue_detectors import (
    OtsuTissueDetector,
)

# Stain normalization
from .stain_normalizers import (
    MacenkoStainNormalizer,
)

__all__ = [
    # Version and metadata
    "__version__",
    # Core slide classes
    "Slide",
    "Tile",
    # Tiling strategies
    "Tiler",
    "GridTiler",
    "RandomTiler",
    "ConditionalTiler",
    # Dataset generation
    "DatasetGenerator",
    "DatasetConfig",
    # Storage
    "StorageOrganizer",
    "DatasetMetadata",
    "SlideMetadata",
    "TileMetadata",
    # Tissue detection
    "OtsuTissueDetector",
    # Stain normalization
    "MacenkoStainNormalizer",
]
