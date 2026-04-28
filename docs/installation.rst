.. _installation:

Installation
============

Install from PyPI (recommended):

.. code:: bash

   pip install glasscut

For GPU acceleration, install with the ``gpu`` extra:

.. code:: bash

   pip install "glasscut[gpu]"

Install from source (development):

.. code:: bash

   git clone https://github.com/CamiloSinningUN/GlassCut.git
   cd GlassCut
   uv sync

GPU Acceleration (Optional)
---------------------------

To enable GPU-accelerated WSI reading via CuCim:

.. code:: bash

   uv sync --extra gpu

This requires a CUDA-compatible GPU and driver. See the
`CuCim documentation <https://docs.rapids.ai/api/cucim/stable/>`_ for details.

Verifying the Installation
--------------------------

.. code:: python

   import glasscut
   print(glasscut.__version__)
