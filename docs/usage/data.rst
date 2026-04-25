Sample Data
===========

GlassCut provides built-in access to public whole slide image samples for testing and
prototyping. Data is downloaded on demand via ``pooch`` and cached locally. This
functionality was adapted from the HistoLab implementation.

Sample Functions
----------------

.. list-table::
    :header-rows: 1

   * - Function
      - Source
      - Description
   * - :func:`~glasscut.data.aorta_tissue`
      - Aperio
      - Aorta tissue, JPEG 2000
   * - :func:`~glasscut.data.breast_tissue`
      - TCGA-BRCA
      - Breast carcinoma, H&E
   * - :func:`~glasscut.data.breast_tissue_diagnostic_green_pen`
      - TCGA-BRCA
      - Breast with green pen marks
   * - :func:`~glasscut.data.breast_tissue_diagnostic_red_pen`
      - TCGA-BRCA
      - Breast with red pen marks
   * - :func:`~glasscut.data.breast_tissue_diagnostic_black_pen`
      - TCGA-BRCA
      - Breast with black pen marks
   * - :func:`~glasscut.data.cmu_small_region`
      - CMU
      - MRXS small region (CC0)
   * - :func:`~glasscut.data.heart_tissue`
      - Aperio
      - Heart tissue, JPEG 2000
   * - :func:`~glasscut.data.ihc_breast`
      - IDR
      - Breast cancer, IHC (CD3/CD20)
   * - :func:`~glasscut.data.ihc_kidney`
      - IDR
      - Kidney tissue, IHC (CD3/CD20)
   * - :func:`~glasscut.data.ovarian_tissue`
      - TCGA-OV
      - Ovarian carcinoma
   * - :func:`~glasscut.data.prostate_tissue`
      - TCGA-PRAD
      - Prostate adenocarcinoma

Usage
-----

.. code:: python

    from glasscut.data import breast_tissue, cmu_small_region

    slide, path = breast_tissue()
    print(f"Loaded: {path}")

    slide, path = cmu_small_region()
    print(f"Loaded: {path}")
