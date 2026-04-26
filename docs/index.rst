GlassCut
========

A lightweight, extensible toolkit for preprocessing and analyzing whole slide images (WSI) in digital pathology.

GlassCut combines efficient WSI reading, and grid tiling into a modular pipeline, with optional GPU acceleration via CuCim, following optimized preprocessing workflows [Horst2024]_, and [Marcolini2022]. It is designed to be both usable out-of-the-box and easily extensible for custom research workflows.

.. toctree::
   :hidden:

   installation
   quickstart
   usage/index
   api/index
   contributing

   Whole slide image processing with GlassCut.

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: [1] Multi-backend WSI reading
      :link: usage/slides
      :link-type: doc

      OpenSlide (CPU) and CuCim (GPU) with automatic fallback

   .. grid-item-card:: [2] Grid tiling
      :link: usage/tiling
      :link-type: doc

      Regular grid extraction with overlap, prescreening, and parallelism

   .. grid-item-card:: [3] Tissue detection
      :link: usage/tissue_detection
      :link-type: doc

      Otsu-based segmentation with a pluggable detector interface

   .. grid-item-card:: [4] Stain normalization
      :link: usage/stain_normalization
      :link-type: doc

      Macenko and Reinhardt methods with custom normalizer support

   .. grid-item-card:: [5] Dataset generation
      :link: usage/dataset
      :link-type: doc

      Multi-slide extraction with checkpoint/resume and metadata

   .. grid-item-card:: [6] Sample data
      :link: usage/data
      :link-type: doc

      Built-in downloader for public WSI samples (TCGA [TCGA]_, GDC [GDC]_, Aperio [Aperio]_, IDR [IDR]_); adapted from HistoLab [Marcolini2022]_

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

.. [IDR] Williams, E., Moore, J., Li, S. W., et al. (2017). Image Data
   Resource: A bioimage data integration and publication platform. *Nature
   Methods*, 14, 775--776. https://doi.org/10.1038/nmeth.4326

.. [Aperio] Leica Biosystems. Aperio AT2 — Digital Pathology Scanner.
   https://www.leicabiosystems.com/digital-pathology/scan/aperio-at2/

.. [GDC] Genomic Data Commons (GDC). National Cancer Institute.
   https://portal.gdc.cancer.gov

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
