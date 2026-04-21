"""Storage management for dataset generation outputs."""

from datetime import datetime
from pathlib import Path
from typing import cast

import orjson

from .structures import (
    DatasetMetadata,
    JsonValue,
    SlideMetadata,
    TileMetadata,
    dataclass_to_dict,
)


class StorageOrganizer:
    """Manage output directory layout and JSON metadata persistence."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def init_dataset(self, dataset_id: str) -> Path:
        """Create dataset root directory."""
        dataset_path = self.output_dir / dataset_id
        dataset_path.mkdir(parents=True, exist_ok=True)
        return dataset_path

    def init_slide(self, dataset_id: str, slide_id: str) -> dict[str, Path]:
        """Create standard directories for one processed slide."""
        slide_root = self.output_dir / dataset_id / slide_id
        directories = {
            "root": slide_root,
            "tiles": slide_root / "tiles",
            "thumbnails": slide_root / "thumbnails",
            "masks": slide_root / "masks",
        }
        for directory in directories.values():
            directory.mkdir(parents=True, exist_ok=True)
        return directories

    def save_dataset_metadata(
        self,
        dataset_id: str,
        metadata: DatasetMetadata,
    ) -> Path:
        """Persist top-level metadata as dataset_id/metadata.json."""
        metadata_path = self.output_dir / dataset_id / "metadata.json"
        self._write_json(metadata_path, dataclass_to_dict(metadata))
        return metadata_path

    def save_slide_metadata(
        self,
        dataset_id: str,
        slide_id: str,
        metadata: SlideMetadata,
    ) -> Path:
        """Persist per-slide metadata as slide_metadata.json."""
        metadata_path = self.output_dir / dataset_id / slide_id / "slide_metadata.json"
        self._write_json(metadata_path, dataclass_to_dict(metadata))
        return metadata_path

    def save_processed_json(self, dataset_id: str, processed_slides: list[str]) -> Path:
        """Persist processed slide IDs in PathoPatcher-style processed.json."""
        processed_path = self.output_dir / dataset_id / "processed.json"
        payload: dict[str, JsonValue] = {
            "processed_files": cast(
                list[JsonValue], [str(name) for name in processed_slides]
            ),
            "timestamp": datetime.now().isoformat(),
            "total": len(processed_slides),
        }
        self._write_json(processed_path, payload)
        return processed_path

    def load_processed_json(self, dataset_id: str) -> list[str]:
        """Load processed slide IDs from processed.json.

        Returns an empty list when the file does not exist.
        """
        processed_path = self.output_dir / dataset_id / "processed.json"
        if not processed_path.exists():
            return []

        payload = self._read_json(processed_path)
        if not isinstance(payload, dict):
            return []

        processed = payload.get("processed_files")
        if not isinstance(processed, list):
            return []

        result: list[str] = []
        for value in processed:
            if isinstance(value, str):
                result.append(value)
        return result

    def load_slide_metadata(self, dataset_id: str, slide_id: str) -> SlideMetadata:
        """Load slide metadata from disk and reconstruct dataclasses."""
        metadata_path = self.output_dir / dataset_id / slide_id / "slide_metadata.json"
        payload = self._read_json(metadata_path)
        if not isinstance(payload, dict):
            raise ValueError(f"Invalid slide metadata format: {metadata_path}")

        raw_tiles = payload.get("tiles", [])
        if not isinstance(raw_tiles, list):
            raw_tiles = []

        tiles: list[TileMetadata] = []
        for raw_tile in raw_tiles:
            if not isinstance(raw_tile, dict):
                continue
            tiles.append(
                TileMetadata(
                    tile_id=self._as_str(raw_tile.get("tile_id", "")),
                    x=self._as_int(raw_tile.get("x", 0)),
                    y=self._as_int(raw_tile.get("y", 0)),
                    width=self._as_int(raw_tile.get("width", 0)),
                    height=self._as_int(raw_tile.get("height", 0)),
                    level=self._as_int(raw_tile.get("level", 0)),
                    magnification=self._as_float(raw_tile.get("magnification", 0.0)),
                    tissue_ratio=self._as_float(raw_tile.get("tissue_ratio", 0.0)),
                    file_path=self._as_str(raw_tile.get("file_path", "")),
                )
            )

        raw_available_mags = payload.get("available_magnifications", [])
        available_magnifications: list[float] = []
        if isinstance(raw_available_mags, list):
            for value in raw_available_mags:
                if isinstance(value, (int, float)):
                    available_magnifications.append(float(value))

        raw_tile_size = payload.get("tile_size", [0, 0])
        tile_size: tuple[int, int]
        if (
            isinstance(raw_tile_size, list)
            and len(raw_tile_size) == 2
            and isinstance(raw_tile_size[0], (int, float))
            and isinstance(raw_tile_size[1], (int, float))
        ):
            tile_size = (int(raw_tile_size[0]), int(raw_tile_size[1]))
        else:
            tile_size = (0, 0)

        raw_dimensions = payload.get("dimensions", [0, 0])
        dimensions: tuple[int, int]
        if (
            isinstance(raw_dimensions, list)
            and len(raw_dimensions) == 2
            and isinstance(raw_dimensions[0], (int, float))
            and isinstance(raw_dimensions[1], (int, float))
        ):
            dimensions = (int(raw_dimensions[0]), int(raw_dimensions[1]))
        else:
            dimensions = (0, 0)

        return SlideMetadata(
            slide_id=self._as_str(payload.get("slide_id", slide_id)),
            slide_name=self._as_str(payload.get("slide_name", "")),
            slide_path=self._as_str(payload.get("slide_path", "")),
            total_tiles=self._as_int(payload.get("total_tiles", len(tiles))),
            dimensions=dimensions,
            mpp=self._as_float(payload.get("mpp", 0.0)),
            available_magnifications=available_magnifications,
            tile_size=tile_size,
            tiler_name=self._as_str(payload.get("tiler_name", "")),
            timestamp=self._as_str(payload.get("timestamp", "")),
            tiles=tiles,
        )

    @staticmethod
    def _write_json(path: Path, payload: JsonValue) -> None:
        # Keep metadata human-readable while using faster serialization.
        serialized = orjson.dumps(payload, option=orjson.OPT_INDENT_2)
        path.write_bytes(serialized)

    @staticmethod
    def _read_json(path: Path) -> JsonValue:
        return cast(JsonValue, orjson.loads(path.read_bytes()))

    @staticmethod
    def _as_int(value: JsonValue) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        return 0

    @staticmethod
    def _as_float(value: JsonValue) -> float:
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    @staticmethod
    def _as_str(value: JsonValue) -> str:
        if isinstance(value, str):
            return value
        return ""
