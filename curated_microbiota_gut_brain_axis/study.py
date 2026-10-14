from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._data import CATEGORICAL_TARGETS, PRIMARY_TARGETS, TARGET_COLUMNS, validate
from ._fetch import cached as _cached
from ._fetch import fetch as _fetch


@dataclass(frozen=True, slots=True)
class Target:
    name: str
    column: str
    task: str
    problem_type: str


@dataclass(frozen=True, slots=True)
class EvaluationDesign:
    protocol: str = "nested_cv"
    outer_folds: int = 5
    inner_folds: int = 3
    repeats: int = 1
    random_state: int = 42


@dataclass(frozen=True, slots=True)
class SplitSet:
    design: EvaluationDesign = EvaluationDesign()
    benchmark: str = "gutbrain-multimodal-v1"
    task: str = "regression"

    def mllabiome(self, **settings: Any) -> Any:
        try:
            from mllabiome import mll
        except ImportError as exc:
            raise ImportError("Install mllabiome to use the evaluation adapter") from exc
        values = {
            "protocol": self.design.protocol,
            "outer_folds": self.design.outer_folds,
            "inner_folds": self.design.inner_folds,
            "repeats": self.design.repeats,
            "random_state": self.design.random_state,
            "optimize_metric": "log_loss" if self.task == "classification" else "RMSE",
            "n_jobs": "auto",
            "benchmark_id": self.benchmark,
        }
        values.update(settings)
        return mll.Evaluation(**values)


@dataclass(frozen=True, slots=True)
class Study:
    name: str = "gutbrain"
    title: str = "GUTBRAIN microbiota and BrainHarmonix"
    version: str = "0.1.0"
    accession: str = "PRJNA1000574;ds004648"
    condition: str = "gut_brain_axis"
    assay: str = "16s_v3_v4_and_brainharmonix"
    role: str = "benchmark"
    status: str = "ready"
    samples: int = 88
    microbiota_features: int = 670
    brainharmonix_features: int = 768

    @property
    def path(self) -> Path:
        return _fetch()

    @property
    def cached(self) -> bool:
        return _cached()

    @property
    def metadata(self) -> Path:
        return self.path / "participants.tsv"

    @property
    def microbiota(self) -> Path:
        return self.path / "HEALTHY_COLOMBIA_microbiota_profiles.tsv"

    @property
    def brainharmonix(self) -> Path:
        return self.path / "brainharmonix_f_mllabiome.tsv"

    def targets(self, primary_only: bool = False) -> tuple[str, ...]:
        return PRIMARY_TARGETS if primary_only else TARGET_COLUMNS

    def target(self, name: str = "Zung_S") -> Target:
        canonical = "Zung_S" if name == "zung_depression" else name
        if canonical not in TARGET_COLUMNS:
            raise KeyError(name)
        task = "classification" if canonical in CATEGORICAL_TARGETS else "regression"
        return Target(canonical, canonical, task, task)

    def fetch(self) -> Path:
        return self.path

    def validate(self, target: str = "Zung_S") -> dict[str, int]:
        return validate(self.path, self.target(target).column)

    def splits(self, target: str = "Zung_S", benchmark: str = "gutbrain-multimodal-v1") -> SplitSet:
        selected = self.target(target)
        if benchmark != "gutbrain-multimodal-v1":
            raise KeyError(benchmark)
        return SplitSet(benchmark=benchmark, task=selected.task)

    def mllabiome(self, target: str = "Zung_S") -> dict[str, Any]:
        selected = self.target(target)
        try:
            from mllabiome import mll
        except ImportError as exc:
            raise ImportError("Install mllabiome to use the multimodal adapter") from exc
        root = self.path
        validate(root, selected.column)
        return {
            "data": None,
            "samples": mll.Samples(
                path=root / "participants.tsv",
                sample_id_col="participant_id",
                target_col=selected.column,
                task=selected.task,
            ),
            "modalities": (
                mll.Modality(
                    "microbiota",
                    path=root / "HEALTHY_COLOMBIA_microbiota_profiles.tsv",
                    format="matrix_tsv",
                    primary=True,
                ),
                mll.Modality(
                    "brainharmonix",
                    path=root / "brainharmonix_f_mllabiome.tsv",
                    format="matrix_tsv",
                ),
            ),
            "representations": {"microbiota": (("species", ("species",)),)},
        }
