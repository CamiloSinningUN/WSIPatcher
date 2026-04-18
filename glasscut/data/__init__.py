"""GlassCut data module for downloading and loading sample histology slides."""

from pathlib import Path
from typing import Tuple

import openslide

from .fetcher import DataFetcher

# ===== Data Loading Functions =====

_fetcher = DataFetcher()


def aorta_tissue() -> Tuple[openslide.OpenSlide, Path]:
    """Load aorta tissue sample.

    Aorta tissue, brightfield, JPEG 2000, YCbCr format from OpenSlide test data.

    Source: http://openslide.cs.cmu.edu/download/openslide-testdata/Aperio/

    Returns
    -------
    Tuple[openslide.OpenSlide, Path]
        H&E-stained WSI of aortic tissue and its file path
    """
    return _fetcher.load_slide("aperio/JP2K-33003-1.svs")


def breast_tissue() -> Tuple[openslide.OpenSlide, Path]:
    """Load breast tissue sample from TCGA-BRCA.

    Source: TCGA-A8-A082-01A-01-TS1.3cad4a77-47a6-4658-becf-d8cffa161d3a.svs
    Access: open

    Returns
    -------
    Tuple[openslide.OpenSlide, Path]
        H&E-stained WSI of breast tissue and its file path
    """
    return _fetcher.load_slide(
        "tcga/breast/TCGA-A8-A082-01A-01-TS1.3cad4a77-47a6-4658-becf-d8cffa161d3a.svs"
    )


def breast_tissue_diagnostic_green_pen() -> Tuple[openslide.OpenSlide, Path]:
    """Load breast tissue diagnostic slide with green pen marks.

    Source: TCGA-A1-A0SH-01Z-00-DX1.90E71B08-E1D9-4FC2-85AC-062E56DDF17C.svs
    Access: open

    Returns
    -------
    Tuple[openslide.OpenSlide, Path]
        H&E-stained WSI with green pen annotations and its file path
    """
    return _fetcher.load_slide(
        "tcga/breast/TCGA-A1-A0SH-01Z-00-DX1.90E71B08-E1D9-4FC2-85AC-062E56DDF17C.svs"
    )


def breast_tissue_diagnostic_red_pen() -> Tuple[openslide.OpenSlide, Path]:
    """Load breast tissue diagnostic slide with red pen marks.

    Source: TCGA-E9-A24A-01Z-00-DX1.F0342837-5750-4172-B60D-5F902E2A02FD.svs
    Access: open

    Returns
    -------
    Tuple[openslide.OpenSlide, Path]
        H&E-stained WSI with red pen annotations and its file path
    """
    return _fetcher.load_slide(
        "tcga/breast/TCGA-E9-A24A-01Z-00-DX1.F0342837-5750-4172-B60D-5F902E2A02FD.svs"
    )


def breast_tissue_diagnostic_black_pen() -> Tuple[openslide.OpenSlide, Path]:
    """Load breast tissue diagnostic slide with black pen marks.

    Source: TCGA-BH-A201-01Z-00-DX1.6D6E3224-50A0-45A2-B231-EEF27CA7EFD2.svs
    Access: open

    Returns
    -------
    Tuple[openslide.OpenSlide, Path]
        H&E-stained WSI with black pen annotations and its file path
    """
    return _fetcher.load_slide(
        "tcga/breast/TCGA-BH-A201-01Z-00-DX1.6D6E3224-50A0-45A2-B231-EEF27CA7EFD2.svs"
    )


def cmu_small_region() -> Tuple[openslide.OpenSlide, Path]:
    """Load Carnegie Mellon University MRXS sample tissue.

    Small region from CMU test data.

    Source: http://openslide.cs.cmu.edu/download/openslide-testdata/Aperio/
    Licensed under CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

    Returns
    -------
    Tuple[openslide.OpenSlide, Path]
        H&E-stained WSI and its file path
    """
    return _fetcher.load_slide("data/cmu_small_region.svs")


def heart_tissue() -> Tuple[openslide.OpenSlide, Path]:
    """Load heart tissue sample.

    Heart tissue, brightfield, JPEG 2000, YCbCr format from OpenSlide test data.

    Source: http://openslide.cs.cmu.edu/download/openslide-testdata/Aperio/

    Returns
    -------
    Tuple[openslide.OpenSlide, Path]
        H&E-stained WSI of heart tissue and its file path
    """
    return _fetcher.load_slide("aperio/JP2K-33003-2.svs")


def ihc_breast() -> Tuple[openslide.OpenSlide, Path]:
    """Load breast cancer resection with IHC staining.

    Staining: CD3 (brown) and CD20 (red)

    Source: https://idr.openmicroscopy.org/ (accession idr0073, ID breastCancer12)

    Returns
    -------
    Tuple[openslide.OpenSlide, Path]
        IHC-stained WSI of breast tissue and its file path
    """
    return _fetcher.load_slide("9798433/?format=tif")


def ihc_kidney() -> Tuple[openslide.OpenSlide, Path]:
    """Load kidney tissue with IHC staining.

    Renal allograft staining: CD3 (brown) and CD20 (red)

    Source: https://idr.openmicroscopy.org/ (accession idr0073, ID kidney_46_4)

    Returns
    -------
    Tuple[openslide.OpenSlide, Path]
        IHC-stained WSI of kidney tissue and its file path
    """
    return _fetcher.load_slide("9798554/?format=tif")


def ovarian_tissue() -> Tuple[openslide.OpenSlide, Path]:
    """Load ovarian tissue from TCGA-OV (Serous Cystadenocarcinoma).

    Source: TCGA-13-1404-01A-01-TS1.cecf7044-1d29-4d14-b137-821f8d48881e.svs
    Access: open

    Returns
    -------
    Tuple[openslide.OpenSlide, Path]
        H&E-stained WSI of ovarian tissue and its file path
    """
    return _fetcher.load_slide(
        "tcga/ovarian/TCGA-13-1404-01A-01-TS1.cecf7044-1d29-4d14-b137-821f8d48881e.svs"
    )


def prostate_tissue() -> Tuple[openslide.OpenSlide, Path]:
    """Load prostate tissue from TCGA-PRAD (Adenocarcinoma).

    Source: TCGA-CH-5753-01A-01-BS1.4311c533-f9c1-4c6f-8b10-922daa3c2e3e.svs
    Access: open

    Returns
    -------
    Tuple[openslide.OpenSlide, Path]
        H&E-stained WSI of prostate tissue and its file path
    """
    return _fetcher.load_slide(
        "tcga/prostate/TCGA-CH-5753-01A-01-BS1.4311c533-f9c1-4c6f-8b10-922daa3c2e3e.svs"
    )


# ===== Public API =====

__all__ = [
    "aorta_tissue",
    "breast_tissue",
    "breast_tissue_diagnostic_green_pen",
    "breast_tissue_diagnostic_red_pen",
    "breast_tissue_diagnostic_black_pen",
    "cmu_small_region",
    "heart_tissue",
    "ihc_breast",
    "ihc_kidney",
    "ovarian_tissue",
    "prostate_tissue",
]
