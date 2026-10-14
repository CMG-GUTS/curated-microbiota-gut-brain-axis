# GUTBRAIN dataset

The GUTBRAIN collection consists of participant metadata and two aligned feature matrices.

| Data asset | Description |
| --- | --- |
| `participants.tsv` | Participant identifiers, mental-health scores, physiological measures, dietary variables and other outcomes |
| `HEALTHY_COLOMBIA_microbiota_profiles.tsv` | Taxonomic microbiota features, with participants as columns |
| `brainharmonix_f_mllabiome.tsv` | BrainHarmonix-derived features, with participants as columns |

The Python interface retrieves files from the curated collection’s versioned data release on first access, verifies their integrity, validates participant alignment and caches them locally. Dataset files are distributed through this repository rather than embedded in the Python wheel.

```python
from curated_microbiota_gut_brain_axis.collections import gutbrain

root = gutbrain.fetch()
metadata = gutbrain.metadata
microbiota = gutbrain.microbiota
brainharmonix = gutbrain.brainharmonix
```

See the [project README](../README.md) for installation, supported prediction targets and benchmarking examples.
