"""RandomTiler: Random sampling-based tile extraction strategy."""

from typing import Generator, List, Tuple, Optional
import numpy as np
from glasscut.slides import Slide
from glasscut.tile import Tile
from .base import Tiler


class RandomTiler(Tiler):
    """Random sampling tile extraction strategy.

    Extracts tiles by randomly sampling coordinates from the slide.
    Useful for creating representative datasets without bias towards
    any particular region of the slide.

    Parameters
    ----------
    num_tiles : int, optional
        Number of tiles to extract. Default is 100.
    tile_size : Tuple[int, int], optional
        Size of tiles (width, height) in pixels. Default is (512, 512).
    seed : Optional[int], optional
        Random seed for reproducibility. If None, uses non-deterministic sampling.
        Default is None.
    min_tissue_ratio : float, optional
        Minimum ratio of tissue required to include a tile (0.0 to 1.0).
        Tiles with less tissue are skipped. Default is 0.0 (include all tiles).
    max_attempts : int, optional
        Maximum number of attempts to find valid tiles. Default is 1000.

    Attributes
    ----------
    num_tiles : int
        Number of tiles to extract
    tile_size : Tuple[int, int]
        Size of tiles to extract
    seed : Optional[int]
        Random seed

    Example:
        >>> from glasscut import Slide, RandomTiler
        >>> slide = Slide("path/to/slide.svs")
        >>> tiler = RandomTiler(num_tiles=50, seed=42)
        >>> for tile in tiler.extract(slide, magnification=20):
        ...     print(f"Tile at {tile.coords}")
    """

    def __init__(
        self,
        num_tiles: int = 100,
        tile_size: Tuple[int, int] = (512, 512),
        seed: Optional[int] = None,
        min_tissue_ratio: float = 0.0,
        max_attempts: int = 1000,
    ):
        """Initialize RandomTiler.

        Parameters
        ----------
        num_tiles : int, optional
            Number of tiles to extract. Default is 100.
        tile_size : Tuple[int, int], optional
            Tile dimensions (width, height). Default is (512, 512).
        seed : Optional[int], optional
            Random seed for reproducibility. Default is None.
        min_tissue_ratio : float, optional
            Minimum tissue ratio (0.0-1.0). Default is 0.0.
        max_attempts : int, optional
            Max attempts to find valid tiles. Default is 1000.

        Raises
        ------
        ValueError
            If num_tiles < 1 or min_tissue_ratio out of range
        """
        if num_tiles < 1:
            raise ValueError(f"num_tiles must be >= 1, got {num_tiles}")

        if not (0.0 <= min_tissue_ratio <= 1.0):
            raise ValueError(
                f"min_tissue_ratio must be between 0.0 and 1.0, got {min_tissue_ratio}"
            )

        self.num_tiles = num_tiles
        self.tile_size = tile_size
        self.seed = seed
        self.min_tissue_ratio = min_tissue_ratio
        self.max_attempts = max_attempts

        # Initialize random state
        self.rng = np.random.RandomState(seed)

    def get_tile_coordinates(
        self,
        slide: Slide,
        magnification: int | float,
        tile_size: Tuple[int, int] = (512, 512),
    ) -> List[Tuple[int, int]]:
        """Generate random tile coordinates.

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
            List of (x, y) coordinates for random sampling
        """
        # Use provided tile_size or instance tile_size
        w_tile, h_tile = tile_size if tile_size != (512, 512) else self.tile_size

        # Get slide dimensions
        slide_width, slide_height = slide.dimensions

        # Make sure tiles fit within slide
        max_x = max(0, slide_width - w_tile)
        max_y = max(0, slide_height - h_tile)

        if max_x < 0 or max_y < 0:
            # Slide is smaller than tile
            return [(0, 0)]

        coordinates = []
        for _ in range(self.num_tiles):
            x = self.rng.randint(0, max_x + 1)
            y = self.rng.randint(0, max_y + 1)
            coordinates.append((x, y))

        return coordinates

    def extract(
        self,
        slide: Slide,
        magnification: int | float,
        tile_size: Tuple[int, int] = (512, 512),
    ) -> Generator[Tile, None, None]:
        """Extract tiles randomly.

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
            Next randomly sampled tile
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
            f"RandomTiler(num_tiles={self.num_tiles}, "
            f"tile_size={self.tile_size}, "
            f"seed={self.seed})"
        )
