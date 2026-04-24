"""Live in-memory slide-level dataset utilities.

This module provides a dataset-like interface where each item corresponds to one
slide and contains all extracted tiles for that slide, without writing artifacts
to disk.
"""

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from glasscut.slides import Slide
from glasscut.tile import Tile
from glasscut.tiler import Tiler


@dataclass
class LiveSlideSample:
    """Container for one in-memory slide sample.

    Attributes
    ----------
    slide_id : str
        Slide identifier in ``slide_XXX`` format.
    slide_name : str
        Slide basename without extension.
    slide_path : str
        Absolute slide path.
    dimensions : tuple[int, int]
        Level-0 dimensions as ``(width, height)``.
    mpp : float
        Microns-per-pixel at level 0.
    magnifications : list[float]
        Available magnification values.
    tiles : list[Tile]
        All extracted tiles for this slide, in extraction order.
    """

    slide_id: str
    slide_name: str
    slide_path: str
    dimensions: tuple[int, int]
    mpp: float
    magnifications: list[float]
    tiles: list[Tile]


class LiveSlideDataset:
    """Slide-level in-memory dataset.

    Each ``__getitem__`` call opens one slide, extracts all tiles in memory using
    the configured tiler, and returns a :class:`LiveSlideSample`.
    """

    def __init__(
        self,
        slide_paths: Sequence[str | Path],
        *,
        tiler: Tiler,
        n_workers: int = 4,
        batch_size: int = 128,
        use_cucim: bool = True,
    ) -> None:
        if not slide_paths:
            raise ValueError("slide_paths must not be empty")
        if n_workers < 1:
            raise ValueError("n_workers must be >= 1")
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")

        self.slide_paths = [str(Path(path).resolve()) for path in slide_paths]
        self.tiler = tiler
        self.n_workers = n_workers
        self.batch_size = batch_size
        self.use_cucim = use_cucim

    def __len__(self) -> int:
        """Return number of slides in the live dataset."""
        return len(self.slide_paths)

    def __getitem__(self, index: int) -> LiveSlideSample:
        """Return all extracted tiles for one slide.

        Parameters
        ----------
        index : int
            Slide index in the dataset.
        """
        if index < 0 or index >= len(self.slide_paths):
            raise IndexError(f"index out of range: {index}")

        slide_path = self.slide_paths[index]
        slide_id = f"slide_{index:03d}"
        tiler = self._build_tiler()

        with Slide(slide_path, use_cucim=self.use_cucim) as slide:
            tiles: list[Tile] = list(
                tiler.extract(
                    slide,
                    n_workers=self.n_workers,
                    batch_size=self.batch_size,
                )
            )

            return LiveSlideSample(
                slide_id=slide_id,
                slide_name=slide.name,
                slide_path=slide_path,
                dimensions=slide.dimensions,
                mpp=slide.mpp,
                magnifications=[float(mag) for mag in slide.magnifications],
                tiles=tiles,
            )

    def _build_tiler(self) -> Tiler:
        """Build an independent tiler instance per slide access."""
        return copy.deepcopy(self.tiler)
