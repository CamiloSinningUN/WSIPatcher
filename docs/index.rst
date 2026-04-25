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
