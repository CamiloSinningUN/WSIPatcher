"""
Example: Complete Dataset Generation Workflow

This example demonstrates how to use GlassCut's DatasetGenerator to process
multiple whole slide images (WSI) into an organized dataset with tiles,
thumbnails, masks, and comprehensive metadata.

Features demonstrated:
- Single slide extraction
- Multi-slide batch processing
- Parallel processing with multiple workers
- Different tiling strategies (Grid, Random, Conditional)
- Storage organization (PathoPatcher-compatible format)
- Metadata management (JSON files)

Output structure:
    output/
    ├── metadata.json              # Dataset-level metadata
    ├── processed.json             # List of processed slides
    ├── Slide_000/
    │   ├── tiles/                 # Extracted tile PNG files
    │   │   ├── tile_0000000.png
    │   │   ├── tile_0000001.png
    │   │   └── ...
    │   ├── thumbnails/
    │   │   ├── slide_thumbnail.png
    │   │   └── mask_thumbnail.png
    │   ├── masks/
    │   │   └── tissue_mask.png
    │   └── slide_metadata.json    # Per-slide metadata
    └── Slide_001/
        └── (same structure)
"""

from pathlib import Path
from glasscut import DatasetGenerator, DatasetConfig


def example_simple_grid_tiling():
    """Example 1: Simple grid tiling of a single slide."""
    print("\n" + "=" * 70)
    print("Example 1: Simple Grid Tiling")
    print("=" * 70)

    # Configuration
    config = DatasetConfig(
        dataset_id="simple_grid_dataset",
        output_dir="./datasets/example_output",
        tile_size=(512, 512),
        magnification=20,
        tiler="grid",
        tiler_params={
            "overlap": 50,
            "min_tissue_ratio": 0.3,  # Skip mostly empty tiles
        },
        num_workers=1,  # Sequential for this example
        verbose=True,
    )

    # Create generator
    generator = DatasetGenerator(config)

    # Process slide(s)
    # In real usage, provide actual WSI files
    slide_paths = [
        "/path/to/slide_001.svs",
        "/path/to/slide_002.svs",
    ]

    try:
        dataset_meta = generator.process_dataset(slide_paths)

        print(f"\n✓ Dataset generated successfully!")
        print(f"  - Slides processed: {dataset_meta.total_slides}")
        print(f"  - Total tiles: {dataset_meta.total_tiles}")
        print(f"  - Output directory: {config.output_dir}")

    except FileNotFoundError as e:
        print(f"\n! Slide files not found (expected for example): {e}")
        print("  To run this example, provide real WSI file paths")


def example_random_sampling():
    """Example 2: Random sampling strategy."""
    print("\n" + "=" * 70)
    print("Example 2: Random Sampling Strategy")
    print("=" * 70)

    config = DatasetConfig(
        dataset_id="random_sampling_dataset",
        output_dir="./datasets/example_output",
        tile_size=(256, 256),  # Smaller tiles
        magnification=40,  # Higher magnification
        tiler="random",
        tiler_params={
            "num_tiles": 50,  # Extract exactly 50 tiles per slide
            "seed": 42,  # Reproducible
            "min_tissue_ratio": 0.5,
        },
        num_workers=1,
        verbose=True,
    )

    generator = DatasetGenerator(config)
    slide_paths = ["/path/to/slide.svs"]

    try:
        dataset_meta = generator.process_dataset(slide_paths)
        print(f"\n✓ Random sampling complete: {dataset_meta.total_tiles} tiles")
    except FileNotFoundError:
        print("\n! Slide file not found (expected for example)")


def example_parallel_processing():
    """Example 3: Parallel processing with multiple workers."""
    print("\n" + "=" * 70)
    print("Example 3: Parallel Processing (Multiple Workers)")
    print("=" * 70)

    config = DatasetConfig(
        dataset_id="parallel_dataset",
        output_dir="./datasets/example_output",
        tile_size=(512, 512),
        magnification=20,
        tiler="grid",
        tiler_params={"overlap": 50},
        num_workers=4,  # Use 4 parallel workers
        save_thumbnails=True,
        save_masks=True,
        verbose=True,
    )

    generator = DatasetGenerator(config)

    # Process multiple slides in parallel
    slide_paths = [
        f"/path/to/slide_{i:03d}.svs"
        for i in range(10)  # 10 slides
    ]

    try:
        dataset_meta = generator.process_dataset(slide_paths)
        print(f"\n✓ Parallel processing complete!")
        print(
            f"  - Tiles/slide: {dataset_meta.total_tiles // len(dataset_meta.slides):.0f}"
        )
    except FileNotFoundError:
        print("\n! Slide files not found (expected for example)")


def example_tissue_aware_tiling():
    """Example 4: Tissue-aware conditional tiling."""
    print("\n" + "=" * 70)
    print("Example 4: Tissue-Aware Conditional Tiling")
    print("=" * 70)

    # This strategy only extracts tiles that have sufficient tissue content
    config = DatasetConfig(
        dataset_id="tissue_aware_dataset",
        output_dir="./datasets/example_output",
        tile_size=(512, 512),
        magnification=20,
        tiler="conditional",
        tiler_params={
            "overlap": 0,
            "min_tissue_in_tile": 0.8,  # At least 80% tissue in tile
        },
        num_workers=2,
        verbose=True,
    )

    generator = DatasetGenerator(config)
    slide_paths = ["/path/to/slide.svs"]

    try:
        dataset_meta = generator.process_dataset(slide_paths)
        print(f"\n✓ Tissue-aware tiling complete")
    except FileNotFoundError:
        print("\n! Slide file not found (expected for example)")


def example_custom_configuration():
    """Example 5: Highly customized configuration."""
    print("\n" + "=" * 70)
    print("Example 5: Custom Configuration")
    print("=" * 70)

    config = DatasetConfig(
        dataset_id="custom_workflow_v2",
        output_dir="./datasets/histopathology_study",
        # Tile parameters
        tile_size=(768, 768),  # Large tiles
        magnification=10,  # Low magnification
        overlap=100,
        # Tiling strategy
        tiler="grid",
        tiler_params={
            "min_tissue_ratio": 0.2,
            "save_empty": False,
        },
        # Output artifacts
        save_thumbnails=True,
        save_masks=True,
        save_processed_json=True,
        # Processing
        num_workers=8,  # Aggressive parallelism
        verbose=True,
    )

    print(f"\nConfiguration:\n{config}")
    print(f"\nOutput directory: {Path(config.output_dir).resolve()}")


def print_metadata_structure():
    """Show the structure of generated metadata."""
    print("\n" + "=" * 70)
    print("Generated Metadata Structure")
    print("=" * 70)

    print("""
Dataset JSON File (metadata.json):
{
  "dataset_id": "my_dataset",
  "created_at": "2024-01-15T10:30:00.123456",
  "total_slides": 2,
  "total_tiles": 8432,
  "config": { ... },
  "slides": [
    {
      "slide_id": "Slide_000",
      "slide_name": "patient_001_biopsy",
      "slide_path": "/path/to/slide_001.svs",
      "total_tiles": 4200,
      "dimensions": [50000, 45000],
      "mpp": 0.499,
      "magnification": 20.0,
      "tile_size": [512, 512],
      "tiler_name": "GridTiler",
      "timestamp": "2024-01-15T10:30:05.123456",
      "tiles": [
        {
          "tile_id": "tile_0000000",
          "x": 0, "y": 0,
          "width": 512, "height": 512,
          "level": 0,
          "magnification": 20.0,
          "tissue_ratio": 0.95,
          "file_path": "my_dataset/Slide_000/tiles/tile_0000000.png"
        },
        ...
      ]
    }
  ]
}

Per-Slide JSON File (slide_metadata.json):
{
  "slide_id": "Slide_000",
  "total_tiles": 4200,
  ...
}

Processed JSON File (processed.json):
{
  "processed_files": ["Slide_000", "Slide_001"],
  "timestamp": "2024-01-15T10:35:00.123456",
  "total": 2
}
    """)


if __name__ == "__main__":
    print("\n" + "#" * 70)
    print("# GlassCut Dataset Generation Examples")
    print("# Demonstrates tiling strategies and batch processing")
    print("#" * 70)

    # Run examples
    example_simple_grid_tiling()
    example_random_sampling()
    example_parallel_processing()
    example_tissue_aware_tiling()
    example_custom_configuration()
    print_metadata_structure()

    print("\n" + "#" * 70)
    print("# Examples Complete!")
    print("# See code for more details and configuration options")
    print("#" * 70 + "\n")
