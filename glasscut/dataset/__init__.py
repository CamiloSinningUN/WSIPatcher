"""Dataset generation module.

High-level orchestration for multi-slide tile extraction with parallel processing,
storage organization, and comprehensive metadata tracking.

Main Classes:
    - DatasetGenerator: Main orchestrator for dataset generation
    - DatasetConfig: Configuration for dataset generation

Example:
    >>> from glasscut import DatasetGenerator, DatasetConfig
    >>> config = DatasetConfig(
    ...     dataset_id="histopath_dataset",
    ...     output_dir="./datasets",
    ...     tile_size=(512, 512),
    ...     tiler="grid",
    ...     tiler_params={"overlap": 50},
    ...     num_workers=4
    ... )
    >>> generator = DatasetGenerator(config)
    >>> dataset_meta = generator.process_dataset([
    ...     "slide_001.svs",
    ...     "slide_002.svs",
    ... ])
"""

from .config import DatasetConfig
from .generator import DatasetGenerator

__all__ = [
    "DatasetConfig",
    "DatasetGenerator",
]
