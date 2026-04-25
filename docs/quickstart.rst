.. _quickstart:

Quick Start
===========

This guide walks through the core workflow: opening a slide, configuring a tiler,
extracting tiles with tissue filtering, and saving the results.

Loading a Slide
---------------

.. code:: python

   from glasscut import Slide

   slide = Slide("path/to/slide.svs")
   print(f"Slide: {slide.name}")
   print(f"Dimensions: {slide.dimensions}")
   print(f"Magnifications: {slide.magnifications}")
   print(f"MPP: {slide.mpp}")

The :class:`~glasscut.slides.Slide` class automatically selects the best available backend
(CuCim GPU → OpenSlide CPU).

Configuring a Tiler
-------------------

.. code:: python

   from glasscut import GridTiler, OtsuTissueDetector

   tiler = GridTiler(
       tile_size=(512, 512),
       magnification=20
   )

Extracting Tiles
----------------

.. code:: python

   for tile in tiler.extract(slide):
         tile.save(f"output/{tile.coords}.png")

   slide.close()

Visualising the Tile Grid
-------------------------

.. code:: python

   viz = tiler.visualize(slide)

Complete Example
----------------

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
   print("Done!")
