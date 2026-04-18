# Complete Documentation Index

## Overview

This documentation package provides comprehensive analysis of three pathology image processing libraries in your workspace:

1. **GlassCut** - Lightweight tile extraction library (primary)
2. **HistoLab** - Flexible, protocol-driven preprocessing library (legacy)
3. **PathoPatcher** - Production-grade preprocessing pipeline (legacy)

---

## GlassCut Documentation

### 1. [LIBRARY_ARCHITECTURE.md](LIBRARY_ARCHITECTURE.md)
**Complete architectural breakdown of GlassCut**

**Covers**:
- Core module responsibilities (Slide, Tile, TissueDetector, StainNormalizer, etc.)
- Backend architecture (OpenSlide vs cuCIM)
- Strategy pattern implementation
- Lazy evaluation with caching
- Module dependency graph
- Data flow diagrams
- Extension points for customization

**Best For**: Understanding the overall structure and relationships

### 2. [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
**Quick lookup guide for GlassCut**

**Covers**:
- Module quick reference cards
- When each module is used
- Performance considerations
- Common issues & solutions
- Extension points
- Data structure summary

**Best For**: Quick lookups and troubleshooting

### 3. [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
**7 practical examples of GlassCut usage**

**Examples**:
1. Basic slide loading and tile extraction
2. Tissue detection in tiles
3. Custom tissue detector implementation
4. Stain normalization workflow
5. Complete pipeline (extraction + tissue + normalization)
6. Error handling
7. Batch processing multiple slides

**Best For**: Learning by example

---

## PathoPatcher Documentation

### 4. [PATHOPATCHER_ARCHITECTURE.md](PATHOPATCHER_ARCHITECTURE.md)
**Complete architectural breakdown of PathoPatcher**

**Covers**:
- Configuration system (Pydantic models, hierarchy)
- CLI & entry points
- WSI interfaces (OpenSlide, cuCIM, DICOM)
- PreProcessor: main orchestration class
- Patch extraction pipeline
- Storage organization
- Utilities (masking, filtering, annotation, stain normalization)
- Multiprocessing architecture
- Module communication flows
- Design patterns (strategy, configuration objects, worker pattern)

**Best For**: Understanding the complete preprocessing pipeline

### 5. [PATHOPATCHER_QUICK_REFERENCE.md](PATHOPATCHER_QUICK_REFERENCE.md)
**Quick reference guide for PathoPatcher**

**Covers**:
- Module quick reference cards
- Configuration system overview
- WSI backend selection
- Tissue detection & masking
- Patch utilities functions
- PyTorch dataset integration
- Annotation handling
- Stain normalization vectors
- Common workflows (5-8 scenarios)
- Parameter priority & overrides
- Multiprocessing architecture
- Performance tuning
- Error handling
- Metadata output format

**Best For**: Quick configuration and troubleshooting

### 6. [PATHOPATCHER_USAGE_EXAMPLES.md](PATHOPATCHER_USAGE_EXAMPLES.md)
**11 practical examples of PathoPatcher usage**

**Examples**:
1. Basic CLI preprocessing
2. YAML configuration
3. Annotated dataset with tumor regions
4. Masked Otsu with annotation
5. Generating stain normalization vectors
6. Multi-scale context patches
7. WSI filelist processing
8. Python API (programmatic usage)
9. Error handling & validation
10. Batch processing multiple datasets
11. Loading patches with PyTorch

**Best For**: Learning by example

---

## HistoLab Documentation

### 7. [HISTOLAB_ARCHITECTURE.md](HISTOLAB_ARCHITECTURE.md)
**Complete architectural breakdown of HistoLab**

**Covers**:
- Core module responsibilities (Slide, Tile, Tiler, Filters, Masks, Scorer, Stain Normalizer)
- Protocol-based architecture and design patterns
- Comprehensive filter system (image and morphological)
- Binary mask strategy pattern
- Scoring system for tile quality assessment
- Data flow diagrams
- Module communication flows
- Extension points for customization

**Best For**: Understanding the protocol-driven, flexible architecture

### 8. [HISTOLAB_QUICK_REFERENCE.md](HISTOLAB_QUICK_REFERENCE.md)
**Quick lookup guide for HistoLab**

**Covers**:
- Installation and setup
- Core API reference (Slide, Tile, Tiler, Filters, Masks, Scorer, StainNormalizer)
- Available filters and their parameters
- Common workflows (6-7 scenarios)
- Configuration guide
- Cheat sheet for quick operations
- Troubleshooting guide
- Performance considerations

**Best For**: Quick lookups and common patterns

### 9. [HISTOLAB_USAGE_EXAMPLES.md](HISTOLAB_USAGE_EXAMPLES.md)
**10 practical examples of HistoLab usage**

**Examples**:
1. Basic tile extraction
2. Preprocessing pipeline
3. Quality-based tile selection with scoring
4. Stain normalization across slides
5. Batch processing multiple slides with progress tracking
6. Custom mask strategy implementation
7. Advanced filter composition
8. Tissue detection & visualization
9. Custom scorer implementation
10. End-to-end production pipeline

**Best For**: Learning by example

---

## Comparison Documentation

### 10. [HISTOLAB_VS_OTHERS.md](HISTOLAB_VS_OTHERS.md)
**Comprehensive comparison of all three libraries**

**Covers**:
- Quick comparison matrix (20+ features)
- Architecture overview for each library
- Module breakdown comparison
- Feature comparison (8 major categories)
- Use case recommendations for each
- Integration scenarios combining libraries
- API comparison for common operations
- Performance characteristics
- Migration paths between libraries
- Detailed feature matrix (30+ features)
- Decision tree for library selection

**Best For**: Choosing the right tool and understanding relationships

### 11. [GLASSCUT_VS_PATHOPATCHER.md](GLASSCUT_VS_PATHOPATCHER.md)
**Focused comparison of GlassCut and PathoPatcher**

**Covers**:
- High-level purpose comparison
- Feature comparison table
- Architecture differences
- Code examples showing same task, different approaches
- When to use each library
- Integration scenarios (using both together)
- Module overlap analysis
- Data flow combining both libraries
- Performance characteristics
- Ecosystem positioning
- Future integration opportunities

**Best For**: Understanding the specific GlassCut vs PathoPatcher tradeoffs

---


## Quick Navigation

### I want to understand GlassCut...
1. Start: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 5 min overview
2. Then: [LIBRARY_ARCHITECTURE.md](LIBRARY_ARCHITECTURE.md) - Deep dive
3. Finally: [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - Practical examples

### I want to understand HistoLab...
1. Start: [HISTOLAB_QUICK_REFERENCE.md](HISTOLAB_QUICK_REFERENCE.md) - 5 min overview
2. Then: [HISTOLAB_ARCHITECTURE.md](HISTOLAB_ARCHITECTURE.md) - Deep dive
3. Finally: [HISTOLAB_USAGE_EXAMPLES.md](HISTOLAB_USAGE_EXAMPLES.md) - Practical examples

### I want to understand PathoPatcher...
1. Start: [PATHOPATCHER_QUICK_REFERENCE.md](PATHOPATCHER_QUICK_REFERENCE.md) - 5 min overview
2. Then: [PATHOPATCHER_ARCHITECTURE.md](PATHOPATCHER_ARCHITECTURE.md) - Deep dive
3. Finally: [PATHOPATCHER_USAGE_EXAMPLES.md](PATHOPATCHER_USAGE_EXAMPLES.md) - Practical examples

### I want to compare them...
- Read: [HISTOLAB_VS_OTHERS.md](HISTOLAB_VS_OTHERS.md) - All three libraries
- Read: [GLASSCUT_VS_PATHOPATCHER.md](GLASSCUT_VS_PATHOPATCHER.md) - GlassCut vs PathoPatcher focus

### I want practical examples...
- GlassCut: [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
- HistoLab: [HISTOLAB_USAGE_EXAMPLES.md](HISTOLAB_USAGE_EXAMPLES.md)
- PathoPatcher: [PATHOPATCHER_USAGE_EXAMPLES.md](PATHOPATCHER_USAGE_EXAMPLES.md)

### I want to extend/customize...
- GlassCut: See "Extension Points" in [LIBRARY_ARCHITECTURE.md](LIBRARY_ARCHITECTURE.md)
- HistoLab: See "Extension Points" in [HISTOLAB_ARCHITECTURE.md](HISTOLAB_ARCHITECTURE.md)
- PathoPatcher: See "Extension Points" in [PATHOPATCHER_ARCHITECTURE.md](PATHOPATCHER_ARCHITECTURE.md)

---

## Key Insights

### GlassCut Architecture
```
Simple, focused library for WSI operations
└─ Slide (main API)
   ├─ Backend abstraction (cuCIM/OpenSlide)
   ├─ Tile representation
   ├─ Pluggable tissue detection
   ├─ Pluggable stain normalization
   └─ Lightweight utilities
```

**Key Features**:
- Strategy pattern for extensibility
- Lazy evaluation with caching
- Context manager for resource management
- Minimal dependencies
- GPU support via backend selection

### HistoLab Architecture
```
Flexible, protocol-driven library for preprocessing
└─ Slide (main API, requires processed_path)
   ├─ Backend abstraction (OpenSlide primary, large_image fallback)
   ├─ Tile with filter application
   ├─ Tiler (protocol-based extraction)
   ├─ BinaryMask (strategy for tissue detection)
   ├─ Filters system (comprehensive image/morphological chains)
   ├─ Scorer (quality assessment)
   ├─ StainNormalizer (color harmonization)
   └─ Utilities
```

**Key Features**:
- Protocol-based extensibility (Tiler, Scorer, Filter)
- Comprehensive filter system with compositions
- Multiple tissue detection strategies
- Built-in quality scoring
- Stain normalization with fit/transform pattern

### PathoPatcher Architecture
```
Production pipeline for dataset creation
└─ PreProcessor (main orchestrator)
   ├─ Configuration system (50+ parameters)
   ├─ Backend selection (cuCIM/OpenSlide/DICOM)
   ├─ Tissue detection (masked + Otsu)
   ├─ Annotation handling (GeoJSON/XML)
   ├─ Multiprocessing workers
   ├─ Storage organization
   ├─ Stain normalization (Macenko)
   ├─ Context patches (multi-scale)
   └─ Complete metadata system
```

**Key Features**:
- End-to-end preprocessing pipeline
- Configuration hierarchy (CLI/YAML/defaults)
- Parallel processing with queue workers
- Organized dataset output structure
- Automatic metadata generation
- Production-grade logging
- PyTorch dataset integration

### Positioning
- **GlassCut**: "How do I work with individual slides?"
- **HistoLab**: "How do I flexibly preprocess slides with custom strategies?"
- **PathoPatcher**: "How do I create training datasets at scale?"

---

## Module Communication at a Glance

### GlassCut Data Flow
```
User Code
    ↓ creates
Slide ←reads→ Backend (cuCIM/OpenSlide)
    ↓ extracts  
Tile ←uses→ TissueDetector + StainNormalizer
    ↓ saves
Output files
```

### HistoLab Data Flow
```
User Code
    ↓ creates (processed_path REQUIRED)
Slide ←reads→ Backend (OpenSlide/large_image)
    ↓ extracts via
Tiler (Protocol) ←creates → Tile
    ↓ processes
Filters (Compose) ← applies to Tile
    ├─ BinaryMask (Protocol) ← detects tissue
    ├─ Scorer (Protocol) ← scores quality
    └─ apply_filters() ← returns new Tile
    ↓ saves
Output files
```

### PathoPatcher Data Flow
```
CLI/Config ←parses→ PreProcessingConfig
    ↓
PreProcessor ←initializes
    ├─ Hardware selection
    ├─ WSI discovery
    ├─ Annotation loading
    └─ Storage setup
    ↓
For each slide:
    ├─ Backend ←reads→ DeepZoomGenerator
    ├─ Utils ←generates→ Tissue mask
    ├─ Utils ←processes→ Annotations
    └─ process_queue() ←sends→ Workers
        ├─ Normalize stains
        ├─ Extract context
        └─ Storage ←saves→ Organized dataset
```

---

## Features Across Libraries

### Tissue Detection
| Feature | GlassCut | HistoLab | PathoPatcher |
|---------|----------|----------|--------------|
| Basic Otsu | ✓ | ✓ | ✓ |
| Masked Otsu | ✗ | ✓ | ✓ |
| Prefilter | ✗ | ✓ | ✓ |
| Custom detectors | ✓ (via strategy) | ✓ (BinaryMask ABC) | Limited |

### Stain Normalization
| Feature | GlassCut | HistoLab | PathoPatcher |
|---------|----------|----------|--------------|
| Macenko | ✓ (via strategy) | ✓ (built-in) | ✓ (integrated) |
| Reinhardt | ✓ (via strategy) | ✗ | ✗ |
| Custom normalizers | ✓ (via strategy) | ✓ (mixin pattern) | Limited |

### Quality Scoring
| Feature | GlassCut | HistoLab | PathoPatcher |
|---------|----------|----------|--------------|
| Tissue ratio | ✓ (automatic) | ✓ (automatic) | ✗ |
| Cellularity scoring | ✗ | ✓ (built-in) | ✗ |
| Random scoring | ✗ | ✓ (for testing) | ✗ |
| Custom scorers | ✗ | ✓ (protocol) | ✗ |

### Filters & Preprocessing
| Feature | GlassCut | HistoLab | PathoPatcher |
|---------|----------|----------|--------------|
| Image filters | ✗ (external) | ✓ (built-in) | ✓ (fixed) |
| Morphological filters | ✗ (external) | ✓ (built-in) | ✓ (fixed) |
| Custom filters | ✗ | ✓ (protocol) | Limited |
| Filter composition | ✗ | ✓ (factory) | ✓ (fixed) |

### Annotation Support
| Feature | GlassCut | HistoLab | PathoPatcher |
|---------|----------|----------|--------------|
| GeoJSON parsing | ✗ | ✗ | ✓ |
| Geometry handling | ✗ | ✗ | ✓ |
| Mask generation | ✗ | ✗ | ✓ |
| Class mapping | ✗ | ✗ | ✓ |

### Output Organization
| Feature | GlassCut | HistoLab | PathoPatcher |
|---------|----------|----------|--------------|
| Structured output | ✗ | ✗ | ✓ |
| Metadata YAML | ✗ | ✗ | ✓ |
| Tissue masks | ✗ | ✗ | ✓ |
| Thumbnails | ✓ (manual) | ✗ | ✓ (automatic) |
| Context patches | ✗ | ✗ | ✓ |
| Multiple formats | ✗ | ✗ | ✓ (HDF5, etc) |

---

## Common Tasks & How to Accomplish Them

### Extract tiles from a slide
- **With GlassCut**: See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) Example 1
- **With HistoLab**: See [HISTOLAB_USAGE_EXAMPLES.md](HISTOLAB_USAGE_EXAMPLES.md) Example 1
- **With PathoPatcher**: See [PATHOPATCHER_USAGE_EXAMPLES.md](PATHOPATCHER_USAGE_EXAMPLES.md) Example 1

### Detect tissue in patches
- **With GlassCut**: See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) Example 2
- **With HistoLab**: See [HISTOLAB_USAGE_EXAMPLES.md](HISTOLAB_USAGE_EXAMPLES.md) Example 6 & 8
- **With PathoPatcher**: See [PATHOPATCHER_ARCHITECTURE.md](PATHOPATCHER_ARCHITECTURE.md#6-utils-module-utilspy)

### Apply preprocessing filters
- **With GlassCut**: Use external packages
- **With HistoLab**: See [HISTOLAB_USAGE_EXAMPLES.md](HISTOLAB_USAGE_EXAMPLES.md) Example 2 & 7
- **With PathoPatcher**: See [PATHOPATCHER_ARCHITECTURE.md](PATHOPATCHER_ARCHITECTURE.md)

### Score tile quality
- **With GlassCut**: Manual scoring
- **With HistoLab**: See [HISTOLAB_USAGE_EXAMPLES.md](HISTOLAB_USAGE_EXAMPLES.md) Example 3 & 9
- **With PathoPatcher**: Not built-in

### Apply stain normalization
- **With GlassCut**: See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) Example 4
- **With HistoLab**: See [HISTOLAB_USAGE_EXAMPLES.md](HISTOLAB_USAGE_EXAMPLES.md) Example 4
- **With PathoPatcher**: See [PATHOPATCHER_USAGE_EXAMPLES.md](PATHOPATCHER_USAGE_EXAMPLES.md) Example 5

### Process multiple slides
- **With GlassCut**: See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) Example 6
- **With HistoLab**: See [HISTOLAB_USAGE_EXAMPLES.md](HISTOLAB_USAGE_EXAMPLES.md) Example 5
- **With PathoPatcher**: See [PATHOPATCHER_USAGE_EXAMPLES.md](PATHOPATCHER_USAGE_EXAMPLES.md) Example 10

### Use with PyTorch
- **With GlassCut**: Manual dataset creation required
- **With HistoLab**: Manual dataset creation required
- **With PathoPatcher**: See [PATHOPATCHER_USAGE_EXAMPLES.md](PATHOPATCHER_USAGE_EXAMPLES.md) Example 11

---

## Diagrams Available

### GlassCut
- **Architecture diagram**: Module structure and relationships
- **Workflow sequence**: Slide loading, tile extraction, processing

### PathoPatcher
- **Architecture diagram**: Complete preprocessing pipeline
- **Workflow sequence**: End-to-end preprocessing from CLI to dataset

---

## Design Patterns Used

### GlassCut
1. **Strategy Pattern**: Pluggable backends, tissue detectors, stain normalizers
2. **Lazy Evaluation**: Properties computed on-demand and cached
3. **Context Manager**: Automatic resource cleanup
4. **Factory Pattern**: Backend selection with fallback

### HistoLab
1. **Protocol Pattern**: Tiler, Scorer, Filter all use runtime_checkable protocols
2. **Strategy Pattern**: BinaryMask ABC, FiltersComposition factory
3. **Composite Pattern**: Compose chains filters into pipelines
4. **Mixin Pattern**: TransformerStainMatrixMixin, LinalgMixin for shared functionality
5. **Lazy Evaluation**: @lazyproperty and @cached_property decorators

### PathoPatcher
1. **Strategy Pattern**: Backend selection, detector configuration
2. **Configuration as Object**: Pydantic models with validation
3. **Multiprocessing Worker**: Main thread generates work, workers consume
4. **Storage Abstraction**: Centralized directory/file management
5. **Parser Chain**: CLI → YAML → Config object

---

## Extension Points

### GlassCut: Easy to Extend
- Custom tissue detectors (inherit `TissueDetector`)
- Custom WSI backends (inherit `SlideBackend`)
- Custom stain normalizers (inherit `StainNormalizer`)

### HistoLab: Very Extensible (Protocol-Based)
- Custom extractors (implement `Tiler` protocol)
- Custom scorers (implement `Scorer` protocol)
- Custom filters (implement `Filter` protocol)
- Custom masks (inherit `BinaryMask` ABC)
- Custom morphological filters (implement `MorphologicalFilter`)

### PathoPatcher: More Complex to Extend
- Custom filters in `masking.py`
- Custom annotation formats in `patch_util.py`
- Custom backends in `wsi_interfaces/`

---

## Dependencies

### GlassCut
```
Required:
- PIL (images)
- numpy (arrays)
- scikit-image (filters, thresholding)

Optional:
- OpenSlide (CPU backend)
- cuCIM (GPU backend)
```

### PathoPatcher
```
Required:
- Everything from GlassCut
- Pydantic (configuration validation)
- scipy/rasterio (geometry, rasterization)
- torch (dataset utilities)
- shapely (polygon operations)
- pandas (data handling)
- PyYAML (configuration)
- tqdm (progress bars)

Optional:
- cuCIM (GPU acceleration)
- wsidicomizer (DICOM support)
```

---

## File Structure

Generated documentation files:
```
GlassCut/
├── LIBRARY_ARCHITECTURE.md              # GlassCut detailed architecture
├── QUICK_REFERENCE.md                   # GlassCut quick guide
├── USAGE_EXAMPLES.md                    # GlassCut 7 examples
├── HISTOLAB_ARCHITECTURE.md             # HistoLab detailed architecture
├── HISTOLAB_QUICK_REFERENCE.md          # HistoLab quick guide
├── HISTOLAB_USAGE_EXAMPLES.md           # HistoLab 10 examples
├── PATHOPATCHER_ARCHITECTURE.md         # PathoPatcher detailed architecture
├── PATHOPATCHER_QUICK_REFERENCE.md      # PathoPatcher quick guide
├── PATHOPATCHER_USAGE_EXAMPLES.md       # PathoPatcher 11 examples
├── HISTOLAB_VS_OTHERS.md                # Three-way comparison document
├── GLASSCUT_VS_PATHOPATCHER.md          # GlassCut vs PathoPatcher focused
└── INDEX.md                             # This file (master index)
```

---

## Reading Recommendations

### For Quick Understanding (15 minutes)
1. Read "Step 1" of appropriate QUICK_REFERENCE document
2. Skim the architecture diagrams
3. Read first example in USAGE_EXAMPLES

### For Complete Understanding (1-2 hours)
1. Read full QUICK_REFERENCE document
2. Read full ARCHITECTURE document
3. Work through 3-4 USAGE_EXAMPLES
4. Study design patterns

### For Implementation (2-4 hours)
1. Complete understanding from above
2. Review all USAGE_EXAMPLES for your use case
3. Study extension points if needed
4. Review error handling examples

### For Comparison (30-45 minutes)
1. Read GLASSCUT_VS_PATHOPATCHER.md completely
2. Reference QUICK_REFERENCE documents for specific features
3. Review integration scenarios

---

## Questions & Answers

### "Which library should I use?"

**Use GlassCut if**:
- You're doing research or exploration
- You need lightweight dependencies
- You want fine-grained control
- You're working with a few slides
- You're implementing custom logic

**Use HistoLab if**:
- You need flexible, composable preprocessing
- You want multiple quality scoring strategies
- You need extensible architecture (protocols)
- You're doing research with custom strategies
- You want built-in stain normalization

**Use PathoPatcher if**:
- You're creating ML training datasets
- You need to process many slides efficiently
- You require annotation support
- You want automatic organization/metadata
- You need production-grade quality control

### "Can I use multiple libraries together?"

Yes! Here are common integration patterns:

1. **GlassCut + HistoLab**: Use HistoLab's filters with GlassCut's simple I/O
2. **HistoLab + PathoPatcher**: Use HistoLab for preprocessing, PathoPatcher for batch
3. **All Three**: GlassCut for exploration, HistoLab for algorithm dev, PathoPatcher for production

See [HISTOLAB_VS_OTHERS.md](HISTOLAB_VS_OTHERS.md) Integration Scenarios for examples.

### "How do I extend these libraries?"

For customization:
- **GlassCut**: Inherit from abstract base classes
- **HistoLab**: Implement protocol interfaces (preferred) or inherit ABCs
- **PathoPatcher**: Modify utility functions or extend config objects

See "Extension Points" sections and "Custom Implementation" examples in respective documentation.

### "What are the performance characteristics?"

See tables in respective QUICK_REFERENCE and ARCHITECTURE documents:
- Single-tile: GlassCut is fastest
- Batch processing: PathoPatcher is much faster (multiprocessing)
- Preprocessing: HistoLab has rich filtering system (moderate speed)
- GPU support: GlassCut (cuCIM) and HistoLab (large_image compatible)

### "Where do I find examples for my specific use case?"

Check the index in USAGE_EXAMPLES documents:
- **GlassCut**: 7 examples covering most cases
- **HistoLab**: 10 examples covering research to production
- **PathoPatcher**: 11 examples covering production scenarios

Or use the decision tree in [HISTOLAB_VS_OTHERS.md](HISTOLAB_VS_OTHERS.md).

### "How do I debug issues?"

1. Check "Error Handling & Troubleshooting" in respective QUICK_REFERENCE
2. Review relevant examples in USAGE_EXAMPLES
3. Check logging output (all support verbose logging)
4. Verify configuration/parameters
5. Test with small subset of data first


---

## Updates & Maintenance

These documents describe the current state of:
- **GlassCut**: Main library in `glasscut/`
- **HistoLab**: Legacy library in `__legacy__/histolab/`
- **PathoPatcher**: Legacy library in `__legacy__/PathoPatcher/`

**Last Updated**: Current Session
**Total Files**: 12 documentation files
**Total Lines**: 20,000+ lines of documentation
**Total Examples**: 28 practical examples (7 GlassCut, 10 HistoLab, 11 PathoPatcher)

For updates:
1. Review module files for changes
2. Update relevant documentation sections
3. Add new examples if new features added
4. Update comparison document if API changes
5. Keep INDEX.md synchronized with new documents


---

## Contact & Support

For questions about:
- **Code structure**: Review ARCHITECTURE documents
- **Usage**: Review USAGE_EXAMPLES
- **Configuration**: Review QUICK_REFERENCE
- **Integration**: Review GLASSCUT_VS_PATHOPATCHER

---

## License & Attribution

Documentation generated from source code analysis.
Respects original licenses of both libraries.

