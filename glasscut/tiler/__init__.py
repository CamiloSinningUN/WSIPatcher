"""Tiler module for tile extraction strategies.

Main Classes:
    - Tiler: Abstract base class for all tiling strategies
    - GridTiler: Regular grid tiling
    - RandomTiler: Random sampling based tiling

Example:
    >>> from glasscut import Slide, GridTiler
    >>> slide = Slide("path/to/slide.svs")
    >>> tiler = GridTiler(tile_size=512, overlap=50)
    >>> for tile in tiler.extract(slide, magnification=20):
    ...     print(f"Tile at {tile.coords}: size {tile.image.size}")
"""

from .base import Tiler, TileTransform
from .grid import GridTiler

__all__ = [
    "Tiler",
    "TileTransform",
    "GridTiler",
]