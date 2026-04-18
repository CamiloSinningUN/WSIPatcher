"""Storage management for dataset organization.

Handles creation and management of the directory structure for datasets,
following PathoPatcher's organizational style.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from .structures import DatasetMetadata, SlideMetadata, dataclass_to_dict


class StorageOrganizer:
    """Manages dataset directory structure and file organization.

    This class handles creating the proper directory structure for storing
    extracted tiles, thumbnails, masks, and metadata according to the format:

        output/
        ├── metadata.json
        ├── processed.json
        ├── Slide_001/
        │   ├── tiles/
        │   ├── thumbnails/
        │   ├── masks/
        │   └── slide_metadata.json
        └── ...

    Parameters
    ----------
    output_dir : str | Path
        Root directory where the dataset will be stored

    Attributes
    ----------
    output_dir : Path
        Resolved path to output directory

    Example:
        >>> organizer = StorageOrganizer("./output")
        >>> dataset_path = organizer.init_dataset("my_dataset")
        >>> dirs = organizer.init_slide("my_dataset", "Slide_001")
        >>> tile_path = organizer.get_tile_path("my_dataset", "Slide_001", "tile_000000")
        >>> tile.save(tile_path)
    """

    def __init__(self, output_dir: str | Path):
        """Initialize storage organizer.

        Parameters
        ----------
        output_dir : str | Path
            Root directory for output (will be created if doesn't exist)
        """
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ===== Dataset-level operations =====

    def init_dataset(self, dataset_id: str) -> Path:
        """Initialize dataset directory structure.

        Creates the base directory for a dataset and initializes subdirectories.

        Parameters
        ----------
        dataset_id : str
            Unique identifier for the dataset

        Returns
        -------
        Path
            Path to the created dataset directory

        Example:
            >>> organizer = StorageOrganizer("./output")
            >>> dataset_dir = organizer.init_dataset("histopathology_v1")
            >>> print(dataset_dir)
            Path('/path/to/output/histopathology_v1')
        """
        dataset_path = self.output_dir / dataset_id
        dataset_path.mkdir(parents=True, exist_ok=True)
        return dataset_path

    def get_dataset_path(self, dataset_id: str) -> Path:
        """Get path to dataset directory.

        Parameters
        ----------
        dataset_id : str
            Dataset identifier

        Returns
        -------
        Path
            Path to dataset directory
        """
        return self.output_dir / dataset_id

    # ===== Slide-level operations =====

    def init_slide(self, dataset_id: str, slide_id: str) -> Dict[str, Path]:
        """Initialize slide subdirectories.

        Creates the standard subdirectory structure for a slide:
        - tiles/      : Extracted tile PNG files
        - thumbnails/ : Generated thumbnails and mask visualizations
        - masks/      : Tissue mask and other binary masks

        Parameters
        ----------
        dataset_id : str
            Dataset identifier
        slide_id : str
            Identifier for this slide (e.g., "Slide_001")

        Returns
        -------
        Dict[str, Path]
            Dictionary with keys: 'root', 'tiles', 'thumbnails', 'masks'
            mapping to their respective Path objects

        Example:
            >>> dirs = organizer.init_slide("my_dataset", "Slide_001")
            >>> dirs['tiles']  # Use to save tiles
            Path('.../my_dataset/Slide_001/tiles')
        """
        slide_dir = self.output_dir / dataset_id / slide_id

        dirs = {
            "root": slide_dir,
            "tiles": slide_dir / "tiles",
            "thumbnails": slide_dir / "thumbnails",
            "masks": slide_dir / "masks",
        }

        for dir_path in dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

        return dirs

    def get_slide_path(self, dataset_id: str, slide_id: str) -> Path:
        """Get path to slide directory.

        Parameters
        ----------
        dataset_id : str
            Dataset identifier
        slide_id : str
            Slide identifier

        Returns
        -------
        Path
            Path to slide root directory
        """
        return self.output_dir / dataset_id / slide_id

    # ===== Tile file operations =====

    def get_tile_path(
        self, dataset_id: str, slide_id: str, tile_id: str, ext: str = "png"
    ) -> Path:
        """Get path for a tile file.

        Parameters
        ----------
        dataset_id : str
            Dataset identifier
        slide_id : str
            Slide identifier
        tile_id : str
            Tile identifier (e.g., "tile_000000")
        ext : str, optional
            File extension without dot (default "png")

        Returns
        -------
        Path
            Path where tile should be saved
        """
        return self.output_dir / dataset_id / slide_id / "tiles" / f"{tile_id}.{ext}"

    # ===== Thumbnail operations =====

    def get_slide_thumbnail_path(self, dataset_id: str, slide_id: str) -> Path:
        """Get path for slide thumbnail.

        Parameters
        ----------
        dataset_id : str
            Dataset identifier
        slide_id : str
            Slide identifier

        Returns
        -------
        Path
            Path to save slide thumbnail
        """
        return (
            self.output_dir
            / dataset_id
            / slide_id
            / "thumbnails"
            / "slide_thumbnail.png"
        )

    def get_mask_thumbnail_path(self, dataset_id: str, slide_id: str) -> Path:
        """Get path for mask thumbnail.

        Parameters
        ----------
        dataset_id : str
            Dataset identifier
        slide_id : str
            Slide identifier

        Returns
        -------
        Path
            Path to save mask thumbnail
        """
        return (
            self.output_dir
            / dataset_id
            / slide_id
            / "thumbnails"
            / "mask_thumbnail.png"
        )

    # ===== Mask operations =====

    def get_tissue_mask_path(self, dataset_id: str, slide_id: str) -> Path:
        """Get path for tissue mask.

        Parameters
        ----------
        dataset_id : str
            Dataset identifier
        slide_id : str
            Slide identifier

        Returns
        -------
        Path
            Path to save tissue mask
        """
        return self.output_dir / dataset_id / slide_id / "masks" / "tissue_mask.png"

    # ===== Metadata operations =====

    def save_dataset_metadata(self, dataset_id: str, metadata: DatasetMetadata) -> Path:
        """Save dataset-level metadata to JSON.

        Saves complete dataset information to metadata.json in the dataset root.
        This includes all slide metadata and configuration.

        Parameters
        ----------
        dataset_id : str
            Dataset identifier
        metadata : DatasetMetadata
            Metadata object to save

        Returns
        -------
        Path
            Path where metadata was saved
        """
        metadata_path = self.output_dir / dataset_id / "metadata.json"

        # Convert dataclasses to dict
        data = dataclass_to_dict(metadata)

        with open(metadata_path, "w") as f:
            json.dump(data, f, indent=2)

        return metadata_path

    def load_dataset_metadata(self, dataset_id: str) -> DatasetMetadata:
        """Load dataset metadata from JSON.

        Parameters
        ----------
        dataset_id : str
            Dataset identifier

        Returns
        -------
        DatasetMetadata
            Loaded metadata object
        """
        metadata_path = self.output_dir / dataset_id / "metadata.json"

        if not metadata_path.exists():
            raise FileNotFoundError(f"Dataset metadata not found at {metadata_path}")

        with open(metadata_path, "r") as f:
            data = json.load(f)

        # Reconstruct dataclasses (simplified - doesn't fully reconstruct nested structure)
        return DatasetMetadata(**data)

    def save_slide_metadata(
        self, dataset_id: str, slide_id: str, metadata: SlideMetadata
    ) -> Path:
        """Save slide-level metadata to JSON.

        Saves slide and tile information to slide_metadata.json in the slide directory.

        Parameters
        ----------
        dataset_id : str
            Dataset identifier
        slide_id : str
            Slide identifier
        metadata : SlideMetadata
            Metadata object to save

        Returns
        -------
        Path
            Path where metadata was saved
        """
        metadata_path = self.output_dir / dataset_id / slide_id / "slide_metadata.json"

        # Convert dataclasses to dict
        data = dataclass_to_dict(metadata)

        with open(metadata_path, "w") as f:
            json.dump(data, f, indent=2)

        return metadata_path

    def save_processed_json(self, dataset_id: str, processed_slides: list[str]) -> Path:
        """Save processed.json file listing all processed slides.

        Creates a simple JSON file with list of successfully processed slide names,
        matching PathoPatcher's format.

        Parameters
        ----------
        dataset_id : str
            Dataset identifier
        processed_slides : list[str]
            List of slide identifiers that were processed

        Returns
        -------
        Path
            Path where processed.json was saved
        """
        processed_path = self.output_dir / dataset_id / "processed.json"

        data = {
            "processed_files": processed_slides,
            "timestamp": datetime.now().isoformat(),
            "total": len(processed_slides),
        }

        with open(processed_path, "w") as f:
            json.dump(data, f, indent=2)

        return processed_path

    def __repr__(self) -> str:
        """String representation."""
        return f"StorageOrganizer(output_dir={self.output_dir})"
