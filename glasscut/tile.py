from pathlib import Path
from typing import cast
import os

import numpy as np
from PIL import Image

from glasscut.utils import lazyproperty
from glasscut.tissue_detectors import TissueDetector, OtsuTissueDetector


class Tile:
    """Provide Tile object representing a tile generated from a Slide object.

    Arguments
    ---------
    image : Image.Image
        Image describing the tile
    coords : tuple[int, int]
        Coordinates (x, y) of the tile at level 0 (upper-left corner)
    magnification : int | float
        Magnification at which the tile was extracted
    tissue_detector : TissueDetector | None, optional
        Strategy for tissue detection. Defaults to OtsuTissueDetector.
    """

    def __init__(
        self,
        image: Image.Image,
        coords: tuple[int, int] | None,
        magnification: int | float | None,
        tissue_detector: TissueDetector | None = None,
    ) -> None:
        """Initialize a Tile.

        Parameters
        ----------
        image : Image.Image
            The tile image in RGB format
        coords : tuple[int, int] | None
            Coordinates (x, y) of the tile at level 0. Can be None for utility tiles.
        magnification : int | float | None
            Magnification at which the tile was extracted. Can be None for utility tiles.
        tissue_detector : TissueDetector | None, optional
            Strategy for detecting tissue. If None, uses OtsuTissueDetector.
        """
        self.image = image
        self.coords = coords
        self.magnification = magnification
        self.tissue_detector = tissue_detector or OtsuTissueDetector()

    def has_enough_tissue(
        self,
        tissue_threshold: float = 0.8,
    ) -> bool:
        """Check if the tile has enough tissue.

        This method checks if the proportion of the detected tissue over the total area
        of the tile is above a specified threshold (by default 80%).

        Parameters
        ----------
        tissue_threshold : float, optional
            Number between 0.0 and 1.0 representing the minimum required percentage of
            tissue over the total area of the image, default is 0.8

        Returns
        -------
        enough_tissue : bool
            Whether the image has enough tissue, i.e. if the proportion of tissue
            over the total area of the image is more than ``tissue_threshold``.
        """
        tissue_ratio = cast(float, np.mean(self.tissue_mask))
        return tissue_ratio > tissue_threshold

    def save(self, path: str | Path) -> None:
        """Save tile at given path.

        The format to use is determined from the filename extension (to be compatible to
        PIL.Image formats). If no extension is provided, the image will be saved in png
        format.

        Parameters
        ---------
        path: str or pathlib.Path
            Path to which the tile is saved.

        """
        ext = os.path.splitext(path)[1]
        if not ext:
            path = f"{path}.png"

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.image.save(path)

    @lazyproperty
    def tissue_mask(self) -> np.ndarray:
        """Binary mask representing the tissue in the tile.

        The mask is computed using the configured tissue detector strategy.

        Returns
        -------
        np.ndarray
            Binary mask representing the tissue in the tile (dtype: uint8, values 0 or 1)
        """
        return self.tissue_detector.detect(self.image)

    @lazyproperty
    def tissue_ratio(self) -> float:
        """Ratio of the tissue area over the total area of the tile.

        Returns
        -------
        float
            Ratio of the tissue area over the total area of the tile
        """
        tissue_ratio = np.count_nonzero(self.tissue_mask) / self.tissue_mask.size
        return tissue_ratio
