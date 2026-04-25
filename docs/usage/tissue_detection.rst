Tissue Detection
================

Tissue detection identifies regions containing tissue vs. background in whole slide images.
This is a critical preprocessing step in digital pathology pipelines.

.. important::

   The built-in :class:`~glasscut.tissue_detectors.otsu.OtsuTissueDetector` is a **reference
   implementation** meant to demonstrate the :class:`~glasscut.tissue_detectors.base.TissueDetector`
   interface. For production use, we strongly recommend implementing your own detector tailored
   to your specific tissue types, staining protocols, and scanning artefacts.

OtsuTissueDetector
------------------

.. code:: python

   from glasscut import OtsuTissueDetector
   from PIL import Image

   detector = OtsuTissueDetector()
   image = Image.open("region.png")
   mask = detector.detect(image)  # np.ndarray, 0=background, 1=tissue

The detector converts the image to grayscale, applies Otsu's thresholding via
``skimage.filters.threshold_otsu``, and returns a binary mask.

Custom Detectors
----------------

Implement a custom tissue detector by subclassing :class:`~glasscut.tissue_detectors.base.TissueDetector`:

.. code:: python

   from glasscut.tissue_detectors import TissueDetector
   import numpy as np
   from PIL import Image

   class MyTissueDetector(TissueDetector):
      def detect(self, image: Image.Image) -> np.ndarray:
         # Your custom detection logic here
         # Return binary mask: 0 = background, 1 = tissue
         pass

Using with GridTiler
--------------------

Pass your detector instance to the tiler:

.. code:: python

   tiler = GridTiler(
      tissue_detector=MyTissueDetector(),
      min_tissue_ratio=0.2,
   )
