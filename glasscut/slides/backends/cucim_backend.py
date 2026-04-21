"""CuCim backend for GPU-accelerated slide reading."""

from pathlib import Path
from typing import Protocol, runtime_checkable, cast

import numpy as np
import PIL.Image
import importlib.util

from glasscut.exceptions import BackendError
from .base import SlideBackend
from .openslide_backend import OpenSlideBackend


@runtime_checkable
class CuPyArrayProtocol(Protocol):
    """Protocol for CuPy GPU arrays with NumPy-like interface."""

    def get(self) -> object:
        """Transfer array from GPU to CPU (NumPy array)."""
        ...


@runtime_checkable
class CuImageProtocol(Protocol):
    """Protocol describing the interface of cucim.CuImage objects."""

    @property
    def shape(self) -> tuple[int, ...]:
        """Image shape as (height, width, channels)."""
        ...

    def read_region(
        self, location: tuple[int, int], level: int, size: tuple[int, int]
    ) -> CuPyArrayProtocol | object:
        """Read a region from the image at specified level.

        Returns a CuPy array or NumPy array.
        """
        ...


CUCIM_AVAILABLE = importlib.util.find_spec("cucim") is not None

if CUCIM_AVAILABLE:
    import cucim


class CuCimBackend(SlideBackend):
    """CuCim-based backend for GPU-accelerated slide reading.

    This backend uses RAPIDS cuCim for high-performance GPU-accelerated
    reading of whole slide images. Falls back to OpenSlide for metadata
    and operations not supported by cuCim.
    """

    def __init__(self) -> None:
        if not CUCIM_AVAILABLE:
            raise BackendError(
                "cuCim is not installed. Install it with: "
                "pip install cupy-cuda12x cucim"
            )

        self._cucim_slide: CuImageProtocol | None = None
        self._openslide_backend: OpenSlideBackend | None = None
        self._path: str | None = None

    def open(self, path: str | Path) -> None:
        """Open a slide file using CuCim.

        Parameters
        ----------
        path : str | Path
            Path to the slide file

        Raises
        ------
        FileNotFoundError
            If the slide file does not exist
        BackendError
            If cuCim cannot open the file
        """
        self._path = str(path) if isinstance(path, Path) else path

        try:
            # Open with cuCim for GPU acceleration
            self._cucim_slide = cast(CuImageProtocol, cucim.CuImage(self._path)) # type: ignore

            # Also open with OpenSlide for metadata (fallback)
            self._openslide_backend = OpenSlideBackend()
            self._openslide_backend.open(self._path)

        except FileNotFoundError:
            raise FileNotFoundError(f"Slide file not found: {self._path}")
        except Exception as e:
            raise BackendError(f"Failed to open slide with cuCim: {e}")

    def close(self) -> None:
        """Close the slide and free GPU memory."""
        if self._cucim_slide is not None:
            self._cucim_slide = None

        if self._openslide_backend is not None:
            self._openslide_backend.close()
            self._openslide_backend = None

    @property
    def dimensions(self) -> tuple[int, int]:
        """Get slide dimensions at level 0.

        Returns
        -------
        Tuple[int, int]
            (width, height) at highest magnification
        """
        if self._cucim_slide is None:
            raise RuntimeError("Slide not opened")

        # CuCim stores dimensions as (height, width)
        shape = self._cucim_slide.shape
        return (shape[1], shape[0])

    @property
    def properties(self) -> dict[str, str]:
        """Get slide metadata properties.

        Falls back to OpenSlide for metadata retrieval.

        Returns
        -------
        dict[str, str]
            Dictionary of slide properties
        """
        if self._openslide_backend is None:
            raise RuntimeError("Slide not opened")

        return self._openslide_backend.properties

    @property
    def num_levels(self) -> int:
        """Get number of pyramid levels.

        Falls back to OpenSlide for level information.

        Returns
        -------
        int
            Number of pyramid levels
        """
        if self._openslide_backend is None:
            raise RuntimeError("Slide not opened")

        return self._openslide_backend.num_levels

    def read_region(
        self, location: tuple[int, int], level: int, size: tuple[int, int]
    ) -> PIL.Image.Image:
        """Read a region/tile from the slide using GPU acceleration.

        Parameters
        ----------
        location : tuple[int, int]
            (x, y) coordinates at level 0
        level : int
            Pyramid level to read from
        size : tuple[int, int]
            (width, height) of the tile in pixels

        Returns
        -------
        PIL.Image.Image
            The tile image in RGB format
        """
        if self._cucim_slide is None:
            raise RuntimeError("Slide not opened")

        try:
            # Read region using cuCim's GPU acceleration
            region_array = self._cucim_slide.read_region(
                location=location, level=level, size=size
            )

            # Convert to PIL Image
            # cuCim returns CuPy arrays, convert to NumPy then PIL
            if isinstance(region_array, CuPyArrayProtocol):
                # It's a CuPy array, move to CPU
                region_array = cast(np.ndarray, region_array.get())
            else:
                region_array = cast(np.ndarray, region_array)

            image = PIL.Image.fromarray(region_array)
            return image.convert("RGB")

        except Exception:
            # Fallback to OpenSlide if cuCim fails
            if self._openslide_backend is None:
                raise RuntimeError("Slide not opened")

            return self._openslide_backend.read_region(location, level, size)

    def get_thumbnail(self, size: tuple[int, int]) -> PIL.Image.Image:
        """Get thumbnail of the slide.

        Falls back to OpenSlide if available.

        Parameters
        ----------
        size : tuple[int, int]
            Maximum size of the thumbnail (width, height)

        Returns
        -------
        PIL.Image.Image
            Thumbnail image in RGB format
        """
        if self._openslide_backend is None:
            raise RuntimeError("Slide not opened")

        return self._openslide_backend.get_thumbnail(size)

    @property
    def mpp(self) -> float:
        """Get microns per pixel at base magnification.

        Falls back to OpenSlide for metadata retrieval.

        Returns
        -------
        float
            Microns per pixel (MPP)

        Raises
        ------
        SlidePropertyError
            If MPP cannot be determined from metadata
        """
        if self._openslide_backend is None:
            raise RuntimeError("Slide not opened")

        return self._openslide_backend.mpp

    @property
    def base_magnification(self) -> int | float:
        """Get the base magnification (objective power) of the slide.

        Falls back to OpenSlide for metadata retrieval.

        Returns
        -------
        int | float
            Base magnification value

        Raises
        ------
        SlidePropertyError
            If base magnification cannot be determined from metadata
        """
        if self._openslide_backend is None:
            raise RuntimeError("Slide not opened")

        return self._openslide_backend.base_magnification
