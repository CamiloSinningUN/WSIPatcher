"""Dataset generation orchestration for multi-slide tiling workflows."""

import copy
import logging
from datetime import datetime
from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import Image

from glasscut.slides import Slide
from glasscut.stain_normalizers import StainNormalizer
from glasscut.tile import Tile
from glasscut.tiler import Tiler
from glasscut.tissue_detectors import OtsuTissueDetector
from glasscut.storage import (
    DatasetMetadata,
    SlideMetadata,
    StorageOrganizer,
    TileMetadata,
)
from glasscut.storage.structures import JsonValue

# TODO: Add parallel processing

class DatasetGenerator:
    """Generate a tile dataset from one or more slide files."""

    def __init__(
        self,
        dataset_id: str,
        output_dir: str | Path,
        *,
        tiler: Tiler,
        stain_normalizer: StainNormalizer | None = None,
        save_thumbnails: bool = True,
        save_masks: bool = True,
        save_processed_json: bool = True,
        show_progress: bool = True,
        verbose: bool = True,
    ) -> None:
        """Initialize generator from direct parameters.

        Parameters
        ----------
        dataset_id : str
            Dataset identifier.
        output_dir : str | Path
            Output root directory.
        tiler : Tiler
            Preconfigured tiler instance used for extraction.
        stain_normalizer : StainNormalizer | None, optional
            Optional fitted stain normalizer. If provided, each extracted tile
            is transformed before it is saved.
        save_thumbnails : bool, optional
            Whether to save slide thumbnail artifacts.
        save_masks : bool, optional
            Whether to save tissue mask artifacts.
        save_processed_json : bool, optional
            Whether to save ``processed.json`` at dataset root.
        show_progress : bool, optional
            Whether to display progress bars for slides and tiles.
        verbose : bool, optional
            Whether to enable info-level logs.
        """
        self._validate_parameters(
            dataset_id=dataset_id,
            output_dir=output_dir,
        )

        self.dataset_id = dataset_id
        self.output_dir = str(Path(output_dir).resolve())
        self.tiler = tiler
        self.stain_normalizer = stain_normalizer
        self.save_thumbnails = save_thumbnails
        self.save_masks = save_masks
        self.save_processed_json = save_processed_json
        self.show_progress = show_progress
        self.verbose = verbose

        self.storage = StorageOrganizer(self.output_dir)
        self.logger = self._setup_logger()

    def process_dataset(self, slide_paths: Sequence[str | Path]) -> DatasetMetadata:
        """Process all provided slides and persist tiles, artifacts, and metadata."""
        if not slide_paths:
            raise ValueError("No slide paths were provided")

        normalized_paths = [str(Path(path)) for path in slide_paths]
        self.storage.init_dataset(self.dataset_id)

        all_tasks = list(enumerate(normalized_paths))
        all_slide_ids = {self._slide_id_from_index(index) for index, _ in all_tasks}

        resumed_metadata: list[SlideMetadata] = []
        processed_slide_ids: list[str] = []
        if self.save_processed_json:
            previously_processed = self.storage.load_processed_json(self.dataset_id)
            for slide_id in previously_processed:
                if slide_id not in all_slide_ids:
                    continue
                try:
                    resumed_metadata.append(
                        self.storage.load_slide_metadata(self.dataset_id, slide_id)
                    )
                    processed_slide_ids.append(slide_id)
                except (FileNotFoundError, ValueError):
                    self.logger.warning(
                        "Skipping stale checkpoint entry for %s (missing/invalid metadata)",
                        slide_id,
                    )

        processed_set = set(processed_slide_ids)
        pending_tasks = [
            (index, slide_path)
            for index, slide_path in all_tasks
            if self._slide_id_from_index(index) not in processed_set
        ]

        self.logger.info(
            "Starting dataset generation for %s (%d slides, %d remaining)",
            self.dataset_id,
            len(normalized_paths),
            len(pending_tasks),
        )

        new_slides_metadata: list[SlideMetadata] = []
        total_pending = len(pending_tasks)
        for pending_index, (index, slide_path) in enumerate(pending_tasks, start=1):
            if self.show_progress:
                print(f"Processing slide {pending_index}/{total_pending}")
            slide_meta = self._process_single_slide(slide_path, index)
            new_slides_metadata.append(slide_meta)
            self._checkpoint_processed_slide(processed_slide_ids, slide_meta.slide_id)

        slides_metadata = resumed_metadata + new_slides_metadata
        slides_metadata.sort(
            key=lambda metadata: self._slide_index_from_id(metadata.slide_id)
        )

        total_tiles = sum(slide_meta.total_tiles for slide_meta in slides_metadata)
        dataset_metadata = DatasetMetadata(
            dataset_id=self.dataset_id,
            created_at=datetime.now().isoformat(),
            total_slides=len(slides_metadata),
            total_tiles=total_tiles,
            config=self._config_dict(),
            slides=slides_metadata,
        )

        self.storage.save_dataset_metadata(self.dataset_id, dataset_metadata)
        if self.save_processed_json and pending_tasks:
            self.storage.save_processed_json(self.dataset_id, processed_slide_ids)

        self.logger.info(
            "Dataset generation complete: %d slides, %d tiles",
            len(slides_metadata),
            total_tiles,
        )
        return dataset_metadata

    def _checkpoint_processed_slide(
        self,
        processed_slide_ids: list[str],
        slide_id: str,
    ) -> None:
        """Persist progress checkpoint after each completed slide."""
        if slide_id not in processed_slide_ids:
            processed_slide_ids.append(slide_id)

        if self.save_processed_json:
            self.storage.save_processed_json(self.dataset_id, processed_slide_ids)

    @staticmethod
    def _slide_id_from_index(slide_index: int) -> str:
        """Format slide ID from zero-based index."""
        return f"slide_{slide_index:03d}"

    @staticmethod
    def _slide_index_from_id(slide_id: str) -> int:
        """Extract numeric index from slide ID for sorting."""
        try:
            return int(slide_id.split("_")[1])
        except (IndexError, ValueError):
            return 10**9

    def _process_single_slide(self, slide_path: str, slide_index: int) -> SlideMetadata:
        """Process a single slide end-to-end."""
        slide_id = self._slide_id_from_index(slide_index)
        directories = self.storage.init_slide(self.dataset_id, slide_id)
        tiler = self._build_tiler()

        with Slide(slide_path) as slide:
            tile_metadata = self._extract_and_save_tiles(
                slide=slide,
                tiler=tiler,
                tiles_dir=directories["tiles"],
            )

            if self.save_thumbnails:
                slide.thumbnail.save(directories["thumbnails"] / "slide_thumbnail.png")

            if self.save_masks:
                self._save_tissue_mask(slide.thumbnail, directories["masks"])

            slide_metadata = SlideMetadata(
                slide_id=slide_id,
                slide_name=slide.name,
                slide_path=str(Path(slide_path).resolve()),
                total_tiles=len(tile_metadata),
                dimensions=slide.dimensions,
                mpp=slide.mpp,
                available_magnifications=[
                    float(magnification) for magnification in slide.magnifications
                ],
                tile_size=self._resolve_slide_tile_size(tile_metadata),
                tiler_name=tiler.__class__.__name__,
                timestamp=datetime.now().isoformat(),
                tiles=tile_metadata,
            )

        self.storage.save_slide_metadata(self.dataset_id, slide_id, slide_metadata)
        self.logger.info(
            "Processed %s with %d tiles", Path(slide_path).name, len(tile_metadata)
        )
        return slide_metadata

    def _extract_and_save_tiles(
        self,
        slide: Slide,
        tiler: Tiler,
        tiles_dir: Path,
    ) -> list[TileMetadata]:
        """Extract tiles and persist them to disk while collecting metadata."""
        metadata: list[TileMetadata] = []

        for tile_index, tile in enumerate(tiler.extract(slide)):
            tile_id = f"tile_{tile_index:07d}"
            tile_path = tiles_dir / f"{tile_id}.png"

            image_to_save = tile.image
            if self.stain_normalizer is not None:
                image_to_save = self.stain_normalizer.transform(image_to_save)
            image_to_save.save(tile_path)

            x, y = tile.coords if tile.coords is not None else (0, 0)
            width, height = tile.image.size

            metadata.append(
                TileMetadata(
                    tile_id=tile_id,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    level=0,
                    magnification=self._resolve_tile_magnification(tile),
                    tissue_ratio=self._safe_tissue_ratio(tile),
                    file_path=str(tile_path.relative_to(Path(self.output_dir))),
                )
            )

        return metadata

    def _build_tiler(self) -> Tiler:
        """Build a configured tiler instance for extraction."""
        # Use an independent tiler instance per slide to avoid shared mutable state.
        return copy.deepcopy(self.tiler)

    @staticmethod
    def _resolve_tile_magnification(tile: Tile) -> float:
        """Return tile magnification, requiring tilers to emit it explicitly."""
        if tile.magnification is None:
            raise ValueError(
                "Tile magnification is missing. Custom tilers must emit tiles "
                "with a valid magnification value."
            )
        return float(tile.magnification)

    @staticmethod
    def _resolve_slide_tile_size(tile_metadata: list[TileMetadata]) -> tuple[int, int]:
        """Return representative slide tile size.

        For mixed-size tilers this reflects the first produced tile.
        """
        if not tile_metadata:
            return (0, 0)
        return (tile_metadata[0].width, tile_metadata[0].height)

    @staticmethod
    def _safe_tissue_ratio(tile: Tile) -> float:
        """Compute tissue ratio and return 0.0 on detector failures."""
        try:
            return float(tile.tissue_ratio)
        except Exception:
            return 0.0

    @staticmethod
    def _save_tissue_mask(thumbnail: Image.Image, masks_dir: Path) -> None:
        """Generate and persist a thumbnail-level tissue mask."""
        detector = OtsuTissueDetector()
        mask = detector.detect(thumbnail)
        mask = np.asarray(mask)
        if mask.dtype != np.uint8:
            mask = mask.astype(np.uint8)
        Image.fromarray(mask * 255).save(masks_dir / "tissue_mask.png")

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"glasscut.dataset.{self.dataset_id}")
        logger.handlers.clear()
        logger.setLevel(logging.INFO if self.verbose else logging.WARNING)
        logger.propagate = False

        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
                )
            )
            logger.addHandler(handler)

        return logger

    @staticmethod
    def _validate_parameters(
        dataset_id: str,
        output_dir: str | Path,
    ) -> None:
        if not dataset_id:
            raise ValueError("dataset_id is required")

        if not output_dir:
            raise ValueError("output_dir is required")

    def _config_dict(self) -> dict[str, JsonValue]:
        """Build JSON-serializable config payload for metadata.json."""
        return {
            "dataset_id": self.dataset_id,
            "output_dir": self.output_dir,
            "tiler_name": self.tiler.__class__.__name__,
            "stain_normalizer": (
                self.stain_normalizer.__class__.__name__
                if self.stain_normalizer is not None
                else None
            ),
            "show_progress": self.show_progress,
            "save_thumbnails": self.save_thumbnails,
            "save_masks": self.save_masks,
            "save_processed_json": self.save_processed_json,
            "verbose": self.verbose,
        }
