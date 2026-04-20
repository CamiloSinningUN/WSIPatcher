"""Storage module for organizing generated datasets and metadata."""

from .manager import StorageOrganizer
from .structures import DatasetMetadata, SlideMetadata, TileMetadata, dataclass_to_dict

__all__ = [
    "DatasetMetadata",
    "SlideMetadata",
    "StorageOrganizer",
    "TileMetadata",
    "dataclass_to_dict",
]
