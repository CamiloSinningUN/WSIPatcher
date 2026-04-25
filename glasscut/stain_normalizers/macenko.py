import warnings
from warnings import warn
from typing import Any, List
import logging

import numpy as np
from PIL import Image

from glasscut.tile import Tile
from glasscut.tissue_detectors import OtsuTissueDetector

from .base import StainNormalizer, TransformerStainMatrixMixin


class MacenkoStainNormalizer(TransformerStainMatrixMixin, StainNormalizer):
    """Stain normalizer using M. Macenko et al.'s method.

    This method performs unsupervised color deconvolution to identify stain vectors,
    then normalizes stain concentrations to a reference image. It works well for
    standard H&E stained histopathology images.

    The algorithm:
    1. Converts image to optical density (OD) space
    2. Performs principal component analysis on OD values
    3. Identifies stain vectors using angular decomposition
    4. Normalizes stain concentrations to match reference

    Attributes
    ----------
    stain_color_map : dict
        Mapping of stain names to their normalized OD vectors.

    Examples
    --------
    >>> from PIL import Image
    >>> from glasscut.stain_normalizers import MacenkoStainNormalizer
    >>> normalizer = MacenkoStainNormalizer()
    >>> ref_image = Image.open("reference.png")
    >>> normalizer.fit(ref_image)
    >>> test_image = Image.open("test.png")
    >>> normalized_image = normalizer.transform(test_image)
    """

    # Normalized OD vectors for standard stains
    stain_color_map = {
        "hematoxylin": np.array([0.65, 0.70, 0.29]),
        "eosin": np.array([0.07, 0.99, 0.11]),
        "dab": np.array([0.27, 0.57, 0.78]),
        "null": np.array([0.0, 0.0, 0.0]),
    }

    _logger = logging.getLogger(__name__)

    def __init__(self):
        """Initialize MacenkoStainNormalizer."""
        warnings.warn(
            "MacenkoStainNormalizer is experimental and may produce errors or "
            "unexpected results on certain images. Use with caution.",
            UserWarning,
            stacklevel=2,
        )
        super().__init__()
        self.stain_matrix_target = None
        self.max_concentrations_target = None

    def stain_matrix(
        self,
        img_rgb: Image.Image,
        background_intensity: int = 240,
        **kwargs: Any,
    ) -> np.ndarray:
        """Estimate stain matrix using Macenko's method.

        Parameters
        ----------
        img_rgb : PIL.Image.Image
            Input image in RGB or RGBA format.
        background_intensity : int, optional
            Background transmitted light intensity. Default is 240.
        **kwargs
            Additional keyword arguments.

        Other Parameters
        ----------------
        alpha : int, optional
            Minimum angular percentile. Default is 1.
        beta : float, optional
            Threshold for OD magnitude filtering. Default is 0.15.
        stains : list of str, optional
            List of stain names in order. Default is ``["hematoxylin", "eosin"]``.

        Returns
        -------
        np.ndarray
            Calculated 3×3 stain matrix with stain vectors as columns.

        Raises
        ------
        ValueError
            If stains is not a 2-element list.
        ValueError
            If image is not RGB or RGBA.
        """
        alpha = kwargs.get("alpha", 1)
        beta = kwargs.get("beta", 0.15)
        stains = kwargs.get("stains", None)

        if stains is not None and len(stains) != 2:
            raise ValueError("Only 2-stain lists are currently supported.")

        stains = ["hematoxylin", "eosin"] if stains is None else stains

        if img_rgb.mode not in ["RGB", "RGBA"]:
            raise ValueError("Input image must be RGB or RGBA")

        # Convert to OD and apply tissue masking
        tile = Tile(img_rgb, None, None, tissue_detector=OtsuTissueDetector())
        tissue_mask = tile.tissue_mask.astype(bool)

        if img_rgb.mode == "RGBA":
            red, green, blue, _ = img_rgb.split()
            img_rgb = Image.merge("RGB", (red, green, blue))
            warn(
                "Input image is RGBA. Converting to RGB before OD conversion. "
                "Alpha channel will be discarded.",
                stacklevel=2,
            )

        img_arr = np.array(img_rgb)
        od = -np.log((img_arr.astype(np.float64) + 1) / background_intensity)
        od = od[tissue_mask].reshape(-1, 3)

        if od.size == 0:
            self._logger.warning(
                "Macenko fallback: no tissue pixels available for stain matrix estimation."
            )
            return self._default_stain_matrix(stains)

        # Remove data with OD intensity less than β
        od_hat = od[~np.any(od < beta, axis=1)]
        if od_hat.shape[0] < 3:
            self._logger.warning(
                "Macenko fallback: insufficient OD samples after beta filtering (%d).",
                od_hat.shape[0],
            )
            return self._default_stain_matrix(stains)

        # Calculate principal components and project input
        try:
            V = np.linalg.eigh(np.cov(od_hat, rowvar=False))[1][:, -2:]
        except np.linalg.LinAlgError:
            self._logger.warning(
                "Macenko fallback: covariance eigendecomposition failed.",
                exc_info=True,
            )
            return self._default_stain_matrix(stains)

        if not np.isfinite(V).all():
            self._logger.warning(
                "Macenko fallback: non-finite principal components encountered."
            )
            return self._default_stain_matrix(stains)

        proj = np.dot(od_hat, V)

        # Angular coordinates with respect to principal orthogonal eigenvectors
        phi = np.arctan2(proj[:, 1], proj[:, 0])

        # Min and max angles
        min_phi = np.percentile(phi, alpha)
        max_phi = np.percentile(phi, 100 - alpha)

        # The two principal stains
        min_v = V.dot(np.array([(np.cos(min_phi), np.sin(min_phi))]).T)
        max_v = V.dot(np.array([(np.cos(max_phi), np.sin(max_phi))]).T)

        # Fill out empty columns in stain matrix and reorder
        _arr = np.hstack([min_v, max_v])
        if not np.isfinite(_arr).all():
            self._logger.warning(
                "Macenko fallback: non-finite stain vectors encountered."
            )
            return self._default_stain_matrix(stains)

        unordered_stain_matrix = self._complement_stain_matrix(
            _arr / np.linalg.norm(_arr, axis=0)
        )
        ordered_stain_matrix = self._reorder_stains(
            unordered_stain_matrix, stains=stains
        )
        return ordered_stain_matrix

    @classmethod
    def _default_stain_matrix(cls, stains: List[str]) -> np.ndarray:
        """Return a robust fallback 3x3 stain matrix for H&E-like normalization."""
        first = np.array(cls.stain_color_map[stains[0]], dtype=np.float64)
        second = np.array(cls.stain_color_map[stains[1]], dtype=np.float64)

        first = first / np.linalg.norm(first)
        second = second / np.linalg.norm(second)
        third = np.cross(first, second)
        third_norm = np.linalg.norm(third)
        if third_norm == 0:
            third = np.array(cls.stain_color_map["null"], dtype=np.float64)
        else:
            third = third / third_norm

        return np.stack([first, second, third], axis=1)

    @staticmethod
    def _complement_stain_matrix(stain_matrix: np.ndarray) -> np.ndarray:
        """Complete a 3×2 stain matrix to 3×3 using cross product.

        Parameters
        ----------
        stain_matrix : np.ndarray
            A 3×2 stain matrix with normalized stain vectors as columns.

        Returns
        -------
        np.ndarray
            A 3×3 stain matrix with a third orthogonal column computed
            as the normalized cross product of the first two columns.
        """
        stain0 = stain_matrix[:, 0]
        stain1 = stain_matrix[:, 1]
        stain2 = np.cross(stain0, stain1)

        # Normalize new vector to unit norm
        return np.array([stain0, stain1, stain2 / np.linalg.norm(stain2)]).T

    @staticmethod
    def _find_stain_index(reference: np.ndarray, stain_matrix: np.ndarray) -> int:
        """Find column index in stain matrix closest to reference vector.

        Parameters
        ----------
        reference : np.ndarray
            Reference stain vector (1D array).
        stain_matrix : np.ndarray
            Stain matrix with normalized column vectors.

        Returns
        -------
        int
            Index of the column with smallest angular distance to reference.

        Notes
        -----
        Uses absolute dot product as similarity metric (angular distance).
        """
        dot_products = np.dot(reference, stain_matrix)
        return int(np.argmax(np.abs(dot_products)))

    @staticmethod
    def _reorder_stains(stain_matrix: np.ndarray, stains: List[str]) -> np.ndarray:
        """Reorder stain matrix columns to match expected stain order.

        Parameters
        ----------
        stain_matrix : np.ndarray
            A 3×3 matrix of stain column vectors.
        stains : list of str
            Ordered list of stain names. Must be length 2.

        Returns
        -------
        np.ndarray
            Reordered 3×3 stain matrix with columns in specified order.

        Notes
        -----
        The third column (null stain) is always placed last.
        """

        def _get_channel_order(stain_matrix: np.ndarray) -> tuple[int, int, int]:
            first = MacenkoStainNormalizer._find_stain_index(
                MacenkoStainNormalizer.stain_color_map[stains[0]], stain_matrix
            )
            second = 1 - first
            # If 2 stains, third "stain" is cross product of 1st 2 channels
            third = 2
            return first, second, third

        def _ordered_stack(
            stain_matrix: np.ndarray, order: tuple[int, int, int]
        ) -> np.ndarray:
            return np.stack([stain_matrix[..., j] for j in order], -1)

        return _ordered_stack(stain_matrix, _get_channel_order(stain_matrix))
