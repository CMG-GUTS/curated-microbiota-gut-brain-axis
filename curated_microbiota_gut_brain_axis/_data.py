from __future__ import annotations

import csv
import math
from pathlib import Path

FILES = (
    "participants.tsv",
    "HEALTHY_COLOMBIA_microbiota_profiles.tsv",
    "brainharmonix_f_mllabiome.tsv",
)

TARGET_COLUMNS = (
    "Age", "Parasite", "LoE", "SES", "PA", "BMI", "WHR", "SDNN_all",
    "RMSSD", "ln_LF_all", "ln_HF_all", "SQ_all", "SQ", "LF", "HF",
    "Zung_S", "STAI_R", "STAI_S", "Kcal", "Prot", "TF", "SatFat",
    "MUF", "Poly_InsFat", "Chol", "Carb", "Fiber", "Chao1",
    "Shannon", "InvSimpson", "FR_rumi_unc", "FR_rumi_fam",
)

PRIMARY_TARGETS = ("Zung_S", "STAI_R", "STAI_S")
CATEGORICAL_TARGETS = frozenset(("Parasite", "LoE", "SES", "PA"))

EXPECTED_FEATURES = {
    "HEALTHY_COLOMBIA_microbiota_profiles.tsv": 670,
    "brainharmonix_f_mllabiome.tsv": 768,
}


def validate(root: Path, target: str = "Zung_S") -> dict[str, int]:
    if target not in TARGET_COLUMNS:
        raise KeyError(target)
    root = Path(root)
    paths = {name: root / name for name in FILES}
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    with paths["participants.tsv"].open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = tuple(reader.fieldnames or ())
        missing = {"participant_id", *TARGET_COLUMNS}.difference(fields)
        if missing:
            raise ValueError(f"Missing GUTBRAIN metadata columns: {', '.join(sorted(missing))}")
        rows = list(reader)
    ids = [str(row["participant_id"]).strip() for row in rows]
    if len(ids) != 88 or len(set(ids)) != len(ids) or any(not item for item in ids):
        raise ValueError("GUTBRAIN must contain 88 unique participants")
    values = [str(row[target] or "").strip() for row in rows]
    if any(not value for value in values):
        raise ValueError(f"GUTBRAIN {target} target values must not be missing")
    if target in CATEGORICAL_TARGETS:
        if len(set(values)) < 2:
            raise ValueError(f"GUTBRAIN {target} must contain at least two classes")
    else:
        for value in values:
            try:
                if not math.isfinite(float(value)):
                    raise ValueError(value)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"GUTBRAIN {target} target values must be finite numeric values") from exc
    stats = {"participants": len(ids)}
    for name, n_features in EXPECTED_FEATURES.items():
        with paths[name].open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle, delimiter="\t")
            header = next(reader, ())
            samples = [value.strip() for value in header[1:]]
            if len(samples) != len(ids) or set(samples) != set(ids) or len(set(samples)) != len(samples):
                raise ValueError(f"{name} does not align with the participant identifiers")
            count = 0
            observed = set()
            for row in reader:
                if len(row) != len(header) or not row[0] or row[0] in observed:
                    raise ValueError(f"Invalid feature matrix in {name}")
                observed.add(row[0])
                count += 1
        if count != n_features:
            raise ValueError(f"{name}: expected {n_features} features, found {count}")
        stats[name] = count
    return stats
