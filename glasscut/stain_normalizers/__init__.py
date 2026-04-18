"""Stain normalization module for histopathology image preprocessing.

This module provides multiple stain normalization methods to standardize color
variations in histological images, which is critical for downstream analysis
and computer vision tasks.

Available Methods
-----------------
- **MacenkoStainNormalizer**: Unsupervised color deconvolution-based method,
  well-suited for H&E stained images. Fast and robust.
- **ReinhardtStainNormalizer**: Color transfer-based method, computationally
  efficient and good for interactive normalization.

References
----------
For method details, see the docstrings of individual normalizer classes.

Examples
--------
Basic usage with Macenko normalizer:

>>> from PIL import Image
>>> from glasscut.stain_normalizers import MacenkoStainNormalizer
>>> normalizer = MacenkoStainNormalizer()
>>> reference_image = Image.open("reference.png")
>>> normalizer.fit(reference_image)
>>> test_image = Image.open("test.png")
>>> normalized = normalizer.transform(test_image)

Usage with Reinhardt normalizer:

>>> from glasscut.stain_normalizers import ReinhardtStainNormalizer
>>> normalizer = ReinhardtStainNormalizer()
>>> normalizer.fit(reference_image)
>>> normalized = normalizer.transform(test_image)
"""

from .base import StainNormalizer, TransformerStainMatrixMixin
from .macenko import MacenkoStainNormalizer
from .reinhardt import ReinhardtStainNormalizer

__all__ = [
    "StainNormalizer",
    "TransformerStainMatrixMixin",
    "MacenkoStainNormalizer",
    "ReinhardtStainNormalizer",
]
