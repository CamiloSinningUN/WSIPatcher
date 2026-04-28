"""Grid-based tiler implementation for GlassCut."""

import copy
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Generator

import numpy as np
from tqdm.auto import tqdm

from glasscut.slides import Slide
from glasscut.slides.utils import magnification_to_level
from glasscut.tile import Tile
from glasscut.tissue_detectors import OtsuTissueDetector, TissueDetector
from glasscut.utils import Profiler

from .base import Tiler, TileTransform

_Candidate = tuple[int, int, int, int, float]

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
    debug : bool, optional
        When True, record and print per-phase timing breakdown (tissue mask,
        candidate grid, tile extraction, transforms). Default is False.
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
        debug: bool = False,
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
        self._profiler = Profiler(enabled=debug)

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
    ) -> list[_Candidate]:
        """Return preselected boxes with tissue ratio as ``(x, y, w, h, ratio)``."""
        self._validate_overlap(self.overlap, self.tile_size)

        level = magnification_to_level(self.magnification, slide.magnifications)
        downsample: int = 2**level

        tile_w, tile_h = self.tile_size
        step_x = tile_w - self.overlap
        step_y = tile_h - self.overlap
        if step_x <= 0 or step_y <= 0:
            raise ValueError(
                "Grid step must be positive. Reduce overlap or increase tile_size."
            )

        slide_w_lvl0: int = slide.dimensions[0]
        slide_h_lvl0: int = slide.dimensions[1]
        slide_w_lvl = slide_w_lvl0 // downsample
        slide_h_lvl = slide_h_lvl0 // downsample

        with self._profiler.phase("tissue_mask"):
            tissue_mask = self._slide_tissue_mask(slide)  # bool H×W
        mask_h: int = tissue_mask.shape[0]
        mask_w: int = tissue_mask.shape[1]

        boxes_lvl0: list[_Candidate] = []

        with self._profiler.phase("candidate_grid"):
            # ── Integral image for O(1) region-mean queries ────────────────
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

            cols = np.arange(0, max_x + 1, step_x)
            rows = np.arange(0, max_y + 1, step_y)
            if cols.size == 0 or rows.size == 0:
                return []

            col_grid, row_grid = np.meshgrid(cols, rows)

            x0_all = col_grid * downsample
            y0_all = row_grid * downsample

            mx0 = np.clip((x0_all * sx).astype(np.int64), 0, mask_w - 1)
            my0 = np.clip((y0_all * sy).astype(np.int64), 0, mask_h - 1)
            mx1 = np.clip(
                np.ceil((x0_all + w0) * sx).astype(np.int64), mx0 + 1, mask_w
            )
            my1 = np.clip(
                np.ceil((y0_all + h0) * sy).astype(np.int64), my0 + 1, mask_h
            )

            area = (mx1 - mx0) * (my1 - my0)
            total = (
                sat[my1, mx1]
                - sat[my0, mx1]
                - sat[my1, mx0]
                + sat[my0, mx0]
            )
            tissue_ratios = total / area

            keep = tissue_ratios >= self.min_tissue_ratio
            boxes_lvl0 = [
                (int(x), int(y), int(w0), int(h0), float(r))
                for x, y, r in zip(x0_all[keep], y0_all[keep], tissue_ratios[keep])
            ]

        return boxes_lvl0

    def extract(
        self,
        slide: Slide,
        *,
        n_workers: int = 4,
        batch_size: int = 128,
    ) -> Generator[Tile, None, None]:
        """Yield tiles using batched parallel extraction.

        Each worker thread extracts a single tile from the slide and immediately
        applies the full transform pipeline.
        """
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

        def _extract_one(item: _Candidate) -> Tile:
            return self._extract_and_transform(slide, item)

        for start in batch_iterator:
            end = min(start + batch_size, total_tiles)
            batch: list[_Candidate] = candidates[start:end]

            with ThreadPoolExecutor(max_workers=n_workers) as executor:
                tiles = list(executor.map(_extract_one, batch))

            yield from tiles

    def _extract_and_transform(
        self,
        slide: Slide,
        candidate: _Candidate,
    ) -> Tile:
        """Extract a single tile and apply the transform pipeline.

        This is the worker function executed by each thread in :meth:`extract`.
        By fusing extraction and transforms in one call, I/O wait and CPU work
        overlap across tiles within the same batch.

        Parameters
        ----------
        slide : Slide
            The slide to read from.
        candidate : tuple[int, int, int, int, float]
            A single entry from :meth:`get_tile_candidates` in the form
            ``(x, y, w, h, tissue_ratio)`` in level-0 coordinates.

        Returns
        -------
        Tile
            Extracted and transformed tile.
        """
        x, y, _, _, tissue_ratio = candidate
        with self._profiler.phase("extract_tile"):
            tile = slide.extract_tile(
                coords=(x, y),
                tile_size=self.tile_size,
                magnification=self.magnification,
            )
        tile.set_precomputed_tissue_ratio(tissue_ratio)
        with self._profiler.phase("apply_transforms"):
            return self._apply_transforms(tile)

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

    def __deepcopy__(self, memo: dict[int, Any]) -> "GridTiler":
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k == "_profiler":
                object.__setattr__(result, k, v)
            else:
                object.__setattr__(result, k, copy.deepcopy(v, memo))
        return result

    def print_profile(self) -> None:
        self._profiler.print_summary()

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
