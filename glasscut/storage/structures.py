"""Storage metadata models for generated datasets."""

from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import TypeAlias, cast

JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]


@dataclass
class TileMetadata:
    """Metadata for a single extracted tile."""

    tile_id: str
    x: int
    y: int
    width: int
    height: int
    level: int
    magnification: float
    tissue_ratio: float
    file_path: str


@dataclass
class SlideMetadata:
    """Metadata for a processed slide and all generated tiles."""

    slide_id: str
    slide_name: str
    slide_path: str
    total_tiles: int
    dimensions: tuple[int, int]
    mpp: float
    available_magnifications: list[float]
    tile_size: tuple[int, int]
    tiler_name: str
    timestamp: str
    tiles: list[TileMetadata] = field(default_factory=lambda: list[TileMetadata]())


@dataclass
class DatasetMetadata:
    """Top-level metadata for a generated dataset."""

    dataset_id: str
    created_at: str
    total_slides: int
    total_tiles: int
    config: dict[str, JsonValue] = field(default_factory=lambda: dict[str, JsonValue]())
    slides: list[SlideMetadata] = field(default_factory=lambda: list[SlideMetadata]())


def dataclass_to_dict(obj: object) -> JsonValue:
    """Recursively convert dataclasses, tuples, and paths into JSON-safe objects."""
    if is_dataclass(obj) and not isinstance(obj, type):
        result: dict[str, JsonValue] = {}
        for data_field in fields(obj):
            result[data_field.name] = dataclass_to_dict(getattr(obj, data_field.name))
        return result

    if isinstance(obj, Path):
        return str(obj)

    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj

    if isinstance(obj, tuple):
        tuple_obj = cast(tuple[object, ...], obj)
        return [dataclass_to_dict(value) for value in tuple_obj]

    if isinstance(obj, list):
        list_obj = cast(list[object], obj)
        return [dataclass_to_dict(value) for value in list_obj]

    if isinstance(obj, dict):
        dict_obj = cast(dict[object, object], obj)
        return {str(key): dataclass_to_dict(value) for key, value in dict_obj.items()}

    raise TypeError(
        f"Unsupported metadata type for serialization: {type(obj).__name__}"
    )
