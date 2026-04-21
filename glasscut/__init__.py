"""GlassCut: Fast and flexible histopathology image tiling library.

A lightweight, extensible library for extracting tiles from whole slide images (WSI)
with support for multiple tiling strategies, and parallel processing.

Core Components:
    Slide I/O:
        - Slide: WSI reader with backend abstraction
        - Tile: Individual tile image with metadata

    Tiling Strategies:
        - Tiler: Abstract base class for tiling strategies
        - GridTiler: Regular grid tiling with optional overlap

    Tissue Detection:
        - OtsuTissueDetector: Otsu method tissue detection

    Stain Normalization:
        - MacenkoNormalizer: Stain color normalization
        - ReinhardtNormalizer: Fast color transfer-based normalization

See documentation at: https://github.com/CamiloSinningUN/glasscut
"""

__version__ = "0.0.0"
__author__ = "Camilo Jose Sinning Lopez"

# Core slide classes
from .slides import Slide
from .tile import Tile

# Tiling strategies
from .tiler import (
    Tiler,
    GridTiler,
)

# Tissue detection
from .tissue_detectors import (
    OtsuTissueDetector,
)

# Dataset generation
from .dataset import DatasetGenerator, LiveSlideDataset, LiveSlideSample

# Stain normalization
from .stain_normalizers import MacenkoStainNormalizer, ReinhardtStainNormalizer

__all__ = [
    # Version and metadata
    "__version__",
    # Core slide classes
    "Slide",
    "Tile",
    # Tiling strategies
    "Tiler",
    "GridTiler",
    # Tissue detection
    "OtsuTissueDetector",
    # Dataset generation
    "DatasetGenerator",
    "LiveSlideDataset",
    "LiveSlideSample",
    # Stain normalization
    "MacenkoStainNormalizer",
    "ReinhardtStainNormalizer",
]
