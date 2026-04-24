"""Grid-based tiler implementation for GlassCut."""

import math
from typing import Generator

import numpy as np
from tqdm.auto import tqdm

from glasscut.slides import Slide
from glasscut.slides.utils import magnification_to_level
from glasscut.tile import Tile
from glasscut.tissue_detectors import OtsuTissueDetector, TissueDetector

from .base import Tiler, TileTransform


class GridTiler(Tiler):
    """Extract tiles using a regular grid.

    Parameters
    ----------
    tile_size : tuple[int, int], optional
        Default tile size as ``(width, height)`` in pixels at requested magnification.
        Default is ``(512, 512)``.
    magnification : int | float, optional
        Magnification used for extraction and coordinate generation.
        Default is ``20``.
    overlap : int, optional
        Overlap between neighboring tiles in pixels at requested magnification.
        Default is ``0``.
    min_tissue_ratio : float, optional
        Minimum tissue ratio in ``[0.0, 1.0]`` required for preselection.
        Default is ``0.2``.
    tissue_detector : TissueDetector | None, optional
        Tissue detector used for preselection mask. Defaults to OtsuTissueDetector.
    show_progress : bool, optional
        Whether to display a loading bar while extracting tiles. Default is True.
    """

    def __init__(
        self,
        tile_size: tuple[int, int] = (512, 512),
        magnification: int | float = 20,
        overlap: int = 0,
        min_tissue_ratio: float = 0.2,
        tissue_detector: TissueDetector | None = None,
        transforms: list[TileTransform] | None = None,
        show_progress: bool = True,
    ) -> None:
        self._validate_tile_size(tile_size)
        self._validate_overlap(overlap, tile_size)
        self._validate_tissue_ratio(min_tissue_ratio)

        self.tile_size = tile_size
        self.magnification = magnification
        self.overlap = overlap
        self.min_tissue_ratio = min_tissue_ratio
        self.tissue_detector = tissue_detector or OtsuTissueDetector()
        self.transforms: list[TileTransform] = transforms or []
        self.show_progress = show_progress

    def get_tile_boxes(
        self,
        slide: Slide,
    ) -> list[tuple[int, int, int, int]]:
        """Return preselected grid boxes as ``(x, y, width, height)``."""
        candidates = self.get_tile_candidates(slide)
        return [(x, y, w, h) for x, y, w, h, _ in candidates]

    def get_tile_candidates(
        self,
        slide: Slide,
    ) -> list[tuple[int, int, int, int, float]]:
        """Return preselected boxes with tissue ratio as ``(x, y, w, h, ratio)``."""
        self._validate_overlap(self.overlap, self.tile_size)

        level = magnification_to_level(self.magnification, slide.magnifications)
        downsample = 2**level

        tile_w, tile_h = self.tile_size
        step_x = tile_w - self.overlap
        step_y = tile_h - self.overlap
        if step_x <= 0 or step_y <= 0:
            raise ValueError(
                "Grid step must be positive. Reduce overlap or increase tile_size."
            )

        slide_w_lvl0, slide_h_lvl0 = slide.dimensions
        slide_w_lvl = slide_w_lvl0 // downsample
        slide_h_lvl = slide_h_lvl0 // downsample

        tissue_mask = self._slide_tissue_mask(slide)  # bool H×W
        mask_h, mask_w = tissue_mask.shape

        # ── Integral image for O(1) region-mean queries ────────────────────
        # sat[i, j] = sum of tissue_mask[0:i, 0:j] (1-indexed padded form)
        mask_f = tissue_mask.astype(np.float32)
        sat = np.zeros((mask_h + 1, mask_w + 1), dtype=np.float64)
        sat[1:, 1:] = np.cumsum(np.cumsum(mask_f, axis=0), axis=1)

        max_y = max(slide_h_lvl - tile_h, 0)
        max_x = max(slide_w_lvl - tile_w, 0)

        # Precompute scale factors
        sx = mask_w / slide_w_lvl0
        sy = mask_h / slide_h_lvl0
        w0 = tile_w * downsample
        h0 = tile_h * downsample

        boxes_lvl0: list[tuple[int, int, int, int, float]] = []

        for row in range(0, max_y + 1, step_y):
            for col in range(0, max_x + 1, step_x):
                x0 = col * downsample
                y0 = row * downsample

                # Map tile corners into mask coordinates (1-indexed SAT space)
                mx0 = max(0, min(int(x0 * sx), mask_w - 1))
                my0 = max(0, min(int(y0 * sy), mask_h - 1))
                mx1 = max(mx0 + 1, min(int(math.ceil((x0 + w0) * sx)), mask_w))
                my1 = max(my0 + 1, min(int(math.ceil((y0 + h0) * sy)), mask_h))

                # O(1) mean via integral image
                area = (mx1 - mx0) * (my1 - my0)
                total = (
                    sat[my1, mx1]
                    - sat[my0, mx1]
                    - sat[my1, mx0]
                    + sat[my0, mx0]
                )
                tissue_ratio = float(total / area)

                if tissue_ratio >= self.min_tissue_ratio:
                    boxes_lvl0.append((x0, y0, w0, h0, tissue_ratio))

        return boxes_lvl0

    def extract(
        self,
        slide: Slide,
        *,
        n_workers: int = 4,
        batch_size: int = 128,
    ) -> Generator[Tile, None, None]:
        """Yield tiles using batched extraction with internal parallel fallback."""
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        if n_workers < 1:
            raise ValueError("n_workers must be >= 1")

        candidates = self.get_tile_candidates(slide)
        total_tiles = len(candidates)

        batch_iterator = range(0, total_tiles, batch_size)
        if self.show_progress:
            batch_iterator = tqdm(
                batch_iterator,
                total=(total_tiles + batch_size - 1) // batch_size,
                desc="Extracting tile batches",
                unit="batch",
            )

        for start in batch_iterator:
            end = min(start + batch_size, total_tiles)
            batch = candidates[start:end]
            coords_batch = [(x, y) for x, y, _, _, _ in batch]

            try:
                tiles = slide.extract_tiles(
                    coords_list=coords_batch,
                    tile_size=self.tile_size,
                    magnification=self.magnification,
                    num_workers=n_workers,
                )
            except Exception:
                tiles = [
                    slide.extract_tile(
                        coords=coords,
                        tile_size=self.tile_size,
                        magnification=self.magnification,
                    )
                    for coords in coords_batch
                ]

            for idx, tile in enumerate(tiles):
                _, _, _, _, tissue_ratio = batch[idx]
                tile.set_precomputed_tissue_ratio(tissue_ratio)
                yield self._apply_transforms(tile)

    def _apply_transforms(self, tile: Tile) -> Tile:
        """Apply the transform pipeline to *tile* in-place and return it.

        Parameters
        ----------
        tile : Tile
            Tile whose ``.image`` will be passed through each transform in
            ``self.transforms`` in order.

        Returns
        -------
        Tile
            The same tile object with ``.image`` replaced by the transformed image.
        """
        for transform in self.transforms:
            tile.image = transform(tile.image)
        return tile

    def _slide_tissue_mask(self, slide: Slide) -> np.ndarray:
        """Compute a binary tissue mask once from the slide thumbnail."""
        mask = self.tissue_detector.detect(slide.thumbnail)
        mask = np.asarray(mask)
        if mask.dtype != bool:
            mask = mask > 0
        return mask

    @staticmethod
    def _validate_tile_size(tile_size: tuple[int, int]) -> None:
        if tile_size[0] < 1 or tile_size[1] < 1:
            raise ValueError(f"tile_size must contain positive values, got {tile_size}")

    @staticmethod
    def _validate_overlap(overlap: int, tile_size: tuple[int, int]) -> None:
        if overlap < 0:
            raise ValueError(f"overlap must be >= 0, got {overlap}")
        if overlap >= tile_size[0] or overlap >= tile_size[1]:
            raise ValueError(
                "overlap must be smaller than both tile dimensions. "
                f"Got overlap={overlap}, tile_size={tile_size}"
            )

    @staticmethod
    def _validate_tissue_ratio(min_tissue_ratio: float) -> None:
        if not (0.0 <= min_tissue_ratio <= 1.0):
            raise ValueError(
                f"min_tissue_ratio must be in [0.0, 1.0], got {min_tissue_ratio}"
            )

    def __repr__(self) -> str:
        return (
            "GridTiler("
            f"tile_size={self.tile_size}, "
            f"magnification={self.magnification}, "
            f"overlap={self.overlap}, "
            f"min_tissue_ratio={self.min_tissue_ratio}, "
            f"transforms={[t.__name__ if hasattr(t, '__name__') else repr(t) for t in self.transforms]}, "
            f"show_progress={self.show_progress}, "
            f"tissue_detector={self.tissue_detector.__class__.__name__}"
            ")"
        )
