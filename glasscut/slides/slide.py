"""Main Slide class for WSI manipulation."""

import math
import ntpath
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from types import TracebackType

import numpy as np
import PIL.Image

from .backends import CuCimBackend, OpenSlideBackend, SlideBackend
from .utils import build_magnification_mapping, magnification_to_level
from glasscut.exceptions import TileSizeOrCoordinatesError
from glasscut.tile import Tile
from glasscut.utils import lazyproperty

class Slide:
    """Represents a whole slide image with magnification-based access.

    This class provides an interface to access whole slide images.
    It abstracts away the backend (OpenSlide or cuCim).

    Parameters
    ----------
    path : Union[str, pathlib.Path]
        Path to the slide file
    use_cucim : bool, optional
        Whether to try using cuCim GPU backend. If False or cuCim is not
        available, falls back to OpenSlide. Default is True.
    """

    def __init__(self, path: str | Path, use_cucim: bool = True) -> None:
        self._path = str(path) if isinstance(path, Path) else path
        self._backend: SlideBackend | None = None

        # Try to initialize backend
        if use_cucim:
            try:
                self._backend = CuCimBackend()
                self._backend.open(self._path)
            except Exception:
                # Fallback to OpenSlide
                self._backend = OpenSlideBackend()
                self._backend.open(self._path)
        else:
            self._backend = OpenSlideBackend()
            self._backend.open(self._path)

    def __repr__(self) -> str:
        return (
            f"Slide(path={self._path}, "
            f"magnifications={self.magnifications}, "
            f"dimensions={self.dimensions})"
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the slide and free resources."""
        if self._backend is not None:
            self._backend.close()

    # ===== Public Properties =====

    @lazyproperty
    def name(self) -> str:
        """Slide name without extension.

        Returns
        -------
        str
            Slide filename without extension
        """
        bname = ntpath.basename(self._path)
        return bname[: bname.rfind(".")]

    @lazyproperty
    def dimensions(self) -> tuple[int, int]:
        """Slide dimensions (width, height) at base magnification.

        Returns
        -------
        tuple[int, int]
            (width, height) in pixels at highest magnification (typically 40x)
        """

        if self._backend is None:
            raise RuntimeError("Slide not opened")

        return self._backend.dimensions

    @lazyproperty
    def magnifications(self) -> list[float]:
        """Available magnifications for this slide.

        These are calculated from the actual slide's base magnification
        (objective power) and the number of pyramid levels.

        Returns
        -------
        list[float]
            List of magnifications in descending order (e.g., [40.0, 20.0, 10.0, 5.0])
        """

        if self._backend is None:
            raise RuntimeError("Slide not opened")

        base_mag = self._backend.base_magnification
        return build_magnification_mapping(base_mag, self._backend.num_levels)

    @lazyproperty
    def mpp(self) -> float:
        """Microns per pixel at base magnification.

        Returns
        -------
        float
            Microns per pixel

        Raises
        ------
        SlidelazypropertyError
            If MPP cannot be determined from slide metadata
        """

        if self._backend is None:
            raise RuntimeError("Slide not opened")

        return self._backend.mpp

    @lazyproperty
    def properties(self) -> dict[str, str]:
        """Slide metadata properties.

        Returns
        -------
        dict
            Dictionary of all slide properties
        """
        if self._backend is None:
            raise RuntimeError("Slide not opened")

        return self._backend.properties

    @lazyproperty
    def thumbnail(self) -> PIL.Image.Image:
        """Get thumbnail of the slide.

        The thumbnail size is automatically calculated based on slide dimensions.

        Returns
        -------
        PIL.Image.Image
            Thumbnail image in RGB format
        """

        if self._backend is None:
            raise RuntimeError("Slide not opened")

        size = self._compute_thumbnail_size()
        return self._backend.get_thumbnail(size)

    # ===== Public Methods =====

    def extract_tile(
        self,
        coords: tuple[int, int],
        tile_size: tuple[int, int],
        magnification: int | float,
    ) -> Tile:
        """Extract a single tile from the slide at specified magnification.

        The requested magnification must be available on this slide.
        If the exact magnification is not available, a MagnificationError is raised.

        Parameters
        ----------
        coords : tuple[int, int]
            Coordinates (x, y) at level 0 (upper-left corner of the tile)
        tile_size : tuple[int, int]
            Desired tile size (width, height) in pixels
        magnification : int | float
            Target magnification (e.g., 40, 20, 10, 5)

        Returns
        -------
        Tile
            Extracted tile object

        Raises
        ------
        MagnificationError
            If the requested magnification is not available on this slide
        TileSizeOrCoordinatesError
            If the coordinates or tile size are invalid
        """
        # Get available magnifications
        available_mags = self.magnifications

        # Validate magnification - this will raise MagnificationError if not available
        level = magnification_to_level(magnification, available_mags)

        # Validate coordinates in level-0 space using the true level footprint.
        downsample = 2**level
        tile_size_lvl0 = (tile_size[0] * downsample, tile_size[1] * downsample)
        if not self._has_valid_coords(coords, tile_size_lvl0):
            raise TileSizeOrCoordinatesError(
                f"Coordinates {coords} with tile_size {tile_size} at magnification "
                f"{magnification}x are invalid for slide dimensions {self.dimensions}. "
                f"Level-0 footprint is {tile_size_lvl0}."
            )

        if self._backend is None:
            raise RuntimeError("Slide not opened")

        # Read region from backend
        image = self._backend.read_region(
            location=coords,
            level=level,
            size=tile_size,
        )

        return Tile(image, coords, magnification)

    def _extract_tile_direct(
        self,
        coords: tuple[int, int],
        tile_size: tuple[int, int],
        level: int,
        magnification: int | float,
    ) -> Tile:
        """Extract a tile bypassing per-call validation (internal hot path).

        This is used by :meth:`extract_tiles` where level, magnification and
        coordinate validity have already been confirmed for the entire batch.
        """
        image = self._backend.read_region(  # type: ignore[union-attr]
            location=coords,
            level=level,
            size=tile_size,
        )
        return Tile(image, coords, magnification)

    def extract_tiles(
        self,
        coords_list: list[tuple[int, int]],
        tile_size: tuple[int, int],
        magnification: int | float,
        num_workers: int = 4,
    ) -> list[Tile]:
        """Extract multiple tiles in parallel.

        The requested magnification must be available on this slide.
        If the exact magnification is not available, a MagnificationError is raised.

        Parameters
        ----------
        coords_list : list[tuple[int, int]]
            List of (x, y) coordinates for each tile
        tile_size : tuple[int, int]
            Tile size (width, height) in pixels
        magnification : int | float
            Target magnification
        num_workers : int, optional
            Number of parallel workers. Default is 4.

        Returns
        -------
        List[Tile]
            List of extracted tiles in the same order as coords_list

        Raises
        ------
        MagnificationError
            If magnification is not available on this slide
        """
        # Resolve level once for the whole batch – avoids 128× repeated lookups
        # inside the thread pool.
        level = magnification_to_level(magnification, self.magnifications)

        if self._backend is None:
            raise RuntimeError("Slide not opened")

        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            tiles = list(
                executor.map(
                    lambda coords: self._extract_tile_direct(
                        coords, tile_size, level, magnification
                    ),
                    coords_list,
                )
            )

        return tiles


    # ===== Private Helper Methods =====

    def _has_valid_coords(self, coords: tuple[int, int], tile_size: tuple[int, int]) -> bool:
        """Check if coordinates are valid for the slide.

        Parameters
        ----------
        coords : tuple[int, int]
            (x, y) coordinates (upper-left corner of tile)
        tile_size : tuple[int, int]
            (width, height) of the tile

        Returns
        -------
        bool
            True if coordinates are valid, False otherwise
        """
        x, y = coords
        w, h = tile_size
        slide_w, slide_h = self.dimensions
        
        return (
            0 <= x < slide_w
            and 0 <= y < slide_h
            and x + w <= slide_w
            and y + h <= slide_h
        )

    def _compute_thumbnail_size(self) -> tuple[int, int]:
        """Compute thumbnail size proportionally to slide dimensions.

        Returns
        -------
        tuple[int, int]
            Thumbnail size (width, height)
        """
        width, height = self.dimensions
        return (
            int(width / np.power(10, math.ceil(math.log10(width)) - 3)),
            int(height / np.power(10, math.ceil(math.log10(height)) - 3)),
        )
