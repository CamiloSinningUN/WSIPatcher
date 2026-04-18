"""Storage data structures using dataclasses.

Defines the metadata models used throughout the storage system,
matching PathoPatcher's JSON format while maintaining GlassCut's cleanliness.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional
from datetime import datetime


@dataclass
class TileMetadata:
    """Metadata for a single extracted tile.

    Stores information about a tile including its position, size, and quality metrics.
    This is saved per-tile in the patch_metadata.json file.

    Attributes
    ----------
    tile_id : str
        Unique identifier for the tile (e.g., "tile_0000000")
    x : int
        X coordinate of tile's top-left corner in Level 0 coordinates
    y : int
        Y coordinate of tile's top-left corner in Level 0 coordinates
    width : int
        Tile width in pixels
    height : int
        Tile height in pixels
    level : int
        Pyramid level from which tile was extracted (usually 0)
    magnification : float
        Magnification level used for extraction
    tissue_ratio : float
        Ratio of tissue detected in tile (0.0 to 1.0)
    file_path : str
        Relative path to tile image file within dataset structure
    """

    tile_id: str
    x: int
    y: int
    width: int
    height: int
    level: int
    magnification: float
    tissue_ratio: float
    file_path: str


@dataclass
class SlideMetadata:
    """Metadata for a single processed slide.

    Stores information about a slide including extracted tiles and slide properties.
    This is saved in {slide_id}/slide_metadata.json.

    Attributes
    ----------
    slide_id : str
        Unique identifier for the slide (e.g., "Slide_001")
    slide_name : str
        Human-readable slide name (e.g., original filename without extension)
    slide_path : str
        Path to original WSI file
    total_tiles : int
        Total number of tiles extracted from this slide
    dimensions : Tuple[int, int]
        Slide dimensions (width, height) at base magnification
    mpp : float
        Microns per pixel for the slide
    magnification : float
        Magnification used for extraction
    tile_size : Tuple[int, int]
        Size of extracted tiles (width, height)
    tiler_name : str
        Name of tiler strategy used (e.g., "GridTiler")
    timestamp : str
        ISO format timestamp of when slide was processed
    tiles : List[TileMetadata] = field(default_factory=list)
        Metadata for each extracted tile
    """

    slide_id: str
    slide_name: str
    slide_path: str
    total_tiles: int
    dimensions: Tuple[int, int]
    mpp: float
    magnification: float
    tile_size: Tuple[int, int]
    tiler_name: str
    timestamp: str
    tiles: List[TileMetadata] = field(default_factory=list)


@dataclass
class DatasetMetadata:
    """Metadata for complete dataset.

    Top-level metadata storing information about the entire processed dataset.
    Saved as metadata.json in the dataset root directory.

    Attributes
    ----------
    dataset_id : str
        Unique identifier for the dataset
    created_at : str
        ISO format timestamp of dataset creation
    total_slides : int
        Total number of slides processed
    total_tiles : int
        Total number of tiles across all slides
    config : Dict
        Configuration used for processing (preserved for reproducibility)
    slides : List[SlideMetadata] = field(default_factory=list)
        Metadata for each processed slide
    """

    dataset_id: str
    created_at: str
    total_slides: int
    total_tiles: int
    config: Dict = field(default_factory=dict)
    slides: List[SlideMetadata] = field(default_factory=list)


def dataclass_to_dict(obj) -> dict:
    """Convert dataclass to dictionary recursively.

    Handles nested dataclasses and converts them to dictionaries.
    """
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name)
            if isinstance(value, (list, tuple)):
                result[field_name] = [
                    dataclass_to_dict(v) if hasattr(v, "__dataclass_fields__") else v
                    for v in value
                ]
            elif hasattr(value, "__dataclass_fields__"):
                result[field_name] = dataclass_to_dict(value)
            else:
                result[field_name] = value
        return result
    else:
        return obj
