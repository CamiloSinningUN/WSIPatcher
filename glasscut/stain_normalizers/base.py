# encoding: utf-8

"""Base classes for stain normalization.

This module provides abstract base classes and mixins for implementing
stain normalization strategies in histopathology image processing.
"""

from abc import ABC, abstractmethod
from typing import Any
from warnings import warn

import numpy as np
from PIL import Image

from glasscut.utils import np_to_pil


class StainNormalizer(ABC):
    """Abstract base class for stain normalization strategies.

    Stain normalization is a crucial preprocessing step in digital pathology
    to reduce color variations caused by staining protocols and imaging conditions.

    Subclasses must implement the `fit` and `transform` methods.
    """

    @abstractmethod
    def fit(self, target_image: Image.Image, **kwargs: Any) -> None:
        """Fit the normalizer to a target image.

        Parameters
        ----------
        target_image : Image.Image
            Target reference image for normalization.
        **kwargs
            Additional arguments specific to the normalization method.
        """
        pass

    @abstractmethod
    def transform(self, image: Image.Image, **kwargs: Any) -> Image.Image:
        """Apply stain normalization to an image.

        Parameters
        ----------
        image : Image.Image
            Image to normalize.
        **kwargs
            Additional arguments specific to the normalization method.

        Returns
        -------
        Image.Image
            Normalized image.
        """
        pass


class TransformerStainMatrixMixin:
    """Mixin implementing fit/transform for matrix-based stain normalizers.

    This mixin assumes the subclass implements a `stain_matrix` method that
    returns a 3×3 stain matrix.
    """

    def fit(self, target_image: Image.Image, **kwargs: Any) -> None:
        """Fit stain normalizer using target image.

        Parameters
        ----------
        target_image : Image.Image
            Target image for stain normalization. Can be RGB or RGBA.
        **kwargs
            Additional arguments passed to stain_matrix method.
            Commonly includes background_intensity (int, default 240).
        """
        background_intensity = kwargs.get("background_intensity", 240)
        self.stain_matrix_target = self.stain_matrix(
            target_image, background_intensity=background_intensity, **kwargs
        )

        target_concentrations = self._find_concentrations(
            target_image, self.stain_matrix_target, background_intensity
        )

        self.max_concentrations_target = np.percentile(
            target_concentrations, 99, axis=1
        )

    def transform(self, image: Image.Image, **kwargs: Any) -> Image.Image:
        """Normalize staining of image.

        Parameters
        ----------
        image : Image.Image
            Image to normalize. Can be RGB or RGBA.
        **kwargs
            Additional arguments passed to stain_matrix method.
            Commonly includes background_intensity (int, default 240).

        Returns
        -------
        Image.Image
            Image with normalized stain.
        """
        background_intensity = kwargs.get("background_intensity", 240)
        stain_matrix_source = self.stain_matrix(
            image, background_intensity=background_intensity, **kwargs
        )

        source_concentrations = self._find_concentrations(
            image, stain_matrix_source, background_intensity
        )

        max_concentrations_source = np.percentile(source_concentrations, 99, axis=1)
        max_concentrations_source = np.divide(
            max_concentrations_source, self.max_concentrations_target
        )
        conc_tmp = np.divide(
            source_concentrations, max_concentrations_source[:, np.newaxis]
        )

        img_norm = np.multiply(
            background_intensity, np.exp(-self.stain_matrix_target.dot(conc_tmp))
        )
        img_norm = np.clip(img_norm, a_min=None, a_max=255)
        img_norm = np.reshape(img_norm.T, (*image.size[::-1], 3))
        return np_to_pil(img_norm)

    @staticmethod
    def _find_concentrations(
        img_rgb: Image.Image,
        stain_matrix: np.ndarray,
        background_intensity: int = 240,
    ) -> np.ndarray:
        """Return concentrations of individual stains in image.

        Parameters
        ----------
        img_rgb : Image.Image
            Input image.
        stain_matrix : np.ndarray
            Stain matrix of image. Shape (3, 3).
        background_intensity : int, optional
            Background transmitted light intensity. Default is 240.

        Returns
        -------
        np.ndarray
            Concentrations of individual stains. Shape (3, n_pixels).

        Notes
        -----
        Uses least squares to solve the underdetermined system:
        stain_matrix @ concentrations = optical_density
        """

        if img_rgb.mode == "RGBA":
            red, green, blue, _ = img_rgb.split()
            img_rgb = Image.merge("RGB", (red, green, blue))
            warn(
                "Input image is RGBA. Converting to RGB before OD conversion. "
                "Alpha channel will be discarded."
            )

        img_arr = np.array(img_rgb)
        od = -np.log((img_arr.astype(np.float64) + 1) / background_intensity)

        # rows correspond to channels (RGB), columns to OD values
        od = np.reshape(od, (-1, 3)).T

        # determine concentrations of the individual stains
        # Precompute 3x3 pseudo-inverse once → fast matmul per pixel
        stain_matrix_pinv = np.linalg.pinv(stain_matrix)
        return stain_matrix_pinv @ od

    @abstractmethod
    def stain_matrix(
        self,
        img_rgb: Image.Image,
        background_intensity: int = 240,
        **kwargs: Any,
    ) -> np.ndarray:
        """Calculate stain matrix for image.

        Parameters
        ----------
        img_rgb : Image.Image
            Input image.
        background_intensity : int, optional
            Background transmitted light intensity. Default is 240.
        **kwargs
            Additional arguments specific to the normalization method.

        Returns
        -------
        np.ndarray
            Stain matrix of image. Shape (3, 3).
        """
        pass
