from typing import cast

import numpy as np
from PIL import Image
from skimage import filters

from .base import TissueDetector

class OtsuTissueDetector(TissueDetector):
    """Otsu-based tissue detection

    This detector applies Otsu thresholding with optional morphological operations.
    It's fast, robust, and works well for standard histopathology images.

    Parameters
    ----------
    apply_prefilter : bool, optional
        If True, attempts to remove marker artifacts before thresholding, by default False
    apply_morphology : bool, optional
        If True, applies morphological operations (dilation, hole filling), by default False
    morphology_disk_size : int, optional
        Size of the disk for morphological operations, by default 2
    """

    def detect(self, image: Image.Image) -> np.ndarray:
        """Detect tissue using Otsu thresholding.

        Pipeline:
        1. Convert RGB to grayscale
        2. (Optional) Apply pre-filtering to remove markers
        3. Apply Otsu thresholding
        4. (Optional) Apply morphological operations

        Parameters
        ----------
        image : Image.Image
            Input RGB image

        Returns
        -------
        np.ndarray
            Binary mask (dtype: uint8 with values 0 or 1)
        """
        # Convert to numpy and grayscale
        img_array = np.array(image.convert("L")).astype(np.uint8)

        # Apply Otsu thresholding
        threshold = cast(float, filters.threshold_otsu(img_array)) # type: ignore
        tissue_mask: np.ndarray = (img_array < threshold).astype(np.uint8)

        return tissue_mask