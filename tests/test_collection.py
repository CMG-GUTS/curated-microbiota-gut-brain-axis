from __future__ import annotations

import csv
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from curated_microbiota_gut_brain_axis import collections
from curated_microbiota_gut_brain_axis._data import validate
from curated_microbiota_gut_brain_axis.collections import gutbrain


def test_registry() -> None:
    assert collections.available() == (gutbrain,)
    assert collections.available(condition="none") == ()
    assert collections.available(problem_type="regression") == (gutbrain,)
    assert collections.available(benchmark=False) == ()
    assert gutbrain.target().column == "Zung_S"
    assert gutbrain.splits().design.outer_folds == 5
    with pytest.raises(KeyError):
        gutbrain.target("other")


def test_validation(sample_data: Path) -> None:
    assert validate(sample_data)["participants"] == 88
    assert validate(sample_data)["brainharmonix_f_mllabiome.tsv"] == 768


def test_misalignment(sample_data: Path) -> None:
    path = sample_data / "participants.tsv"
    with path.open(newline="", encoding="utf-8") as handle:
        content = list(csv.reader(handle, delimiter="\t"))
    content[1][0] = "other"
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle, delimiter="\t").writerows(content)
    with pytest.raises(ValueError, match="align"):
        validate(sample_data)


def test_adapters(sample_data: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CURATED_GUTBRAIN_DATA_DIR", str(sample_data))
    proxy = SimpleNamespace(
        Samples=lambda **kwargs: SimpleNamespace(**kwargs),
        Modality=lambda name, **kwargs: SimpleNamespace(name=name, primary=kwargs.pop("primary", False), **kwargs),
        Evaluation=lambda **kwargs: SimpleNamespace(**kwargs),
    )
    monkeypatch.setitem(sys.modules, "mllabiome", SimpleNamespace(mll=proxy))
    data = gutbrain.mllabiome()
    assert data["data"] is None
    assert data["samples"].target_col == "Zung_S"
    assert data["samples"].path == sample_data / "participants.tsv"
    assert [value.name for value in data["modalities"]] == ["microbiota", "brainharmonix"]
    assert data["modalities"][0].primary
    assert not data["modalities"][1].primary
    assert data["modalities"][1].format == "matrix_tsv"
    assert data["representations"] == {"microbiota": (("species", ("species",)),)}
    evaluation = gutbrain.splits().mllabiome()
    assert evaluation.optimize_metric == "RMSE"
    assert (evaluation.protocol, evaluation.outer_folds, evaluation.inner_folds) == ("nested_cv", 5, 3)
    assert evaluation.random_state == 42
    assert gutbrain.cached
    assert gutbrain.validate()["participants"] == 88


def test_import_script(sample_data: Path, tmp_path: Path) -> None:
    import subprocess

    import json

    repo = Path(__file__).resolve().parent.parent
    destination = tmp_path / "copy" / "data"
    result = subprocess.run(
        [sys.executable, str(repo / "scripts" / "import_gutbrain.py"), "--source", str(sample_data), "--destination", str(destination)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    manifest = json.loads((destination.parent / "release-manifest.json").read_text())
    assert manifest["schema"] == 1
    assert manifest["counts"]["participants"] == 88
    assert len(manifest["files"]) == 3
    assert "88" in result.stdout
    assert validate(destination / "gutbrain")["participants"] == 88


def test_target_catalog() -> None:
    from curated_microbiota_gut_brain_axis._data import TARGET_COLUMNS

    assert gutbrain.targets() == TARGET_COLUMNS
    assert len(gutbrain.targets()) == 32
    assert gutbrain.targets(primary_only=True) == ("Zung_S", "STAI_R", "STAI_S")
    assert gutbrain.target("Zung_S").column == "Zung_S"
    assert gutbrain.target("STAI_R").task == "regression"
    assert gutbrain.target("STAI_S").task == "regression"
    assert gutbrain.target("Parasite").task == "classification"
    assert gutbrain.target("LoE").task == "classification"
    assert gutbrain.target("SES").task == "classification"
    assert gutbrain.target("PA").task == "classification"
    assert gutbrain.target("zung_depression").column == "Zung_S"
    assert collections.available(target="STAI_R") == (gutbrain,)
    assert collections.available(target="Parasite", problem_type="classification") == (gutbrain,)
    assert collections.available(target="STAI_R", problem_type="classification") == ()
    assert collections.available(problem_type="classification") == (gutbrain,)
    assert collections.available(target="unknown") == ()
    with pytest.raises(KeyError, match="unknown"):
        gutbrain.mllabiome(target="unknown")


def test_selectable_targets(sample_data: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CURATED_GUTBRAIN_DATA_DIR", str(sample_data))
    proxy = SimpleNamespace(
        Samples=lambda **kwargs: SimpleNamespace(**kwargs),
        Modality=lambda name, **kwargs: SimpleNamespace(name=name, **kwargs),
        Evaluation=lambda **kwargs: SimpleNamespace(**kwargs),
    )
    monkeypatch.setitem(sys.modules, "mllabiome", SimpleNamespace(mll=proxy))
    for target in ("Zung_S", "STAI_R", "STAI_S", "Age", "Shannon", "Fiber"):
        data = gutbrain.mllabiome(target=target)
        assert data["samples"].target_col == target
        assert data["samples"].task == "regression"
        assert gutbrain.splits(target=target).mllabiome().optimize_metric == "RMSE"
    for target in ("Parasite", "LoE", "SES", "PA"):
        data = gutbrain.mllabiome(target=target)
        assert data["samples"].target_col == target
        assert data["samples"].task == "classification"
        assert gutbrain.splits(target=target).mllabiome().optimize_metric == "log_loss"
    assert gutbrain.mllabiome(target="zung_depression")["samples"].target_col == "Zung_S"


def test_invalid_target_values(sample_data: Path) -> None:
    path = sample_data / "participants.tsv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
        fields = tuple(rows[0])
    rows[0]["STAI_R"] = ""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="STAI_R.*missing"):
        validate(sample_data, target="STAI_R")
    assert validate(sample_data, target="Zung_S")["participants"] == 88
    rows[0]["STAI_R"] = "NaN"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="finite numeric"):
        validate(sample_data, target="STAI_R")
