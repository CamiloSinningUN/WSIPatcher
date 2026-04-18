# HistoLab Usage Examples

**Purpose**: Production-ready HistoLab examples for common histopathology workflows  
**Complexity**: Beginner to Advanced  
**Dependencies**: histolab, numpy, pillow, scikit-image

---

## Table of Contents

1. [Example 1: Basic Tile Extraction](#example-1-basic-tile-extraction)
2. [Example 2: Preprocessing Pipeline](#example-2-preprocessing-pipeline)
3. [Example 3: Quality-Based Tile Selection](#example-3-quality-based-tile-selection)
4. [Example 4: Stain Normalization](#example-4-stain-normalization)
5. [Example 5: Batch Processing](#example-5-batch-processing-multiple-slides)
6. [Example 6: Custom Mask Strategy](#example-6-custom-mask-strategy)
7. [Example 7: Advanced Filter Composition](#example-7-advanced-filter-composition)
8. [Example 8: Tissue Detection & Visualization](#example-8-tissue-detection--visualization)
9. [Example 9: Custom Scorer Implementation](#example-9-custom-scorer-implementation)
10. [Example 10: End-to-End Pipeline](#example-10-end-to-end-production-pipeline)

---

## Example 1: Basic Tile Extraction

**Use Case**: Extract tiles from a single slide at fixed size  
**Complexity**: Beginner  
**Output**: PNG tiles saved to output directory

```python
"""
Example 1: Basic Tile Extraction
Extract tiles from a WSI file with minimal configuration
"""

from histolab.slides import Slide
from pathlib import Path
from PIL import Image
import numpy as np

def extract_tiles_basic(slide_path: str, output_dir: str, tile_size: int = 512):
    """
    Extract tiles from WSI using grid pattern.
    
    Args:
        slide_path: Path to .svs or other WSI format
        output_dir: Output directory for tiles
        tile_size: Tile dimensions in pixels
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize slide
    slide = Slide(
        path=slide_path,
        processed_path=str(output_path)
    )
    
    print(f"Slide dimensions: {slide.size}")
    print(f"Slide MPP: {slide.base_mpp}")
    print(f"Pyramid levels: {len(slide.level_dimensions)}")
    
    # Extract tiles in grid pattern
    tile_count = 0
    step = tile_size  # Non-overlapping
    
    for y in range(0, slide.size[1], step):
        for x in range(0, slide.size[0], step):
            # Adjust edge tiles
            w = min(tile_size, slide.size[0] - x)
            h = min(tile_size, slide.size[1] - y)
            
            if w < tile_size // 2 or h < tile_size // 2:
                continue  # Skip edges
            
            try:
                # Read tile region
                tile_image = slide.read_region(
                    coordinates=(x, y),
                    level=0,
                    size=(w, h)
                )
                
                # Save
                tile_path = output_path / f"tile_{tile_count:06d}.png"
                tile_image.save(tile_path)
                
                tile_count += 1
                
                if tile_count % 100 == 0:
                    print(f"  Extracted {tile_count} tiles...")
                    
            except Exception as e:
                print(f"  Error at ({x}, {y}): {e}")
    
    print(f"Total tiles extracted: {tile_count}")
    return tile_count


# Usage
if __name__ == "__main__":
    extract_tiles_basic(
        slide_path="/data/sample.svs",
        output_dir="/output/tiles",
        tile_size=512
    )
```

---

## Example 2: Preprocessing Pipeline

**Use Case**: Apply consistent image preprocessing to tiles  
**Complexity**: Intermediate  
**Output**: Preprocessed tiles after filtering

```python
"""
Example 2: Preprocessing Pipeline
Apply filters to normalize and enhance tissue images
"""

from histolab.slides import Slide
from histolab.filters import Compose, RgbToGrayscale, OtsuThreshold
from histolab.filters.morphological_filters import RemoveSmallObjects, RemoveSmallHoles
from PIL import Image
import numpy as np
from pathlib import Path

class HistopathologyPreprocessor:
    """Pipeline for preprocessing histopathology images"""
    
    def __init__(self):
        """Initialize preprocessing pipeline"""
        self.pipeline = Compose([
            RgbToGrayscale(),              # Convert RGB to grayscale
            OtsuThreshold(),                # Automatic thresholding
            RemoveSmallObjects(             # Remove noise
                min_size=3000,
                avoid_overmask=True,
                overmask_thresh=95
            ),
            RemoveSmallHoles(              # Fill small gaps
                area_threshold=2000
            ),
        ])
    
    def preprocess(self, image: Image.Image) -> Image.Image:
        """
        Apply preprocessing pipeline to image
        
        Args:
            image: PIL Image
            
        Returns:
            Preprocessed PIL Image
        """
        return self.pipeline(image)
    
    def batch_preprocess_tiles(self, input_dir: str, output_dir: str):
        """
        Preprocess all tiles in a directory
        
        Args:
            input_dir: Directory containing original tiles
            output_dir: Directory for preprocessed tiles
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Process all PNG files
        tile_files = list(input_path.glob("*.png"))
        print(f"Found {len(tile_files)} tiles to process")
        
        for i, tile_file in enumerate(tile_files):
            try:
                # Load tile
                tile = Image.open(tile_file)
                
                # Preprocess
                processed = self.preprocess(tile)
                
                # Save
                output_file = output_path / tile_file.name
                processed.save(output_file)
                
                if (i + 1) % 50 == 0:
                    print(f"  Processed {i + 1}/{len(tile_files)} tiles")
                    
            except Exception as e:
                print(f"  Error processing {tile_file.name}: {e}")
        
        print(f"Preprocessing complete!")


# Usage
if __name__ == "__main__":
    preprocessor = HistopathologyPreprocessor()
    
    # Option 1: Single image
    image = Image.open("/data/sample_tile.png")
    processed = preprocessor.preprocess(image)
    processed.save("/output/processed_tile.png")
    
    # Option 2: Batch processing
    preprocessor.batch_preprocess_tiles(
        input_dir="/output/tiles",
        output_dir="/output/tiles_preprocessed"
    )
```

---

## Example 3: Quality-Based Tile Selection

**Use Case**: Extract only tiles meeting tissue quality thresholds  
**Complexity**: Intermediate  
**Output**: Only high-quality tiles saved

```python
"""
Example 3: Quality-Based Tile Selection
Filter tiles based on tissue content and scoring
"""

from histolab.slides import Slide
from histolab.tiles import Tile
from histolab.scorer import CellularityScorer, RandomScorer
from histolab.filters.compositions import FiltersComposition
from pathlib import Path
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class TileQualityMetrics:
    """Metrics for tile quality assessment"""
    tissue_ratio: float
    cellularity_score: float
    passed: bool


class QualityTileExtractor:
    """Extract tiles with quality control"""
    
    def __init__(
        self,
        tissue_threshold: float = 0.75,
        cellularity_threshold: float = 0.6
    ):
        """
        Initialize extractor with quality thresholds
        
        Args:
            tissue_threshold: Minimum tissue ratio (0-1)
            cellularity_threshold: Minimum cellularity score (0-1)
        """
        self.tissue_threshold = tissue_threshold
        self.cellularity_threshold = cellularity_threshold
        self.scorer = CellularityScorer()
        self.preprocessor = FiltersComposition.of(Tile)  # Default Tile filters
        self.metrics: List[TileQualityMetrics] = []
    
    def assess_tile_quality(self, tile: Tile) -> TileQualityMetrics:
        """
        Assess whether tile meets quality criteria
        
        Args:
            tile: Tile object to assess
            
        Returns:
            TileQualityMetrics with assessment results
        """
        # Preprocess
        processed = tile.apply_filters(self.preprocessor)
        
        # Check tissue content
        tissue_ratio = processed.tissue_ratio
        
        # Score cellularity
        cellularity = self.scorer.score(tile)
        
        # Determine if passes
        passed = (
            tissue_ratio >= self.tissue_threshold and
            cellularity >= self.cellularity_threshold
        )
        
        metrics = TileQualityMetrics(
            tissue_ratio=tissue_ratio,
            cellularity_score=cellularity,
            passed=passed
        )
        
        self.metrics.append(metrics)
        return metrics
    
    def extract_quality_tiles(
        self,
        slide_path: str,
        output_dir: str,
        tile_size: int = 512
    ) -> Tuple[int, int]:
        """
        Extract tiles meeting quality criteria
        
        Args:
            slide_path: Path to WSI
            output_dir: Output directory for tiles
            tile_size: Tile dimensions
            
        Returns:
            (total_extracted, total_quality)
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        slide = Slide(
            path=slide_path,
            processed_path=str(output_path)
        )
        
        total_extracted = 0
        total_quality = 0
        
        # Extract grid of tiles
        step = tile_size
        
        for y in range(0, slide.size[1], step):
            for x in range(0, slide.size[0], step):
                w = min(tile_size, slide.size[0] - x)
                h = min(tile_size, slide.size[1] - y)
                
                if w < tile_size // 2 or h < tile_size // 2:
                    continue
                
                try:
                    # Read tile
                    tile_image = slide.read_region(
                        coordinates=(x, y),
                        level=0,
                        size=(w, h)
                    )
                    
                    # Create Tile object
                    from histolab.types import CoordinatePair
                    tile = Tile(
                        image=tile_image,
                        coords=CoordinatePair(x=x, y=y),
                        level=0,
                        slide=slide
                    )
                    
                    total_extracted += 1
                    
                    # Assess quality
                    metrics = self.assess_tile_quality(tile)
                    
                    if metrics.passed:
                        total_quality += 1
                        tile_path = output_path / f"quality_tile_{total_quality:06d}.png"
                        tile_image.save(tile_path)
                        
                except Exception as e:
                    print(f"Error at ({x}, {y}): {e}")
        
        return total_extracted, total_quality
    
    def print_statistics(self):
        """Print quality assessment statistics"""
        if not self.metrics:
            print("No metrics collected")
            return
        
        tissue_ratios = [m.tissue_ratio for m in self.metrics]
        cellularity_scores = [m.cellularity_score for m in self.metrics]
        passed_count = sum(1 for m in self.metrics if m.passed)
        
        print("Quality Assessment Statistics:")
        print(f"  Total tiles: {len(self.metrics)}")
        print(f"  Passed quality: {passed_count} ({100*passed_count/len(self.metrics):.1f}%)")
        print(f"  Tissue ratio: {np.mean(tissue_ratios):.3f} ± {np.std(tissue_ratios):.3f}")
        print(f"  Cellularity: {np.mean(cellularity_scores):.3f} ± {np.std(cellularity_scores):.3f}")


# Usage
if __name__ == "__main__":
    extractor = QualityTileExtractor(
        tissue_threshold=0.8,
        cellularity_threshold=0.6
    )
    
    total, quality = extractor.extract_quality_tiles(
        slide_path="/data/sample.svs",
        output_dir="/output/quality_tiles",
        tile_size=512
    )
    
    print(f"Extracted {total} tiles, {quality} meeting quality criteria")
    extractor.print_statistics()
```

---

## Example 4: Stain Normalization

**Use Case**: Normalize color variations across different slides/scanners  
**Complexity**: Intermediate  
**Output**: Color-normalized tiles

```python
"""
Example 4: Stain Normalization
Normalize histological stains across multiple slides
"""

from histolab.slides import Slide
from histolab.stain_normalizer import StainNormalizer
from histolab.util import np_to_pil
import numpy as np
from pathlib import Path
from typing import Optional

class StainNormalizationPipeline:
    """Normalize stains across dataset"""
    
    def __init__(self, reference_slide_path: str, processed_path: str):
        """
        Initialize with reference slide
        
        Args:
            reference_slide_path: Path to reference slide
            processed_path: Output directory for processing
        """
        self.reference_slide = Slide(
            path=reference_slide_path,
            processed_path=processed_path
        )
        self.normalizer = StainNormalizer()
        self._reference_fitted = False
    
    def fit_reference(self, region_coords: tuple = (0, 0), size: tuple = (2048, 2048)):
        """
        Learn normalization parameters from reference slide region
        
        Args:
            region_coords: (x, y) coordinates to read
            size: (width, height) of region
        """
        # Read reference region
        ref_image = self.reference_slide.read_region(
            coordinates=region_coords,
            level=0,
            size=size
        )
        
        # Convert to numpy
        ref_array = np.array(ref_image.convert('RGB'))
        
        # Fit normalizer
        self.normalizer.fit(ref_array)
        self._reference_fitted = True
        
        print(f"Reference fitted from {self.reference_slide._path}")
    
    def normalize_slide(
        self,
        slide_path: str,
        output_dir: str,
        tile_size: int = 512
    ):
        """
        Extract tiles from slide and normalize stains
        
        Args:
            slide_path: Path to slide to normalize
            output_dir: Output directory for normalized tiles
            tile_size: Tile dimensions
        """
        if not self._reference_fitted:
            raise RuntimeError("Reference not fitted. Call fit_reference() first.")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        target_slide = Slide(
            path=slide_path,
            processed_path=str(output_path)
        )
        
        print(f"Processing {Path(slide_path).name}...")
        
        tile_count = 0
        step = tile_size
        
        for y in range(0, target_slide.size[1], step):
            for x in range(0, target_slide.size[0], step):
                w = min(tile_size, target_slide.size[0] - x)
                h = min(tile_size, target_slide.size[1] - y)
                
                if w < tile_size // 2 or h < tile_size // 2:
                    continue
                
                try:
                    # Read tile
                    tile_image = target_slide.read_region(
                        coordinates=(x, y),
                        level=0,
                        size=(w, h)
                    )
                    
                    # Convert to numpy
                    tile_array = np.array(tile_image.convert('RGB'))
                    
                    # Normalize
                    normalized_array = self.normalizer.transform(tile_array)
                    
                    # Convert back to PIL
                    normalized_image = np_to_pil(normalized_array)
                    
                    # Save
                    tile_path = output_path / f"normalized_tile_{tile_count:06d}.png"
                    normalized_image.save(tile_path)
                    
                    tile_count += 1
                    
                    if tile_count % 50 == 0:
                        print(f"  Processed {tile_count} tiles...")
                    
                except Exception as e:
                    print(f"  Error at ({x}, {y}): {e}")
        
        print(f"  Total normalized tiles: {tile_count}")
        return tile_count
    
    def batch_normalize(
        self,
        slides_dir: str,
        output_base_dir: str,
        pattern: str = "*.svs"
    ):
        """
        Normalize multiple slides
        
        Args:
            slides_dir: Directory containing slide files
            output_base_dir: Base output directory
            pattern: File pattern to match
        """
        slides_path = Path(slides_dir)
        output_base = Path(output_base_dir)
        
        slide_files = list(slides_path.glob(pattern))
        print(f"Found {len(slide_files)} slides to process")
        
        results = {}
        for slide_file in slide_files:
            try:
                output_dir = output_base / slide_file.stem
                tile_count = self.normalize_slide(
                    str(slide_file),
                    str(output_dir)
                )
                results[slide_file.name] = tile_count
            except Exception as e:
                print(f"Failed to process {slide_file.name}: {e}")
        
        # Summary
        print("\nProcessing Summary:")
        for slide_name, count in results.items():
            print(f"  {slide_name}: {count} tiles")


# Usage
if __name__ == "__main__":
    pipeline = StainNormalizationPipeline(
        reference_slide_path="/data/reference.svs",
        processed_path="/tmp"
    )
    
    # Fit to reference
    pipeline.fit_reference(
        region_coords=(0, 0),
        size=(2048, 2048)
    )
    
    # Option 1: Single slide
    pipeline.normalize_slide(
        slide_path="/data/target.svs",
        output_dir="/output/normalized",
        tile_size=512
    )
    
    # Option 2: Batch processing
    pipeline.batch_normalize(
        slides_dir="/data/slides",
        output_base_dir="/output/normalized_batch"
    )
```

---

## Example 5: Batch Processing Multiple Slides

**Use Case**: Process dataset of multiple slides efficiently  
**Complexity**: Intermediate  
**Output**: Organized tiles from all slides

```python
"""
Example 5: Batch Processing Multiple Slides
Process all slides in a directory with progress tracking
"""

from histolab.slides import Slide
from pathlib import Path
import logging
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProcessingResult:
    """Result of processing one slide"""
    slide_name: str
    tiles_extracted: int
    error: Optional[str] = None
    processing_time: float = 0.0


class BatchTileProcessing:
    """Batch process multiple WSI files"""
    
    def __init__(self, output_base_dir: str):
        """
        Initialize batch processor
        
        Args:
            output_base_dir: Base directory for all output
        """
        self.output_base = Path(output_base_dir)
        self.output_base.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for batch processing"""
        logger = logging.getLogger("BatchTileProcessing")
        logger.setLevel(logging.INFO)
        
        # File handler
        fh = logging.FileHandler(self.output_base / "processing.log")
        fh.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        return logger
    
    def process_slide(
        self,
        slide_path: str,
        tile_size: int = 512,
        tissue_threshold: float = 0.7
    ) -> ProcessingResult:
        """
        Process single slide
        
        Args:
            slide_path: Path to WSI file
            tile_size: Tile dimensions
            tissue_threshold: Minimum tissue ratio
            
        Returns:
            ProcessingResult with status
        """
        import time
        start_time = time.time()
        
        slide_name = Path(slide_path).name
        self.logger.info(f"Starting: {slide_name}")
        
        try:
            # Create output directory
            output_dir = self.output_base / Path(slide_path).stem
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize slide
            slide = Slide(
                path=slide_path,
                processed_path=str(output_dir)
            )
            
            # Log slide info
            self.logger.info(f"  Size: {slide.size}")
            self.logger.info(f"  MPP: {slide.base_mpp}")
            
            # Extract tiles
            tile_count = 0
            step = tile_size
            
            for y in range(0, slide.size[1], step):
                for x in range(0, slide.size[0], step):
                    w = min(tile_size, slide.size[0] - x)
                    h = min(tile_size, slide.size[1] - y)
                    
                    if w < tile_size // 2 or h < tile_size // 2:
                        continue
                    
                    try:
                        tile_image = slide.read_region(
                            coordinates=(x, y),
                            level=0,
                            size=(w, h)
                        )
                        
                        # Save tile
                        tile_path = output_dir / f"tile_{tile_count:06d}.png"
                        tile_image.save(tile_path)
                        
                        tile_count += 1
                        
                    except Exception as e:
                        self.logger.warning(f"  Error at ({x}, {y}): {e}")
            
            processing_time = time.time() - start_time
            self.logger.info(f"Completed: {slide_name} - {tile_count} tiles in {processing_time:.1f}s")
            
            return ProcessingResult(
                slide_name=slide_name,
                tiles_extracted=tile_count,
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"Failed: {slide_name} - {e}")
            return ProcessingResult(
                slide_name=slide_name,
                tiles_extracted=0,
                error=str(e)
            )
    
    def batch_process(
        self,
        slides_dir: str,
        pattern: str = "*.svs",
        tile_size: int = 512
    ) -> List[ProcessingResult]:
        """
        Process all slides in directory
        
        Args:
            slides_dir: Directory containing slides
            pattern: File pattern to match
            tile_size: Tile dimensions
            
        Returns:
            List of processing results
        """
        slides_path = Path(slides_dir)
        slide_files = sorted(slides_path.glob(pattern))
        
        self.logger.info(f"Processing {len(slide_files)} slides from {slides_dir}")
        
        results = []
        for i, slide_file in enumerate(slide_files):
            self.logger.info(f"[{i+1}/{len(slide_files)}] Processing {slide_file.name}")
            
            result = self.process_slide(
                slide_path=str(slide_file),
                tile_size=tile_size
            )
            results.append(result)
        
        # Summary
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: List[ProcessingResult]):
        """Print summary statistics"""
        self.logger.info("\n" + "="*60)
        self.logger.info("BATCH PROCESSING SUMMARY")
        self.logger.info("="*60)
        
        total_slides = len(results)
        successful = sum(1 for r in results if r.error is None)
        total_tiles = sum(r.tiles_extracted for r in results)
        total_time = sum(r.processing_time for r in results)
        
        self.logger.info(f"Total slides: {total_slides}")
        self.logger.info(f"Successful: {successful}/{total_slides}")
        self.logger.info(f"Total tiles extracted: {total_tiles}")
        self.logger.info(f"Total processing time: {total_time:.1f}s")
        
        if successful > 0:
            avg_tiles = total_tiles / successful
            self.logger.info(f"Average tiles per slide: {avg_tiles:.1f}")
        
        # List failures
        failures = [r for r in results if r.error is not None]
        if failures:
            self.logger.info("\nFAILED SLIDES:")
            for result in failures:
                self.logger.info(f"  {result.slide_name}: {result.error}")


# Usage
if __name__ == "__main__":
    processor = BatchTileProcessing(
        output_base_dir="/output/batch_processing"
    )
    
    results = processor.batch_process(
        slides_dir="/data/slides",
        pattern="*.svs",
        tile_size=512
    )
    
    print(f"Processed {len(results)} slides")
    successful = sum(1 for r in results if r.error is None)
    print(f"Success rate: {100*successful/len(results):.1f}%")
```

---

## Example 6: Custom Mask Strategy

**Use Case**: Implement domain-specific tissue detection  
**Complexity**: Advanced  
**Output**: Custom tissue masks

```python
"""
Example 6: Custom Mask Strategy
Implement and use custom tissue detection strategy
"""

from histolab.masks import BinaryMask
from histolab.slides import Slide
import numpy as np
from skimage.filters import threshold_local, threshold_otsu
from scipy import ndimage
from pathlib import Path
from PIL import Image

class AdaptiveThresholdMask(BinaryMask):
    """Custom mask using local adaptive thresholding"""
    
    def __init__(self, window_size: int = 51, tissue_threshold: float = 0.7):
        """
        Initialize adaptive threshold mask
        
        Args:
            window_size: Local window size (must be odd)
            tissue_threshold: Fraction of image that can be tissue
        """
        if window_size % 2 == 0:
            window_size += 1
        self.window_size = window_size
        self.tissue_threshold = tissue_threshold
    
    def get_mask(self, slide: Slide) -> np.ndarray:
        """
        Generate tissue mask using adaptive thresholding
        
        Args:
            slide: Slide object
            
        Returns:
            Binary numpy array (1 = tissue, 0 = background)
        """
        # Get low-res image for speed
        region = slide.read_region(
            coordinates=(0, 0),
            level=4,  # Low resolution
            size=(2048, 2048)
        )
        
        # Convert to grayscale
        gray = region.convert('L')
        gray_array = np.array(gray)
        
        # Apply local threshold
        local_threshold = threshold_local(
            gray_array,
            block_size=self.window_size,
            method='gaussian',
            offset=0
        )
        
        # Binary mask
        mask = gray_array > local_threshold
        
        # Remove small noise
        from scipy.ndimage import binary_opening
        mask = binary_opening(mask, iterations=2)
        
        # Get largest connected component
        labeled = ndimage.label(mask)[0]
        if labeled.max() > 0:
            sizes = ndimage.sum(mask, labeled, range(labeled.max() + 1))
            largest_label = np.argmax(sizes)
            mask = labeled == largest_label
        
        # Upscale to full resolution
        # Note: In practice, you'd use proper upscaling
        scale_factor = 2 ** 4  # Match level 4
        full_mask = np.repeat(
            np.repeat(mask, scale_factor, axis=0),
            scale_factor,
            axis=1
        )
        
        return full_mask.astype(np.uint8)


class EdgeBasedMask(BinaryMask):
    """Mask based on edge detection"""
    
    def __init__(self, edge_threshold: float = 0.3):
        """
        Initialize edge-based mask
        
        Args:
            edge_threshold: Edge strength threshold
        """
        self.edge_threshold = edge_threshold
    
    def get_mask(self, slide: Slide) -> np.ndarray:
        """
        Generate mask using edge detection
        
        Args:
            slide: Slide object
            
        Returns:
            Binary numpy array
        """
        from skimage.filters import sobel
        
        # Get region
        region = slide.read_region(
            coordinates=(0, 0),
            level=3,
            size=(2048, 2048)
        )
        
        # Grayscale
        gray = region.convert('L')
        gray_array = np.array(gray, dtype=np.float32) / 255.0
        
        # Compute edges
        edges = sobel(gray_array)
        
        # Binary mask based on edge intensity
        tissue_areas = edges > self.edge_threshold
        
        # Dilate to get surrounding area
        from scipy.ndimage import binary_dilation
        tissue_mask = binary_dilation(tissue_areas, iterations=10)
        
        return tissue_mask.astype(np.uint8)


class HyridMask(BinaryMask):
    """Combine multiple mask strategies"""
    
    def __init__(self):
        """Initialize hybrid mask"""
        self.adaptive_mask = AdaptiveThresholdMask()
        self.edge_mask = EdgeBasedMask()
    
    def get_mask(self, slide: Slide) -> np.ndarray:
        """
        Combine masks using voting
        
        Args:
            slide: Slide object
            
        Returns:
            Combined binary mask
        """
        mask1 = self.adaptive_mask.get_mask(slide)
        mask2 = self.edge_mask.get_mask(slide)
        
        # Simple voting: both must agree
        combined = (mask1 > 0) & (mask2 > 0)
        
        return combined.astype(np.uint8)


def compare_mask_strategies(slide_path: str, output_dir: str):
    """
    Compare different mask strategies visually
    
    Args:
        slide_path: Path to WSI
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    slide = Slide(
        path=slide_path,
        processed_path=str(output_path)
    )
    
    # Get region for visualization
    region = slide.read_region((0, 0), 3, (2048, 2048))
    region.save(str(output_path / "original.png"))
    
    # Generate masks
    masks = {
        "adaptive": AdaptiveThresholdMask(),
        "edge_based": EdgeBasedMask(),
        "hybrid": HyridMask(),
    }
    
    print("Generating masks...")
    for name, mask_strategy in masks.items():
        try:
            mask = mask_strategy.get_mask(slide)
            
            # Visualize as white mask
            mask_image = Image.fromarray(mask * 255)
            mask_image.save(str(output_path / f"{name}_mask.png"))
            
            print(f"  {name}: Coverage = {100*mask.mean():.1f}%")
            
        except Exception as e:
            print(f"  {name}: Error - {e}")


# Usage
if __name__ == "__main__":
    # Compare strategies
    compare_mask_strategies(
        slide_path="/data/sample.svs",
        output_dir="/output/mask_comparison"
    )
    
    # Use specific strategy
    slide = Slide(
        path="/data/sample.svs",
        processed_path="/tmp"
    )
    
    mask_strategy = AdaptiveThresholdMask(window_size=51)
    tissue_mask = mask_strategy.get_mask(slide)
    
    print(f"Tissue coverage: {100*tissue_mask.mean():.1f}%")
```

---

## Example 7: Advanced Filter Composition

**Use Case**: Create custom preprocessing pipeline  
**Complexity**: Advanced  
**Output**: Specialized filter chains

```python
"""
Example 7: Advanced Filter Composition
Create and combine custom filter compositions
"""

from histolab.filters import Compose, Filter, Lambda, RgbToGrayscale, OtsuThreshold
from histolab.filters.morphological_filters import RemoveSmallObjects, RemoveSmallHoles, Dilation, Erosion
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

class HistogramEqualization:
    """Custom filter for histogram equalization"""
    
    def __call__(self, image: Image.Image) -> Image.Image:
        """Apply histogram equalization"""
        # Convert to numpy
        img_array = np.array(image.convert('L'))
        
        # Histogram equalization
        from skimage import exposure
        equalized = exposure.equalize_hist(img_array)
        
        # Convert back
        return Image.fromarray((equalized * 255).astype(np.uint8))


class ContrastEnhancement:
    """Custom filter for contrast enhancement"""
    
    def __init__(self, factor: float = 2.0):
        self.factor = factor
    
    def __call__(self, image: Image.Image) -> Image.Image:
        """Enhance contrast"""
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(self.factor)


class TexturePreservingSmoothing:
    """Smooth while preserving texture"""
    
    def __init__(self, iterations: int = 3):
        self.iterations = iterations
    
    def __call__(self, image: Image.Image) -> Image.Image:
        """Apply morphological smoothing"""
        # Convert
        img_array = np.array(image)
        
        # Morphological smoothing (open then close)
        from scipy.ndimage import binary_opening, binary_closing
        
        for _ in range(self.iterations):
            img_array = binary_closing(
                binary_opening(img_array, iterations=1),
                iterations=1
            )
        
        return Image.fromarray((img_array * 255).astype(np.uint8))


class AdvancedPreprocessing:
    """Advanced preprocessing pipeline"""
    
    @staticmethod
    def basic_cleaning() -> Compose:
        """Basic noise removal"""
        return Compose([
            RgbToGrayscale(),
            OtsuThreshold(),
            RemoveSmallObjects(min_size=2000),
            RemoveSmallHoles(area_threshold=1000),
        ])
    
    @staticmethod
    def enhancement_pipeline() -> Compose:
        """Enhancement focused"""
        return Compose([
            HistogramEqualization(),
            ContrastEnhancement(factor=1.5),
            RgbToGrayscale(),
            OtsuThreshold(),
        ])
    
    @staticmethod
    def tissue_extraction() -> Compose:
        """Aggressive tissue extraction"""
        return Compose([
            RgbToGrayscale(),
            OtsuThreshold(),
            RemoveSmallObjects(
                min_size=5000,
                avoid_overmask=True,
                overmask_thresh=95
            ),
            RemoveSmallHoles(area_threshold=3000),
            Dilation(kernel_size=5),  # Expand tissue
            TexturePreservingSmoothing(iterations=2),
        ])
    
    @staticmethod
    def edge_preservation() -> Compose:
        """Preserve fine structures"""
        return Compose([
            RgbToGrayscale(),
            OtsuThreshold(),
            RemoveSmallObjects(min_size=500),  # Keep small structures
            # Don't remove holes to preserve glands
        ])
    
    @staticmethod
    def custom(filters) -> Compose:
        """Create custom pipeline"""
        return Compose(filters)


class PipelineComparator:
    """Compare different preprocessing pipelines"""
    
    def __init__(self, image_path: str):
        """
        Initialize with test image
        
        Args:
            image_path: Path to test image
        """
        self.image = Image.open(image_path)
    
    def compare_pipelines(self, output_dir: str):
        """
        Apply and compare pipelines visually
        
        Args:
            output_dir: Output directory for results
        """
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save original
        self.image.save(str(output_path / "original.png"))
        
        pipelines = {
            "basic_cleaning": AdvancedPreprocessing.basic_cleaning(),
            "enhancement": AdvancedPreprocessing.enhancement_pipeline(),
            "tissue_extraction": AdvancedPreprocessing.tissue_extraction(),
            "edge_preservation": AdvancedPreprocessing.edge_preservation(),
        }
        
        print("Comparing pipelines...")
        for name, pipeline in pipelines.items():
            try:
                result = pipeline(self.image)
                result.save(str(output_path / f"{name}.png"))
                print(f"  {name}: OK")
            except Exception as e:
                print(f"  {name}: Error - {e}")


# Usage
if __name__ == "__main__":
    # Create pipeline
    pipeline = AdvancedPreprocessing.tissue_extraction()
    
    # Apply
    image = Image.open("/data/sample_tile.png")
    result = pipeline(image)
    result.save("/output/preprocessed.png")
    
    # Compare pipelines
    comparator = PipelineComparator("/data/sample_tile.png")
    comparator.compare_pipelines("/output/pipeline_comparison")
```

---

## Example 8: Tissue Detection & Visualization

**Use Case**: Visualize tissue detection and tile locations  
**Complexity**: Intermediate  
**Output**: Annotated slide images

```python
"""
Example 8: Tissue Detection & Visualization
Visualize tissue detection results and tile placement
"""

from histolab.slides import Slide
from histolab.masks import BiggestTissueBoxMask, BinaryMask
from histolab.util import apply_mask_image
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
from typing import Optional

class TissueVisualization:
    """Visualize tissue detection on slides"""
    
    @staticmethod
    def draw_tissue_mask(
        slide: Slide,
        mask_strategy: BinaryMask,
        output_path: str,
        scale_factor: int = 32
    ):
        """
        Draw tissue mask on slide thumbnail
        
        Args:
            slide: Slide object
            mask_strategy: BinaryMask strategy
            output_path: Output image path
            scale_factor: Scale factor for display
        """
        print(f"Generating tissue visualization...")
        
        # Get thumbnail
        thumb = slide.get_thumbnail((2048 // scale_factor, 2048 // scale_factor))
        
        # Get mask
        tissue_mask = mask_strategy.get_mask(slide)
        
        # Scale mask to thumbnail size
        scaled_mask = Image.fromarray(tissue_mask.astype(np.uint8) * 255)
        scaled_mask = scaled_mask.resize(thumb.size, Image.BILINEAR)
        
        # Create overlay
        overlay = thumb.copy()
        
        # Apply semi-transparent mask
        mask_array = np.array(scaled_mask) > 128
        overlay_array = np.array(overlay)
        
        # Green channel for tissue
        overlay_array[mask_array, 1] = np.minimum(
            overlay_array[mask_array, 1] + 100, 255
        )
        
        overlay = Image.fromarray(overlay_array)
        overlay.save(output_path)
        
        print(f"Saved to {output_path}")
        return overlay
    
    @staticmethod
    def draw_tiles_on_slide(
        slide: Slide,
        tiles_coords: list,
        output_path: str,
        scale_factor: int = 32,
        tile_size_display: int = 512
    ):
        """
        Draw tile extraction grid on slide
        
        Args:
            slide: Slide object
            tiles_coords: List of (x, y) tile coordinates
            output_path: Output image path
            scale_factor: Scale factor for display
            tile_size_display: Tile size at original resolution
        """
        print(f"Drawing {len(tiles_coords)} tiles...")
        
        # Get thumbnail
        thumb = slide.get_thumbnail((slide.size[0] // scale_factor, slide.size[1] // scale_factor))
        
        # Draw on copy
        draw = ImageDraw.Draw(thumb, 'RGBA')
        
        # Convert coordinates to thumbnail space
        for x, y in tiles_coords:
            # Scale coordinates
            tx = x // scale_factor
            ty = y // scale_factor
            tx2 = tx + tile_size_display // scale_factor
            ty2 = ty + tile_size_display // scale_factor
            
            # Draw rectangle
            draw.rectangle(
                [(tx, ty), (tx2, ty2)],
                outline=(255, 0, 0, 255),
                width=2
            )
        
        thumb.save(output_path)
        print(f"Saved to {output_path}")
        return thumb
    
    @staticmethod
    def create_mask_comparison(
        slide: Slide,
        output_dir: str,
        scale_factor: int = 32
    ):
        """
        Create multi-panel comparison of different tissue masks
        
        Args:
            slide: Slide object
            output_dir: Output directory
            scale_factor: Display scale factor
        """
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Base thumbnail
        thumb = slide.get_thumbnail((slide.size[0] // scale_factor, slide.size[1] // scale_factor))
        
        # Get mask
        mask_strategy = BiggestTissueBoxMask(slide)
        tissue_mask = mask_strategy.get_mask(slide)
        
        # Visualize original
        thumb.save(str(output_path / "01_original.png"))
        
        # Visualize mask
        mask_image = Image.fromarray(tissue_mask.astype(np.uint8) * 255)
        mask_image.save(str(output_path / "02_mask.png"))
        
        # Overlay mask on thumbnail
        scaled_mask = mask_image.resize(thumb.size, Image.BILINEAR)
        mask_array = np.array(scaled_mask) > 128
        
        # Create colored overlay
        overlay = np.array(thumb)
        overlay[mask_array] = [
            np.minimum(overlay[mask_array, 0] + 50, 255),
            overlay[mask_array, 1],
            np.minimum(overlay[mask_array, 2] + 50, 255),
        ]
        
        overlay_image = Image.fromarray(overlay.astype(np.uint8))
        overlay_image.save(str(output_path / "03_overlay.png"))
        
        print(f"Comparison saved to {output_dir}")


def visualize_extraction_results(
    slide_path: str,
    output_dir: str,
    tile_coords: Optional[list] = None
):
    """
    Complete visualization of extraction process
    
    Args:
        slide_path: Path to WSI
        output_dir: Output directory
        tile_coords: Optional list of extracted tile coordinates
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    slide = Slide(
        path=slide_path,
        processed_path=str(output_path)
    )
    
    viz = TissueVisualization()
    
    # Visualize tissue mask
    mask_strategy = BiggestTissueBoxMask(slide)
    viz.draw_tissue_mask(
        slide,
        mask_strategy,
        str(output_path / "tissue_mask.png")
    )
    
    # Visualize tile coordinates if provided
    if tile_coords:
        viz.draw_tiles_on_slide(
            slide,
            tile_coords,
            str(output_path / "tiles_grid.png")
        )
    
    # Create comparison
    viz.create_mask_comparison(
        slide,
        str(output_path / "mask_comparison")
    )


# Usage
if __name__ == "__main__":
    slide_path = "/data/sample.svs"
    output_dir = "/output/tissue_visualization"
    
    # Example tile coordinates
    tiles = [(0, 0), (512, 0), (1024, 0), (0, 512), (512, 512)]
    
    visualize_extraction_results(
        slide_path=slide_path,
        output_dir=output_dir,
        tile_coords=tiles
    )
```

---

## Example 9: Custom Scorer Implementation

**Use Case**: Implement domain-specific tile quality scoring  
**Complexity**: Advanced  
**Output**: Scored tiles

```python
"""
Example 9: Custom Scorer Implementation
Create custom tile scoring strategies
"""

from histolab.tiles import Tile
import numpy as np
from PIL import Image
from typing import List

class EntropyScorer:
    """Score tiles based on information entropy"""
    
    def score(self, tile: Tile) -> float:
        """
        Score based on image entropy (higher = more information)
        
        Args:
            tile: Tile object
            
        Returns:
            Score between 0 and 1
        """
        # Convert to grayscale array
        gray = tile.image.convert('L')
        gray_array = np.array(gray, dtype=np.float32) / 255.0
        
        # Calculate entropy
        hist, _ = np.histogram(gray_array, bins=256)
        hist = hist / hist.sum()  # Normalize
        entropy = -np.sum(hist[hist > 0] * np.log2(hist[hist > 0]))
        
        # Normalize (max entropy for 8-bit = 8)
        return min(entropy / 8.0, 1.0)


class ColorDiversityScorer:
    """Score based on color diversity"""
    
    def score(self, tile: Tile) -> float:
        """
        Score based on color channel diversity
        
        Args:
            tile: Tile object
            
        Returns:
            Score between 0 and 1
        """
        # Convert to RGB
        rgb_array = np.array(tile.image.convert('RGB'), dtype=np.float32) / 255.0
        
        # Calculate channel statistics
        r_std = np.std(rgb_array[:, :, 0])
        g_std = np.std(rgb_array[:, :, 1])
        b_std = np.std(rgb_array[:, :, 2])
        
        # Channel diversity
        diversity = (r_std + g_std + b_std) / 3.0
        
        return min(diversity, 1.0)


class PinkScorer:
    """Score based on pinkish coloration (H&E stain)"""
    
    def score(self, tile: Tile) -> float:
        """
        Score based on typical H&E appearance (pink-red highlights)
        
        Args:
            tile: Tile object
            
        Returns:
            Score between 0 and 1
        """
        # Convert to RGB
        rgb_array = np.array(tile.image.convert('RGB'), dtype=np.float32)
        
        # H&E typical: high red, moderate blue, low green
        red = rgb_array[:, :, 0]
        green = rgb_array[:, :, 1]
        blue = rgb_array[:, :, 2]
        
        # Pink score: red > green > blue
        pink_mask = (red > green) & (green > blue)
        pink_ratio = pink_mask.mean()
        
        # Normalize intensity
        intensity_score = np.mean(red[pink_mask]) / 255.0 if pink_mask.any() else 0
        
        return pink_ratio * intensity_score


class SharpnessScorer:
    """Score based on image sharpness"""
    
    def score(self, tile: Tile) -> float:
        """
        Score based on Laplacian sharpness metric
        
        Args:
            tile: Tile object
            
        Returns:
            Score between 0 and 1
        """
        from scipy.ndimage import laplace
        
        # Grayscale
        gray = np.array(tile.image.convert('L'), dtype=np.float32)
        
        # Laplacian
        laplacian = laplace(gray)
        sharpness = np.var(laplacian)
        
        # Normalize (assume max reasonable is 1000)
        score = min(sharpness / 1000.0, 1.0)
        
        return score


class VoteScorer:
    """Combine multiple scorers through voting"""
    
    def __init__(self, scorers: dict, weights: dict = None):
        """
        Initialize ensemble scorer
        
        Args:
            scorers: Dict of {name: scorer} objects
            weights: Optional dict of {name: weight} for weighted voting
        """
        self.scorers = scorers
        self.weights = weights or {name: 1.0 for name in scorers}
    
    def score(self, tile: Tile) -> float:
        """
        Score by combining multiple scorers
        
        Args:
            tile: Tile object
            
        Returns:
            Weighted average score
        """
        scores = []
        total_weight = 0
        
        for name, scorer in self.scorers.items():
            try:
                score = scorer.score(tile)
                weight = self.weights.get(name, 1.0)
                scores.append(score * weight)
                total_weight += weight
            except Exception as e:
                print(f"Scorer {name} failed: {e}")
        
        if not scores:
            return 0.0
        
        return sum(scores) / total_weight


def score_tiles(tiles: List[Tile], scorers_dict: dict) -> list:
    """
    Score multiple tiles with ensemble of scorers
    
    Args:
        tiles: List of Tile objects
        scorers_dict: Dict of {scorer_name: scorer_object}
        
    Returns:
        List of dicts with scores
    """
    results = []
    
    for i, tile in enumerate(tiles):
        scores = {"tile_id": i}
        
        for name, scorer in scorers_dict.items():
            try:
                score = scorer.score(tile)
                scores[name] = score
            except Exception as e:
                print(f"Tile {i}, Scorer {name}: {e}")
                scores[name] = 0.0
        
        # Average
        img_scores = [v for k, v in scores.items() if k != "tile_id"]
        scores["average"] = np.mean(img_scores) if img_scores else 0.0
        
        results.append(scores)
    
    return results


# Usage
if __name__ == "__main__":
    # Create ensemble
    scorers = {
        "entropy": EntropyScorer(),
        "color": ColorDiversityScorer(),
        "pink": PinkScorer(),
        "sharpness": SharpnessScorer(),
    }
    
    weights = {
        "entropy": 1.0,
        "color": 1.0,
        "pink": 2.0,       # Double weight for H&E
        "sharpness": 1.0,
    }
    
    ensemble_scorer = VoteScorer(scorers, weights)
    
    # Example: Score some tiles
    # tile = Tile(image, coords, level, slide)
    # score = ensemble_scorer.score(tile)
```

---

## Example 10: End-to-End Production Pipeline

**Use Case**: Complete production-ready pipeline  
**Complexity**: Advanced  
**Output**: Processed tiles with metadata

```python
"""
Example 10: End-to-End Production Pipeline
Complete pipeline with logging, error handling, and metadata
"""

from histolab.slides import Slide
from histolab.tiles import Tile
from histolab.scorer import CellularityScorer
from histolab.masks import BiggestTissueBoxMask
from histolab.filters.compositions import FiltersComposition
from histolab.stain_normalizer import StainNormalizer
import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
from typing import Optional, Dict, List

@dataclass
class TileMetadata:
    """Metadata for extracted tile"""
    tile_id: str
    coordinates: tuple
    level: int
    tissue_ratio: float
    cellularity_score: float
    size: tuple
    extraction_time: float


class ProductionTilePipeline:
    """Production-ready tile extraction pipeline"""
    
    def __init__(
        self,
        output_base: str,
        reference_slide_path: Optional[str] = None,
        tissue_threshold: float = 0.75,
        cellularity_threshold: float = 0.6
    ):
        """
        Initialize production pipeline
        
        Args:
            output_base: Base output directory
            reference_slide_path: Optional reference for stain normalization
            tissue_threshold: Min tissue ratio to keep tile
            cellularity_threshold: Min cellularity to keep tile
        """
        self.output_base = Path(output_base)
        self.output_base.mkdir(parents=True, exist_ok=True)
        
        self.tissue_threshold = tissue_threshold
        self.cellularity_threshold = cellularity_threshold
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Initialize scorers/detectors
        self.scorer = CellularityScorer()
        self.preprocessor = FiltersComposition.of(Tile)
        
        # Optional stain normalization
        self.normalizer = None
        if reference_slide_path:
            self._initialize_normalizer(reference_slide_path)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger("ProductionPipeline")
        logger.setLevel(logging.DEBUG)
        
        # File handler
        fh = logging.FileHandler(self.output_base / "pipeline.log")
        fh.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def _initialize_normalizer(self, reference_path: str):
        """Initialize stain normalizer"""
        try:
            self.logger.info(f"Initializing normalizer with {reference_path}")
            
            ref_slide = Slide(
                path=reference_path,
                processed_path=str(self.output_base / ".tmp")
            )
            
            # Sample from reference
            ref_region = ref_slide.read_region((0, 0), 0, (2048, 2048))
            ref_array = np.array(ref_region.convert('RGB'))
            
            # Fit normalizer
            self.normalizer = StainNormalizer()
            self.normalizer.fit(ref_array)
            
            self.logger.info("Stain normalizer initialized")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize normalizer: {e}")
            self.normalizer = None
    
    def process_slide(
        self,
        slide_path: str,
        tile_size: int = 512,
        save_images: bool = True,
        save_masks: bool = False
    ) -> Dict:
        """
        Process single slide end-to-end
        
        Args:
            slide_path: Path to WSI
            tile_size: Tile dimensions
            save_images: Save tile images
            save_masks: Save tissue masks
            
        Returns:
            Processing results
        """
        import time
        start_time = time.time()
        
        slide_name = Path(slide_path).stem
        self.logger.info(f"Starting: {slide_name}")
        
        try:
            # Create output directory
            output_dir = self.output_base / slide_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize slide
            slide = Slide(
                path=slide_path,
                processed_path=str(output_dir)
            )
            
            self.logger.debug(f"Slide dimensions: {slide.size}, MPP: {slide.base_mpp}")
            
            # Generate tissue mask
            mask_strategy = BiggestTissueBoxMask(slide)
            tissue_mask = mask_strategy.get_mask(slide)
            
            if save_masks:
                from PIL import Image
                mask_image = Image.fromarray(tissue_mask * 255)
                mask_image.save(str(output_dir / "tissue_mask.png"))
            
            # Extract and process tiles
            tiles_metadata: List[TileMetadata] = []
            accepted_count = 0
            rejected_count = 0
            step = tile_size
            
            for y in range(0, slide.size[1], step):
                for x in range(0, slide.size[0], step):
                    tile_start = time.time()
                    
                    w = min(tile_size, slide.size[0] - x)
                    h = min(tile_size, slide.size[1] - y)
                    
                    if w < tile_size // 2 or h < tile_size // 2:
                        continue
                    
                    try:
                        # Read tile
                        tile_image = slide.read_region(
                            coordinates=(x, y),
                            level=0,
                            size=(w, h)
                        )
                        
                        # Create Tile object
                        from histolab.types import CoordinatePair
                        tile = Tile(
                            image=tile_image,
                            coords=CoordinatePair(x=x, y=y),
                            level=0,
                            slide=slide
                        )
                        
                        # Preprocess
                        processed = tile.apply_filters(self.preprocessor)
                        
                        # Quality checks
                        tissue_ratio = processed.tissue_ratio
                        cellularity = self.scorer.score(tile)
                        
                        tile_time = time.time() - tile_start
                        
                        if (tissue_ratio >= self.tissue_threshold and
                            cellularity >= self.cellularity_threshold):
                            
                            # Apply stain normalization if available
                            if self.normalizer:
                                try:
                                    tile_array = np.array(tile_image.convert('RGB'))
                                    normalized_array = self.normalizer.transform(tile_array)
                                    from histolab.util import np_to_pil
                                    tile_image = np_to_pil(normalized_array)
                                except Exception as e:
                                    self.logger.warning(f"Normalization failed: {e}")
                            
                            # Save
                            if save_images:
                                tile_path = output_dir / f"tile_{accepted_count:06d}.png"
                                tile_image.save(tile_path)
                            
                            # Record metadata
                            metadata = TileMetadata(
                                tile_id=f"{slide_name}_tile_{accepted_count:06d}",
                                coordinates=(x, y),
                                level=0,
                                tissue_ratio=tissue_ratio,
                                cellularity_score=cellularity,
                                size=(w, h),
                                extraction_time=tile_time
                            )
                            tiles_metadata.append(metadata)
                            
                            accepted_count += 1
                        else:
                            rejected_count += 1
                        
                    except Exception as e:
                        self.logger.debug(f"Error at ({x}, {y}): {e}")
                        rejected_count += 1
            
            # Save metadata
            metadata_file = output_dir / "metadata.json"
            metadata_json = [asdict(m) for m in tiles_metadata]
            with open(metadata_file, 'w') as f:
                json.dump(metadata_json, f, indent=2)
            
            # Summary
            total_time = time.time() - start_time
            
            results = {
                "slide": slide_name,
                "accepted_tiles": accepted_count,
                "rejected_tiles": rejected_count,
                "total_time": total_time,
                "avg_time_per_tile": total_time / (accepted_count + rejected_count + 1),
                "success": True
            }
            
            self.logger.info(
                f"Completed: {slide_name} - "
                f"{accepted_count} accepted, {rejected_count} rejected in {total_time:.1f}s"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed: {slide_name} - {e}", exc_info=True)
            return {"slide": slide_name, "success": False, "error": str(e)}
    
    def process_batch(
        self,
        slides_dir: str,
        pattern: str = "*.svs",
        tile_size: int = 512
    ) -> List[Dict]:
        """
        Process multiple slides
        
        Args:
            slides_dir: Directory with slides
            pattern: File pattern
            tile_size: Tile dimensions
            
        Returns:
            List of results
        """
        slides_path = Path(slides_dir)
        slide_files = sorted(slides_path.glob(pattern))
        
        self.logger.info(f"Processing {len(slide_files)} slides")
        
        results = []
        for i, slide_file in enumerate(slide_files):
            self.logger.info(f"[{i+1}/{len(slide_files)}] {slide_file.name}")
            
            result = self.process_slide(
                slide_path=str(slide_file),
                tile_size=tile_size
            )
            results.append(result)
        
        # Save summary
        summary_file = self.output_base / "processing_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Log summary
        self._log_summary(results)
        
        return results
    
    def _log_summary(self, results: List[Dict]):
        """Log processing summary"""
        self.logger.info("\n" + "="*60)
        self.logger.info("PROCESSING SUMMARY")
        self.logger.info("="*60)
        
        total_slides = len(results)
        successful = sum(1 for r in results if r.get("success", False))
        total_tiles = sum(r.get("accepted_tiles", 0) for r in results)
        total_time = sum(r.get("total_time", 0) for r in results)
        
        self.logger.info(f"Total slides: {total_slides}")
        self.logger.info(f"Successful: {successful}/{total_slides}")
        self.logger.info(f"Total tiles: {total_tiles}")
        self.logger.info(f"Total time: {total_time:.1f}s")


# Usage
if __name__ == "__main__":
    pipeline = ProductionTilePipeline(
        output_base="/output/production",
        reference_slide_path=None,  # Optional
        tissue_threshold=0.75,
        cellularity_threshold=0.6
    )
    
    # Process single slide
    result = pipeline.process_slide(
        slide_path="/data/sample.svs",
        tile_size=512,
        save_images=True
    )
    
    print(json.dumps(result, indent=2))
    
    # Or batch process
    # results = pipeline.process_batch(
    #     slides_dir="/data/slides",
    #     pattern="*.svs"
    # )
```

---

## Summary

These 10 examples cover the full spectrum of HistoLab usage:

1. **Basic** - Simple tile extraction
2. **Preprocessing** - Filter application
3. **Quality Control** - Scoring and filtering
4. **Stain Normalization** - Color harmonization
5. **Batch Processing** - Multi-slide workflows
6. **Custom Masks** - Domain-specific detection
7. **Advanced Filters** - Complex pipelines
8. **Visualization** - Annotated outputs
9. **Custom Scoring** - Quality metrics
10. **Production** - Complete end-to-end system

All examples are production-ready with proper error handling, logging, and metadata tracking.
