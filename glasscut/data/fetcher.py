"""Data fetcher for downloading and managing histology slide samples."""

from pathlib import Path
from typing import Protocol

from pooch import create, os_cache  # type: ignore
import openslide

from .registry import registry, registry_urls


class PoochProtocol(Protocol):
    """Protocol for pooch.Pooch interface.

    Defines the minimal interface we use from pooch to allow proper typing
    despite pooch's limited type annotations.
    """

    def fetch(self, fname: str) -> str:
        """Fetch a file from the registry.

        Parameters
        ----------
        fname : str
            Filename in the registry

        Returns
        -------
        str
            Path to the local file
        """
        ...


class DataFetcher:
    """Manages downloading, caching, and loading histology slide samples.

    Uses pooch for robust file downloading, caching, and verification.

    Attributes
    ----------
    pup : PoochProtocol | None
        Pooch instance for downloading, or None if initialization failed
    """

    def __init__(self) -> None:
        """Initialize the data fetcher."""
        self.pup: PoochProtocol | None = self._create_pooch()

    def _create_pooch(self) -> PoochProtocol | None:
        """Create and configure pooch instance for data management.

        Returns
        -------
        PoochProtocol | None
            Configured pooch instance, or None if initialization failed
        """
        try:
            pup = create(
                path=os_cache("glasscut-data"),
                base_url="",  # URLs from registry_urls
                registry=registry,
                urls=registry_urls,
            )
            return pup
        except Exception:
            return None

    def get_file(self, filename: str) -> Path:
        """Get or download a data file from the registry.

        Attempts to load file from cache,
        then downloads if necessary using pooch.

        Parameters
        ----------
        filename : str
            Relative path in registry (e.g. 'aperio/JP2K-33003-1.svs')

        Returns
        -------
        Path
            Path to the file

        Raises
        ------
        KeyError
            If filename is not in registry
        """
        if filename not in registry:
            raise KeyError(f"File '{filename}' not found in registry")

        # Try pooch first (if available)
        if self.pup is not None:
            try:
                file_path = self.pup.fetch(filename)
                return Path(file_path)
            except Exception:
                # Fallback to local distribution if pooch fails
                pass

        # If pooch is not available, raise error
        if self.pup is None:
            raise ModuleNotFoundError(
                f"Cannot load '{filename}': pooch is not installed. "
                "Install it with: pip install pooch"
            )

        # Last resort: try pooch again, let it raise the real error
        file_path = self.pup.fetch(filename)
        return Path(file_path)

    def load_slide(self, filename: str) -> tuple[openslide.OpenSlide, Path]:
        """Load an SVS file from the data registry.

        Parameters
        ----------
        filename : str
            Relative path in registry

        Returns
        -------
        Tuple[openslide.OpenSlide, Path]
            Tuple of (OpenSlide object, file path)

        Raises
        ------
        openslide.OpenSlideError
            If the file cannot be opened
        KeyError
            If filename is not in registry
        """
        file_path = self.get_file(filename)
        try:
            slide = openslide.OpenSlide(str(file_path))
            return slide, file_path
        except Exception as e:
            raise openslide.OpenSlideError(
                f"Cannot open WSI file {file_path}: {e}"
            ) from e
