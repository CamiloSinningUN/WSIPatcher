"""Storage module for dataset organization.

This module handles the creation and management of dataset directory structures,
metadata, and file organization for processed WSI data.

Main Classes:
    - StorageOrganizer: Manages dataset directory structure and file paths
    - DatasetMetadata: Top-level dataset metadata
    - SlideMetadata: Per-slide metadata
    - TileMetadata: Per-tile metadata

Example:
    >>> from glasscut.storage import StorageOrganizer, DatasetMetadata
    >>> organizer = StorageOrganizer("./output")
    >>> dataset_dir = organizer.init_dataset("my_dataset")
    >>> dirs = organizer.init_slide("my_dataset", "Slide_001")
    >>> tile_path = organizer.get_tile_path("my_dataset", "Slide_001", "tile_000000")
"""

from .structures import (
    TileMetadata,
    SlideMetadata,
    DatasetMetadata,
    dataclass_to_dict,
)
from .manager import StorageOrganizer

__all__ = [
    "TileMetadata",
    "SlideMetadata",
    "DatasetMetadata",
    "StorageOrganizer",
    "dataclass_to_dict",
]
