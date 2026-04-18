from typing import Any, cast
from warnings import warn

import numpy as np
from PIL import Image
from skimage import color as sk_color

from glasscut.tile import Tile
from glasscut.tissue_detectors import OtsuTissueDetector
from glasscut.utils import np_to_pil

from .base import StainNormalizer


class ReinhardtStainNormalizer(StainNormalizer):
    """Stain normalizer using E. Reinhardt et al.'s color transfer method.

    This method normalizes stain appearance by matching the mean and standard
    deviation of each channel in LAB color space between source and target images.
    The normalization is performed only on tissue regions.

    The algorithm is:
    1. Identify tissue using tissue masking
    2. Convert to LAB color space
    3. Compute per-channel mean and std on tissue
    4. Normalize source statistics to match target statistics
    5. Convert back to RGB

    Attributes
    ----------
    target_means : np.ndarray or None
        Target mean values per LAB channel.
    target_stds : np.ndarray or None
        Target standard deviation values per LAB channel.

    Notes
    -----
    This method is computationally fast and suitable for real-time preview
    during stain normalization parameter tuning. However, it may not preserve
    color relationships as well as matrix-based methods for complex stains.

    Examples
    --------
    >>> from PIL import Image
    >>> from glasscut.stain_normalizers import ReinhardtStainNormalizer
    >>> normalizer = ReinhardtStainNormalizer()
    >>> ref_image = Image.open("reference.png")
    >>> normalizer.fit(ref_image)
    >>> test_image = Image.open("test.png")
    >>> normalized_image = normalizer.transform(test_image)
    """

    def __init__(self):
        """Initialize ReinhardtStainNormalizer."""
        self.target_means = None
        self.target_stds = None

    def fit(self, target_image: Image.Image, **kwargs: Any) -> None:
        """Fit stain normalizer using target image.

        Parameters
        ----------
        target_image : Image.Image
            Target image for stain normalization. Can be RGB or RGBA.
        **kwargs
            Additional arguments (unused for Reinhardt method).
        """
        means, stds = self._summary_statistics(target_image)
        self.target_means = means
        self.target_stds = stds

    def transform(self, image: Image.Image, **kwargs: Any) -> Image.Image:
        """Normalize staining of image.

        Parameters
        ----------
        image : Image.Image
            Image to normalize. Can be RGB or RGBA.
        **kwargs
            Additional arguments (unused for Reinhardt method).

        Returns
        -------
        Image.Image
            Image with normalized stain.
        """
        means, stds = self._summary_statistics(image)
        
        img_lab = self.rgb_to_lab(image)

        mask = self._tissue_mask(image)
        mask = np.dstack((mask, mask, mask))

        masked_img_lab = np.ma.masked_array(img_lab, ~mask)

        # Normalize each channel: (x - source_mean) * (target_std / source_std) + target_mean
        
        if self.target_means is None or self.target_stds is None:
            raise ValueError("Normalizer must be fitted with a target image before transformation.")
        
        norm_lab = (
            ((masked_img_lab - means) * (self.target_stds / stds)) + self.target_means
        ).data

        # Restore non-tissue regions with original values
        for i in range(3):
            original = img_lab[:, :, i].copy()
            new = norm_lab[:, :, i].copy()
            original[np.not_equal(~mask[:, :, 0], True)] = 0
            new[~mask[:, :, 0]] = 0
            norm_lab[:, :, i] = new + original

        norm_rgb = self.lab_to_rgb(norm_lab)
        return norm_rgb

    def _summary_statistics(
        self, img_rgb: Image.Image
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute mean and std of each LAB channel on tissue region.

        Parameters
        ----------
        img_rgb : Image.Image
            Input image.

        Returns
        -------
        np.ndarray
            Mean of each channel in LAB space. Shape (3,).
        np.ndarray
            Standard deviation of each channel in LAB space. Shape (3,).

        Notes
        -----
        Statistics are only computed on pixels identified as tissue
        to avoid background artifacts.
        """
        mask = self._tissue_mask(img_rgb)
        mask = np.dstack((mask, mask, mask))

        img_lab = self.rgb_to_lab(img_rgb)
        mean_per_channel = img_lab.mean(axis=(0, 1), where=mask)
        std_per_channel = img_lab.std(axis=(0, 1), where=mask)
        return mean_per_channel, std_per_channel

    @staticmethod
    def _tissue_mask(img_rgb: Image.Image) -> np.ndarray:
        """Compute binary tissue mask for image.

        Parameters
        ----------
        img_rgb : Image.Image
            Input image in RGB or RGBA format.

        Returns
        -------
        np.ndarray
            Binary tissue mask with same spatial dimensions as image.
            1 = tissue, 0 = background.
        """
        tile = Tile(
            img_rgb, coords=None, magnification=None, tissue_detector=OtsuTissueDetector()
        )
        return tile.tissue_mask
    
    # ==== helper implementations ====
    
    @staticmethod
    def rgb_to_lab(img_rgb: Image.Image) -> np.ndarray:
        """Convert RGB image to LAB color space.

        Parameters
        ----------
        img_rgb : Image.Image
            Input image in RGB or RGBA format.

        Returns
        -------
        np.ndarray
            Array representation of the image in LAB space.

        Raises
        ------
        ValueError
            If the input image is grayscale.
        """
        if img_rgb.mode == "L":
            raise ValueError("Input image must be RGB or RGBA, not grayscale (L mode)")

        if img_rgb.mode == "RGBA":
            red, green, blue, _ = img_rgb.split()
            img_rgb = Image.merge("RGB", (red, green, blue))
            warn(
                "Input image is RGBA. Converting to RGB before LAB conversion. "
                "Alpha channel will be discarded."
            )

        img_arr = np.array(img_rgb)
        lab_arr = cast(np.ndarray, sk_color.rgb2lab(img_arr)) # type: ignore
        return lab_arr
    
    @staticmethod
    def lab_to_rgb(img_lab: np.ndarray) -> Image.Image:
        """Convert LAB image to RGB color space.

        Parameters
        ----------
        img_lab : np.ndarray
            Input image in LAB color space.

        Returns
        -------
        Image.Image
            Image in RGB color space.
        """
        rgb_arr = cast(np.ndarray, sk_color.lab2rgb(img_lab)) # type: ignore
        return np_to_pil(rgb_arr)
