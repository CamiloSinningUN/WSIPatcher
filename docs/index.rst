GlassCut
========

A lightweight, extensible toolkit for preprocessing and analyzing whole slide images (WSI) in digital pathology.

GlassCut combines efficient WSI reading, and grid tiling into a modular pipeline, with optional GPU acceleration via CuCim. It is designed to be both usable out-of-the-box and easily extensible for custom research workflows.

.. toctree::
   :hidden:

   installation
   quickstart
   usage/index
   api/index
   contributing

Key Features
------------

* **Multi-backend WSI reading** — OpenSlide (CPU) and CuCim (GPU) with automatic fallback
* **Grid tiling** — Regular grid extraction with overlap, tissue prescreening, and parallel processing
* **Tissue detection** — Otsu-based segmentation (Experimental - Custom detectors can be implemented by subclassing ``TissueDetector``)
* **Stain normalization** — Macenko and Reinhardt methods (Experimental - Custom normalizers can be implemented by subclassing ``StainNormalizer``)
* **Dataset generation** — Multi-slide tile extraction with checkpoint/resume, metadata, and structured storage
* **Live dataset** — In-memory per-slide dataset for interactive exploration
* **Sample data** — Built-in downloader for public WSI samples (TCGA, Aperio, IDR)

Quick Start
-----------

.. code:: python

    from glasscut import Slide, GridTiler

    slide = Slide("slide.svs")

    tiler = GridTiler(
        tile_size=(512, 512),
        magnification=20
    )

    for tile in tiler.extract(slide):
        tile.save(f"tiles/{tile.coords}.png")

    slide.close()

See the :ref:`quickstart` guide for more details.

Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

References
----------

.. [TCGA] The Cancer Genome Atlas Program (TCGA). National Cancer Institute,
   National Institutes of Health. https://www.cancer.gov/tcga

.. [GDC] Genomic Data Commons (GDC). National Cancer Institute.
   https://portal.gdc.cancer.gov

.. [IDR] Williams, E., Moore, J., Li, S. W., et al. (2017). Image Data
   Resource: A bioimage data integration and publication platform. *Nature
   Methods*, 14, 775--776. https://doi.org/10.1038/nmeth.4326

.. [Aperio] Leica Biosystems. Aperio AT2 — Digital Pathology Scanner.
   https://www.leicabiosystems.com/digital-pathology/scan/aperio-at2/

.. [Marcolini2022] Marcolini, A., Bussola, N., Arbitrio, E., Amgad, M.,
   Jurman, G., & Furlanello, C. (2022). histolab: A Python library for
   reproducible Digital Pathology preprocessing with automated testing.
   *SoftwareX*, 20(101237). https://doi.org/10.1016/j.softx.2022.101237

.. [Horst2024] Hörst, F., Schaheer, S. H., Baldini, G., Bahnsen, F. H.,
   Egger, J., & Kleesiek, J. (2024). Accelerating Artificial
   Intelligence-based Whole Slide Image Analysis with an Optimized
   Preprocessing Pipeline. *Bildverarbeitung für die Medizin 2024*,
   pp. 356--361. https://doi.org/10.1007/978-3-658-44037-4_91

.. [kaiko2024] kaiko.ai et al. (2024). Towards Large-Scale Training of
   Pathology Foundation Models. *arXiv preprint* arXiv:2404.15217.
   https://arxiv.org/abs/2404.15217
