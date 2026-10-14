from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from platformdirs import user_cache_dir

from ._data import FILES, validate

REPOSITORY = "https://raw.githubusercontent.com/CMG-GUTS/curated--microbiota-gut-brain-axis"
RELEASE_REFS = ("v0.1.0", "main")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _get(url: str) -> bytes:
    with urlopen(url, timeout=45) as response:
        return response.read()


def _cache_root() -> Path:
    override = os.environ.get("CURATED_GUTBRAIN_CACHE_DIR")
    return Path(override).expanduser() if override else Path(user_cache_dir("curated-microbiota-gut-brain-axis"))


def _manifest(data: bytes) -> dict[str, object]:
    value = json.loads(data)
    files = value.get("files")
    if value.get("schema") != 1 or not isinstance(files, dict) or set(files) != set(FILES):
        raise ValueError("Invalid GUTBRAIN release manifest")
    if not all(isinstance(files[name], str) and re.fullmatch(r"[a-f0-9]{64}", files[name]) for name in FILES):
        raise ValueError("Invalid GUTBRAIN file digests")
    if not isinstance(value.get("version"), str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value["version"]) or value["version"] in {".", ".."}:
        raise ValueError("Invalid GUTBRAIN version")
    return value


def _valid(root: Path, hashes: dict[str, str] | None = None) -> bool:
    if not all((root / name).is_file() for name in FILES):
        return False
    if hashes is None and (root / ".release-manifest.json").is_file():
        try:
            hashes = dict(_manifest((root / ".release-manifest.json").read_bytes())["files"])
        except (OSError, ValueError, TypeError, KeyError):
            return False
    if hashes and any(_digest((root / name).read_bytes()) != hashes[name] for name in FILES):
        return False
    try:
        validate(root)
    except (OSError, ValueError, StopIteration):
        return False
    return True


def _checkout_data() -> Path | None:
    if os.environ.get("CURATED_GUTBRAIN_CACHE_DIR"):
        return None
    project = Path(__file__).resolve().parent.parent
    root = project / "data" / "gutbrain"
    return root if (project / "pyproject.toml").is_file() and _valid(root) else None


def cached() -> bool:
    override = os.environ.get("CURATED_GUTBRAIN_DATA_DIR")
    if override:
        return _valid(Path(override).expanduser())
    if _checkout_data() is not None:
        return True
    root = _cache_root()
    return any(_valid(folder) for folder in root.iterdir() if folder.is_dir() and (folder / ".release-manifest.json").is_file()) if root.exists() else False


def _download(base: str, root: Path, hashes: dict[str, str] | None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        destination = root / name
        if destination.is_file() and (hashes is None or _digest(destination.read_bytes()) == hashes[name]):
            continue
        data = _get(f"{base}/{name}")
        if hashes is not None and _digest(data) != hashes[name]:
            raise ValueError(f"SHA-256 mismatch: {name}")
        with tempfile.NamedTemporaryFile(dir=root, prefix=".download-", delete=False) as handle:
            temporary = Path(handle.name)
            try:
                handle.write(data)
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        temporary.replace(destination)
    validate(root)
    return root


def fetch() -> Path:
    override = os.environ.get("CURATED_GUTBRAIN_DATA_DIR")
    if override:
        root = Path(override).expanduser().resolve()
        validate(root)
        return root
    checkout = _checkout_data()
    if checkout is not None:
        return checkout
    cache = _cache_root()
    failures = []
    for ref in RELEASE_REFS:
        base = f"{REPOSITORY}/{ref}"
        try:
            remote = _get(f"{base}/release-manifest.json")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            failures.append(f"{ref}: {exc}")
            continue
        manifest = _manifest(remote)
        version = str(manifest["version"])
        hashes = dict(manifest["files"])
        root = cache / version
        if _valid(root, hashes):
            return root
        directory = _download(f"{base}/data/gutbrain", root, hashes)
        (directory / ".release-manifest.json").write_bytes(remote)
        return directory
    for directory in cache.iterdir() if cache.exists() else ():
        if directory.is_dir() and (directory / ".release-manifest.json").is_file() and _valid(directory):
            return directory
    raise RuntimeError(
        "GUTBRAIN data unavailable from the curated-microbiota-gut-brain-axis data release. "
        "Set CURATED_GUTBRAIN_DATA_DIR to a directory containing the three dataset TSV files. "
        + "; ".join(failures)
    )
