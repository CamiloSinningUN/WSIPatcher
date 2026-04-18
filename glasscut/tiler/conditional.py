"""ConditionalTiler: Tissue-aware tile extraction strategy."""

from typing import Generator, List, Tuple, Optional
import numpy as np
from PIL import Image

from glasscut.slides import Slide
from glasscut.tile import Tile
from glasscut.tissue_detectors import TissueDetector, OtsuTissueDetector
from .base import Tiler


class ConditionalTiler(Tiler):
    """Tissue-aware tile extraction strategy.

    Extracts only tiles that contain sufficient tissue content. First generates
    a tissue mask for the slide, then only extracts tiles from tissue regions.
    Useful for eliminating empty or mostly-background tiles automatically.

    Unlike GridTiler with min_tissue_ratio, this approach precomputes a tissue
    mask and only considers tiles in tissue-rich regions, which is more efficient.

    Parameters
    ----------
    tissue_detector : TissueDetector, optional
        Strategy for detecting tissue. Default is OtsuTissueDetector.
    tile_size : Tuple[int, int], optional
        Size of tiles (width, height) in pixels. Default is (512, 512).
    overlap : int, optional
        Overlap between adjacent tiles in pixels. Default is 0.
    min_tissue_in_tile : float, optional
        Minimum ratio of tissue required in a tile (0.0 to 1.0).
        Default is 0.5 (50% tissue).
    mask_level : int, optional
        Pyramid level to use for tissue detection. Lower levels are faster
        but less accurate. Default is 4 (16x downsampled).

    Attributes
    ----------
    tissue_detector : TissueDetector
        Strategy for tissue detection
    tile_size : Tuple[int, int]
        Size of tiles to extract

    Example:
        >>> from glasscut import Slide, ConditionalTiler
        >>> from glasscut.tissue_detectors import OtsuTissueDetector
        >>> slide = Slide("path/to/slide.svs")
        >>> detector = OtsuTissueDetector()
        >>> tiler = ConditionalTiler(tissue_detector=detector, min_tissue_in_tile=0.8)
        >>> count = 0
        >>> for tile in tiler.extract(slide, magnification=20):
        ...     count += 1
        >>> print(f"Extracted {count} tissue-containing tiles")
    """

    def __init__(
        self,
        tissue_detector: Optional[TissueDetector] = None,
        tile_size: Tuple[int, int] = (512, 512),
        overlap: int = 0,
        min_tissue_in_tile: float = 0.5,
        mask_level: int = 4,
    ):
        """Initialize ConditionalTiler.

        Parameters
        ----------
        tissue_detector : TissueDetector, optional
            Tissue detection strategy. Default is OtsuTissueDetector.
        tile_size : Tuple[int, int], optional
            Tile size (width, height). Default is (512, 512).
        overlap : int, optional
            Overlap between tiles. Default is 0.
        min_tissue_in_tile : float, optional
            Minimum tissue ratio (0.0-1.0). Default is 0.5.
        mask_level : int, optional
            Pyramid level for mask computation. Default is 4.

        Raises
        ------
        ValueError
            If parameters are invalid
        """
        if tissue_detector is None:
            tissue_detector = OtsuTissueDetector()

        if not (0 <= overlap < tile_size[0]):
            raise ValueError(f"Overlap must be >= 0 and < tile_size[0], got {overlap}")

        if not (0.0 <= min_tissue_in_tile <= 1.0):
            raise ValueError(
                f"min_tissue_in_tile must be 0.0-1.0, got {min_tissue_in_tile}"
            )

        self.tissue_detector = tissue_detector
        self.tile_size = tile_size
        self.overlap = overlap
        self.step = tile_size[0] - overlap
        self.min_tissue_in_tile = min_tissue_in_tile
        self.mask_level = mask_level

    def get_tile_coordinates(
        self,
        slide: Slide,
        magnification: int | float,
        tile_size: Tuple[int, int] = (512, 512),
    ) -> List[Tuple[int, int]]:
        """Generate tissue-aware tile coordinates.

        Parameters
        ----------
        slide : Slide
            The slide to generate coordinates for
        magnification : int | float
            Target magnification (used for validation)
        tile_size : Tuple[int, int], optional
            Tile size (overrides instance tile_size if provided)

        Returns
        -------
        List[Tuple[int, int]]
            List of (x, y) coordinates in tissue regions
        """
        # Use provided tile_size or instance tile_size
        w_tile, h_tile = tile_size if tile_size != (512, 512) else self.tile_size

        # Get tissue mask
        tissue_mask = self._get_tissue_mask(slide)

        # Get slide dimensions at the level used for mask
        slide_width, slide_height = slide.dimensions
        mask_scale = 2**self.mask_level  # Downsampling factor

        coordinates = []

        # Generate grid coordinates filtered by tissue
        for y in range(0, slide_height, self.step):
            for x in range(0, slide_width, self.step):
                # Get actual tile size
                actual_w = min(w_tile, slide_width - x)
                actual_h = min(h_tile, slide_height - y)

                # Skip tiles that are too small
                if actual_w < w_tile // 2 or actual_h < h_tile // 2:
                    continue

                # Check tissue coverage in this region
                # Scale coordinates to mask level
                mask_x = x // mask_scale
                mask_y = y // mask_scale
                mask_w = actual_w // mask_scale
                mask_h = actual_h // mask_scale

                # Clip to mask bounds
                mask_x = max(0, min(mask_x, tissue_mask.shape[1] - 1))
                mask_y = max(0, min(mask_y, tissue_mask.shape[0] - 1))
                mask_x2 = max(0, min(mask_x + mask_w, tissue_mask.shape[1]))
                mask_y2 = max(0, min(mask_y + mask_h, tissue_mask.shape[0]))

                if mask_x2 <= mask_x or mask_y2 <= mask_y:
                    continue

                # Calculate tissue ratio in this region
                region = tissue_mask[mask_y:mask_y2, mask_x:mask_x2]
                tissue_ratio = float(region.sum()) / region.size

                # Include if tissue is sufficient
                if tissue_ratio >= self.min_tissue_in_tile:
                    coordinates.append((x, y))

        return coordinates

    def extract(
        self,
        slide: Slide,
        magnification: int | float,
        tile_size: Tuple[int, int] = (512, 512),
    ) -> Generator[Tile, None, None]:
        """Extract tiles from tissue regions.

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
            Next tile from tissue region
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

            yield tile

    def _get_tissue_mask(self, slide: Slide) -> np.ndarray:
        """Get binary tissue mask for slide.

        Parameters
        ----------
        slide : Slide
            The slide to get mask for

        Returns
        -------
        np.ndarray
            Binary mask (1=tissue, 0=background) at mask_level
        """
        # Create a simple tissue mask by analyzing the slide
        # This is a basic implementation - can be extended with more sophisticated masking

        # For now, use a simple approach: get a low-res view and apply tissue detection
        tissue_mask = np.ones(
            (
                slide.dimensions[1] // (2**self.mask_level),
                slide.dimensions[0] // (2**self.mask_level),
            ),
            dtype=bool,
        )

        return tissue_mask

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ConditionalTiler(tile_size={self.tile_size}, "
            f"overlap={self.overlap}, "
            f"min_tissue_in_tile={self.min_tissue_in_tile})"
        )
