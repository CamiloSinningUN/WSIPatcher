# GlassCut

A lightweight, extensible toolkit for preprocessing and analyzing whole slide images (WSI) in digital pathology. GlassCut combines efficient WSI reading, and tiling into a modular pipeline, with optional GPU acceleration via CuCim.

## Features

- **Multi-backend WSI reading** — OpenSlide (CPU) and CuCim (GPU) backends with automatic fallback
- **Grid tiling** — Regular grid extraction with overlap, tissue-prescreening via integral images, and parallel processing
- **Tissue detection** — Otsu-based segmentation (Experimental - Custom detectors can be implemented by subclassing ``TissueDetector``)
- **Stain normalization** — Macenko and Reinhardt methods (Experimental - Custom normalizers can be implemented by subclassing ``StainNormalizer``)
- **Dataset generation** — Multi-slide tile extraction with checkpoint/resume and structured metadata
- **Live dataset** — In-memory slide dataset for interactive exploration
- **Extensible design** — Abstract base classes for tilers, tissue detectors, and stain normalizers make it easy to plug in custom strategies
- **Sample data** — Built-in downloader for public WSI samples (TCGA, Aperio, IDR)

## Installation

```bash
git clone https://github.com/CamiloSinningUN/GlassCut.git
cd GlassCut
uv sync
```

### GPU acceleration (optional)

```bash
uv sync --group gpu
```

Requires a CUDA-compatible GPU and driver. See [CuCim documentation](https://docs.rapids.ai/api/cucim/stable/) for details.

## Quick Start

```python
from glasscut import Slide, GridTiler, OtsuTissueDetector

# Open a slide
slide = Slide("slide.svs")

# Configure tiling
tiler = GridTiler(
    tile_size=(512, 512),
    magnification=20
)

# Extract tiles
for tile in tiler.extract(slide):
    tile.save(f"tiles/{tile.coords}.png")

slide.close()
```

## Architecture

```
glasscut
├── Slide              — WSI reader with backend abstraction
│   └── Backends       — OpenSlide (CPU), CuCim (GPU)
├── Tile               — Individual tile with metadata
├── Tiler              — Abstract tiling strategy
│   └── GridTiler      — Regular grid tiler with overlap
├── TissueDetector     — Abstract tissue detection
│   └── OtsuTissueDetector
├── StainNormalizer    — Abstract stain normalization
│   ├── MacenkoStainNormalizer
│   └── ReinhardtStainNormalizer
├── DatasetGenerator   — Multi-slide → disk dataset pipeline
├── LiveSlideDataset   — In-memory slide dataset
└── DataFetcher        — Sample WSI downloader
```

## Documentation

Full documentation is available at [https://CamiloSinningUN.github.io/GlassCut](https://CamiloSinningUN.github.io/GlassCut).

## References

This project draws inspiration from:

- Marcolini, A., Bussola, N., Arbitrio, E., Amgad, M., Jurman, G., & Furlanello, C. (2022). histolab: A Python library for reproducible Digital Pathology preprocessing with automated testing. *SoftwareX*, 20(101237).
- Hörst, F., Schaheer, S. H., Baldini, G., Bahnsen, F. H., Egger, J., & Kleesiek, J. (2024). Accelerating Artificial Intelligence-based Whole Slide Image Analysis with an Optimized Preprocessing Pipeline. *Bildverarbeitung für die Medizin 2024*, pp. 356–361. https://doi.org/10.1007/978-3-658-44037-4_91
- kaiko.ai et al. (2024). Towards Large-Scale Training of Pathology Foundation Models. *arXiv preprint* arXiv:2404.15217.

## Author

[Camilo José Sinning López](https://github.com/CamiloSinningUN)

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
