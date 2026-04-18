"""GridTiler: Regular grid-based tile extraction strategy."""

from typing import Generator, List, Tuple
from glasscut.slides import Slide
from glasscut.tile import Tile
from .base import Tiler


class GridTiler(Tiler):
    """Regular grid tiling strategy.

    Extracts tiles in a regular grid pattern across the slide. Tiles are
    extracted row by row, optionally with overlap. Useful for systematic,
    non-overlapping or slightly overlapping tile extraction.

    Parameters
    ----------
    tile_size : Tuple[int, int], optional
        Size of tiles (width, height) in pixels. Default is (512, 512).
    overlap : int, optional
        Overlap between adjacent tiles in pixels. Must be >= 0 and < tile_size.
        Default is 0 (no overlap).
    min_tissue_ratio : float, optional
        Minimum ratio of tissue required to include a tile (0.0 to 1.0).
        Tiles with less tissue are skipped. Default is 0.0 (include all tiles).
    save_empty : bool, optional
        If True, include tiles with no tissue. If False, skip empty tiles.
        Requires tissue detection if min_tissue_ratio > 0. Default is False.

    Attributes
    ----------
    tile_size : Tuple[int, int]
        Size of tiles to extract
    overlap : int
        Overlap between consecutive tiles
    step : int
        Step size between tile origins (tile_size - overlap)

    Example:
        >>> from glasscut import Slide, GridTiler
        >>> slide = Slide("path/to/slide.svs")
        >>> tiler = GridTiler(tile_size=(512, 512), overlap=50)
        >>> count = 0
        >>> for tile in tiler.extract(slide, magnification=20):
        ...     tile.save(f"outputs/tile_{count:06d}.png")
        ...     count += 1
        >>> print(f"Extracted {count} tiles")
    """

    def __init__(
        self,
        tile_size: Tuple[int, int] = (512, 512),
        overlap: int = 0,
        min_tissue_ratio: float = 0.0,
        save_empty: bool = False,
    ):
        """Initialize GridTiler.

        Parameters
        ----------
        tile_size : Tuple[int, int], optional
            Tile dimensions (width, height). Default is (512, 512).
        overlap : int, optional
            Overlap in pixels. Must satisfy: 0 <= overlap < tile_size[0].
            Default is 0.
        min_tissue_ratio : float, optional
            Minimum tissue ratio to keep tile (0.0-1.0). Default is 0.0.
        save_empty : bool, optional
            Whether to save tiles with no tissue. Default is False.

        Raises
        ------
        ValueError
            If overlap is invalid or min_tissue_ratio is out of range
        """
        if not (0 <= overlap < tile_size[0]):
            raise ValueError(
                f"Overlap must be >= 0 and < tile_size[0] ({tile_size[0]}), got {overlap}"
            )

        if not (0.0 <= min_tissue_ratio <= 1.0):
            raise ValueError(
                f"min_tissue_ratio must be between 0.0 and 1.0, got {min_tissue_ratio}"
            )

        self.tile_size = tile_size
        self.overlap = overlap
        self.step = tile_size[0] - overlap  # Step size between tile origins
        self.min_tissue_ratio = min_tissue_ratio
        self.save_empty = save_empty

    def get_tile_coordinates(
        self,
        slide: Slide,
        magnification: int | float,
        tile_size: Tuple[int, int] = (512, 512),
    ) -> List[Tuple[int, int]]:
        """Generate grid coordinates for tiles.

        Parameters
        ----------
        slide : Slide
            The slide to generate coordinates for
        magnification : int | float
            Target magnification (used for validation, not coordinate computation)
        tile_size : Tuple[int, int], optional
            Tile size (overrides instance tile_size if provided)

        Returns
        -------
        List[Tuple[int, int]]
            List of (x, y) coordinates for all tiles
        """
        # Use provided tile_size or instance tile_size
        w_tile, h_tile = tile_size if tile_size != (512, 512) else self.tile_size

        # Get slide dimensions
        slide_width, slide_height = slide.dimensions

        coordinates = []

        # Generate grid coordinates
        for y in range(0, slide_height, self.step):
            for x in range(0, slide_width, self.step):
                # Get actual tile size (may be smaller at edges)
                actual_w = min(w_tile, slide_width - x)
                actual_h = min(h_tile, slide_height - y)

                # Skip tiles that are too small
                if actual_w < w_tile // 2 or actual_h < h_tile // 2:
                    continue

                coordinates.append((x, y))

        return coordinates

    def extract(
        self,
        slide: Slide,
        magnification: int | float,
        tile_size: Tuple[int, int] = (512, 512),
    ) -> Generator[Tile, None, None]:
        """Extract tiles in grid pattern.

        Parameters
        ----------
        slide : Slide
            The slide to extract tiles from
        magnification : int | float
            Target magnification
        tile_size : Tuple[int, int], optional
            Tile size (overrides instance tile_size if provided)

        Yields
        ------
        Tile
            Next tile in grid order (row by row, left to right)
        """
        # Use provided tile_size or instance tile_size
        w_tile, h_tile = tile_size if tile_size != (512, 512) else self.tile_size

        # Get coordinates
        coords = self.get_tile_coordinates(slide, magnification, tile_size)

        # Extract each tile
        for x, y in coords:
            # Extract tile using Slide's extract_tile method
            tile = slide.extract_tile(
                coords=(x, y),
                tile_size=(w_tile, h_tile),
                magnification=magnification,
            )

            # Filter by tissue if needed
            if self.min_tissue_ratio > 0:
                tissue_ratio = self._get_tissue_ratio(tile)

                if tissue_ratio < self.min_tissue_ratio:
                    if not self.save_empty:
                        continue  # Skip this tile

            yield tile

    @staticmethod
    def _get_tissue_ratio(tile: Tile) -> float:
        """Calculate tissue ratio for a tile.

        Parameters
        ----------
        tile : Tile
            The tile to analyze

        Returns
        -------
        float
            Proportion of tissue (0.0 to 1.0)
        """
        try:
            # Use the tile's built-in tissue detection
            tissue_mask = tile.tissue_mask
            tissue_ratio = float(tissue_mask.sum()) / tissue_mask.size
            return tissue_ratio
        except Exception:
            # If tissue detection fails, assume full tissue
            return 1.0

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"GridTiler(tile_size={self.tile_size}, "
            f"overlap={self.overlap}, "
            f"min_tissue_ratio={self.min_tissue_ratio})"
        )
