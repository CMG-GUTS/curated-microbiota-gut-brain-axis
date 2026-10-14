from __future__ import annotations

import csv
from pathlib import Path

import pytest

from curated_microbiota_gut_brain_axis._data import CATEGORICAL_TARGETS, TARGET_COLUMNS


@pytest.fixture
def sample_data(tmp_path: Path) -> Path:
    ids = [f"sub-MIC{i:03d}" for i in range(1, 89)]
    participants = tmp_path / "participants.tsv"
    with participants.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(("participant_id", *TARGET_COLUMNS))
        writer.writerows(
            (value, *(1 + i % 3 if col in CATEGORICAL_TARGETS else 30.0 + i / 10 for col in TARGET_COLUMNS))
            for i, value in enumerate(ids)
        )
    for name, features, prefix in (
        ("HEALTHY_COLOMBIA_microbiota_profiles.tsv", 670, "k__Bacteria___s__"),
        ("brainharmonix_f_mllabiome.tsv", 768, "embedding_"),
    ):
        with (tmp_path / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, delimiter="\t")
            writer.writerow(("feature_id", *reversed(ids)))
            for i in range(features):
                writer.writerow((f"{prefix}{i:04d}", *([i % 11] * 88)))
    return tmp_path
