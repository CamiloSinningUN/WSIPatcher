"""Dataset generation with parallel processing.

Main orchestrator for multi-slide dataset generation with tile extraction,
artifact generation, and metadata management.
"""

import logging
from pathlib import Path
from typing import List, Optional, Callable
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import traceback

from glasscut.slides import Slide
from glasscut.tiler import Tiler, GridTiler, RandomTiler, ConditionalTiler
from glasscut.storage import (
    StorageOrganizer,
    DatasetMetadata,
    SlideMetadata,
    TileMetadata,
    dataclass_to_dict,
)
from .config import DatasetConfig


class DatasetGenerator:
    """Orchestrate multi-slide dataset generation.

    Manages the complete pipeline for extracting tiles from multiple WSI files,
    organizing outputs, and generating metadata. Supports parallel processing
    for multi-slide datasets.

    Features:
        - Pluggable tiler strategies (GridTiler, RandomTiler, ConditionalTiler)
        - Parallel slide processing with configurable workers
        - Automatic directory structure creation (tiles, thumbnails, masks)
        - Comprehensive metadata tracking (PathoPatcher JSON format)
        - Tissue mask visualization
        - Detailed logging and progress tracking

    Parameters
    ----------
    config : DatasetConfig
        Configuration for dataset generation

    Attributes
    ----------
    config : DatasetConfig
        Configuration object
    storage : StorageOrganizer
        Storage management system
    logger : logging.Logger
        Logger instance

    Example:
        >>> from glasscut import DatasetGenerator, DatasetConfig
        >>> config = DatasetConfig(
        ...     dataset_id="my_dataset",
        ...     output_dir="./output",
        ...     tiler="grid",
        ...     tiler_params={"overlap": 50},
        ...     num_workers=4
        ... )
        >>> generator = DatasetGenerator(config)
        >>> slide_paths = [
        ...     "slide_001.svs",
        ...     "slide_002.svs",
        ... ]
        >>> dataset_meta = generator.process_dataset(slide_paths)
        >>> print(f"Generated {dataset_meta.total_tiles} tiles")
    """

    def __init__(self, config: DatasetConfig):
        """Initialize dataset generator.

        Parameters
        ----------
        config : DatasetConfig
            Configuration for processing
        """
        self.config = config
        self.storage = StorageOrganizer(config.output_dir)
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration.

        Returns
        -------
        logging.Logger
            Configured logger
        """
        logger = logging.getLogger(f"DatasetGenerator[{self.config.dataset_id}]")

        # Clear existing handlers
        logger.handlers.clear()

        # Set level
        level = logging.INFO if self.config.verbose else logging.WARNING
        logger.setLevel(level)

        # Add console handler if not already present
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def process_dataset(self, slide_paths: List[str | Path]) -> DatasetMetadata:
        """Process multiple slides into dataset.

        Main entry point for dataset generation. Processes all slides,
        extracts tiles, generates artifacts, and creates metadata.

        Parameters
        ----------
        slide_paths : List[str | Path]
            List of paths to WSI files

        Returns
        -------
        DatasetMetadata
            Complete dataset metadata with all slide and tile information

        Raises
        ------
        ValueError
            If no slides provided or all slides fail processing
        """
        if not slide_paths:
            raise ValueError("No slides provided")

        # Convert to strings
        slide_paths = [str(p) for p in slide_paths]

        self.logger.info(f"Starting dataset generation: {self.config.dataset_id}")
        self.logger.info(
            f"Processing {len(slide_paths)} slides with {self.config.num_workers} workers"
        )
        self.logger.info(f"Configuration: {self.config}")

        # Initialize dataset
        self.storage.init_dataset(self.config.dataset_id)

        # Process slides
        if self.config.num_workers == 1:
            # Sequential processing
            slides_metadata, processed_slides = self._process_sequential(slide_paths)
        else:
            # Parallel processing
            slides_metadata, processed_slides = self._process_parallel(slide_paths)

        if not slides_metadata:
            raise RuntimeError("All slides failed to process")

        # Calculate totals
        total_tiles = sum(sm.total_tiles for sm in slides_metadata)

        # Create dataset metadata
        dataset_meta = DatasetMetadata(
            dataset_id=self.config.dataset_id,
            created_at=datetime.now().isoformat(),
            total_slides=len(slides_metadata),
            total_tiles=total_tiles,
            config=dataclass_to_dict(self.config),
            slides=slides_metadata,
        )

        # Save metadata
        self.storage.save_dataset_metadata(self.config.dataset_id, dataset_meta)

        # Save processed.json
        if self.config.save_processed_json:
            self.storage.save_processed_json(self.config.dataset_id, processed_slides)

        self.logger.info(
            f"Dataset complete! Generated {total_tiles} tiles from "
            f"{len(slides_metadata)} slides"
        )

        return dataset_meta

    def _process_sequential(
        self, slide_paths: List[str]
    ) -> tuple[List[SlideMetadata], List[str]]:
        """Process slides sequentially (single worker).

        Parameters
        ----------
        slide_paths : List[str]
            Slide paths to process

        Returns
        -------
        tuple[List[SlideMetadata], List[str]]
            Processed slide metadata and list of successfully processed slide names
        """
        slides_metadata = []
        processed_slides = []

        for i, slide_path in enumerate(slide_paths):
            self.logger.info(
                f"[{i + 1}/{len(slide_paths)}] Processing {Path(slide_path).name}"
            )

            try:
                slide_meta = self._process_single_slide(
                    slide_path=slide_path, slide_index=i
                )
                slides_metadata.append(slide_meta)
                processed_slides.append(slide_meta.slide_id)

            except Exception as e:
                self.logger.error(
                    f"Failed to process {Path(slide_path).name}: {e}\n{traceback.format_exc()}"
                )

        return slides_metadata, processed_slides

    def _process_parallel(
        self, slide_paths: List[str]
    ) -> tuple[List[SlideMetadata], List[str]]:
        """Process slides in parallel (multiple workers).

        Parameters
        ----------
        slide_paths : List[str]
            Slide paths to process

        Returns
        -------
        tuple[List[SlideMetadata], List[str]]
            Processed slide metadata and list of successfully processed slide names
        """
        slides_metadata = []
        processed_slides = []

        # Create a worker function that can be pickled
        def process_wrapper(args):
            slide_path, slide_index, config = args
            return self._process_single_slide(slide_path, slide_index, config)

        # Submit all tasks
        with ProcessPoolExecutor(max_workers=self.config.num_workers) as executor:
            futures = {
                executor.submit(process_wrapper, (slide_path, i, self.config)): (
                    slide_path,
                    i,
                )
                for i, slide_path in enumerate(slide_paths)
            }

            # Collect results as they complete
            completed = 0
            for future in as_completed(futures):
                slide_path, i = futures[future]
                completed += 1

                try:
                    slide_meta = future.result()
                    slides_metadata.append(slide_meta)
                    processed_slides.append(slide_meta.slide_id)
                    self.logger.info(
                        f"[{completed}/{len(slide_paths)}] "
                        f"Processed {Path(slide_path).name} "
                        f"({slide_meta.total_tiles} tiles)"
                    )

                except Exception as e:
                    self.logger.error(
                        f"[{completed}/{len(slide_paths)}] "
                        f"Failed to process {Path(slide_path).name}: {e}"
                    )

        # Sort by index to maintain original order
        slides_metadata.sort(key=lambda x: int(x.slide_id.split("_")[1]))
        processed_slides.sort(key=lambda x: int(x.split("_")[1]))

        return slides_metadata, processed_slides

    def _process_single_slide(
        self,
        slide_path: str,
        slide_index: int,
        config: Optional[DatasetConfig] = None,
    ) -> SlideMetadata:
        """Process a single slide.

        Extracts tiles, generates thumbnails, and creates metadata for one slide.
        This method is typically called by the orchestrator or in parallel workers.

        Parameters
        ----------
        slide_path : str
            Path to WSI file
        slide_index : int
            Index of this slide in the dataset (for naming)
        config : Optional[DatasetConfig]
            Configuration (for multiprocessing context). If None, uses self.config.

        Returns
        -------
        SlideMetadata
            Complete metadata for this slide including all tiles
        """
        # Use provided config or instance config
        cfg = config or self.config

        slide_name = Path(slide_path).stem
        slide_id = f"Slide_{slide_index:03d}"

        # Initialize storage for this slide
        dirs = self.storage.init_slide(cfg.dataset_id, slide_id)

        # Open slide
        slide = Slide(slide_path)

        try:
            # Get tiler
            tiler = self._get_tiler()

            # Extract tiles
            tile_list = []
            tile_count = 0

            for tile in tiler.extract(
                slide, magnification=cfg.magnification, tile_size=cfg.tile_size
            ):
                tile_id = f"tile_{tile_count:07d}"

                # Save tile
                tile_path = dirs["tiles"] / f"{tile_id}.png"
                tile.image.save(tile_path)

                # Calculate tissue ratio
                tissue_ratio = self._get_tissue_ratio(tile)

                # Create tile metadata
                tile_meta = TileMetadata(
                    tile_id=tile_id,
                    x=tile.coords[0],
                    y=tile.coords[1],
                    width=tile.image.width,
                    height=tile.image.height,
                    level=0,  # Always at level 0 for our extraction
                    magnification=cfg.magnification,
                    tissue_ratio=tissue_ratio,
                    file_path=str(tile_path.relative_to(self.storage.output_dir)),
                )
                tile_list.append(tile_meta)
                tile_count += 1

            # Generate artifacts
            if cfg.save_thumbnails:
                self._save_thumbnails(slide, dirs)

            if cfg.save_masks:
                self._save_masks(slide, dirs)

            # Create slide metadata
            slide_meta = SlideMetadata(
                slide_id=slide_id,
                slide_name=slide_name,
                slide_path=str(slide_path),
                total_tiles=len(tile_list),
                dimensions=slide.dimensions,
                mpp=slide.mpp,
                magnification=cfg.magnification,
                tile_size=cfg.tile_size,
                tiler_name=tiler.__class__.__name__,
                timestamp=datetime.now().isoformat(),
                tiles=tile_list,
            )

            # Save slide metadata
            self.storage.save_slide_metadata(cfg.dataset_id, slide_id, slide_meta)

            return slide_meta

        finally:
            slide.close()

    def _get_tiler(self) -> Tiler:
        """Get configured tiler instance.

        Returns
        -------
        Tiler
            Instantiated tiler of the configured type

        Raises
        ------
        ValueError
            If tiler type is unknown
        """
        tiler_type = self.config.tiler.lower()
        params = self.config.tiler_params or {}

        if tiler_type == "grid":
            return GridTiler(
                tile_size=self.config.tile_size, overlap=self.config.overlap, **params
            )

        elif tiler_type == "random":
            return RandomTiler(tile_size=self.config.tile_size, **params)

        elif tiler_type == "conditional":
            return ConditionalTiler(
                tile_size=self.config.tile_size, overlap=self.config.overlap, **params
            )

        else:
            raise ValueError(f"Unknown tiler: {tiler_type}")

    def _save_thumbnails(self, slide: Slide, dirs: dict) -> None:
        """Save slide thumbnail.

        Parameters
        ----------
        slide : Slide
            Slide object
        dirs : dict
            Directory paths from init_slide()
        """
        try:
            thumb = slide.thumbnail
            thumb.save(dirs["thumbnails"] / "slide_thumbnail.png")
        except Exception as e:
            self.logger.warning(f"Failed to save thumbnail: {e}")

    def _save_masks(self, slide: Slide, dirs: dict) -> None:
        """Save tissue mask.

        Parameters
        ----------
        slide : Slide
            Slide object
        dirs : dict
            Directory paths from init_slide()
        """
        try:
            from glasscut.tissue_detectors import OtsuTissueDetector
            from PIL import Image
            import numpy as np

            detector = OtsuTissueDetector()
            # Create a dummy tile to get tissue mask
            dummy_tile = slide.extract_tile(
                coords=(0, 0),
                tile_size=(256, 256),
                magnification=self.config.magnification,
            )

            # Save using built-in tissue mask
            tissue_mask = dummy_tile.tissue_mask
            mask_img = Image.fromarray((tissue_mask * 255).astype(np.uint8))
            mask_img.save(dirs["masks"] / "tissue_mask.png")

        except Exception as e:
            self.logger.warning(f"Failed to save mask: {e}")

    @staticmethod
    def _get_tissue_ratio(tile) -> float:
        """Calculate tissue ratio for a tile.

        Parameters
        ----------
        tile : Tile
            Tile object

        Returns
        -------
        float
            Tissue ratio (0.0 to 1.0)
        """
        try:
            tissue_mask = tile.tissue_mask
            tissue_ratio = float(tissue_mask.sum()) / tissue_mask.size
            return tissue_ratio
        except Exception:
            return 0.5  # Default if detection fails

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"DatasetGenerator(dataset_id={self.config.dataset_id!r}, "
            f"workers={self.config.num_workers})"
        )
