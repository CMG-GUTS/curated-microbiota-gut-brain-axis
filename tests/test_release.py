from __future__ import annotations

import json
from pathlib import Path

from curated_microbiota_gut_brain_axis import __version__
from curated_microbiota_gut_brain_axis._data import EXPECTED_FEATURES, FILES
from curated_microbiota_gut_brain_axis._fetch import RELEASE_REFS, REPOSITORY, _manifest


def test_release_manifest() -> None:
    root = Path(__file__).resolve().parent.parent
    manifest = _manifest((root / "release-manifest.json").read_bytes())
    assert __version__ == "0.1.0"
    assert manifest["version"] == "gutbrain-v1"
    assert set(manifest["files"]) == set(FILES)
    assert json.loads((root / "release-manifest.json").read_text())["counts"] == {
        "participants": 88,
        **EXPECTED_FEATURES,
    }


def test_public_data_source() -> None:
    assert REPOSITORY == "https://raw.githubusercontent.com/CMG-GUTS/curated-microbiota-gut-brain-axis"
    assert "main" in RELEASE_REFS
    assert "v0.1.0" in RELEASE_REFS
