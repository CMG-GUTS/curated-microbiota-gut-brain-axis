# v0.1.0 — Initial Multimodal Benchmark Preview

The first preview of **Curated Microbiota–Gut–Brain Axis** introduces an installable Python interface for paired gut microbiota, BrainHarmonix-derived features and participant-level phenotypes in the GUTBRAIN collection.

## Highlights

- Access to aligned microbiota and BrainHarmonix feature matrices for 88 participants.
- A registry of 32 selectable prediction targets, including the primary outcomes `Zung_S`, `STAI_R` and `STAI_S`.
- Target-specific regression and classification adapters for `mllabiome`.
- Default 5 × 3 nested cross-validation configuration with a fixed random seed.
- Lazy dataset retrieval, local caching and data-integrity checks.
- An example multimodal regression benchmark and a documented Python API.

## Getting started

```bash
python -m pip install "git+https://github.com/CMG-GUTS/curated--microbiota-gut-brain-axis.git"
```

```python
from curated_microbiota_gut_brain_axis.collections import gutbrain

print(gutbrain.targets(primary_only=True))
print(gutbrain.fetch())
```

This is an initial research preview. Benchmark results should be interpreted in light of the small sample size and the absence of external-cohort validation.
