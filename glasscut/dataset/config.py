"""Dataset generation configuration.

Configuration models for dataset generation, specifying how to process slides
and extract tiles.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class DatasetConfig:
    """Configuration for dataset generation.

    Controls all aspects of the tile extraction process including tiling strategy,
    tile sizes, output organization, and processing options.

    Parameters
    ----------
    dataset_id : str
        Unique identifier for the dataset
    output_dir : str
        Root directory where output will be stored
    tile_size : Tuple[int, int], optional
        Size of tiles to extract (width, height) in pixels. Default is (512, 512).
    magnification : int | float, optional
        Target magnification for extraction. Default is 20x.
    overlap : int, optional
        Overlap between tiles in pixels (for GridTiler). Default is 0.
    tiler : str, optional
        Type of tiler to use: 'grid', 'random', or 'conditional'.
        Default is 'grid'.
    tiler_params : Dict, optional
        Additional parameters for tiler. For example:
        - GridTiler: {'overlap': 50, 'min_tissue_ratio': 0.5}
        - RandomTiler: {'num_tiles': 100, 'seed': 42}
        - ConditionalTiler: {'min_tissue_in_tile': 0.5}
        Default is None (use tiler defaults).
    save_thumbnails : bool, optional
        Whether to save slide thumbnails. Default is True.
    save_masks : bool, optional
        Whether to save tissue masks. Default is True.
    save_processed_json : bool, optional
        Whether to save processed.json tracking successfully processed slides.
        Default is True.
    num_workers : int, optional
        Number of parallel workers for slide processing. Set to 1 for sequential.
        Default is 4.
    verbose : bool, optional
        Enable verbose logging. Default is True.

    Attributes
    ----------
    tile_size : tuple[int, int]
        Tile dimensions
    magnification : float
        Magnification level
    overlap : int
        Tile overlap
    tiler : str
        Tiler strategy name
    tiler_params : dict
        Tiler-specific parameters
    """

    # Required
    dataset_id: str
    output_dir: str

    # Tile extraction parameters
    tile_size: tuple[int, int] = field(default=(512, 512))
    magnification: int | float = field(default=20)
    overlap: int = field(default=0)

    # Tiler strategy
    tiler: str = field(default="grid")  # 'grid', 'random', 'conditional'
    tiler_params: Dict = field(default_factory=dict)

    # Output options
    save_thumbnails: bool = field(default=True)
    save_masks: bool = field(default=True)
    save_processed_json: bool = field(default=True)

    # Processing options
    num_workers: int = field(default=4)
    verbose: bool = field(default=True)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.dataset_id is None or not self.dataset_id:
            raise ValueError("dataset_id is required")

        if self.output_dir is None or not self.output_dir:
            raise ValueError("output_dir is required")

        if self.tile_size[0] <= 0 or self.tile_size[1] <= 0:
            raise ValueError(f"tile_size must be positive, got {self.tile_size}")

        if self.magnification <= 0:
            raise ValueError(
                f"magnification must be positive, got {self.magnification}"
            )

        if self.overlap < 0:
            raise ValueError(f"overlap must be >= 0, got {self.overlap}")

        if self.tiler not in ("grid", "random", "conditional"):
            raise ValueError(
                f"tiler must be 'grid', 'random', or 'conditional', got {self.tiler}"
            )

        if self.num_workers < 1:
            raise ValueError(f"num_workers must be >= 1, got {self.num_workers}")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"DatasetConfig(dataset_id={self.dataset_id!r}, "
            f"tiler={self.tiler}, tile_size={self.tile_size}, "
            f"magnification={self.magnification}x, "
            f"num_workers={self.num_workers})"
        )
