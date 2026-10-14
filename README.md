# Curated Microbiota–Gut–Brain Axis

**Multimodal microbiota–gut–brain axis data for reproducible machine-learning benchmarking.**

`curated-microbiota-gut-brain-axis` provides a Python interface to the GUTBRAIN collection, pairing gut microbiota profiles with BrainHarmonix features and participant-level phenotypes. The collection supports regression and classification benchmarks and integrates with [`mllabiome`](https://github.com/CMG-GUTS/mllabiome).

## Benchmark at a glance

| Property | GUTBRAIN collection |
| --- | --- |
| Participants | 88 |
| Microbiota features | 670 |
| BrainHarmonix features | 768 |
| Prediction outcomes | 32 metadata columns |
| Primary outcomes | `Zung_S`, `STAI_R`, `STAI_S` |
| Evaluation | 5-fold outer × 3-fold inner nested cross-validation |
| Default random seed | 42 |
| Benchmark identifier | `gutbrain-multimodal-v1` |

The collection combines taxonomic profiles, derived BrainHarmonix embeddings and participant metadata. It does not include raw sequencing reads or raw neuroimaging acquisitions.

## Installation

Python 3.10–3.13 is supported. Install from GitHub:

```bash
python -m pip install "git+https://github.com/CMG-GUTS/curated--microbiota-gut-brain-axis.git"
```

For model benchmarking, install [`mllabiome`](https://github.com/CMG-GUTS/mllabiome) in the same environment:

```bash
python -m pip install mllabiome
```

The dataset interface is independent of `mllabiome`; only the optional benchmark adapter requires it. Data are hosted by this repository, not the modeling framework.

## Quick start

```python
from curated_microbiota_gut_brain_axis.collections import gutbrain

print(gutbrain.targets(primary_only=True))
print(gutbrain.target("STAI_R"))

root = gutbrain.fetch()
print(gutbrain.metadata)
print(gutbrain.microbiota)
print(gutbrain.brainharmonix)
print(gutbrain.validate(target="STAI_R"))
```

Data files are retrieved on first access and cached locally. Subsequent calls reuse cached files. See [Data access](#data-access) for cache options.

## Prediction targets

The three primary gut–brain axis prediction outcomes are:

| Target | Outcome | Task |
| --- | --- | --- |
| `Zung_S` | Zung depression score | Regression |
| `STAI_R` | Trait anxiety score | Regression |
| `STAI_S` | State anxiety score | Regression |

All 32 non-identifier metadata columns can be selected as prediction targets.

| Domain | Targets | Task |
| --- | --- | --- |
| Mental health | `Zung_S`, `STAI_R`, `STAI_S` | Regression |
| Autonomic physiology | `SDNN_all`, `RMSSD`, `ln_LF_all`, `ln_HF_all`, `SQ_all`, `SQ`, `LF`, `HF` | Regression |
| Demographic and anthropometric | `Age`, `BMI`, `WHR` | Regression |
| Coded metadata | `Parasite`, `LoE`, `SES`, `PA` | Classification |
| Dietary intake | `Kcal`, `Prot`, `TF`, `SatFat`, `MUF`, `Poly_InsFat`, `Chol`, `Carb`, `Fiber` | Regression |
| Microbiota-related measures | `Chao1`, `Shannon`, `InvSimpson`, `FR_rumi_unc`, `FR_rumi_fam` | Regression |

```python
from curated_microbiota_gut_brain_axis.collections import gutbrain

all_targets = gutbrain.targets()
primary_targets = gutbrain.targets(primary_only=True)
target_info = gutbrain.target("Zung_S")
```

`gutbrain.target(name)` reports the metadata column and corresponding machine-learning task. The `zung_depression` alias maps to `Zung_S`. Coded metadata should be interpreted in the context of the source study; their category semantics are not inferred by this package.

## Multimodal benchmarking with mllabiome

The collection exposes `mll.Samples`, the two `mll.Modality` definitions and microbiota representations through a target-selectable adapter:

```python
from pathlib import Path

from curated_microbiota_gut_brain_axis.collections import gutbrain
from mllabiome import mll
from sklearn.ensemble import RandomForestRegressor

TARGET = "Zung_S"
DATA = gutbrain.mllabiome(target=TARGET)
EVALUATION = gutbrain.splits(target=TARGET).mllabiome(
    optimize_metric="RMSE",
    n_jobs="auto",
)

SWEEP = mll.Sweep(
    **DATA,
    title="GUTBRAIN multimodal benchmark",
    experiment_dir=Path("runs/GUTBRAIN-MULTIMODAL-NCV"),
    learners=(("RandomForest", RandomForestRegressor(random_state=42)),),
    evaluation=EVALUATION,
    transformations=(mll.Transformation("identity"),),
    integrations=(
        mll.Integration("intermediate_joint_pca", n_components=(16, 32)),
        mll.Integration("late_super_learner"),
    ),
)
```

`gutbrain.mllabiome(target=...)` returns a mapping with `data=None`, `samples`, `modalities` and `representations`. Pass it into `mll.Sweep` using `**DATA` for the multimodal API.

The included [`examples/gutbrain_multimodal.py`](examples/gutbrain_multimodal.py) provides a more extensive regression sweep with preprocessing, integration and ensemble configurations. For categorical outcomes, choose classification estimators; the target adapter sets the task to `classification`.

## Evaluation protocol

```python
from curated_microbiota_gut_brain_axis.collections import gutbrain

regression = gutbrain.splits(target="STAI_R").mllabiome()
classification = gutbrain.splits(target="Parasite").mllabiome()
```

The default evaluation uses nested cross-validation with five outer folds, three inner folds, one repetition and random seed 42. The default optimization metric is `RMSE` for regression and `log_loss` for classification. These settings describe a reproducible resampling design; the package does not provide precomputed, immutable fold assignments.

## Data access

The dataset consists of three tab-separated files, linked by `participant_id`:

| File | Content |
| --- | --- |
| `participants.tsv` | Participant identifiers and 32 outcome variables |
| `HEALTHY_COLOMBIA_microbiota_profiles.tsv` | 670 microbiota features across 88 participants |
| `brainharmonix_f_mllabiome.tsv` | 768 BrainHarmonix features across 88 participants |

Feature matrices use the original feature-by-participant layout. Accessing the collection downloads files when they are not cached and validates sample alignment and expected feature counts. Where a versioned dataset manifest is available, downloaded files are also checked against SHA-256 digests.

To use an existing local copy of the three TSV files:

```bash
export CURATED_GUTBRAIN_DATA_DIR=/path/to/GUTBRAIN
```

To specify a download cache location:

```bash
export CURATED_GUTBRAIN_CACHE_DIR=/path/to/cache
```

The collection retrieves data exclusively from the versioned dataset release in this repository. Files are verified using the release manifest and cached locally. Network access is required for first retrieval unless a local data directory is configured.

## Collection discovery

```python
from curated_microbiota_gut_brain_axis import collections

collections.available()
collections.available(problem_type="regression")
collections.available(problem_type="classification")
collections.available(target="STAI_S")
```

## Interpretation and limitations

GUTBRAIN contains 88 participants, so comparisons among high-dimensional modalities require careful control of model complexity and selection bias. Nested cross-validation estimates predictive performance but does not establish external-cohort generalizability. Changes in target distributions, preprocessing or feature definitions can also affect comparability.

Microbiota-derived outcomes such as `Shannon` and `Chao1` are computed from microbiota data. Predicting these quantities from the same profiles measures reconstruction or internal consistency rather than independent biological prediction. Associations and model explanations are not evidence of causation.

## Data provenance and citation

The GUTBRAIN collection brings together derivatives of [BioProject PRJNA1000574](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1000574) and [OpenNeuro ds004648](https://openneuro.org/datasets/ds004648). Please cite the original study and data resources alongside this package, and cite `mllabiome` when using its benchmarking framework.

## License

The package's source code is distributed under the [MIT License](LICENSE). Source datasets may be subject to separate attribution, privacy and reuse requirements.
