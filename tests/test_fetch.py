from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from curated_microbiota_gut_brain_axis import _fetch
from curated_microbiota_gut_brain_axis._data import FILES


def test_verified_release(sample_data: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {name: (sample_data / name).read_bytes() for name in FILES}
    manifest = {
        "schema": 1,
        "version": "gutbrain-v1",
        "files": {name: hashlib.sha256(value).hexdigest() for name, value in payload.items()},
    }
    monkeypatch.delenv("CURATED_GUTBRAIN_DATA_DIR", raising=False)
    monkeypatch.setenv("CURATED_GUTBRAIN_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(_fetch, "_get", lambda url: json.dumps(manifest).encode() if url.endswith("release-manifest.json") else payload[url.rsplit("/", 1)[-1]])
    root = _fetch.fetch()
    assert root == tmp_path / "cache" / "gutbrain-v1"
    assert _fetch.cached()
    assert root == _fetch.fetch()
    assert len(list(root.iterdir())) == 4


def test_bad_hash_rejected(sample_data: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {name: (sample_data / name).read_bytes() for name in FILES}
    manifest = {
        "schema": 1,
        "version": "gutbrain-v1",
        "files": {name: "0" * 64 for name in FILES},
    }
    monkeypatch.delenv("CURATED_GUTBRAIN_DATA_DIR", raising=False)
    monkeypatch.setenv("CURATED_GUTBRAIN_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(_fetch, "_get", lambda url: json.dumps(manifest).encode() if url.endswith("release-manifest.json") else payload[url.rsplit("/", 1)[-1]])
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        _fetch.fetch()


def test_override_rejects_missing(sample_data: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CURATED_GUTBRAIN_DATA_DIR", str(tmp_path / "missing"))
    with pytest.raises(FileNotFoundError):
        _fetch.fetch()
    assert not _fetch.cached()


def test_bad_manifest() -> None:
    with pytest.raises(ValueError, match="manifest"):
        _fetch._manifest(b'{"schema": 1, "files": {}}')


def test_download_never_references_mllabiome(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from urllib.error import HTTPError

    addresses = []

    def fail(url: str) -> bytes:
        addresses.append(url)
        raise HTTPError(url, 404, "Not Found", {}, None)

    monkeypatch.delenv("CURATED_GUTBRAIN_DATA_DIR", raising=False)
    monkeypatch.setenv("CURATED_GUTBRAIN_CACHE_DIR", str(tmp_path / "unavailable"))
    monkeypatch.setattr(_fetch, "_get", fail)
    with pytest.raises(RuntimeError, match="curated-microbiota-gut-brain-axis data release"):
        _fetch.fetch()
    assert len(addresses) == len(_fetch.RELEASE_REFS)
    assert all("curated--microbiota-gut-brain-axis" in address for address in addresses)
    assert not any("mllabiome" in address for address in addresses)


def test_unversioned_legacy_cache_not_used(tmp_path: Path, sample_data: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from urllib.error import HTTPError
    import shutil

    root = tmp_path / "cache" / "bootstrap"
    root.mkdir(parents=True)
    for name in FILES:
        shutil.copyfile(sample_data / name, root / name)
    monkeypatch.delenv("CURATED_GUTBRAIN_DATA_DIR", raising=False)
    monkeypatch.setenv("CURATED_GUTBRAIN_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(_fetch, "_get", lambda url: (_ for _ in ()).throw(HTTPError(url, 404, "Not Found", {}, None)))
    assert not _fetch.cached()
    with pytest.raises(RuntimeError, match="data unavailable"):
        _fetch.fetch()


def test_checkout_data_without_cache_override(sample_data: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    project = tmp_path / "checkout"
    root = project / "data" / "gutbrain"
    shutil.copytree(sample_data, root)
    (project / "pyproject.toml").write_text("")
    monkeypatch.setattr(_fetch, "__file__", str(project / "curated_microbiota_gut_brain_axis" / "_fetch.py"))
    monkeypatch.delenv("CURATED_GUTBRAIN_DATA_DIR", raising=False)
    monkeypatch.delenv("CURATED_GUTBRAIN_CACHE_DIR", raising=False)
    monkeypatch.setattr(_fetch, "_get", lambda url: (_ for _ in ()).throw(AssertionError(url)))
    assert _fetch.cached()
    assert _fetch.fetch() == root


def test_explicit_cache_overrides_checkout(sample_data: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    project = tmp_path / "checkout"
    root = project / "data" / "gutbrain"
    shutil.copytree(sample_data, root)
    (project / "pyproject.toml").write_text("")
    monkeypatch.setattr(_fetch, "__file__", str(project / "curated_microbiota_gut_brain_axis" / "_fetch.py"))
    monkeypatch.delenv("CURATED_GUTBRAIN_DATA_DIR", raising=False)
    monkeypatch.setenv("CURATED_GUTBRAIN_CACHE_DIR", str(tmp_path / "cache"))
    payload = {name: (sample_data / name).read_bytes() for name in FILES}
    manifest = {
        "schema": 1,
        "version": "gutbrain-v1",
        "files": {name: hashlib.sha256(value).hexdigest() for name, value in payload.items()},
    }
    monkeypatch.setattr(_fetch, "_get", lambda url: json.dumps(manifest).encode() if url.endswith("release-manifest.json") else payload[url.rsplit("/", 1)[-1]])
    assert not _fetch.cached()
    assert _fetch.fetch() == tmp_path / "cache" / "gutbrain-v1"
    assert _fetch.cached()
