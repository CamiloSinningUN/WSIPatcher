# PathoPatcher - Usage Examples

This document shows practical examples of how to use PathoPatcher for different preprocessing scenarios.

---

## Example 1: Basic WSI Preprocessing (CLI)

### Command Line:
```bash
python -m pathopatch.wsi_extraction \
  --wsi_paths /data/slides \
  --output_path /data/output_dataset \
  --patch_size 256 \
  --patch_overlap 0 \
  --target_mag 20 \
  --hardware_selection cucim \
  --processes 8 \
  --filter_patches True
```

### What Happens:
1. Discovers all .svs files in `/data/slides`
2. For each slide:
   - Opens with cuCIM (GPU backend, fallback to OpenSlide)
   - Generates tissue mask (Otsu thresholding)
   - Finds grid of patches (256x256 pixels)
   - Filters patches by tissue ratio
   - Extracts and saves patches
3. Creates output structure:
   ```
   output_dataset/
   ├── slide_1/
   │   ├── patches/
   │   ├── metadata/
   │   ├── tissue_masks/
   │   ├── thumbnails/
   │   └── metadata.yaml
   ├── slide_2/
   └── ...
   ```

---

## Example 2: Using YAML Configuration File

### Configuration File: `config.yaml`
```yaml
# Dataset paths
wsi_paths: /data/slides
output_path: /data/output_dataset
wsi_extension: svs
wsi_filelist: null  # Unused if wsi_paths provided

# Patch extraction
patch_size: 512
patch_overlap: 10  # 10% overlap
target_mag: 20     # 20x magnification
context_scales: [2, 4]  # Extract 2x and 4x context

# Tissue detection
filter_patches: true
masked_otsu: false
apply_prefilter: true

# Stain normalization
normalize_stains: true
normalization_vector_json: /data/macenko_vectors.json

# Processing
hardware_selection: cucim
processes: 8
overwrite: false

# Logging
log_level: info
log_path: /data/logs
```

### Command:
```bash
python -m pathopatch.wsi_extraction --config config.yaml
```

### Module Communication:
```
cli.py
  ↓
PreProcessingParser.get_config()
  ├─ Load YAML
  ├─ Override with CLI args
  └─ Create PreProcessingConfig
  
PreProcessor.__init__()
  ├─ _set_wsi_paths() → Find .svs files
  ├─ _set_hardware() → Load cuCIM/OpenSlide
  └─ _set_tissue_detector() → Configure masking
  
PreProcessor.sample_patches_dataset()
  ├─ For each WSI:
  │   ├─ _prepare_wsi()
  │   │   ├─ Backend.open_slide()
  │   │   ├─ masking.generate_tissue_mask()
  │   │   └─ Storage(create directory)
  │   │
  │   └─ process_queue()
  │       ├─ compute_interesting_patches()
  │       ├─ Queue patches to workers
  │       └─ queue_worker() saves patches
```

---

## Example 3: Annotated Dataset with Tumor Regions

### Configuration:
```yaml
wsi_paths: /data/slides
output_path: /data/annotated_dataset
annotation_paths: /data/annotations  # GeoJSON files
annotation_extension: json

# Only extract patches within annotated regions
save_only_annotated_patches: true

# Store class masks for each patch
store_masks: true

# Map class names to indices
label_map_file: /data/label_map.json

# Generate thumbnails with annotations
generate_thumbnails: true

patch_size: 256
target_mag: 40
```

### Label Map File: `label_map.json`
```json
{
  "tumor": 1,
  "stroma": 2,
  "adipose": 3,
  "background": 0
}
```

### How It Works:
```
1. Load annotations from GeoJSON
   ├─ annotation_conversion.parse_geojson()
   ├─ Create polygons for each class
   └─ Store as List[Polygon]

2. For each patch:
   ├─ Check if overlaps with any annotation
   ├─ If save_only_annotated_patches:
   │   └─ Only save if overlaps
   ├─ Extract patch
   ├─ Generate per-patch mask (matches patch pixels)
   ├─ Save patch PNG
   ├─ Save patch mask NPY
   └─ Save metadata with annotation labels

3. Output per patch:
   ├── patch_0_0.png (RGB image)
   ├── patch_0_0.npy (binary mask or class mask)
   └── patch_0_0.yaml (includes annotation_labels: [1, 2])
```

---

## Example 4: Masked Otsu with Annotation

### Scenario: 
Use annotation region to mask tissue detection (e.g., "tissue" annotation marks valid analysis area)

### Configuration:
```yaml
patch_size: 512
target_mag: 20

# Annotation-based masking
annotation_paths: /data/annotations
masked_otsu: true
otsu_annotation: tissue          # Use "tissue" annotation for masking

# Additional filtering
apply_prefilter: true
filter_patches: true

# Only annotated areas
incomplete_annotations: false    # All slides must have tissue annotation
```

### Processing Flow:
```
generate_tissue_mask():
  1. Load image at target magnification
  2. Filter annotations by label "tissue"
  3. Create mask from tissue polygons
  4. Apply mask to tissue image
  5. Run Otsu thresholding on masked image
  6. Return binary tissue mask
     (only within tissue annotation boundary)

Result:
  - Only patches within tissue-annotated regions are extracted
  - Much better accuracy than blind Otsu
  - Useful for multi-tissue slides
```

---

## Example 5: Generating Stain Normalization Vectors

### Step 1: Generate Vectors from Reference Slide

```bash
python -m pathopatch.macenko_vector_generation \
  --wsi_paths reference_slide.svs \
  --save_json_path macenko_vectors.json \
  --log_level info
```

### Generated File: `macenko_vectors.json`
```json
{
  "hematoxylin": [0.642, 0.711, 0.289],
  "eosin": [0.078, 0.991, 0.110],
  "dab": [0.267, 0.567, 0.778]
}
```

### Step 2: Use in Preprocessing Pipeline

```yaml
wsi_paths: /data/slides
output_path: /data/normalized_dataset
normalize_stains: true
normalization_vector_json: /data/macenko_vectors.json
```

### Module Communication:
```
queue_worker() (multiprocessing):
  1. Dequeue patch (PIL.Image)
  2. If normalize_stains=True:
     ├─ macenko_normalization(patch, vector_path)
     │   ├─ Load stain vectors from JSON
     │   ├─ Convert RGB to OD space
     │   ├─ Apply stain deconvolution
     │   ├─ Normalize to reference vectors
     │   └─ Convert back to RGB
     └─ Save normalized patch
  3. storage.save_elem_to_disk()
  
Result:
  - All patches have consistent stain colors
  - Reduced batch effects
  - Better for ML training
```

---

## Example 6: Multi-Scale Context Patches

### Configuration:
```yaml
patch_size: 256              # Main patch size
context_scales: [2, 4]       # 2x and 4x context

target_mag: 20
```

### Output Structure:
```
output_dataset/slide_1/
├── patches/
│   ├── slide_1_0_0.png           # 256x256 (main)
│   ├── slide_1_0_1.png
│   └── ...
├── context/
│   ├── scale_2x/
│   │   ├── context_0_0_2x.png    # 512x512 (2x context)
│   │   ├── context_0_1_2x.png
│   │   └── ...
│   └── scale_4x/
│       ├── context_0_0_4x.png    # 1024x1024 (4x context)
│       ├── context_0_1_4x.png
│       └── ...
```

### Patch Metadata with Context:
```yaml
coordinates: [1024, 2048]
patch_size: 256
tissue_ratio: 0.85
context:
  scale_2x:
    coordinates: [512, 1024]   # Adjusted for scale
    patch_size: 512
  scale_4x:
    coordinates: [256, 512]    # Adjusted for scale
    patch_size: 1024
```

### Use Case: Multi-scale Neural Networks
```python
# Load main patch and contexts
main_patch = Image.open("patches/slide_1_0_0.png")           # 256x256
context_2x = Image.open("context/scale_2x/context_0_0_2x.png")  # 512x512
context_4x = Image.open("context/scale_4x/context_0_0_4x.png")  # 1024x1024

# Stack for multi-scale model
model_input = {
    'patch_256': torch.tensor(main_patch),
    'context_512': torch.tensor(context_2x),
    'context_1024': torch.tensor(context_4x)
}

# Neural network uses all scales for better context understanding
prediction = model(model_input)
```

---

## Example 7: Processing with WSI Filelist

### Use Case: Process specific slides or provide custom metadata

### CSV Filelist: `wsi_filelist.csv`
```
path,slide_mpp,magnification,batch
/data/slides/patient_001.svs,0.5,40,batch_1
/data/slides/patient_002.svs,0.5,40,batch_1
/data/slides/patient_003.svs,0.25,20,batch_2
/rare_format/patient_004.ndpi,0.3,30,batch_2
```

### Configuration:
```yaml
# Instead of wsi_paths, use filelist
wsi_filelist: /data/wsi_filelist.csv
output_path: /data/output_dataset

# Use magnification from CSV if target_mag not specified
target_mag: null
```

### Advantage:
- Process only specific slides
- Override magnification per slide
- Include custom metadata (batch, cohort, etc.)
- Mix different WSI formats/resolutions

---

## Example 8: Python API (Programmatic Usage)

### Complete Pipeline in Python:
```python
from pathopatch.cli import PreProcessingParser, PreProcessingConfig
from pathopatch.patch_extraction.patch_extraction import PreProcessor
from pathlib import Path
import json

# Option 1: Using CLI parser with YAML
parser = PreProcessingParser()
config, logger = parser.get_config()  # Reads CLI args + YAML

# Option 2: Direct configuration (programmatic)
config = PreProcessingConfig(
    wsi_paths="/data/slides",
    output_path="/data/output",
    wsi_extension="svs",
    patch_size=256,
    patch_overlap=0,
    target_mag=20,
    hardware_selection="cucim",
    processes=8,
    normalize_stains=True,
    normalization_vector_json="/data/macenko.json",
    filter_patches=True,
    apply_prefilter=True,
    log_level="info"
)

# Create preprocessor
preprocessor = PreProcessor(slide_processor_config=config)

# Run pipeline
preprocessor.sample_patches_dataset()

# Now read results
output_dir = Path("/data/output")
for slide_dir in output_dir.iterdir():
    if slide_dir.is_dir():
        metadata_path = slide_dir / "metadata.yaml"
        print(f"Processed: {slide_dir.name}")
        
        # Read slide metadata
        with open(metadata_path) as f:
            slide_meta = yaml.safe_load(f)
            print(f"  Patches: {slide_meta['patch_count']}")
            print(f"  Tissue coverage: {slide_meta['tissue_coverage']:.1%}")
```

---

## Example 9: Error Handling & Validation

```python
from pathopatch.cli import PreProcessingParser
from pathopatch.patch_extraction.patch_extraction import PreProcessor
from pathopatch.utils.exceptions import WrongParameterException, UnalignedDataException

try:
    parser = PreProcessingParser()
    config, logger = parser.get_config()
    
    # Validate paths exist
    if not Path(config.wsi_paths).exists():
        raise FileNotFoundError(f"WSI path not found: {config.wsi_paths}")
    
    # Validate annotation paths if provided
    if config.annotation_paths:
        if not Path(config.annotation_paths).exists():
            raise FileNotFoundError(f"Annotation path not found: {config.annotation_paths}")
    
    # Create preprocessor
    preprocessor = PreProcessor(slide_processor_config=config)
    
    # Run preprocessing
    preprocessor.sample_patches_dataset()
    
    logger.info("Preprocessing completed successfully!")

except FileNotFoundError as e:
    logger.error(f"File error: {e}")
    exit(1)
    
except WrongParameterException as e:
    logger.error(f"Parameter error: {e}")
    logger.info("Check configuration file and CLI arguments")
    exit(1)
    
except UnalignedDataException as e:
    logger.error(f"Data alignment error: {e}")
    logger.info("Annotations may not match slides")
    exit(1)
    
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    exit(1)
```

---

## Example 10: Batch Processing Multiple Datasets

### Configuration for Multiple Projects:

```yaml
# common_config.yaml
patch_size: 256
target_mag: 20
hardware_selection: cucim
processes: 8
normalize_stains: true
filter_patches: true
```

```bash
#!/bin/bash
# process_all_datasets.sh

COMMON_CONFIG="common_config.yaml"
NORMALIZATION_VECTOR="/data/macenko_vectors.json"

# Dataset 1: Clean slides
python -m pathopatch.wsi_extraction \
  --config $COMMON_CONFIG \
  --wsi_paths /data/project1/slides \
  --output_path /data/project1/output \
  --normalization_vector_json $NORMALIZATION_VECTOR

# Dataset 2: With annotations
python -m pathopatch.wsi_extraction \
  --config $COMMON_CONFIG \
  --wsi_paths /data/project2/slides \
  --output_path /data/project2/output \
  --annotation_paths /data/project2/annotations \
  --save_only_annotated_patches true \
  --normalization_vector_json $NORMALIZATION_VECTOR

# Dataset 3: Different magnification
python -m pathopatch.wsi_extraction \
  --config $COMMON_CONFIG \
  --wsi_paths /data/project3/slides \
  --output_path /data/project3/output \
  --target_mag 40 \
  --patch_size 512 \
  --normalization_vector_json $NORMALIZATION_VECTOR

# Collect statistics
echo "Dataset Statistics:" > processing_summary.txt
for dataset in /data/project*/output; do
    echo "" >> processing_summary.txt
    echo "Dataset: $(basename $(dirname $dataset))" >> processing_summary.txt
    find $dataset -name "metadata.yaml" | wc -l >> processing_summary.txt
done
```

---

## Example 11: Loading Processed Patches with PyTorch

```python
from pathlib import Path
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision.transforms import Compose, ToTensor, Normalize
import yaml

class PathoPatcherDataset(Dataset):
    """PyTorch dataset for processed PathoPatcher patches"""
    
    def __init__(self, dataset_path: str, transform=None, return_meta=False):
        self.dataset_path = Path(dataset_path)
        self.transform = transform
        self.return_meta = return_meta
        self.patches = []
        
        # Discover all patches
        for slide_dir in self.dataset_path.iterdir():
            if slide_dir.is_dir():
                patches_dir = slide_dir / "patches"
                if patches_dir.exists():
                    for patch_file in patches_dir.glob("*.png"):
                        meta_file = slide_dir / "metadata" / patch_file.stem / ".yaml"
                        self.patches.append({
                            'image': patch_file,
                            'meta': slide_dir / "metadata" / f"{patch_file.stem}.yaml"
                        })
    
    def __len__(self):
        return len(self.patches)
    
    def __getitem__(self, idx):
        patch_info = self.patches[idx]
        
        # Load image
        image = Image.open(patch_info['image']).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
        else:
            image = torch.tensor(image)
        
        if self.return_meta:
            # Load metadata
            with open(patch_info['meta']) as f:
                meta = yaml.safe_load(f)
            return image, meta
        
        return image

# Create dataset
transforms = Compose([
    ToTensor(),
    Normalize(mean=[0.485, 0.456, 0.406],
              std=[0.229, 0.224, 0.225])
])

dataset = PathoPatcherDataset(
    dataset_path="/data/output_dataset",
    transform=transforms,
    return_meta=True
)

# Create dataloader
dataloader = DataLoader(
    dataset,
    batch_size=32,
    shuffle=True,
    num_workers=4
)

# Training loop example
for batch_idx, (images, metadata_list) in enumerate(dataloader):
    # images: [B, 3, 256, 256]
    # metadata_list: list of B dicts
    
    print(f"Batch {batch_idx}:")
    print(f"  Images: {images.shape}")
    print(f"  First patch tissue ratio: {metadata_list[0]['tissue_ratio']:.1%}")
    
    # Forward pass
    # predictions = model(images)
    # loss = criterion(predictions, targets)
```

---

## Module Communication Summary

| Operation | Modules Involved | Flow |
|-----------|------------------|------|
| Load config | cli.py, config.py | CLI args → YAML → PreProcessingConfig |
| Select backend | PreProcessor, wsi_interfaces | Hardware setting → cuCIM or OpenSlide |
| Generate masks | masking.py, utils | Annotation + Otsu → Binary tissue mask |
| Find patches | patch_util.py | Tissue mask → Patch grid coordinates |
| Extract patches | wsi_interfaces, Backend | DeepZoomGenerator → PIL.Image |
| Save patches | Storage, multiprocessing | queue_worker → save_elem_to_disk → Files |
| Normalize stains | patch_util.py, macenko | Load vectors → Apply to batch → Save |
| Load for ML | patch_dataset.py, utils | Patches → Dataset → DataLoader → Model |

