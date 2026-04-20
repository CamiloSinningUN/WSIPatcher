from typing import cast

import numpy as np
from PIL import Image
from skimage import filters

from .base import TissueDetector

class OtsuTissueDetector(TissueDetector):
    """Otsu-based tissue detection

    This detector applies Otsu thresholding with optional morphological operations.
    It's fast, robust, and works well for standard histopathology images.
    """

    def detect(self, image: Image.Image) -> np.ndarray:
        """Detect tissue using Otsu thresholding.

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