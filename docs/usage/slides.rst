Working with Slides
===================

The :class:`~glasscut.slides.Slide` class is the entry point for reading whole slide images.

Opening a Slide
---------------

.. code:: python

   from glasscut import Slide

   slide = Slide("path/to/slide.svs")

By default, ``Slide`` attempts to use the CuCim GPU backend first. If CuCim is not
available or fails, it falls back to OpenSlide. You can force CPU-only mode:

.. code:: python

   slide = Slide("path/to/slide.svs", use_cucim=False)

Slide Properties
----------------

.. code:: python

   slide.name            # File name without extension
   slide.dimensions      # (width, height) at base magnification
   slide.magnifications  # List of available magnifications
   slide.mpp             # Microns per pixel
   slide.properties      # Full metadata dictionary
   slide.thumbnail       # PIL Image thumbnail

Context Manager
---------------

.. code:: python

   with Slide("slide.svs") as slide:
      print(slide.name)

Backends
--------

GlassCut provides two backends implementing the :class:`~glasscut.slides.backends.base.SlideBackend`
abstract interface:

.. list-table::
   :header-rows: 1

   * - Backend
      - Hardware
      - Dependencies
   * - :class:`~glasscut.slides.backends.openslide_backend.OpenSlideBackend`
      - CPU
      - openslide-python, openslide-bin
   * - :class:`~glasscut.slides.backends.cucim_backend.CuCimBackend`
      - GPU (CUDA)
      - cucim, cupy-cuda13x
